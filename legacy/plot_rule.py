# -*- coding: utf-8 -*-
"""大哥规则 vs 改进版 可视化"""
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif']=['Microsoft YaHei','SimHei']; plt.rcParams['axes.unicode_minus']=False

amv=pd.read_csv('0amv_daily_261113.csv',encoding='utf-8-sig',parse_dates=['date'])[['date','close']].rename(columns={'close':'amv'}).sort_values('date')
sh=pd.read_csv('idx_sh000001.csv',parse_dates=['date'])[['date','close']].rename(columns={'close':'sh'})
cy=pd.read_csv('idx_sz399006.csv',parse_dates=['date'])[['date','close']].rename(columns={'close':'cy'})
d=amv.merge(sh,on='date',how='inner').merge(cy,on='date',how='left').sort_values('date').reset_index(drop=True)
d['amv_r']=d.amv.pct_change()

def nav(df,col,entry,mode,param=20,stop=None,cost=2.0):
    px=df[col].values; n=len(df); pos=np.zeros(n); i=0
    while i<n:
        if entry[i]:
            bi=min(i+1,n-1); si=min(bi+param,n-1)
            if stop is not None:
                for j in range(bi+1,si+1):
                    if px[j]/px[bi]-1<=stop: si=j; break
            pos[bi:si]=1; i=si+1
        else: i+=1
    r=np.r_[0,px[1:]/px[:-1]-1]; pnl=pos*r-np.abs(np.diff(np.r_[0,pos]))*cost/10000
    return np.cumprod(1+pnl)

def nav_rule(df,col,exit_th=-0.023,cost=2.0):
    px=df[col].values; ar=df.amv_r.values; n=len(df); pos=np.zeros(n); i=0
    while i<n:
        if not np.isnan(ar[i]) and ar[i]>=0.04:
            bi=min(i+1,n-1); j=bi+1; si=None
            while j<n:
                if not np.isnan(ar[j]) and ar[j]<=exit_th: si=min(j+1,n-1); break
                if j-bi>=250: si=min(j+1,n-1); break
                j+=1
            if si is None: si=n-1
            pos[bi:si]=1; i=si+1
        else: i+=1
    r=np.r_[0,px[1:]/px[:-1]-1]; pnl=pos*r-np.abs(np.diff(np.r_[0,pos]))*cost/10000
    return np.cumprod(1+pnl)

fig=plt.figure(figsize=(15,10))
gs=fig.add_gridspec(2,2,hspace=0.33,wspace=0.2)

for k,(nm,col) in enumerate([('上证指数','sh'),('创业板指','cy')]):
    ax=fig.add_subplot(gs[0,k])
    s=d[d.date>='2016-01-01'].dropna(subset=[col]).reset_index(drop=True)
    ent=(s.amv_r>=0.04).values
    r=s[col].pct_change().fillna(0).values
    ax.plot(s.date, np.cumprod(1+r), lw=1.4, color='#7f8c8d', label='买入持有')
    ax.plot(s.date, nav_rule(s,col), lw=1.6, color='#2980b9', label='大哥规则 4%进 / -2.3%出')
    ax.plot(s.date, nav(s,col,ent,'h',20,-0.03), lw=1.8, color='#c0392b', label='改进版 4%进 / 持20天 / 止损3%')
    ax.set_yscale('log'); ax.grid(alpha=.25); ax.legend(fontsize=8.5)
    ax.set_title(f'{"①" if k==0 else "②"} {nm} 2016-2026 净值对比', fontsize=10)

# ③ 参数网格热力图（上证）
ax=fig.add_subplot(gs[1,0])
s=d[d.date>='2016-01-01'].dropna(subset=['sh']).reset_index(drop=True)
ent=(s.amv_r>=0.04).values
hs=[5,10,15,20,25,30]; zs=[-0.03,-0.05,-0.08,-0.12,None]
M=np.zeros((len(hs),len(zs)))
for i,h in enumerate(hs):
    for j,z in enumerate(zs):
        px=s.sh.values; n=len(s); pos=np.zeros(n); k=0
        while k<n:
            if ent[k]:
                bi=min(k+1,n-1); si=min(bi+h,n-1)
                if z is not None:
                    for m in range(bi+1,si+1):
                        if px[m]/px[bi]-1<=z: si=m; break
                pos[bi:si]=1; k=si+1
            else: k+=1
        r=np.r_[0,px[1:]/px[:-1]-1]; pnl=pos*r-np.abs(np.diff(np.r_[0,pos]))*2/10000
        M[i,j]=pnl.mean()/pnl.std()*np.sqrt(252)
im=ax.imshow(M,cmap='RdYlGn',aspect='auto',vmin=0.3,vmax=1.1)
ax.set_xticks(range(len(zs))); ax.set_xticklabels(['-3%','-5%','-8%','-12%','无'],fontsize=9)
ax.set_yticks(range(len(hs))); ax.set_yticklabels([f'{h}天' for h in hs],fontsize=9)
for i in range(len(hs)):
    for j in range(len(zs)):
        ax.text(j,i,f'{M[i,j]:.2f}',ha='center',va='center',fontsize=9,
                color='white' if M[i,j]>0.8 else 'black')
ax.set_xlabel('硬止损'); ax.set_ylabel('持有天数')
ax.set_title('③ 上证 2016-2026 参数网格（Sharpe）：成片平台，非孤立尖峰', fontsize=10)
plt.colorbar(im,ax=ax,shrink=.85)

# ④ 4% 相当于几倍 sigma
ax=fig.add_subplot(gs[1,1])
yrs=list(range(1995,2030,3)); zs2=[]; fr=[]
for y in yrs:
    ss=d[d.date.dt.year==y]
    if len(ss)<100: continue
    zs2.append(0.04/ss.amv_r.std()); fr.append((ss.amv_r>=0.04).mean()*100)
ax.plot(yrs[:len(zs2)], zs2, 'o-', color='#c0392b', lw=2, label='4% 相当于多少倍 σ（左轴）')
ax.axhline(1, ls='--', color='gray', lw=1)
ax.set_ylabel('4% = ? σ', color='#c0392b'); ax.tick_params(axis='y', labelcolor='#c0392b')
ax2=ax.twinx()
ax2.bar([y+0.6 for y in yrs[:len(fr)]], fr, 1.8, color='#2980b9', alpha=.45, label='触发频率 %（右轴）')
ax2.set_ylabel('触发频率 %', color='#2980b9'); ax2.tick_params(axis='y', labelcolor='#2980b9')
ax.set_title('④ 同一个 4%，从"常态波动"(0.5σ) 变成"极端事件"(1.9σ)', fontsize=10)
ax.grid(alpha=.2)

plt.savefig('rule_result.png',dpi=140,bbox_inches='tight',facecolor='white')
print('saved')
