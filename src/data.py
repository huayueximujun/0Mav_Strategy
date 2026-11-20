# -*- coding: utf-8 -*-
"""数据加载与预处理"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"


def load_amv(path: str | Path | None = None) -> pd.DataFrame:
    """加载活跃市值（0AMV）日线。

    返回列: date, o, h, l, c, amv_ret
    """
    p = Path(path) if path else DATA_DIR / "amv_daily.csv"
    df = pd.read_csv(p, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    df["amv_ret"] = df["c"].pct_change()
    return df


def load_index(name: str, path: str | Path | None = None) -> pd.DataFrame:
    """加载指数日线。

    name: cyb(创业板) / kc50(科创50) / sse(上证)
    返回列: date, close
    """
    files = {"cyb": "index_cyb.csv", "kc50": "index_kc50.csv", "sse": "index_sse.csv"}
    p = Path(path) if path else DATA_DIR / files[name]
    df = pd.read_csv(p, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
    val_col = [c for c in df.columns if c != "date"][0]
    return df.rename(columns={val_col: name})[["date", name]]


def merge_all(start: str = "2016-01-01") -> pd.DataFrame:
    """AMV 与三个指数按交易日对齐。

    返回列: date, o, h, l, c, amv_ret, cyb, kc50, sse
    """
    amv = load_amv()
    out = amv
    for n in ("cyb", "kc50", "sse"):
        out = out.merge(load_index(n), on="date", how="left")
    out = out[out.date >= start].reset_index(drop=True)
    return out
