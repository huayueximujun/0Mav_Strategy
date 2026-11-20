# -*- coding: utf-8 -*-
"""阶段二：数据身份与拼接痕迹诊断"""
import numpy as np
import pandas as pd

pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 300)

df = pd.read_csv(r'./0amv_daily_261113.csv',
                 encoding='utf-8-sig', parse_dates=['date']).sort_values('date').reset_index(drop=True)
df['ret'] = df.close.pct_change()
df['vwap'] = df.amount/df.volume

print('=== 1. close 最大值出现在何时 ===')
imax = df.close.idxmax()
print('max close=%.2f 在 %s' % (df.close.iloc[imax], df.date.iloc[imax].date()))
print(df.loc[max(0, imax-3):imax+3, ['date','open','high','low','close','volume','amount']].to_string(index=False))

print('\n=== 2. 历史锚点日期 ===')
anchors = ['1993-02-16','1994-07-29','1994-08-01','1996-12-11','1999-05-19','2001-06-14',
           '2005-06-06','2007-10-16','2008-10-28','2009-08-04','2015-06-12','2016-01-27',
           '2018-01-24','2019-01-04','2020-03-23','2021-02-18','2022-04-26','2024-02-05',
           '2024-09-30','2025-12-31','2026-11-13']
for d in anchors:
    sub = df[df.date == d]
    if len(sub) == 0:
        print(d, '  (非交易日或缺失)')
    else:
        row = sub.iloc[0]
        print('%s  O=%10.2f H=%10.2f L=%10.2f C=%10.2f  V=%14.0f  A=%18.0f  vwap=%.2f'
              % (d, row.open, row.high, row.low, row.close, row.volume, row.amount, row.vwap))

print('\n=== 3. close 增长率 vs amount/volume 增长率 相关 ===')
g_close = df.close.pct_change()
g_amt = df.amount.pct_change()
g_vol = df.volume.pct_change()
g_vwap = df.vwap.pct_change()
for a, b in [('close', 'amount'), ('close', 'volume'), ('close', 'vwap')]:
    ga = df[a].pct_change(); gb = df[b].pct_change()
    m = (df.date >= '2016-01-01')
    print('%s~%s 收益相关: 全样本 %+.3f  近10年 %+.3f'
          % (a, b, ga.corr(gb), ga[m].corr(gb[m])))

print('\n=== 4. close 的绝对水平 vs 成交额水平（判断是否累积量）===')
for yr in [1993, 1996, 2000, 2005, 2010, 2015, 2020, 2025, 2026]:
    s = df[df.date.dt.year == yr]
    if len(s) == 0: continue
    print('%d: close末=%12.2f  amount末=%18.0f  close/amount=%12.6f  vwap末=%.2f'
          % (yr, s.close.iloc[-1], s.amount.iloc[-1], s.close.iloc[-1]/s.amount.iloc[-1], s.vwap.iloc[-1]))

print('\n=== 5. 年度路径 (每年首末+极值) ===')
g = df.groupby(df.date.dt.year).agg(o=('close','first'), last=('close','last'),
                                    hi=('close','max'), lo=('close','min'), n=('close','size'))
g['年涨幅%'] = (g['last']/g.o-1)*100
print(g.to_string(float_format=lambda x: f'{x:,.2f}'))

print('\n=== 6. 可疑跳空：|隔夜收益| > 15% 的日期 ===')
df['overnight'] = df.open/df.close.shift(1)-1
big = df[df.overnight.abs() > 0.15]
print('共 %d 天，年份分布: %s' % (len(big), big.date.dt.year.value_counts().sort_index().to_dict()))
print(big[['date','close','open','ret']].head(25).to_string(index=False))

print('\n=== 7. 连续性检查：是否有重复片段（拼接）===')
# 用 20 日收益窗口做指纹，找重复
w = df.close.pct_change().rolling(20)
sig = (df.close.pct_change(20)*10000).round(0)
dup = sig[sig.duplicated(keep=False) & sig.notna()]
print('20日收益率重复值个数:', len(dup))
if len(dup):
    print(dup.head(10).to_string())

print('\n=== 8. 2016 年后 close 与 vwap 的比值稳定性 ===')
m = df.date >= '2016-01-01'
ratio = (df.close/df.vwap)[m]
print(ratio.describe().to_string(float_format=lambda x: f'{x:,.1f}'))

print('\n=== 9. 日收益绝对值分布（近年）===')
r = df.ret[m].dropna()
print('2016+ 日收益: 均值%+.4f%% 标准差%.4f%% 最大%+.2f%% 最小%+.2f%%' % (r.mean()*100, r.std()*100, r.max()*100, r.min()*100))
print('分位数:', {f'{q:.0%}': round(r.quantile(q)*100, 2) for q in [0.01,0.05,0.25,0.5,0.75,0.95,0.99]})
