# -*- coding: utf-8 -*-
"""信号定义"""
import numpy as np
import pandas as pd

ENTRY_TH = 0.04      # AMV 单日涨幅阈值
EXIT_TH = -0.023     # 原始规则的出场阈值（仅用于对照）


def amv_surge(df: pd.DataFrame, th: float = ENTRY_TH) -> pd.Series:
    """入场信号：AMV 单日涨幅 >= th。T 日收盘可得。"""
    return (df["amv_ret"] >= th).fillna(False)


def amv_drop(df: pd.DataFrame, th: float = EXIT_TH) -> pd.Series:
    """原始出场信号：AMV 单日跌幅 <= th（对照用）"""
    return (df["amv_ret"] <= th).fillna(False)


def position_bucket(df: pd.DataFrame, col: str = "cyb", window: int = 250) -> pd.Series:
    """距 N 日高点的回撤分档，用于按位置调整仓位。

    返回: 'deep' (<-25%) / 'mid' (-25~-15%) / 'light' (-15~-8%) /
          'high' (-8~-2%) / 'newhigh' (>-2%)
    """
    dd = df[col] / df[col].rolling(window).max() - 1
    return pd.cut(dd, bins=[-1, -0.25, -0.15, -0.08, -0.02, 1],
                  labels=["deep", "mid", "light", "high", "newhigh"])


def amv_percentile(df: pd.DataFrame, window: int = 250) -> pd.Series:
    """AMV 在 N 日区间内的位置（0~1）"""
    lo = df["c"].rolling(window).min()
    hi = df["c"].rolling(window).max()
    return (df["c"] - lo) / (hi - lo)
