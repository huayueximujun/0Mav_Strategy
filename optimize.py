# -*- coding: utf-8 -*-
"""v4.0 优化搜索：参数网格 + 样本内/样本外切分，找稳健平台"""
import numpy as np
import pandas as pd
from itertools import product
from scipy import stats
pd.set_option('display.width', 280)

# ---------------- 数据 ----------------
amv = pd.read_csv('data/amv_daily.csv', parse_dates=['date']).sort_values('date').reset_index(drop=True)
cy = pd.read_csv('data/index_cyb_ohlcv.csv', parse_dates=['date'])
cy.columns = [c.strip().lower() for c in cy.columns]
cy = cy[['date','open','high','low','close']].sort_values('date').reset_index(drop=True)
kc = pd.read_csv('data/index_kc50.csv', parse_dates=['date']).rename(columns={'close':'kc'})
sh = pd.read_csv('data/index_sse.csv', parse_dates=['date']).rename(columns={'close':'sh'})

# 关键：涨跌幅必须在全量 AMV 序列上算，再与指数合并，否则跨缺口计算会改变信号
amv['amv_r'] = amv['c'].pct_change()
amv['amv_sd60'] = amv['amv_r'].rolling(60).std()
d = amv.merge(cy, on='date', how='inner').merge(kc, on='date', how='left').merge(sh, on='date', how='left')
d = d.sort_values('date').reset_index(drop=True)
d['dd250'] = d['close']/d['close'].rolling(250).max() - 1

def build(start='2016-01-01'):
    s = d[d.date >= start].reset_index(drop=True)
    return s

def sim(s, price='close', entry=None, hold=20, stop=-0.03, mode='open_T1',
        pos_weight=None, cost_bp=2.0):
    """mode: open_T1=次日开盘买 / close_T1=次日收盘买"""
    px = s[price].values
    n = len(s)
    sig = entry.values if hasattr(entry, "values") else np.asarray(entry)
    day = np.zeros(n)
    wt = np.ones(n)
    if pos_weight is not None:
        wt = pos_weight.values if hasattr(pos_weight, "values") else np.asarray(pos_weight)
    tr = []
    i = 0
    while i < n:
        if not np.isnan(sig[i]) and sig[i]:
            if mode == 'open_T1':
                if i+1 >= n: break
                buy = s.open.values[i+1]; start = i+1
            else:
                if i+1 >= n: break
                buy = px[i+1]; start = i+2
            end = min(start + hold - 1, n-1); si = end
            for t in range(start, end+1):
                if px[t]/buy - 1 <= stop:
                    si = t; break
            if si < start: si = start
            w = wt[i]
            if mode == 'open_T1':
                day[i+1] = (px[i+1]/buy - 1)*w - cost_bp/10000
                for t in range(i+2, si+1):
                    day[t] = (px[t]/px[t-1]-1)*w - (cost_bp/10000 if t == si else 0)
            else:
                for t in range(start, si+1):
                    day[t] = (px[t]/px[t-1]-1)*w - (cost_bp/10000 if t == si else 0)
            tr.append((s.date.iloc[i+1].date(), s.date.iloc[si].date(), px[si]/buy-1))
            i = si + 1
        else:
            i += 1
    nav = np.cumprod(1+day)
    t = pd.DataFrame(tr, columns=['b','s','r'])
    yrs = n/252
    return dict(年化=(nav[-1]**(1/yrs)-1)*100,
                Sharpe=day.mean()/day.std()*np.sqrt(252) if day.std()>0 else 0,
                回撤=(nav/np.maximum.accumulate(nav)-1).min()*100,
                笔数=len(t), 胜率=(t.r>0).mean()*100 if len(t) else np.nan,
                仓位=(day!=0).mean()*100, 复利=nav[-1], nav=nav, day=day, trades=t)


def mk_entry(kind, th=0.04):
    if kind == 'fixed':
        return (d.amv_r >= th).astype(float)
    if kind == 'zscore':
        return (d.amv_r >= th*d.amv_sd60).astype(float)
    if kind == 'cum3':
        return (d.amv_r.rolling(3).sum() >= th).astype(float)
    raise ValueError


def weight_by_position(mode):
    """按创业板距250日高点分档给仓位"""
    dd = d.dd250
    if mode == 'flat':
        return pd.Series(1.0, index=d.index)
    if mode == 'deep_only':
        return (dd <= -0.25).astype(float)
    if mode == 'tiered':
        w = pd.Series(1.0, index=d.index)
        w[(dd > -0.25) & (dd <= -0.15)] = 0.5
        w[(dd > -0.15) & (dd <= -0.08)] = 0.5
        w[(dd > -0.08) & (dd <= -0.02)] = 0.0
        return w
    raise ValueError


print('='*110)
print('一、参数网格全样本扫描（创业板 2016-2026，T+1 开盘买，含 2bp 成本）')
print('='*110)
s = build('2016-01-01')
idx = s.index
rows = []
for kind, th in [('fixed',0.03),('fixed',0.04),('fixed',0.05),('fixed',0.06),
                 ('zscore',1.2),('zscore',1.5),('zscore',1.8),('zscore',2.0),('zscore',2.5),
                 ('cum3',0.04),('cum3',0.06),('cum3',0.08)]:
    e = mk_entry(kind, th)
    for hold in [10, 15, 20, 30]:
        for stop in [-0.03, -0.05]:
            sub = s.copy()
            sub['e'] = e.values[idx]
            r = sim(sub, entry=sub.e.fillna(0).values, hold=hold, stop=stop, mode='open_T1')
            rows.append(dict(信号=f'{kind}{th}', 持有=hold, 止损=stop, 年化=r['年化'],
                             Sharpe=r['Sharpe'], 回撤=r['回撤'], 笔数=r['笔数'], 胜率=r['胜率']))
g = pd.DataFrame(rows)
print('按 Sharpe 排序 TOP 15:')
print(g.sort_values('Sharpe', ascending=False).head(15).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))
print('\n按年化排序 TOP 8:')
print(g.sort_values('年化', ascending=False).head(8).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*110)
print('二、样本内/样本外切分（防过拟合）')
print('='*110)
print('  样本内 2016-2021，样本外 2022-2026')
rows = []
for kind, th in [('fixed',0.03),('fixed',0.04),('fixed',0.05),('zscore',1.5),('zscore',1.8),('zscore',2.0),('cum3',0.06)]:
    e = mk_entry(kind, th)
    for hold in [15, 20, 30]:
        for stop in [-0.03, -0.05]:
            out = {}
            for lab, st, en in [('IS', '2016-01-01','2021-12-31'), ('OOS','2022-01-01','2026-12-31')]:
                sub = build(st)
                sub = sub[sub.date <= en].reset_index(drop=True)
                eo = e[e.index.isin(sub.index)].values
                sub['e'] = eo
                r = sim(sub, entry=sub.e.fillna(0).values, hold=hold, stop=stop, mode='open_T1')
                out[lab] = r
            rows.append(dict(信号=f'{kind}{th}', 持有=hold, 止损=stop,
                             IS年化=out['IS']['年化'], IS夏普=out['IS']['Sharpe'],
                             OOS年化=out['OOS']['年化'], OOS夏普=out['OOS']['Sharpe'],
                             OOS回撤=out['OOS']['回撤'], OOS笔数=out['OOS']['笔数']))
sp = pd.DataFrame(rows)
sp['稳健'] = (sp.IS夏普 > 0) & (sp.OOS夏普 > 0)
print(sp.sort_values('OOS夏普', ascending=False).head(14).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*110)
print('三、基线 vs 优化候选：全样本 + 样本外')
print('='*110)
cands = [
    ('v3.0 基线 4%/持20/止损3%/满仓', dict(kind='fixed', th=0.04, hold=20, stop=-0.03, wmode='flat')),
    ('A 自适应1.8σ/持20/止损3%/满仓', dict(kind='zscore', th=1.8, hold=20, stop=-0.03, wmode='flat')),
    ('B 3日累计4%/持20/止损3%/满仓', dict(kind='cum3', th=0.04, hold=20, stop=-0.03, wmode='flat')),
    ('C 4%/持20/止损3%/仅深跌区', dict(kind='fixed', th=0.04, hold=20, stop=-0.03, wmode='deep_only')),
    ('D 4%/持20/止损3%/分层仓位', dict(kind='fixed', th=0.04, hold=20, stop=-0.03, wmode='tiered')),
    ('E 1.8σ/持20/止损3%/分层仓位', dict(kind='zscore', th=1.8, hold=20, stop=-0.03, wmode='tiered')),
    ('F 1.8σ/持30/止损5%/分层仓位', dict(kind='zscore', th=1.8, hold=30, stop=-0.05, wmode='tiered')),
    ('G 3日累计4%/持20/止损3%/分层', dict(kind='cum3', th=0.04, hold=20, stop=-0.03, wmode='tiered')),
]
rows = []
for name, cfg in cands:
    e = mk_entry(cfg['kind'], cfg['th']); w = weight_by_position(cfg['wmode'])
    for lab, st, en in [('全样本','2016-01-01','2026-12-31'), ('样本外','2022-01-01','2026-12-31')]:
        sub = build(st); sub = sub[sub.date <= en].reset_index(drop=True)
        sub['e'] = e[e.index.isin(sub.index)].values
        sub['w'] = w[w.index.isin(sub.index)].values
        r = sim(sub, entry=sub.e.fillna(0).values, hold=cfg['hold'], stop=cfg['stop'],
                mode='open_T1', pos_weight=sub.w)
        rows.append(dict(方案=name, 区间=lab, 年化=r['年化'], Sharpe=r['Sharpe'],
                         回撤=r['回撤'], 笔数=r['笔数'], 胜率=r['胜率'], 仓位=r['仓位']))
res = pd.DataFrame(rows)
for lab in ['全样本','样本外']:
    print(f'\n【{lab}】')
    print(res[res.区间==lab].drop(columns='区间').to_string(index=False, float_format=lambda v: f'{v:,.2f}'))
