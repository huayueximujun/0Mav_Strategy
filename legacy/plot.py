# -*- coding: utf-8 -*-
"""生成诊断图表"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

df = pd.read_csv(r'./0amv_daily_261113.csv',
                 encoding='utf-8-sig', parse_dates=['date']).sort_values('date').reset_index(drop=True)
df['ret'] = df.close.pct_change()
df['on'] = df.open/df.close.shift(1)-1
df['id'] = df.close/df.open-1

# 真实上证（2026-11-02 ~ 11-06，来自公开行情）
real_dates = pd.to_datetime(['2026-11-02','2026-11-03','2026-11-04','2026-11-05','2026-11-06'])
real_close = np.array([3638.03, 3608.10, 3686.17, 3689.91, 3649.18])
real_amt = np.array([8474.59, 8108.29, 9532.65, 9797.12, 7726.35])  # 沪市，亿元

fig = plt.figure(figsize=(15, 11))
gs = fig.add_gridspec(3, 2, hspace=0.38, wspace=0.22)

# 1. 全历史对数价
ax = fig.add_subplot(gs[0, :])
ax.plot(df.date, df.close, lw=0.7, color='#c0392b')
ax.set_yscale('log'); ax.set_title('① 0amv close 全历史（对数轴）：1993 年 3.1 → 2026 年 145,790（33 年 4.7 万倍，年化 37%）', fontsize=10)
ax.grid(alpha=0.25)
ax.axhline(3649.18, color='steelblue', ls='--', lw=1)
ax.text(df.date.iloc[100], 4200, '上证当前 3,649 点（参考线）', color='steelblue', fontsize=8)

# 2. 近30日 vs 真实上证（归一化）
ax = fig.add_subplot(gs[1, 0])
sub = df[(df.date>='2026-10-26')&(df.date<='2026-11-06')]
ax.plot(sub.date, sub.close/sub.close.iloc[0]*100, 'o-', color='#c0392b', label='0amv close（归一）')
d5 = df[df.date.isin(real_dates)]
ax.plot(real_dates, real_close/real_close[0]*100, 's-', color='steelblue', label='真实上证（归一）')
ax.set_title('② 同期走势对比：0amv 波动约为上证 2.5–4 倍', fontsize=10)
ax.legend(fontsize=8); ax.grid(alpha=0.25); ax.tick_params(axis='x', rotation=30)

# 3. 成交额验证
ax = fig.add_subplot(gs[1, 1])
lab = ['11/02','11/03','11/04','11/05','11/06']
x = np.arange(5); w = 0.35
real_total = np.array([17837, 17034, 20377, 21179, 16578])  # 两市，新闻口径
data_total = (df[df.date.isin(real_dates)].amount/1e8).values
ax.bar(x-w/2, real_total, w, label='真实两市成交额（新闻）', color='steelblue')
ax.bar(x+w/2, data_total, w, label='文件 amount/1e8', color='#e67e22')
ax.set_xticks(x); ax.set_xticklabels(lab); ax.set_ylabel('亿元')
ax.set_title('③ 成交额完全吻合（误差<0.05%）→ 量能列是真数据', fontsize=10)
ax.legend(fontsize=8); ax.grid(alpha=0.25, axis='y')

# 4. ACF
ax = fig.add_subplot(gs[2, 0])
r = df.ret.dropna().values; r = r-r.mean()
lags = range(1, 26)
acf = [(r[k:]*r[:-k]).mean()/(r*r).mean() for k in lags]
ri = df.id.dropna().values; ri = ri-ri.mean()
acf_i = [(ri[k:]*ri[:-k]).mean()/(ri*ri).mean() for k in lags]
ax.bar(np.array(list(lags))-0.2, acf, 0.4, label='日收益 ACF', color='#c0392b')
ax.bar(np.array(list(lags))+0.2, acf_i, 0.4, label='日内收益 ACF', color='#27ae60')
ci = 1.96/np.sqrt(len(r))
ax.axhspan(-ci, ci, color='gray', alpha=0.18)
ax.set_title('④ 收益自相关：lag1=+0.42（真实 A 股约 +0.03）；灰带=95%白噪声区间', fontsize=10)
ax.legend(fontsize=8); ax.grid(alpha=0.25, axis='y')

# 5. 隔夜/日内波动比演化
ax = fig.add_subplot(gs[2, 1])
df['ratio'] = df.on.rolling(500).std()/df.id.rolling(500).std()
ax.plot(df.date, df.ratio, lw=0.9, color='#8e44ad')
ax.axhline(1, color='gray', ls='--', lw=0.8)
ax.set_title('⑤ 隔夜/日内波动比：3.4（90年代）→ 0.42（现在）——数据口径在漂移', fontsize=10)
ax.grid(alpha=0.25); ax.set_ylim(0, 4)

plt.savefig(r'./diag.png', dpi=140, bbox_inches='tight', facecolor='white')
print('saved diag.png')

# 第二张：动量可交易性 + 波动率
fig2, axes = plt.subplots(2, 2, figsize=(14, 8))

ax = axes[0, 0]
m = df.date >= '2016-01-01'
for name, series, c in [('全日段', df.ret, '#c0392b'), ('日内段', df.id, '#27ae60'), ('隔夜段', df.on, '#2980b9')]:
    pnl = (np.sign(df.ret.shift(1))*series)[m].dropna()
    cum = (1+pnl).cumprod()
    ax.plot(df.date[m][:len(cum)], cum.values, lw=1.1, label=f'{name} S={pnl.mean()/pnl.std()*np.sqrt(252):.2f}', color=c)
ax.set_title('⑥ 1日动量策略累计净值（2016-2026，信号=昨收涨跌）', fontsize=10)
ax.legend(fontsize=8); ax.grid(alpha=0.25); ax.set_yscale('log')

ax = axes[0, 1]
for name, series, c in [('全日段', df.ret, '#c0392b'), ('日内段', df.id, '#27ae60'), ('隔夜段', df.on, '#2980b9')]:
    pnl = (np.sign(df.ret.shift(1))*series)[m].dropna()
    ax.plot(pnl.rolling(250).apply(lambda x: x.mean()/x.std()*np.sqrt(252), raw=True).values, lw=0.9, label=name, color=c)
ax.axhline(0, color='k', lw=0.6)
ax.set_title('⑦ 滚动250日 Sharpe：动量优势全部来自日内段', fontsize=10)
ax.legend(fontsize=8); ax.grid(alpha=0.25); ax.set_ylim(-3, 8)

ax = axes[1, 0]
r10 = df.ret[m].dropna()
ax.plot(r10.abs().rolling(60).mean()*100, lw=0.8, color='#d35400')
ax.set_title('⑧ 绝对收益 60日均值：波动率聚集明显（波动可预测）', fontsize=10)
ax.grid(alpha=0.25)

ax = axes[1, 1]
ax.hist(r10*100, bins=120, range=(-8,8), color='#c0392b', alpha=0.75)
ax.set_title('⑨ 近10年日收益分布：尖峰厚尾，偏度 %.2f' % r10.skew(), fontsize=10)
ax.set_xlabel('日收益 %'); ax.grid(alpha=0.25, axis='y')

plt.tight_layout()
plt.savefig(r'./diag2.png', dpi=140, bbox_inches='tight', facecolor='white')
print('saved diag2.png')
