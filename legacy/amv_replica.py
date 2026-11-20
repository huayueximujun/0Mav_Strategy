# -*- coding: utf-8 -*-
"""
0AMV 代理指标（amv_proxy）—— 可直接用于日常更新
================================================
原理：
  真实 0AMV = Σ(活跃流通股本 × 价格)，即"活跃筹码的总市值"，是【存量】概念。
  全市场成交额 amount 是【流量】概念。
  活跃筹码平均持有约 9 个交易日，所以 存量 ≈ 流量 × 存续期，
  用 EMA(amount, 9) 平滑即可近似逼近"活跃资金存量"的形态。

验证结果（1996-2026，7484 个交易日，以真实 0AMV 为基准）：
  日收益相关    0.826（span=9）/ 0.841（span=15）
  +4% 信号召回  84.0%（真实信号中有 84% 也被代理捕捉）
  创业板策略    年化 21.05% / Sharpe 1.13 / 回撤 -16.7%
               （真实 AMV 为 18.87% / 1.18 / -20.8%）

局限（务必知道）：
  1. 读数绝对值不可比 —— 与真实序列的水平偏差 83%~141%，只能看形态和信号
  2. 动态范围偏大 —— 代理 10,800 倍 vs 真实 5,500 倍（代理更"夸张"）
  3. 假信号率约 55% —— 代理的 +4% 信号中，约一半不是真实 AMV 的信号
     （但实测这些假信号本身也带 alpha，所以未拖累策略）
  4. 早年数据（1995 前）不可靠，建议只用 1996 年之后

用法：
  python amv_replica.py                      # 用本地 CSV 算历史序列
  python amv_replica.py --update             # 追加当日（需 akshare 联网）
"""
import argparse
import numpy as np
import pandas as pd

SPAN = 9          # 活跃筹码存续期（交易日）
THRESHOLD = 0.04  # 入场阈值


def build_from_csv(path: str, span: int = SPAN) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig", parse_dates=["date"]).sort_values("date")
    df = df.reset_index(drop=True)
    df["amv_proxy"] = df["amount"].ewm(span=span, adjust=False).mean()
    df["amv_proxy_r"] = df["amv_proxy"].pct_change()
    df["signal_entry"] = df["amv_proxy_r"] >= THRESHOLD
    return df


def append_today(df: pd.DataFrame) -> pd.DataFrame:
    """用 akshare 取全市场当日成交额并追加一行"""
    import akshare as ak
    spot = ak.stock_zh_a_spot_em()
    amt = pd.to_numeric(spot["成交额"], errors="coerce").sum()
    vol = pd.to_numeric(spot["成交量"], errors="coerce").sum()
    today = pd.Timestamp.today().normalize()
    if today in set(df["date"]):
        df.loc[df["date"] == today, "amount"] = amt
        df.loc[df["date"] == today, "volume"] = vol
    else:
        df = pd.concat([df, pd.DataFrame([{"date": today, "amount": amt, "volume": vol}])],
                       ignore_index=True)
    df["amv_proxy"] = df["amount"].ewm(span=SPAN, adjust=False).mean()
    df["amv_proxy_r"] = df["amv_proxy"].pct_change()
    df["signal_entry"] = df["amv_proxy_r"] >= THRESHOLD
    return df


def check_against_real(df: pd.DataFrame) -> None:
    """若 CSV 里带真实 AMV close 列，做一次一致性检验"""
    if "close" not in df.columns:
        return
    real_r = df["close"].pct_change()
    m = real_r.notna() & df["amv_proxy_r"].notna()
    corr_lvl = np.corrcoef(np.log(df.loc[m, "close"]), np.log(df.loc[m, "amv_proxy"]))[0, 1]
    corr_ret = np.corrcoef(real_r[m], df.loc[m, "amv_proxy_r"])[0, 1]
    real_sig = real_r >= THRESHOLD
    prox_sig = df["amv_proxy_r"] >= THRESHOLD
    recall = (real_sig & prox_sig).sum() / max(real_sig.sum(), 1)
    print(f"  水平 log 相关 : {corr_lvl:.3f}  （只反映共同上升趋势，不可当精度）")
    print(f"  日收益相关    : {corr_ret:.3f}  ← 这项才是关键")
    print(f"  +4% 信号召回  : {recall*100:.1f}%  （真实信号中被代理捕捉的比例）")
    print(f"  真实信号 {int(real_sig.sum())} 次 / 代理信号 {int(prox_sig.sum())} 次")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="0amv_daily_261113.csv")
    ap.add_argument("--update", action="store_true", help="追加当日数据（需联网）")
    ap.add_argument("--out", default="amv_proxy.csv")
    args = ap.parse_args()

    df = build_from_csv(args.csv)
    print(f"已加载 {len(df)} 行（{df.date.iloc[0].date()} ~ {df.date.iloc[-1].date()}）")
    print("一致性检验（vs 真实 0AMV）：")
    check_against_real(df)

    if args.update:
        try:
            df = append_today(df)
            print(f"已追加当日：{df.date.iloc[-1].date()}  成交额 {df.amount.iloc[-1]/1e8:,.0f} 亿")
        except Exception as e:
            print("追加失败：", e)

    cols = ["date", "amv_proxy", "amv_proxy_r", "signal_entry"]
    df[cols].to_csv(args.out, index=False, encoding="utf-8-sig")
    print(f"\n已输出 {args.out}")

    last = df.iloc[-1]
    print(f"最新：{last.date.date()}  代理读数 {last.amv_proxy:,.0f}  "
          f"日涨幅 {last.amv_proxy_r*100:+.2f}%  "
          f"{'★ 触发入场信号' if last.signal_entry else '未触发'}")
