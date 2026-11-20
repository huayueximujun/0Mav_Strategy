# -*- coding: utf-8 -*-
"""数据加载与预处理"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# 各标的日线文件。cyb 含 OHLC（支持开盘买口径），kc50/sse 仅收盘价
FILES = {"cyb": "index_cyb_ohlcv.csv", "kc50": "index_kc50_ohlcv.csv", "sse": "index_sse_ohlcv.csv"}


def load_amv(path: str | Path | None = None) -> pd.DataFrame:
    """活跃市值（0AMV）日线。返回列: date, o, h, l, c, amv_ret, amv_sd60, amv_3d

    注意：amv_ret 必须在全量序列上计算，涨跌幅才有意义（跨缺口计算会失真）。
    """
    p = Path(path) if path else DATA_DIR / "amv_daily.csv"
    df = pd.read_csv(p, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    df["amv_ret"] = df["c"].pct_change()
    df["amv_sd60"] = df["amv_ret"].rolling(60).std()
    df["amv_3d"] = df["amv_ret"].rolling(3).sum()
    return df


def load_index(name: str, path: str | Path | None = None) -> pd.DataFrame:
    """指数日线。返回列: date, <name>, <name>_open（无开盘价时用收盘价占位）"""
    p = Path(path) if path else DATA_DIR / FILES[name]
    df = pd.read_csv(p, parse_dates=["date"])
    df.columns = [c.strip().lower() for c in df.columns]
    # 必须优先取 close 列，否则会把 open 当成收盘价
    val = "close" if "close" in df.columns else [c for c in df.columns if c != "date"][0]
    out = df.rename(columns={val: name})[["date", name]].copy()
    out[f"{name}_open"] = df["open"].values if "open" in df.columns else out[name].values
    return out.sort_values("date").reset_index(drop=True)


def merge_all(start: str = "2016-01-01", names=("cyb", "kc50", "sse")) -> pd.DataFrame:
    """AMV 与指数按交易日对齐。返回: date, o,h,l,c, amv_ret, amv_sd60, amv_3d, 各指数收盘与开盘价"""
    out = load_amv()
    for n in names:
        out = out.merge(load_index(n), on="date", how="left")
    out = out[out.date >= start].reset_index(drop=True)
    return out
