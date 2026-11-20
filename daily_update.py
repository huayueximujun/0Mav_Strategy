# -*- coding: utf-8 -*-
"""每日更新：AMV + 指数 + 全市场成交额 + 策略状态

用法:
    python daily_update.py                # 更新数据并打印当前策略状态
    python daily_update.py --write-xlsx   # 同时覆盖 D:/Compass/_export 的 Excel

前置：
    1. 打开一次指南针（让终端把当日 AMV 写进 day.vdat），然后关闭它
       （day.vdat 路径: D:/Compass/WavMain/ANALYSE/Data/ChinaStk/Z_SK/day.vdat）
    2. 若提示文件被占用，先完全退出指南针终端再跑

数据源：
    AMV        指南针终端 day.vdat（逆向解析，28 字节/根）
    指数       腾讯财经（不限流，日频带成交额）
    全市场成交额  上证综指 + 深证综指 成交额之和（与公开 AMV 文件的 amount 偏差中位 -1.8%）
"""
import argparse
import io
import contextlib
import struct
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
COMPASS_SRC = Path(r"D:/Compass/WavMain/ANALYSE/Data/ChinaStk/Z_SK/day.vdat")
XLSX_OUT = Path(r"D:/Compass/_export/活跃市值_日线历史_1993-2026.xlsx")

INDEX_MAP = {"sz399006": ("cy", "index_cyb_ohlcv.csv"),
             "sh000001": ("sse", "index_sse_ohlcv.csv"),
             "sh000688": ("kc50", "index_kc50_ohlcv.csv")}
MKT_MAP = {"sh000001": "sh", "sz399106": "sz"}


# ---------- 指南针 AMV 解析 ----------
def parse_amv(path: Path) -> pd.DataFrame:
    raw = path.read_bytes()
    bars, p, n = [], 0, len(raw)
    while p < n - 28:
        v = struct.unpack_from("<I", raw, p)[0]
        y, m, dd = v // 10000, (v // 100) % 100, v % 100
        if 1990 <= y <= 2035 and 1 <= m <= 12 and 1 <= dd <= 31:
            o, h, l, c = struct.unpack_from("<4f", raw, p + 4)
            if all(0.01 < x < 10 ** 7 for x in (o, h, l, c)):
                bars.append((v, o, h, l, c)); p += 28; continue
        p += 1
    df = pd.DataFrame(bars, columns=["yyyymmdd", "o", "h", "l", "c"])
    df["date"] = pd.to_datetime(df["yyyymmdd"].astype(str), format="%Y%m%d")
    for c in ["o", "h", "l", "c"]:
        df[c] = df[c].round(2)
    return df[["date", "o", "h", "l", "c"]].sort_values("date").reset_index(drop=True)


def write_xlsx(df: pd.DataFrame) -> None:
    from openpyxl import Workbook
    from openpyxl.chart import LineChart, Reference
    wb = Workbook(); ws = wb.active; ws.title = "活跃市值_日线"
    ws.append(["日期", "开盘", "最高", "最低", "收盘"])
    for _, r in df.iterrows():
        ws.append([r["date"].to_pydatetime(), r["o"], r["h"], r["l"], r["c"]])
    ch = LineChart(); ch.title = "活跃市值 日线（收盘）"; ch.height = 10; ch.width = 30
    ch.add_data(Reference(ws, min_col=5, min_row=1, max_row=1 + len(df)), titles_from_data=True)
    ch.set_categories(Reference(ws, min_col=1, min_row=2, max_row=1 + len(df)))
    ch.legend = None
    ws.add_chart(ch, "G2")
    wb.save(XLSX_OUT)


# ---------- 腾讯源 ----------
def fetch_tx(symbol: str) -> pd.DataFrame:
    import akshare as ak
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        df = ak.index_zh_daily_tx(symbol=symbol)
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"])
    for c in ["amount", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df[["date", "open", "high", "low", "close", "volume", "amount"]].copy()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-xlsx", action="store_true")
    args = ap.parse_args()

    # 1. AMV
    if not COMPASS_SRC.exists():
        sys.exit(f"找不到 {COMPASS_SRC}")
    amv = parse_amv(COMPASS_SRC)
    print(f"[1] AMV 解析: {len(amv)} 行  至 {amv.date.iloc[-1].date()}")
    if args.write_xlsx:
        write_xlsx(amv); print(f"    已写入 {XLSX_OUT}")

    # 2. 指数
    for sym, (col, fname) in INDEX_MAP.items():
        df = fetch_tx(sym)
        df["px"] = df["close"]
        df.to_csv(DATA / fname, index=False, encoding="utf-8-sig")
        print(f"[2] {col:<6} {len(df):>5} 行  至 {df.date.iloc[-1].date()}  收盘 {df.close.iloc[-1]:.2f}")

    # 3. 全市场成交额
    parts = {}
    for sym, nm in MKT_MAP.items():
        df = fetch_tx(sym).set_index("date")
        parts[nm] = df
    idx = sorted(set(parts["sh"].index) | set(parts["sz"].index))
    mkt = pd.DataFrame(index=pd.Index(idx, name="date"))
    mkt["sh_amount"] = parts["sh"]["amount"]; mkt["sz_amount"] = parts["sz"]["amount"]
    mkt["sh_volume"] = parts["sh"]["volume"]; mkt["sz_volume"] = parts["sz"]["volume"]
    mkt["amount"] = mkt.sh_amount + mkt.sz_amount
    mkt["volume"] = mkt.sh_volume + mkt.sz_volume
    mkt = mkt.reset_index().dropna(subset=["amount"]).reset_index(drop=True)
    mkt.to_csv(DATA / "market_amount_daily.csv", index=False, encoding="utf-8-sig")
    print(f"[3] 全市场成交额 {len(mkt)} 行  至 {mkt.date.iloc[-1].date()}  最新 {mkt.amount.iloc[-1]/1e8:,.0f} 亿")

    # 4. 合并 AMV（OHLC 来自指南针，amount/volume 用原值+市场额补）
    old = pd.read_csv(DATA / "amv_daily.csv", parse_dates=["date"])
    m = amv.merge(old[["date", "volume", "amount"]], on="date", how="left")
    m = m.merge(mkt[["date", "amount", "volume"]].rename(columns={"amount": "m_amt", "volume": "m_vol"}),
                on="date", how="left")
    cut = m.loc[m.amount.notna(), "date"].max()
    m["amount"] = m["amount"].where(m["date"] <= cut, m["m_amt"])
    m["volume"] = m["volume"].where(m["date"] <= cut, m["m_vol"])
    m = m[["date", "o", "h", "l", "c", "volume", "amount"]].sort_values("date").reset_index(drop=True)
    m.to_csv(DATA / "amv_daily.csv", index=False, encoding="utf-8-sig")
    print(f"[4] amv_daily.csv: {len(m)} 行  至 {m.date.iloc[-1].date()}  amount 全覆盖 {m.amount.notna().all()}")

    # 5. 策略状态
    import sys as _s
    _s.path.insert(0, str(ROOT))
    from src.data import merge_all
    from src.backtest import run
    df = merge_all("2016-01-01").dropna(subset=["cyb"]).reset_index(drop=True)
    last = df.iloc[-1]
    dd = last.cyb / df.cyb.rolling(250).max().iloc[-1] - 1
    print("\n" + "=" * 62)
    print(f"策略状态 {last['date'].date()}")
    print("=" * 62)
    print(f"  AMV {last['c']:,.2f}  日涨跌 {last['amv_ret']*100:+.2f}%")
    print(f"  距峰值 {last['c']/268357.2188*100-100:+.1f}%   250日分位 "
          f"{(last['c']-df.c.tail(250).min())/(df.c.tail(250).max()-df.c.tail(250).min())*100:.1f}%")
    print(f"  创业板 {last['cyb']:.2f}   距250日高点 {dd*100:+.1f}%")
    print(f"  入场信号(≥+5%): {'已触发' if last['amv_ret']>=0.05 else '未触发'}"
          f"   |  大哥出场信号(≤-2.3%): {'已触发' if last['amv_ret']<=-0.023 else '未触发'}")
    res = run(df, "cyb", entry=(df.amv_ret >= 0.05), hold=20, stop=-0.03, buy_mode="open_T1")
    s = res.stats
    print(f"\n  全样本 年化 {s['年化']:+.2f}%  Sharpe {s['Sharpe']:.2f}  回撤 {s['最大回撤']:.1f}%  "
          f"笔数 {s['笔数']}  胜率 {s['胜率']:.1f}%")
    if len(res.trades):
        lt = res.trades.iloc[-1]
        inpos = lt.sell_date >= last["date"]
        print(f"  当前持仓: {'是' if inpos else '否（空仓）'}"
              + (f"  上次: {lt.buy_date.date()} → {lt.sell_date.date()} {lt.ret*100:+.2f}%" if len(res.trades) else ""))


if __name__ == "__main__":
    main()
