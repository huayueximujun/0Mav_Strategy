# -*- coding: utf-8 -*-
"""0AMV 代理指标

真实 0AMV = Σ(活跃流通股本 × 价格)，是「存量」概念；活跃筹码平均持有约 9 个交易日，
故可用 EMA(全市场成交额, 9) 近似其形态。

验证（1996-2026，以真实序列为基准）：
    日收益相关 0.826   +4% 信号召回 84.0%
局限：
    读数绝对值不可比（偏差 83%~141%）；动态范围偏大；假信号约 55%
    只能用于「今天有没有资金异动」，不能用于分位/位置判断
"""
import numpy as np
import pandas as pd

SPAN = 9
THRESHOLD = 0.04


def build(amount: pd.Series, span: int = SPAN) -> pd.Series:
    """由全市场成交额序列构造代理指标"""
    return amount.ewm(span=span, adjust=False).mean()


def signal(amount: pd.Series, span: int = SPAN, th: float = THRESHOLD) -> pd.Series:
    """代理指标的入场信号"""
    return (build(amount, span).pct_change() >= th).fillna(False)


def validate(real: pd.Series, proxy: pd.Series) -> dict:
    """与真实序列做一致性检验"""
    real_r = real.pct_change()
    prox_r = proxy.pct_change()
    m = real_r.notna() & prox_r.notna()
    sig_r, sig_p = real_r >= THRESHOLD, prox_r >= THRESHOLD
    return dict(
        水平log相关=float(np.corrcoef(np.log(real[m]), np.log(proxy[m]))[0, 1]),
        日收益相关=float(np.corrcoef(real_r[m], prox_r[m])[0, 1]),
        信号召回=float((sig_r & sig_p).sum() / max(sig_r.sum(), 1) * 100),
        真实信号数=int(sig_r.sum()),
        代理信号数=int(sig_p.sum()),
    )
