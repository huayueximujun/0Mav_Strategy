# -*- coding: utf-8 -*-
"""阶段三：断层定位 + 自相关真伪检验"""
import numpy as np
import pandas as pd
from scipy import stats

pd.set_option('display.width', 260)
pd.set_option('display.max_rows', 400)

df = pd.read_csv(r'./0amv_daily_261113.csv',
                 encoding='utf-8-sig', parse_dates=['date']).sort_values('date').reset_index(drop=True)
df['ret'] = df.close.pct_change()
df['overnight'] = df.open/df.close.shift(1)-1
df['intraday'] = df.close/df.open-1
df['gamt'] = df.amount.pct_change()
df['gvol'] = df.volume.pct_change()

def acf1(x):
    x = pd.Series(x).dropna().values
    x = x - x.mean()
    return (x[1:]*x[:-1]).mean()/(x*x).mean()

print('=== 1. 各类收益的 1 阶自相关（判断平滑/伪影）===')
for name, s in [('close 日收益', df.ret), ('隔夜收益 open/prevC', df.overnight),
                ('日内收益 close/open', df.intraday), ('成交额增长率', df.gamt), ('成交量增长率', df.gvol)]:
    print('  %-22s ρ1=%+.3f' % (name, acf1(s)))

print('\n=== 2. 2024 年逐月路径（异常年）===')
s = df[df.date.dt.year == 2024].copy()
s['m'] = s.date.dt.month
print(s.groupby('m').agg(月首=('close','first'), 月末=('close','last'), 最高=('close','max'),
                          最低=('close','min'), n=('close','size')).to_string(float_format=lambda x: f'{x:,.1f}'))

print('\n=== 3. 2026 年逐月路径 ===')
s = df[df.date.dt.year == 2026].copy(); s['m'] = s.date.dt.month
print(s.groupby('m').agg(月首=('close','first'), 月末=('close','last'), 最高=('close','max'),
                          最低=('close','min'), n=('close','size')).to_string(float_format=lambda x: f'{x:,.1f}'))

print('\n=== 4. 2015-06 至 2016-03 逐月 ===')
s = df[(df.date>='2015-06-01')&(df.date<='2016-03-31')].copy(); s['ym']=s.date.dt.to_period('M')
print(s.groupby('ym').agg(月首=('close','first'), 月末=('close','last'), 最高=('close','max'),
                          最低=('close','min'), n=('close','size')).to_string(float_format=lambda x: f'{x:,.1f}'))

print('\n=== 5. 全样本最大单日涨跌幅 TOP20 ===')
top = df.dropna(subset=['ret']).reindex(df.ret.abs().sort_values(ascending=False).index[:20])
print(top[['date','close','ret','volume']].to_string(index=False, float_format=lambda x: f'{x:,.4f}'))

print('\n=== 6. 结构断点：滚动 250 日均值收益的突变（Bai-Perron 简化版）===')
r = df.ret
roll = r.rolling(60).mean()
# 找 |roll 变化| 最大的 20 个点
chg = roll.diff().abs().sort_values(ascending=False)
seen = []
print('  60日均收益突变最大的日期:')
for i in chg.index[:200]:
    if any(abs(i-j) < 120 for j in seen): continue
    seen.append(i)
    print('   %s  close=%9.2f  60日均收益=%+.4f%%' % (df.date.iloc[i].date(), df.close.iloc[i], roll.iloc[i]*100))
    if len(seen) >= 12: break

print('\n=== 7. 分段波动率（250日滚动年化），取每年末 ===')
vol = r.rolling(250).std()*np.sqrt(252)
for yr in range(1994, 2027):
    sub = df[df.date.dt.year == yr]
    if len(sub)==0: continue
    i = sub.index[-1]
    print('  %d年末: 年化波动 %5.1f%%' % (yr, vol.iloc[i]*100), end='')
    if (yr-1993) % 3 == 0: print()
print()

print('\n=== 8. 若把 close 视作"总市值代理"，与成交额的关系 ===')
m = df.date >= '2016-01-01'
sub = df[m]
print('近10年 log(close) 与 log(amount) 相关: %+.3f' % np.corrcoef(np.log(sub.close), np.log(sub.amount))[0,1])
print('近10年 log(close) 与 log(vwap)   相关: %+.3f' % np.corrcoef(np.log(sub.close), np.log(sub.vwap))[0,1])
print('近10年 log(close) 与 log(volume) 相关: %+.3f' % np.corrcoef(np.log(sub.close), np.log(sub.volume))[0,1])

print('\n=== 9. 近10年（2016+）核心统计 ===')
r10 = df.ret[m].dropna()
print('n=%d  日均%+.4f%%  年化%+.2f%%  年化波动%.2f%%  ρ1=%+.3f'
      % (len(r10), r10.mean()*100, r10.mean()*252*100, r10.std()*np.sqrt(252)*100, acf1(r10)))
print('偏度%.3f 峰度%.2f' % (stats.skew(r10), stats.kurtosis(r10, fisher=False)))

print('\n=== 10. 检查 2015 前后是否存在"乘数切换"（用年度振幅比对比真实上证）===')
print('数据年度 high/low 比:')
for yr in [2014,2015,2016,2021,2022,2024,2025,2026]:
    s = df[df.date.dt.year==yr]
    print('  %d: high=%.1f low=%.1f 振幅比=%.2f' % (yr, s.close.max(), s.close.min(), s.close.max()/s.close.min()))
