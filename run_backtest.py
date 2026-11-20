# -*- coding: utf-8 -*-
"""一键复现：v4.0 主策略 + v3.0 对照 + 样本外 + 阈值敏感性

用法:
    python run_backtest.py
"""
import numpy as np
import pandas as pd

from src.data import merge_all
from src.signals import amv_surge, amv_drop, position_bucket
from src.backtest import run, print_stats

pd.set_option("display.width", 200)

ENTRY_V4 = 0.05      # v4.0 阈值
ENTRY_V3 = 0.04      # v3.0 阈值
HOLD, STOP = 20, -0.03


def main():
    df_all = merge_all("2016-01-01")

    print("=" * 74)
    print("一、v4.0 vs v3.0（创业板指 2016-01 ~ 2026-11，T+1 开盘买，含 2bp）")
    print("=" * 74)
    df = df_all.dropna(subset=["cyb"]).reset_index(drop=True)
    for th, lab in [(ENTRY_V3, "v3.0  4%"), (ENTRY_V4, "v4.0  5%")]:
        res = run(df, "cyb", entry=(df.amv_ret >= th), hold=HOLD, stop=STOP, buy_mode="open_T1")
        print_stats(f"  {lab}", res)

    print("\n" + "=" * 74)
    print("二、执行时点（v4.0 5%）")
    print("=" * 74)
    for mode, lab in [("open_T1", "T+1 开盘买（推荐）"), ("close_T1", "T+1 收盘买（保守）")]:
        res = run(df, "cyb", entry=(df.amv_ret >= ENTRY_V4), hold=HOLD, stop=STOP, buy_mode=mode)
        print_stats(f"  {lab}", res)

    print("\n" + "=" * 74)
    print("三、跨标的（v4.0 5%，T+1 开盘买）")
    print("=" * 74)
    for col, nm, start in [("cyb", "创业板 2016-2026", "2016-01-01"),
                           ("kc50", "科创50 2020-2026", "2020-01-01"),
                           ("sse", "上证 2016-2026", "2016-01-01")]:
        s = df_all[(df_all.date >= start)].dropna(subset=[col]).reset_index(drop=True)
        res = run(s, col, entry=(s.amv_ret >= ENTRY_V4), hold=HOLD, stop=STOP, buy_mode="open_T1")
        st = res.stats
        print("  %-20s 年化 %+6.2f%%  Sharpe %.2f  回撤 %6.1f%%  笔数 %2d  胜率 %5.1f%%  仓位 %.0f%%"
              % (nm, st["年化"], st["Sharpe"], st["最大回撤"], st["笔数"], st["胜率"], st["仓位"]))

    print("\n" + "=" * 74)
    print("四、样本外（2022-01 ~ 2026-11）")
    print("=" * 74)
    s = df_all[df_all.date >= "2022-01-01"].dropna(subset=["cyb"]).reset_index(drop=True)
    for th, lab in [(ENTRY_V3, "v3.0  4%"), (ENTRY_V4, "v4.0  5%")]:
        res = run(s, "cyb", entry=(s.amv_ret >= th), hold=HOLD, stop=STOP, buy_mode="open_T1")
        st = res.stats
        print("  %-10s 年化 %+6.2f%%  Sharpe %.2f  回撤 %6.1f%%  笔数 %2d"
              % (lab, st["年化"], st["Sharpe"], st["最大回撤"], st["笔数"]))

    print("\n" + "=" * 74)
    print("五、阈值敏感性（创业板全样本，T+1 开盘买）")
    print("=" * 74)
    rows = []
    for th in [0.03, 0.035, 0.04, 0.045, 0.05, 0.055, 0.06]:
        res = run(df, "cyb", entry=(df.amv_ret >= th), hold=HOLD, stop=STOP, buy_mode="open_T1")
        st = res.stats
        rows.append(dict(阈值=f"{th*100:.1f}%", 年化=st["年化"], Sharpe=st["Sharpe"],
                         回撤=st["最大回撤"], 笔数=st["笔数"], 胜率=st["胜率"]))
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f"{v:,.2f}"))

    print("\n" + "=" * 74)
    print("六、原始规则对照（AMV +4% 进 / -2.3% 出）")
    print("=" * 74)
    res = run(df, "cyb", entry=amv_surge(df, 0.04), exit_sig=amv_drop(df), stop=None, buy_mode="open_T1")
    print_stats("  大哥原版", res)

    print("\n" + "=" * 74)
    print("七、当前状态")
    print("=" * 74)
    last = df.iloc[-1]
    dd = last.cyb / df.cyb.rolling(250).max().iloc[-1] - 1
    print(f"  {last.date.date()}  AMV {last.c:,.2f}  日涨跌 {last.amv_ret*100:+.2f}%")
    print(f"  创业板距 250 日高点 {dd*100:+.1f}%")
    print(f"  入场信号: {'已触发' if last.amv_ret >= ENTRY_V4 else f'未触发（需 ≥+{ENTRY_V4*100:.0f}%，差 {(ENTRY_V4-last.amv_ret)*100:.2f} 个百分点）'}")


if __name__ == "__main__":
    main()
