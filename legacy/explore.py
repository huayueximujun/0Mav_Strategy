# -*- coding: utf-8 -*-
"""0amv_daily 数据探索"""
import numpy as np
import pandas as pd

pd.set_option('display.width', 200)
pd.set_option('display.max_columns', 50)

df = pd.read_csv(r'./0amv_daily_261113.csv',
                 encoding='utf-8-sig', parse_dates=['date'])
df = df.sort_values('date').reset_index(drop=True)

print('=== 1. 基本信息 ===')
print('样本量:', len(df))
print('起始:', df.date.iloc[0].date(), ' 结束:', df.date.iloc[-1].date())
print('跨度:', (df.date.iloc[-1]-df.date.iloc[0]).days/365.25, '年')
print('重复日期:', df.date.duplicated().sum())
print('缺失值:\n', df.isna().sum().to_dict())

# 交易日历特征
wd = df.date.dt.dayofweek.value_counts().sort_index()
print('\n星期分布(0=周一):', wd.to_dict())

print('\n=== 2. OHLC 一致性 ===')
bad1 = (df.high < df[['open','close']].max(axis=1) - 1e-6).sum()
bad2 = (df.low > df[['open','close']].min(axis=1) + 1e-6).sum()
print('high < max(open,close) 的行数:', bad1)
print('low  > min(open,close) 的行数:', bad2)
print('非正值行数:', (df[['open','high','low','close']] <= 0).sum().to_dict())

print('\n=== 3. 价格水平分段 ===')
df['year'] = df.date.dt.year
g = df.groupby('year').agg(close_first=('close','first'), close_last=('close','last'),
                           vol_mean=('volume','mean'), amt_mean=('amount','mean'))
print(g.to_string(float_format=lambda x: f'{x:,.2f}'))

print('\n=== 4. 收益率 ===')
df['ret'] = df.close.pct_change()
r = df.ret.dropna()
print('日收益: 均值 %.6f  标准差 %.6f  年化均值 %.2f%%  年化波动 %.2f%%'
      % (r.mean(), r.std(), r.mean()*252*100, r.std()*np.sqrt(252)*100))
print('最大单日涨: %.2f%% (%s)' % (r.max()*100, df.date.iloc[r.idxmax()+1].date() if r.idxmax()+1 < len(df) else '-'))
print('最大单日跌: %.2f%%' % (r.min()*100))
print('|收益|>20% 的天数:', (r.abs() > 0.20).sum())
print('|收益|>10% 的天数:', (r.abs() > 0.10).sum())
print('|收益|>20% 分布年份:\n', df.loc[r.index[r.abs()>0.20]].date.dt.year.value_counts().sort_index().to_dict())

print('\n=== 5. 分段收益/波动 ===')
for seg, sub in df.groupby(df.date.dt.year//5*5):
    rr = sub.close.pct_change().dropna()
    if len(rr) < 20: continue
    print(f'{int(seg)}-{int(seg)+4}: n={len(rr):5d}  年化收益={rr.mean()*252*100:8.2f}%  年化波动={rr.std()*np.sqrt(252)*100:7.2f}%  期末价={sub.close.iloc[-1]:,.0f}')

print('\n=== 6. 成交额与价格关系 ===')
print(df[['close','volume','amount']].describe().to_string(float_format=lambda x: f'{x:,.2f}'))
df['vwap'] = df.amount/df.volume
print('\n隐含均价 amount/volume 最近5日:\n', df[['date','close','vwap']].tail(5).to_string(index=False))
print('隐含均价/收盘 中位数:', (df.vwap/df.close).median())
