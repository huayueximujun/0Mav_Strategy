# -*- coding: utf-8 -*-
"""当前状态定位：AMV 刚从峰值腰斩 + 250日分位 0%，历史上这种情形之后怎么走"""
import numpy as np
import pandas as pd
from scipy import stats
import akshare as ak
import warnings
warnings.filterwarnings('ignore')
pd.set_option('display.width', 260)

x = pd.read_csv('amv_xlsx_clean.csv', parse_dates=['date']).sort_values('date').reset_index(drop=True)
x['ret'] = x.c.pct_change()
x['pct250'] = (x.c - x.c.rolling(250).min())/(x.c.rolling(250).max()-x.c.rolling(250).min())
x['dd_from_peak'] = x.c/x.c.cummax()-1

# 更新指数
for sym, nm in [('sh000001','sh'), ('sz399006','cy')]:
    try:
        df = ak.index_zh_daily_sina(symbol=sym)
        df['date'] = pd.to_datetime(df['date'])
        df[['date','close']].rename(columns={'close':nm}).to_csv(f'latest_{nm}.csv', index=False, encoding='utf-8-sig')
        print('已更新 %s 至 %s，收盘 %.2f' % (nm, df.date.iloc[-1].date(), df.close.iloc[-1]))
    except Exception as e:
        print(nm, 'FAIL', e)

sh = pd.read_csv('latest_sh.csv', parse_dates=['date'])
cy = pd.read_csv('latest_cy.csv', parse_dates=['date'])
d = x.merge(sh, on='date', how='left').merge(cy, on='date', how='left')

print('\n' + '='*84)
print('一、当前状态快照（2026-11-19）')
print('='*84)
last = d.iloc[-1]
print('  AMV 收盘 %.2f   日涨跌 %+.2f%%' % (last.c, last.ret*100))
print('  距历史峰值（2026-07-01, 268,357）: %+.1f%%' % (last.dd_from_peak*100))
print('  250 日区间分位: %.1f%%' % (last.pct250*100))
print('  连续下跌: 6 天   近 4 日 %+.2f%%' % ((d.c.iloc[-1]/d.c.iloc[-5]-1)*100))
print('  上证 %.2f (%+.2f%%)   创业板 %.2f (%+.2f%%)'
      % (last.sh, (last.sh/d.sh.iloc[-2]-1)*100 if pd.notna(last.sh) else 0,
         last.cy, (last.cy/d.cy.iloc[-2]-1)*100 if pd.notna(last.cy) else 0))

print('\n' + '='*84)
print('二、历史类比：AMV 若从峰值回撤 50% 以上，之后怎么走')
print('='*84)
ev = d[(d.dd_from_peak <= -0.50) & (d.dd_from_peak.shift(1) > -0.50)].dropna(subset=['sh'])
print('  历史上首次跌破「峰值 -50%%」共 %d 次' % len(ev))
rows = []
for i in ev.index:
    if i+60 >= len(d): continue
    rows.append(dict(日期=d.date.iloc[i].date(), AMV=d.c.iloc[i],
                     之后20日_上证=(d.sh.iloc[i+20]/d.sh.iloc[i]-1)*100 if pd.notna(d.sh.iloc[i]) else np.nan,
                     之后60日_上证=(d.sh.iloc[i+60]/d.sh.iloc[i]-1)*100 if pd.notna(d.sh.iloc[i]) else np.nan,
                     之后20日_AMV=(d.c.iloc[i+20]/d.c.iloc[i]-1)*100,
                     之后60日_AMV=(d.c.iloc[i+60]/d.c.iloc[i]-1)*100))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*84)
print('三、历史类比：AMV 250日分位跌破 5% 且前一日 >20%（即"刚砸到区间底"）')
print('='*84)
ev2 = d[(d.pct250 <= 0.05) & (d.pct250.shift(1) > 0.20)].dropna(subset=['sh'])
print('  共 %d 次' % len(ev2))
rows = []
for i in ev2.index:
    if i+60 >= len(d): continue
    rows.append(dict(日期=d.date.iloc[i].date(),
                     之后5日=(d.sh.iloc[i+5]/d.sh.iloc[i]-1)*100,
                     之后20日=(d.sh.iloc[i+20]/d.sh.iloc[i]-1)*100,
                     之后60日=(d.sh.iloc[i+60]/d.sh.iloc[i]-1)*100))
r = pd.DataFrame(rows)
if len(r):
    print(r.to_string(index=False, float_format=lambda v: f'{v:,.2f}'))
    print('\n  统计: 20日均值 %+.2f%% 胜率 %.0f%% | 60日均值 %+.2f%% 胜率 %.0f%%'
          % (r.之后20日.mean(), (r.之后20日>0).mean()*100, r.之后60日.mean(), (r.之后60日>0).mean()*100))

print('\n' + '='*84)
print('四、历史类比：AMV 6 日累计跌幅 ≤ -9%（当前情形）')
print('='*84)
d['r6'] = d.c/d.c.shift(6)-1
ev3 = d[d.r6 <= -0.09].dropna(subset=['sh'])
print('  共 %d 次，其中 2016 年后 %d 次' % (len(ev3), (ev3.date>='2016-01-01').sum()))
for lab, sub in [('全部', ev3), ('2016后', ev3[ev3.date>='2016-01-01'])]:
    if len(sub) < 3: continue
    a20, a60 = [], []
    for i in sub.index:
        if i+60 < len(d):
            a20.append(d.sh.iloc[i+20]/d.sh.iloc[i]-1)
            a60.append(d.sh.iloc[i+60]/d.sh.iloc[i]-1)
    if a20:
        print('  %s: n=%d  之后20日 %+.2f%% (胜率%.0f%%)  60日 %+.2f%% (胜率%.0f%%)'
              % (lab, len(a20), np.mean(a20)*100, (np.array(a20)>0).mean()*100,
                 np.mean(a60)*100, (np.array(a60)>0).mean()*100))

print('\n' + '='*84)
print('五、信号状态：最近一次触发是什么时候，现在处于什么阶段')
print('='*84)
sig = d[d.ret >= 0.04].tail(5)
print('  最近 5 次 AMV ≥+4% 入场信号:')
for _, r_ in sig.iterrows():
    nxt = d[d.date > r_.date].head(20)
    perf = (nxt.c.iloc[-1]/r_.c-1)*100 if len(nxt) else np.nan
    print('    %s  AMV %+6.2f%%   之后20日AMV %+.1f%%' % (r_.date.date(), r_.ret*100, perf))
print('\n  最近 5 次 AMV ≤-2.3% 出场信号:')
for _, r_ in d[d.ret <= -0.023].tail(5).iterrows():
    print('    %s  AMV %+6.2f%%   上证同日 %+.2f%%'
          % (r_.date.date(), r_.ret*100, (r_.sh/d.sh.shift(1).iloc[r_.name]-1)*100 if pd.notna(r_.sh) else np.nan))

print('\n' + '='*84)
print('六、AMV 与指数的背离（近 10 日）')
print('='*84)
d['amv_chg10'] = d.c.pct_change(10)*100
d['cy_chg10'] = d.cy.pct_change(10)*100
d['sh_chg10'] = d.sh.pct_change(10)*100
print(d.tail(10)[['date','c','ret','cy','sh','amv_chg10','cy_chg10','sh_chg10']]
      .to_string(index=False, float_format=lambda v: f'{v:,.2f}'))
print('\n  AMV 10日 %+.2f%%   创业板10日 %+.2f%%   上证10日 %+.2f%%'
      % (d.amv_chg10.iloc[-1], d.cy_chg10.iloc[-1], d.sh_chg10.iloc[-1]))
print('  → %s' % ('资金跌幅 > 指数跌幅，资金先撤（偏空）' if d.amv_chg10.iloc[-1] < d.cy_chg10.iloc[-1]
                  else '资金跌幅 < 指数跌幅，有资金承接（偏多）'))
