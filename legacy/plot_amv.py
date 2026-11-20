# -*- coding: utf-8 -*-
"""AMV 最终图：事件研究路径 + 样本内外 IC"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei','SimHei']
plt.rcParams['axes.unicode_minus'] = False

amv = pd.read_csv('0amv_daily_261113.csv', encoding='utf-8-sig', parse_dates=['date'])
amv = amv[['date','close']].rename(columns={'close':'amv'}).sort_values('date')
sh = pd.read_csv('idx_sh000001.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'sh'})
cy = pd.read_csv('idx_sz399006.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'cy'})
d = amv.merge(sh, on='date', how='inner').merge(cy, on='date', how='left').sort_values('date').reset_index(drop=True)
d['amv_pct'] = (d.amv-d.amv.rolling(250).min())/(d.amv.rolling(250).max()-d.amv.rolling(250).min())

fig = plt.figure(figsize=(15, 9))
gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.2)

# ① 归一化
ax = fig.add_subplot(gs[0,0])
s = d[d.date>='2016-01-01']
for c,lab,col in [('amv','活跃市值 AMV','#c0392b'),('sh','上证指数','#2980b9'),('cy','创业板指','#27ae60')]:
    ax.plot(s.date, s[c]/s[c].iloc[0]*100, lw=1.2, label=lab, color=col)
ax.set_yscale('log'); ax.legend(fontsize=9); ax.grid(alpha=.25)
ax.set_title('① 近10年：AMV 与指数同向，但 AMV 是"资金规模量"（10年3倍），不能当点位看', fontsize=10)

# ② 策略净值
ax = fig.add_subplot(gs[0,1])
ret = s.sh.pct_change()
def bt(sig, r, cost=2.0):
    pos = sig.shift(1).fillna(0)
    pnl = pos*r - pos.diff().abs().fillna(0)*cost/10000
    return (1+pnl.fillna(0)).cumprod()
for sig,lab,col,c in [
    (pd.Series(1,index=s.index),'买入持有 0.94%/年','#7f8c8d',0),
    ((s.sh>s.sh.rolling(20).mean()).astype(float),'指数MA20 -0.53%/年','#2980b9',2),
    ((s.amv>s.amv.rolling(10).mean()).astype(float),'AMV MA10 5.96%/年','#c0392b',2),
    (((s.amv>s.amv.rolling(20).mean())&(s.sh>s.sh.rolling(60).mean())).astype(float),'双确认 3.04%/年 回撤-15%','#8e44ad',2)]:
    nav = bt(sig, ret, c)
    ax.plot(s.date[:len(nav)], nav.values, lw=1.35, label=lab, color=col)
ax.legend(fontsize=8.5); ax.grid(alpha=.25); ax.set_yscale('log')
ax.set_title('② 上证 2016-2026 策略净值（对数，含2bp成本）', fontsize=10)

# ③ 事件研究：AMV 进入低位后的路径
ax = fig.add_subplot(gs[1,0])
for col, lab, cl in [('sh','上证','#c0392b'), ('cy','创业板','#27ae60')]:
    ss = d.dropna(subset=['amv_pct', col]).reset_index(drop=True)
    low = ss.amv_pct < 0.2
    enters = (low & ~low.shift(1).fillna(False)).values
    idx = np.where(enters)[0]
    idx = idx[(idx+61) < len(ss)]
    path = np.array([ (ss[col].values[i:i+61]/ss[col].values[i]-1)*100 for i in idx ])
    base = np.array([ (ss[col].values[i:i+61]/ss[col].values[i]-1)*100 for i in range(len(ss)-61) ])
    ax.plot(range(61), path.mean(0), lw=2, label=f'{lab}：AMV 进入低位后（n={len(idx)}）', color=cl)
    ax.fill_between(range(61), path.mean(0)-path.std(0)/np.sqrt(len(idx)), path.mean(0)+path.std(0)/np.sqrt(len(idx)), alpha=.15, color=cl)
ax.plot(range(61), base.mean(0), ls='--', lw=1.3, color='gray', label='全样本平均（基准）')
ax.axhline(0, color='k', lw=.7); ax.legend(fontsize=8.5); ax.grid(alpha=.25)
ax.set_xlabel('交易日（进入低位后）'); ax.set_ylabel('累计收益 %')
ax.set_title('③ 事件研究：AMV 跌破 250日区间 20% 分位后，上证 60 日 +3.98%（胜率60%）', fontsize=10)

# ④ IC 全样本 vs 近10年
ax = fig.add_subplot(gs[1,1])
labels, ic_all, ic_10 = [], [], []
for N in [5,20,60]:
    for M in [5,20,60]:
        sig = d.amv.pct_change(N); fwd = d.sh.shift(-M)/d.sh-1
        z = pd.concat([sig, fwd, d.date], axis=1).dropna(); z.columns=['s','f','dt']
        labels.append(f'N{N}→M{M}')
        ic_all.append(stats.spearmanr(z.s, z.f)[0])
        z10 = z[z.dt>='2016-01-01']
        ic_10.append(stats.spearmanr(z10.s, z10.f)[0])
x = np.arange(len(labels)); w=0.38
ax.bar(x-w/2, ic_all, w, label='全样本 1993-2026', color='#2980b9', alpha=.85)
ax.bar(x+w/2, ic_10, w, label='近10年 2016-2026', color='#c0392b', alpha=.85)
ax.axhline(0, color='k', lw=.8); ax.axhspan(-0.05, 0.05, color='gray', alpha=.18)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7.5, rotation=45)
ax.set_ylabel('Spearman IC'); ax.legend(fontsize=8.5); ax.grid(alpha=.25, axis='y')
ax.set_title('④ AMV 增速→上证未来收益的 IC：近期转负（AMV 过热→60日回调）', fontsize=10)

plt.savefig('amv_result.png', dpi=140, bbox_inches='tight', facecolor='white')
print('saved')
