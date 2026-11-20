# -*- coding: utf-8 -*-
"""AMV 择时：分段稳健性 + 显著性 + 与指数均线正面对决"""
import numpy as np
import pandas as pd
from scipy import stats
pd.set_option('display.width', 260)

amv = pd.read_csv('0amv_daily_261113.csv', encoding='utf-8-sig', parse_dates=['date'])
amv = amv[['date','close']].rename(columns={'close':'amv'}).sort_values('date')
sh = pd.read_csv('idx_sh000001.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'sh'})
cy = pd.read_csv('idx_sz399006.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'cy'})
d = amv.merge(sh, on='date', how='inner').merge(cy, on='date', how='left').sort_values('date').reset_index(drop=True)

def bt(sig, ret, cost=2.0):
    pos = sig.shift(1).fillna(0)
    pnl = (pos*ret - pos.diff().abs().fillna(0)*cost/10000).dropna()
    if len(pnl) < 120 or pnl.std() == 0: return None
    cum = (1+pnl).cumprod(); yrs = len(pnl)/252
    return dict(年化=(cum.iloc[-1]**(1/yrs)-1)*100, Sharpe=pnl.mean()/pnl.std()*np.sqrt(252),
                回撤=(cum/cum.cummax()-1).min()*100, 仓位=pos.mean()*100, 交易=int(pos.diff().abs().sum()), n=len(pnl))

print('='*90)
print('分段稳健性：每个子区间内，AMV 策略 vs 指数均线策略（年化收益% / Sharpe）')
print('='*90)
segs = [('1996-2005','1996-01-01','2005-12-31'), ('2006-2015','2006-01-01','2015-12-31'),
        ('2016-2026','2016-01-01','2026-12-31')]
for idx_name, col in [('上证','sh')]:
    print('\n【%s】' % idx_name)
    hdr = '  %-10s' % '区间'
    print(hdr + '%16s%16s%16s%16s%16s' % ('买入持有','指数MA20','AMV-MA20','AMV-MA20&指数MA60','AMV增速20>0'))
    for lab, s0, s1 in segs:
        sub = d[(d.date>=s0)&(d.date<=s1)].dropna(subset=[col]).reset_index(drop=True)
        if len(sub) < 200: continue
        ret = sub[col].pct_change()
        defs = [pd.Series(1, index=sub.index),
                (sub[col] > sub[col].rolling(20).mean()).astype(float),
                (sub.amv > sub.amv.rolling(20).mean()).astype(float),
                ((sub.amv > sub.amv.rolling(20).mean()) & (sub[col] > sub[col].rolling(60).mean())).astype(float),
                (sub.amv.pct_change(20) > 0).astype(float)]
        cells = []
        for sg in defs:
            r = bt(sg, ret, 0 if sg is defs[0] else 2)
            cells.append('%5.1f/%.2f' % (r['年化'], r['Sharpe']) if r else '   n/a  ')
        print('  %-10s' % lab + ''.join('%16s' % c for c in cells))

    print('\n【创业板】')
    print('  %-10s' % '区间' + '%16s%16s%16s%16s%16s' % ('买入持有','指数MA20','AMV-MA20','AMV-MA20&指数MA60','AMV增速20>0'))
    for lab, s0, s1 in [('2011-2015','2011-01-01','2015-12-31'), ('2016-2020','2016-01-01','2020-12-31'), ('2021-2026','2021-01-01','2026-12-31')]:
        sub = d[(d.date>=s0)&(d.date<=s1)].dropna(subset=['cy']).reset_index(drop=True)
        if len(sub) < 200: continue
        ret = sub['cy'].pct_change()
        defs = [pd.Series(1, index=sub.index),
                (sub['cy'] > sub['cy'].rolling(20).mean()).astype(float),
                (sub.amv > sub.amv.rolling(20).mean()).astype(float),
                ((sub.amv > sub.amv.rolling(20).mean()) & (sub['cy'] > sub['cy'].rolling(60).mean())).astype(float),
                (sub.amv.pct_change(20) > 0).astype(float)]
        cells = []
        for sg in defs:
            r = bt(sg, ret, 0 if sg is defs[0] else 2)
            cells.append('%5.1f/%.2f' % (r['年化'], r['Sharpe']) if r else '   n/a  ')
        print('  %-10s' % lab + ''.join('%16s' % c for c in cells))

print('\n' + '='*90)
print('近10年（2016-2026）完整指标表')
print('='*90)
for idx_name, col in [('上证','sh'), ('创业板','cy')]:
    sub = d[d.date>='2016-01-01'].dropna(subset=[col]).reset_index(drop=True)
    ret = sub[col].pct_change()
    rows = []
    for nm, sg, c in [
        ('买入持有', pd.Series(1, index=sub.index), 0),
        ('指数MA20', (sub[col] > sub[col].rolling(20).mean()).astype(float), 2),
        ('指数MA60', (sub[col] > sub[col].rolling(60).mean()).astype(float), 2),
        ('AMV-MA10', (sub.amv > sub.amv.rolling(10).mean()).astype(float), 2),
        ('AMV-MA20', (sub.amv > sub.amv.rolling(20).mean()).astype(float), 2),
        ('AMV-MA60', (sub.amv > sub.amv.rolling(60).mean()).astype(float), 2),
        ('AMV增速20>0', (sub.amv.pct_change(20) > 0).astype(float), 2),
        ('AMV&指数MA60', ((sub.amv > sub.amv.rolling(20).mean()) & (sub[col] > sub[col].rolling(60).mean())).astype(float), 2),
        ('背离(AMV20-指数20)', ((sub.amv.pct_change(20) - sub[col].pct_change(20)) > 0).astype(float), 2),
    ]:
        r = bt(sg, ret, c)
        if r: rows.append(dict(策略=nm, **r))
    print('\n【%s】' % idx_name)
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*90)
print('显著性：AMV-MA20 相对买入持有的超额（近10年，日频 t 检验）')
print('='*90)
for idx_name, col in [('上证','sh'), ('创业板','cy')]:
    sub = d[d.date>='2016-01-01'].dropna(subset=[col]).reset_index(drop=True)
    ret = sub[col].pct_change()
    pos = (sub.amv > sub.amv.rolling(20).mean()).astype(float).shift(1).fillna(0)
    ex = (pos*ret).dropna() - ret.mean()
    t, p = stats.ttest_1samp(ex.dropna(), 0)
    print('  %s: 日均超额 %+.4f%%  t=%+.2f  p=%.3f  年化超额 %+.2f%%'
          % (idx_name, ex.mean()*100, t, p, ex.mean()*252*100))

print('\n' + '='*90)
print('AMV 的领先性到底多强：AMV 增速 vs 指数未来收益（近10年）')
print('='*90)
sub = d[d.date>='2016-01-01']
for idx_name, col in [('上证','sh'), ('创业板','cy')]:
    print('\n  【%s】' % idx_name, end='')
    print('   ' + ''.join('   M=%2d ' % M for M in [1,5,20,60]))
    for N in [1,5,20,60,120]:
        sig = sub.amv.pct_change(N)
        row = []
        for M in [1,5,20,60]:
            fwd = sub[col].shift(-M)/sub[col]-1
            x = pd.concat([sig, fwd], axis=1).dropna()
            row.append('%+7.3f' % stats.spearmanr(x.iloc[:,0], x.iloc[:,1])[0] if len(x)>100 else '  n/a ')
        print('   N=%3d' % N + ''.join(row))
