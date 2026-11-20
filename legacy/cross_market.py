# -*- coding: utf-8 -*-
"""AMV 规则跨市场检验：美股 / 创业板 / 科创50 / 上证"""
import numpy as np
import pandas as pd
from scipy import stats
pd.set_option('display.width', 280)

amv = pd.read_csv('0amv_daily_261113.csv', encoding='utf-8-sig', parse_dates=['date'])[['date','close']]
amv = amv.rename(columns={'close':'amv'}).sort_values('date')
amv['amv_r'] = amv.amv.pct_change()

def load(path, name):
    df = pd.read_csv(path, parse_dates=['date'])[['date','close']].rename(columns={'close':name})
    return df.sort_values('date')

tgts = [
    ('上证指数','sh', 'idx_sh000001.csv'),
    ('创业板指','cy', 'idx_sz399006.csv'),
    ('科创50','kc', 'idx_sh000688.csv'),
    ('标普500','spx', 'idx_usINX.csv'),
    ('纳斯达克','ixic', 'idx_usIXIC.csv'),
    ('纳指100','ndx', 'idx_usNDX.csv'),
]

def run(df, col, mode='hold', hold=20, stop=None, entry=0.04, exit_th=-0.023, lag=1, cost=2.0):
    """lag=1: T日信号→T+1收盘执行; lag=0: T日信号→T日收盘执行"""
    px = df[col].values; ar = df.amv_r.values; n = len(df)
    pos = np.zeros(n); trades = []
    i = 0
    while i < n:
        if not np.isnan(ar[i]) and ar[i] >= entry:
            bi = i + lag
            if bi >= n: break
            if mode == 'hold':
                si = min(bi + hold, n-1)
                if stop is not None:
                    for j in range(bi+1, si+1):
                        if px[j]/px[bi]-1 <= stop: si = j; break
            else:  # 原规则：等 AMV 跌到 exit_th
                j = bi + 1; si = None
                while j < n:
                    if not np.isnan(ar[j]) and ar[j] <= exit_th:
                        si = min(j+lag, n-1); break
                    if j-bi >= 250: si = min(j+lag, n-1); break
                    j += 1
                if si is None: si = n-1
            if si <= bi: si = min(bi+1, n-1)
            pos[bi:si] = 1
            trades.append((bi, si))
            i = si + 1
        else:
            i += 1
    r = np.r_[0, px[1:]/px[:-1]-1]
    pnl = pos*r - np.abs(np.diff(np.r_[0,pos]))*cost/10000
    cum = np.cumprod(1+pnl); yrs = n/252
    tr = np.array([px[si]/px[bi]-1 for bi,si in trades]) if trades else np.array([])
    return dict(n=n, 年化=(cum[-1]**(1/yrs)-1)*100, Sharpe=pnl.mean()/pnl.std()*np.sqrt(252),
                回撤=(cum/np.maximum.accumulate(cum)-1).min()*100, 仓位=pos.mean()*100,
                笔数=len(trades), 胜率=(tr>0).mean()*100 if len(tr) else np.nan,
                平均单笔=tr.mean()*100 if len(tr) else np.nan), pnl

def bh(df, col):
    px = df[col].values; n=len(df)
    r = np.r_[0, px[1:]/px[:-1]-1]
    cum = np.cumprod(1+r)
    return dict(n=n, 年化=(cum[-1]**(252/n)-1)*100, Sharpe=r.mean()/r.std()*np.sqrt(252),
                回撤=(cum/np.maximum.accumulate(cum)-1).min()*100, 仓位=100.0,
                笔数=1, 胜率=np.nan, 平均单笔=np.nan), r

print('='*100)
print('A. 各标的数据范围与对齐情况')
print('='*100)
data = {}
for name, key, path in tgts:
    t = load(path, key)
    m = amv.merge(t, on='date', how='inner').sort_values('date').reset_index(drop=True)
    data[key] = (name, m)
    print('  %-8s 原始 %4d 行  %s ~ %s  | 与AMV对齐后 %4d 行  %s ~ %s'
          % (name, len(t), t.date.iloc[0].date(), t.date.iloc[-1].date(),
             len(m), m.date.iloc[0].date(), m.date.iloc[-1].date()))

print('\n' + '='*100)
print('B. 共同区间（2020-01-01 ~ 2026-11-13）：所有标的同台对比')
print('='*100)
rows = []
for name, key, _ in tgts:
    nm, m = data[key]
    s = m[m.date >= '2020-01-01'].reset_index(drop=True)
    if len(s) < 200: continue
    b, rb = bh(s, key)
    r1, _ = run(s, key, mode='hold', hold=20, stop=-0.03, lag=1)
    r2, _ = run(s, key, mode='rule', lag=1)
    rows.append(dict(标的=nm, 样本=len(s),
                     买持年化=b['年化'], 买持Sharpe=b['Sharpe'], 买持回撤=b['回撤'],
                     原规则年化=r2['年化'], 原规则Sharpe=r2['Sharpe'], 原规则笔数=r2['笔数'],
                     改进年化=r1['年化'], 改进Sharpe=r1['Sharpe'], 改进回撤=r1['回撤'], 改进笔数=r1['笔数']))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*100)
print('C. 全样本：每个标的自有最长区间')
print('='*100)
rows = []
for name, key, _ in tgts:
    nm, m = data[key]
    b, _ = bh(m, key)
    r1, _ = run(m, key, mode='hold', hold=20, stop=-0.03, lag=1)
    r2, _ = run(m, key, mode='rule', lag=1)
    rows.append(dict(标的=nm, 起始=str(m.date.iloc[0].date()), 样本=len(m),
                     买持年化=b['年化'], 买持Sharpe=b['Sharpe'], 买持回撤=b['回撤'],
                     原规则年化=r2['年化'], 原规则Sharpe=r2['Sharpe'],
                     改进年化=r1['年化'], 改进Sharpe=r1['Sharpe'], 改进回撤=r1['回撤'], 改进笔数=r1['笔数']))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*100)
print('D. Alpha 检验：策略日收益 - 买入持有日收益（共同区间 2020+）')
print('='*100)
rows = []
for name, key, _ in tgts:
    nm, m = data[key]
    s = m[m.date >= '2020-01-01'].reset_index(drop=True)
    if len(s) < 200: continue
    _, rb = bh(s, key)
    for lab, kw in [('原规则', dict(mode='rule', lag=1)), ('改进版', dict(mode='hold', hold=20, stop=-0.03, lag=1))]:
        st, pnl = run(s, key, **kw)
        ex = pnl - rb
        t, p = stats.ttest_1samp(ex, 0)
        rows.append(dict(标的=nm, 方案=lab, 年化超额=(st['年化']-bh(s,key)[0]['年化']),
                         日均超额bp=ex.mean()*10000, t值=t, p值=p,
                         Sharpe差=st['Sharpe']-bh(s,key)[0]['Sharpe']))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.3f}'))

print('\n' + '='*100)
print('E. 美股：同日执行 vs 滞后一日（判断是真信号还是当日联动）')
print('='*100)
for name, key, _ in tgts:
    if key not in ('spx','ixic','ndx'): continue
    nm, m = data[key]
    s = m[m.date >= '2020-01-01'].reset_index(drop=True)
    if len(s) < 200: continue
    print('\n【%s】' % nm)
    rows=[]
    for lab, lag in [('同日执行(lag=0)', 0), ('滞后一日(lag=1)', 1), ('滞后两日(lag=2)', 2)]:
        r, _ = run(s, key, mode='hold', hold=20, stop=-0.03, lag=lag)
        rr, _ = run(s, key, mode='rule', lag=lag)
        rows.append(dict(执行=lab, 改进年化=r['年化'], 改进Sharpe=r['Sharpe'], 改进笔数=r['笔数'],
                         原规则年化=rr['年化'], 原规则Sharpe=rr['Sharpe']))
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*100)
print('F. 入场信号本身（AMV ≥+4%）在各市场的 20 日表现')
print('='*100)
rows=[]
for name, key, _ in tgts:
    nm, m = data[key]
    s = m[m.date >= '2020-01-01'].reset_index(drop=True)
    if len(s) < 200: continue
    ev = s[s.amv_r >= 0.04].index
    ev = [i for i in ev if i+21 < len(s)]
    if len(ev) < 10: continue
    for N in [5, 10, 20]:
        fwd = np.array([s[key].iloc[i+N]/s[key].iloc[i]-1 for i in ev])
        base = (s[key].pct_change(N).mean())
        rows.append(dict(标的=nm, 期=N, 信号数=len(ev), 事件收益=fwd.mean()*100,
                         胜率=(fwd>0).mean()*100, 无条件基准=base*100, 超额=fwd.mean()*100-base*100))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))
