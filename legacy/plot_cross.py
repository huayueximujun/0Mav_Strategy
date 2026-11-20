# -*- coding: utf-8 -*-
"""跨市场结果可视化"""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif']=['Microsoft YaHei','SimHei']; plt.rcParams['axes.unicode_minus']=False

amv=pd.read_csv('0amv_daily_261113.csv',encoding='utf-8-sig',parse_dates=['date'])[['date','close']].rename(columns={'close':'amv'}).sort_values('date')
amv['amv_r']=amv.amv.pct_change()
def load(p,n):
    d=pd.read_csv(p,parse_dates=['date'])[['date','close']].rename(columns={'close':n}); return d.sort_values('date')

T=[('上证','idx_sh000001.csv','sh'),('创业板','idx_sz399006.csv','cy'),('科创50','idx_sh000688.csv','kc'),
   ('标普500','idx_usINX.csv','spx'),('纳斯达克','idx_usIXIC.csv','ixic'),('纳指100','idx_usNDX.csv','ndx')]

def nav(df,col,lag,hold=20,stop=-0.03,cost=2.0):
    px=df[col].values; ar=df.amv_r.values; n=len(df); pos=np.zeros(n); i=0
    while i<n:
        if not np.isnan(ar[i]) and ar[i]>=0.04:
            bi=min(i+lag,n-1); si=min(bi+hold,n-1)
            if stop is not None:
                for j in range(bi+1,si+1):
                    if px[j]/px[bi]-1<=stop: si=j; break
            pos[bi:si]=1; i=si+1
        else: i+=1
    r=np.r_[0,px[1:]/px[:-1]-1]; pnl=pos*r-np.abs(np.diff(np.r_[0,pos]))*cost/10000
    return np.cumprod(1+pnl)

fig=plt.figure(figsize=(15,9.5))
gs=fig.add_gridspec(2,2,hspace=0.34,wspace=0.22)

# ① A股
ax=fig.add_subplot(gs[0,0])
cols={'上证':'#2980b9','创业板':'#c0392b','科创50':'#8e44ad'}
for nm,p,col in T[:3]:
    d=amv.merge(load(p,col),on='date',how='inner').sort_values('date').reset_index(drop=True)
    s=d[d.date>='2020-01-01'].reset_index(drop=True)
    nv=nav(s,col,1)
    ax.plot(s.date[:len(nv)], nv/nv[0], lw=1.6, color=cols[nm], label=f'{nm} 改进版')
    r=s[col].pct_change().fillna(0).values
    bh=np.cumprod(1+r); ax.plot(s.date, bh/bh[0], lw=1.0, ls='--', color=cols[nm], alpha=.45)
ax.set_yscale('log'); ax.legend(fontsize=8.5, ncol=1); ax.grid(alpha=.25)
ax.set_title('① A股：改进版（实线）vs 买入持有（虚线）  2020-2026', fontsize=10)

# ② 美股
ax=fig.add_subplot(gs[0,1])
cols2={'标普500':'#16a085','纳斯达克':'#d35400','纳指100':'#2c3e50'}
for nm,p,col in T[3:]:
    d=amv.merge(load(p,col),on='date',how='inner').sort_values('date').reset_index(drop=True)
    s=d[d.date>='2020-01-01'].reset_index(drop=True)
    nv=nav(s,col,0)
    ax.plot(s.date[:len(nv)], nv/nv[0], lw=1.6, color=cols2[nm], label=f'{nm} 改进版')
    r=s[col].pct_change().fillna(0).values
    bh=np.cumprod(1+r); ax.plot(s.date, bh/bh[0], lw=1.0, ls='--', color=cols2[nm], alpha=.45)
ax.set_yscale('log'); ax.legend(fontsize=8.5); ax.grid(alpha=.25)
ax.set_title('② 美股：改进版（实线）vs 买入持有（虚线）  2020-2026', fontsize=10)

# ③ 20日超额
ax=fig.add_subplot(gs[1,0])
names=['上证','创业板','科创50','标普500','纳斯达克','纳指100']
exc=[1.61,3.46,3.37,0.12,0.33,0.25]
colors=['#c0392b','#c0392b','#c0392b','#2980b9','#2980b9','#2980b9']
b=ax.bar(range(6),exc,color=colors,alpha=.85)
ax.set_xticks(range(6)); ax.set_xticklabels(names,fontsize=9,rotation=20)
ax.axhline(0,color='k',lw=.8); ax.set_ylabel('AMV≥+4% 后 20 日超额收益 %')
ax.axhspan(-0.2,0.2,color='gray',alpha=.2)
for i,v in enumerate(exc): ax.text(i,v+0.1,f'{v:+.2f}%',ha='center',fontsize=9)
ax.set_title('③ 信号本身的价值：A股 1.6–3.5%，美股 ≈ 0（灰带内）', fontsize=10)
ax.grid(alpha=.25,axis='y')

# ④ 相关性
ax=fig.add_subplot(gs[1,1])
cor=[0.753,0.768,0.730,0.131,0.137,0.137]
b=ax.bar(range(6),cor,color=colors,alpha=.85)
ax.set_xticks(range(6)); ax.set_xticklabels(names,fontsize=9,rotation=20)
ax.axhline(0,color='k',lw=.8); ax.set_ylabel('AMV 日收益 与 该市场日收益 的相关系数')
ax.axhline(0.5,ls='--',color='gray',lw=1)
for i,v in enumerate(cor): ax.text(i,v+0.02,f'{v:.2f}',ha='center',fontsize=9)
ax.set_title('④ 根因：AMV 只反映 A 股资金，与美股相关仅 0.13', fontsize=10)
ax.grid(alpha=.25,axis='y')

plt.savefig('cross_result.png',dpi=140,bbox_inches='tight',facecolor='white')
print('saved')
