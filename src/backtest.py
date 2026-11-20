# -*- coding: utf-8 -*-
"""回测引擎

执行口径（重要）：
    T 日收盘产生信号  →  T+lag 日收盘成交（默认 lag=1，即次日收盘买入）
    持仓 hold 个交易日后到期卖出；期间若浮亏 <= stop 则当日收盘止损
    单边成本 cost_bp（basis point），买入卖出各计一次
"""
from dataclasses import dataclass, field
import numpy as np
import pandas as pd


@dataclass
class Result:
    nav: pd.Series                 # 策略净值
    bench: pd.Series               # 买入持有净值
    trades: pd.DataFrame           # 逐笔交易
    pos: pd.Series                 # 仓位序列
    stats: dict = field(default_factory=dict)


def run(df: pd.DataFrame,
        price_col: str = "cyb",
        entry: pd.Series | None = None,
        exit_sig: pd.Series | None = None,
        hold: int = 20,
        stop: float | None = -0.03,
        lag: int = 1,
        cost_bp: float = 2.0) -> Result:
    """通用回测。

    entry    : 布尔序列，True 表示 T 日收盘触发入场
    exit_sig : 布尔序列；为 None 时只用 hold 到期 + stop 止损
               传入时按"信号出现即离场"处理（对应大哥原版的 AMV -2.3% 出场）
    """
    px = df[price_col].values
    n = len(df)
    sig = (entry if entry is not None else pd.Series(True, index=df.index)).values
    ex = exit_sig.values if exit_sig is not None else None

    pos = np.zeros(n)
    trades = []
    i = 0
    while i < n:
        if not np.isnan(sig[i]) and sig[i]:
            bi = min(i + lag, n - 1)
            if ex is None:
                si = min(bi + hold, n - 1)
                if stop is not None:
                    for j in range(bi + 1, si + 1):
                        if px[j] / px[bi] - 1 <= stop:
                            si = j
                            break
            else:
                j = bi + 1
                si = None
                while j < n:
                    if not np.isnan(ex[j]) and ex[j]:
                        si = min(j + lag, n - 1)
                        break
                    if j - bi >= 250:
                        si = n - 1
                        break
                    j += 1
                if si is None:
                    si = n - 1
            if si <= bi:
                si = min(bi + 2, n - 1)
            pos[bi:si] = 1
            trades.append(dict(sig_date=df["date"].iloc[i], buy_date=df["date"].iloc[bi],
                               sell_date=df["date"].iloc[si],
                               ret=px[si] / px[bi] - 1, days=si - bi))
            i = si + 1
        else:
            i += 1

    r = np.r_[0, px[1:] / px[:-1] - 1]
    pnl = pos * r - np.abs(np.diff(np.r_[0, pos])) * cost_bp / 10000
    nav = (1 + pnl).cumprod()
    bench = (1 + r).cumprod()

    yrs = n / 252
    tr = pd.DataFrame(trades)
    stats = dict(
        年化=(nav[-1] ** (1 / yrs) - 1) * 100,
        基准年化=(bench[-1] ** (1 / yrs) - 1) * 100,
        Sharpe=pnl.mean() / pnl.std() * np.sqrt(252),
        最大回撤=(nav / np.maximum.accumulate(nav) - 1).min() * 100,
        基准回撤=(bench / np.maximum.accumulate(bench) - 1).min() * 100,
        笔数=len(tr),
        胜率=(tr.ret > 0).mean() * 100 if len(tr) else np.nan,
        平均单笔=tr.ret.mean() * 100 if len(tr) else np.nan,
        平均持仓=tr.days.mean() if len(tr) else np.nan,
        仓位=pos.mean() * 100,
    )
    return Result(nav=pd.Series(nav, index=df["date"]), bench=pd.Series(bench, index=df["date"]),
                  trades=tr, pos=pd.Series(pos, index=df["date"]), stats=stats)


def print_stats(name: str, res: Result) -> None:
    s = res.stats
    print(f"{name}")
    print(f"  年化 {s['年化']:+.2f}%  (买入持有 {s['基准年化']:+.2f}%)   Sharpe {s['Sharpe']:.2f}")
    print(f"  最大回撤 {s['最大回撤']:.1f}%  (买入持有 {s['基准回撤']:.1f}%)   仓位 {s['仓位']:.0f}%")
    print(f"  交易 {s['笔数']} 笔   胜率 {s['胜率']:.1f}%   平均单笔 {s['平均单笔']:+.2f}%   平均持仓 {s['平均持仓']:.1f} 天")
