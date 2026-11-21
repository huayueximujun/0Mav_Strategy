# -*- coding: utf-8 -*-
"""中证2000 / 国证2000 小盘风格的 AMV 策略回测

规则 v4.0：AMV 单日 >=+5% (T日收盘确认) -> T+1 开盘买 -> 持 20 交易日 -> 浮亏 -3% 止损
对照：创业板同窗口 + 中证2000ETF 563300 (实盘标的, 2023-09 起)
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from src.backtest import run

pd.set_option("display.width", 220)


def build(index_csv: str, col: str, start: str) -> pd.DataFrame:
    amv = pd.read_csv("data/amv_daily.csv", parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    # amv_ret 必须在全量序列上算
    amv["amv_ret"] = amv["c"].pct_change()
    idx = pd.read_csv(index_csv, parse_dates=["date"])
    idx.columns = [c.strip().lower() for c in idx.columns]
    idx = idx[["date", "open", "high", "low", "close"]].copy()
    d = amv.merge(idx, on="date", how="inner").sort_values("date").reset_index(drop=True)
    d[col] = d["close"]
    d[col + "_open"] = d["open"]
    d = d[d.date >= start].reset_index(drop=True)
    return d


def bt(d, col, th, hold=20, stop=-0.03, start=None):
    s = d if start is None else d[d.date >= start].reset_index(drop=True)
    return run(s, col, entry=(s.amv_ret >= th), hold=hold, stop=stop, buy_mode="open_T1")


def row(name, res):
    s = res.stats
    return dict(方案=name, 年化=s["年化"], Sharpe=s["Sharpe"], 回撤=s["最大回撤"],
                笔数=s["笔数"], 胜率=s["胜率"], 平均单笔=s["平均单笔"], 仓位=s["仓位"], 复利=s["复利"])


# ============ 1) 国证2000 长历史（2014-2026，12.6年） ============
d = build("data/index_gz2000_ohlcv.csv", "gz2000", "2014-04-01")
print("=" * 104)
print("1) 国证2000指数 (2014-04 ~ 2026-11, %.1f 年, 与中证2000同风格) 日波动 σ=%.2f%%"
      % (len(d) / 252, d.gz2000.pct_change().std() * 100))
print("=" * 104)
rows = []
_bh = run(d, "gz2000", entry=pd.Series(False, index=d.index))
rows.append(dict(方案="买入持有", 年化=_bh.stats["基准年化"], Sharpe=np.nan,
                 回撤=_bh.stats["基准回撤"], 笔数=np.nan, 胜率=np.nan, 平均单笔=np.nan, 仓位=100, 复利=np.nan))
for th in [0.04, 0.05]:
    for stop, sl in [(-0.03, "止损3%"), (-0.05, "止损5%"), (-0.08, "止损8%")]:
        rows.append(row(f"AMV≥{th*100:.0f}% / 持20 / {sl}", bt(d, "gz2000", th, stop=stop)))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:,.2f}"))

# ============ 2) 样本外（2022 起） ============
print()
print("=" * 104)
print("2) 样本外检验 (2022-01 ~ 2026-11)")
print("=" * 104)
rows2 = []
_s22 = d[d.date >= "2022-01-01"].reset_index(drop=True)
_bh2 = run(_s22, "gz2000", entry=pd.Series(False, index=_s22.index))
rows2.append(dict(方案="买入持有", 年化=_bh2.stats["基准年化"], Sharpe=np.nan,
                  回撤=_bh2.stats["基准回撤"], 笔数=np.nan, 胜率=np.nan, 平均单笔=np.nan, 复利=np.nan))
for th in [0.04, 0.05]:
    for stop in [-0.03, -0.05]:
        rows2.append(row(f"AMV≥{th*100:.0f}% / 止损{stop*100:.0f}%",
                         bt(d, "gz2000", th, stop=stop, start="2022-01-01")))
print(pd.DataFrame(rows2).to_string(index=False, float_format=lambda v: f"{v:,.2f}"))

# ============ 3) 中证2000ETF 563300（实盘标的，2023-09 起） ============
d3 = build("data/etf_sh563300.csv", "etf2k", "2023-09-14")
print()
print("=" * 104)
print("3) 中证2000ETF 563300 (2023-09 ~ 2026-11, %.1f 年) 日波动 σ=%.2f%%"
      % (len(d3) / 252, d3.etf2k.pct_change().std() * 100))
print("=" * 104)
_bh3 = run(d3, "etf2k", entry=pd.Series(False, index=d3.index))
rows3 = [dict(方案="买入持有", 年化=_bh3.stats["基准年化"], Sharpe=np.nan,
              回撤=_bh3.stats["基准回撤"], 笔数=np.nan, 胜率=np.nan, 平均单笔=np.nan, 仓位=100, 复利=np.nan)]
for th in [0.04, 0.05]:
    for stop in [-0.03, -0.05]:
        rows3.append(row(f"AMV≥{th*100:.0f}% / 止损{stop*100:.0f}%", bt(d3, "etf2k", th, stop=stop)))
print(pd.DataFrame(rows3).to_string(index=False, float_format=lambda v: f"{v:,.2f}"))

# ============ 4) 与创业板同窗口对照 ============
dcy = build("data/index_cyb_ohlcv.csv", "cyb", "2014-04-01")
print()
print("=" * 104)
print("4) 同窗口对照：创业板指 (2014-04 ~ 2026-11)")
print("=" * 104)
rows4 = []
for col, nm in [("gz2000", "国证2000"), ("cyb", "创业板")]:
    dd = d if col == "gz2000" else dcy
    rows4.append(row(f"{nm} AMV≥5%/止损3%", bt(dd, col, 0.05, stop=-0.03)))
    rows4.append(row(f"{nm} AMV≥5%/止损5%", bt(dd, col, 0.05, stop=-0.05)))
print(pd.DataFrame(rows4).to_string(index=False, float_format=lambda v: f"{v:,.2f}"))

# ============ 5) 相关性与信号质量 ============
print()
print("=" * 104)
print("5) AMV 与各标的日收益相关性 + 信号事件研究")
print("=" * 104)
for dd, col, nm in [(d, "gz2000", "国证2000"), (dcy, "cyb", "创业板")]:
    s = dd.dropna(subset=[col])
    print("  AMV日收益 ~ %s日收益 相关 %+.3f" % (nm, s.amv_ret.corr(s[col].pct_change())))
# 位置分层事件研究（国证2000）
sig = d[d.amv_ret >= 0.05].dropna(subset=["gz2000"])
hi = d.gz2000.rolling(250).max()
dd250 = d.gz2000 / hi - 1
sig_pos = sig.copy()
sig_pos["dd250"] = dd250[sig.index]
print()
print("  AMV≥+5%% 信号时国证2000的位置（距250日高点）:")
for lo, hi_, lab in [(-1.0, -0.25, "深跌<-25%"), (-0.25, -0.15, "中度"), (-0.15, -0.08, "轻度"),
                     (-0.08, -0.02, "近高点"), (-0.02, 1.0, "创新高附近")]:
    g = sig_pos[(sig_pos.dd250 >= lo) & (sig_pos.dd250 < hi_)]
    if len(g) < 3:
        continue
    r20 = [d.gz2000.iloc[i + 20] / d.gz2000.iloc[i] - 1 for i in g.index if i + 20 < len(d)]
    print("    %-12s n=%2d  20日 %+.2f%%  胜率 %.0f%%" % (lab, len(g), np.mean(r20) * 100, (np.array(r20) > 0).mean() * 100))
