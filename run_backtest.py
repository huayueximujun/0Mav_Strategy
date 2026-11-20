# -*- coding: utf-8 -*-
"""一键复现：核心回测 + 位置分层 + 执行时点对比"""
import numpy as np
import pandas as pd

from src.data import merge_all
from src.signals import amv_surge, amv_drop, position_bucket
from src.backtest import run, print_stats

pd.set_option("display.width", 200)


def main():
    print("=" * 72)
    print("一、主策略：AMV 单日 ≥+4% 入场 / 持 20 天 / 止损 -3%")
    print("=" * 72)
    for name, col, start in [("创业板指", "cyb", "2016-01-01"),
                             ("科创50", "kc50", "2020-01-01"),
                             ("上证指数", "sse", "2016-01-01")]:
        df = merge_all(start).dropna(subset=[col]).reset_index(drop=True)
        res = run(df, col, entry=amv_surge(df))
        print_stats(f"【{name}】{df.date.iloc[0].date()} ~ {df.date.iloc[-1].date()}", res)
        print()

    print("=" * 72)
    print("二、原始规则对照：AMV ≤-2.3% 出场（不加时间窗口与止损）")
    print("=" * 72)
    df = merge_all("2016-01-01").dropna(subset=["cyb"]).reset_index(drop=True)
    res_raw = run(df, "cyb", entry=amv_surge(df), exit_sig=amv_drop(df), stop=None)
    print_stats("【创业板指】大哥原版", res_raw)

    print("\n" + "=" * 72)
    print("三、执行时点对比（差一天差 22 个点）")
    print("=" * 72)
    rows = []
    for lag, lab in [(0, "T 日收盘买（偏乐观）"), (1, "T+1 收盘买（回测口径）"), (2, "T+2 收盘买")]:
        r = run(df, "cyb", entry=amv_surge(df), lag=lag).stats
        rows.append(dict(执行=lab, 年化=r["年化"], Sharpe=r["Sharpe"], 笔数=r["笔数"]))
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:,.2f}"))

    # 信号日当天指数涨幅
    sig_days = df[amv_surge(df)]
    r0 = df.set_index("date").cyb.pct_change().reindex(sig_days.date).dropna()
    print(f"\n  信号日当天创业板涨幅：均值 {r0.mean()*100:+.2f}%  中位 {r0.median()*100:+.2f}%  "
          f"上涨占比 {(r0>0).mean()*100:.0f}%")
    print("  → 这就是 lag0 与 lag1 差距的来源")

    print("\n" + "=" * 72)
    print("四、按位置分层（反转逻辑在哪里有效）")
    print("=" * 72)
    df["bucket"] = position_bucket(df, "cyb")
    sig = df[amv_surge(df)].dropna(subset=["bucket"])
    labels = {"deep": "深度回撤 <-25%", "mid": "中度 -25~-15%", "light": "轻度 -15~-8%",
              "high": "近高点 -8~-2%", "newhigh": "创新高附近"}
    rows = []
    for k, lab in labels.items():
        s = sig[sig.bucket == k]
        if len(s) < 3:
            continue
        r20 = [(df.cyb.iloc[i + 20] / df.cyb.iloc[i] - 1) for i in s.index if i + 20 < len(df)]
        rows.append(dict(位置=lab, 信号数=len(s),
                         后20日均值=np.mean(r20) * 100 if r20 else np.nan,
                         后20日胜率=(np.array(r20) > 0).mean() * 100 if r20 else np.nan))
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:,.2f}"))

    print("\n" + "=" * 72)
    print("五、当前状态")
    print("=" * 72)
    last = df.iloc[-1]
    dd = last.cyb / df.cyb.rolling(250).max().iloc[-1] - 1
    print(f"  {last.date.date()}  AMV {last.c:,.2f}  日涨跌 {last.amv_ret*100:+.2f}%")
    print(f"  创业板距 250 日高点 {dd*100:+.1f}%   分档 {last.bucket}")
    print(f"  距入场阈值还差 {(0.04 - last.amv_ret)*100:.2f} 个百分点")


if __name__ == "__main__":
    main()
