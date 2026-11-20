# -*- coding: utf-8 -*-
"""AMV：事件研究 vs 持续持有 + 样本内外 IC 对比"""
import numpy as np
import pandas as pd
from scipy import stats
pd.set_option('display.width', 240)

amv = pd.read_csv('0amv_daily_261113.csv', encoding='utf-8-sig', parse_dates=['date'])
amv = amv[['date','close']].rename(columns={'close':'amv'}).sort_values('date')
sh = pd.read_csv('idx_sh000001.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'sh'})
cy = pd.read_csv('idx_sz399006.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'cy'})
d = amv.merge(sh, on='date', how='inner').merge(cy, on='date', how='left').sort_values('date').reset_index(drop=True)
d['amv_pct'] = (d.amv-d.amv.rolling(250).min())/(d.amv.rolling(250).max()-d.amv.rolling(250).min())

print('='*78)
print('A. 事件研究 vs 持续持有：AMV 分位<20% 的两种用法')
print('='*78)
for nm, col in [('上证','sh'), ('创业板','cy')]:
    s = d.dropna(subset=['amv_pct', col]).copy()
    low = s.amv_pct < 0.2
    print('\n【%s】处于"AMV 250日低位"的天数: %d (%.1f%%)' % (nm, low.sum(), low.mean()*100))
    # 事件：进入低位后 N 日
    enters = low & ~low.shift(1).fillna(False)
    for N in [5, 10, 20, 60]:
        fwd = s[col].shift(-N)/s[col]-1
        ev = fwd[enters].dropna()
        if len(ev) < 10: continue
        t, p = stats.ttest_1samp(ev, 0)
        print('   进入低位后 %2d 日: 均值 %+.2f%%  中位 %+.2f%%  胜率 %.2f  n=%d  t=%+.2f'
              % (N, ev.mean()*100, ev.median()*100, (ev>0).mean(), len(ev), t))
    # 持续持有
    r = s[col].pct_change()
    hold = low.shift(1).fillna(False)
    ph = r[hold].dropna()
    print('   ★ 持续持有(只要在低位就一直拿): 日均 %+.4f%%  年化 %+.2f%%  胜率 %.3f'
          % (ph.mean()*100, ph.mean()*252*100, (ph>0).mean()))

print('\n' + '='*78)
print('B. IC 样本内外对比：AMV 增速 → 指数未来收益')
print('='*78)
rows = []
for nm, col in [('上证','sh'), ('创业板','cy')]:
    for N in [5, 20, 60]:
        for M in [5, 20, 60]:
            sig = d.amv.pct_change(N); fwd = d[col].shift(-M)/d[col]-1
            z = pd.concat([sig, fwd, d.date], axis=1).dropna()
            z.columns = ['s','f','dt']
            ic_all = stats.spearmanr(z.s, z.f)[0]
            z10 = z[z.dt >= '2016-01-01']
            ic_10 = stats.spearmanr(z10.s, z10.f)[0] if len(z10) > 100 else np.nan
            rows.append(dict(指数=nm, AMV窗口=N, 预测期=M, IC全样本=ic_all, IC近10年=ic_10))
r = pd.DataFrame(rows)
piv = r.pivot_table(index=['指数','AMV窗口'], columns='预测期', values=['IC全样本','IC近10年'])
print(piv.to_string(float_format=lambda v: f'{v:+.3f}'))

print('\n' + '='*78)
print('C. 双确认策略为何能降回撤：仓位与波动的关系')
print('='*78)
s = d[d.date>='2016-01-01']
for nm, col in [('上证','sh'), ('创业板','cy')]:
    r = s[col].pct_change()
    sig = ((s.amv>s.amv.rolling(20).mean()) & (s[col]>s[col].rolling(60).mean())).astype(float).shift(1)
    on = r[sig==1].dropna(); off = r[sig==0].dropna()
    print('%s: 持仓日 n=%4d 日均%+.4f%% σ=%.3f%% | 空仓日 n=%4d 日均%+.4f%% σ=%.3f%%'
          % (nm, len(on), on.mean()*100, on.std()*100, len(off), off.mean()*100, off.std()*100))
    print('   信号对次日涨跌的辨别力: 持仓日胜率 %.3f vs 空仓日胜率 %.3f (基准 %.3f)'
          % ((on>0).mean(), (off>0).mean(), (r.dropna()>0).mean()))
