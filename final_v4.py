# -*- coding: utf-8 -*-
"""v4.0 定稿：完整指标 + 图表"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei','SimHei']
plt.rcParams['axes.unicode_minus'] = False

amv = pd.read_csv('data/amv_daily.csv', parse_dates=['date']).sort_values('date').reset_index(drop=True)
amv['amv_r'] = amv['c'].pct_change()
amv['amv_sd60'] = amv['amv_r'].rolling(60).std()

def prep(path, col):
    df = pd.read_csv(path, parse_dates=['date'])
    df.columns = [c.strip().lower() for c in df.columns]
    df = df[['date','open','high','low','close']].copy()
    df['px'] = df['close']; df[col] = df['close']
    return df.sort_values('date').reset_index(drop=True)

cy = prep('data/index_cyb_ohlcv.csv', 'cy')
kc = prep('data/index_kc50_ohlcv.csv', 'kc')
sh = prep('data/index_sse_ohlcv.csv', 'sh')

def build(tgt, start='2016-01-01'):
    a = amv.merge(tgt, on='date', how='inner').sort_values('date').reset_index(drop=True)
    a = a[a.date >= start].reset_index(drop=True)
    a['dd250'] = a['px']/a['px'].rolling(250).max() - 1
    return a

def sim(s, entry, hold=20, stop=-0.03, cost_bp=2.0):
    px = s['px'].values; op = s['open'].values; n = len(s)
    sig = entry.values if hasattr(entry, 'values') else np.asarray(entry)
    day = np.zeros(n); tr = []; i = 0
    while i < n:
        if not np.isnan(sig[i]) and sig[i]:
            if i+1 >= n: break
            buy = op[i+1]; t0 = i+1
            last = min(t0+hold-1, n-1); si = last
            for t in range(t0, last+1):
                if px[t]/buy-1 <= stop: si = t; break
            if si < t0: si = t0
            day[i+1] = (px[i+1]/buy-1) - cost_bp/10000
            for t in range(i+2, si+1):
                day[t] = (px[t]/px[t-1]-1) - (cost_bp/10000 if t == si else 0)
            tr.append((s.date.iloc[i+1].date(), s.date.iloc[si].date(), px[si]/buy-1, si-i))
            i = si + 1
        else: i += 1
    nav = np.cumprod(1+day); tt = pd.DataFrame(tr, columns=['b','s','r','d'])
    yrs = n/252
    return dict(年化=(nav[-1]**(1/yrs)-1)*100,
                Sharpe=day.mean()/day.std()*np.sqrt(252),
                回撤=(nav/np.maximum.accumulate(nav)-1).min()*100,
                笔数=len(tt), 胜率=(tt.r>0).mean()*100, 平均单笔=tt.r.mean()*100,
                平均持仓=tt.d.mean(), 仓位=(day!=0).mean()*100, 复利=nav[-1],
                nav=nav, day=day, trades=tt)

print('='*104)
print('v4.0 定稿指标')
print('='*104)
for nm, tgt, col, st, th in [('创业板 2016-2026', cy, 'cy', '2016-01-01', 0.05),
                              ('科创50 2020-2026', kc, 'kc', '2020-01-01', 0.05),
                              ('上证 2016-2026', sh, 'sh', '2016-01-01', 0.05)]:
    s = build(tgt, st)
    for thr, lab in [(0.04, '4%'), (0.05, '5%')]:
        e = (s.amv_r >= thr).astype(float)
        r = sim(s, e)
        print('  %-16s 阈值%-4s 年化 %+6.2f%%  Sharpe %.2f  回撤 %6.1f%%  笔数 %2d  胜率 %5.1f%%  平均单笔 %+.2f%%  复利 %.2f 倍'
              % (nm, lab, r['年化'], r['Sharpe'], r['回撤'], r['笔数'], r['胜率'], r['平均单笔'], r['复利']))

print('\n样本外（2022-01 ~ 2026-11）:')
for nm, tgt, st in [('创业板', cy, '2022-01-01'), ('科创50', kc, '2022-01-01')]:
    s = build(tgt, st)
    for thr, lab in [(0.04, '4%'), (0.05, '5%')]:
        e = (s.amv_r >= thr).astype(float)
        r = sim(s, e)
        print('  %-8s 阈值%-4s 年化 %+6.2f%%  Sharpe %.2f  回撤 %6.1f%%  笔数 %2d'
              % (nm, lab, r['年化'], r['Sharpe'], r['回撤'], r['笔数']))

# ---------- 图表 ----------
s = build(cy, '2016-01-01')
res = {}
for thr, lab, col in [(0.04, 'v3.0 (4%)', '#95a5a6'), (0.05, 'v4.0 (5%)', '#c0392b')]:
    res[lab] = sim(s, (s.amv_r >= thr).astype(float), hold=20, stop=-0.03)

fig = plt.figure(figsize=(15.5, 10))
gs = fig.add_gridspec(3, 2, height_ratios=[1.5, 1, 1], hspace=0.32, wspace=0.22)
yrs = len(s)/252

ax = fig.add_subplot(gs[0, :])
bh = (1+s.px.pct_change().fillna(0).values).cumprod()
ax.plot(s.date, bh, lw=1.3, color='#95a5a6', label=f'创业板买入持有  年化 {((bh[-1]**(1/yrs))-1)*100:+.1f}%')
for lab, c in [('v3.0 (4%)', '#f39c12'), ('v4.0 (5%)', '#c0392b')]:
    nav = res[lab]['nav']
    ax.plot(s.date, nav, lw=1.9, color=c, label=f'{lab}  年化 {res[lab]["年化"]:+.2f}%  Sharpe {res[lab]["Sharpe"]:.2f}')
ax.set_yscale('log'); ax.grid(alpha=.25); ax.legend(fontsize=9, loc='upper left')
ax.set_title('v4.0 vs v3.0：创业板指净值对比（2016-01 ~ 2026-11，T+1开盘买，含2bp成本）', fontsize=12, pad=10)
ax.set_ylabel('净值（对数轴）')

ax = fig.add_subplot(gs[1, 0])
for lab, c in [('v3.0 (4%)', '#f39c12'), ('v4.0 (5%)', '#c0392b')]:
    nav = res[lab]['nav']
    dd = nav/np.maximum.accumulate(nav)-1
    ax.plot(s.date, dd*100, lw=1.0, color=c, label=f'{lab} {dd.min()*100:.1f}%')
ax.fill_between(s.date, (bh/np.maximum.accumulate(bh)-1)*100, 0, color='#95a5a6', alpha=.3, label=f'买入持有 {(bh/np.maximum.accumulate(bh)-1).min()*100:.1f}%')
ax.legend(fontsize=8.5, loc='lower left'); ax.grid(alpha=.25)
ax.set_title('回撤对比', fontsize=10); ax.set_ylabel('%')

ax = fig.add_subplot(gs[1, 1])
rows = {}
for lab in res:
    d_ = s.copy(); d_['sr'] = pd.Series(res[lab]['nav']).pct_change().fillna(0).values
    rows[lab] = d_.groupby(d_.date.dt.year).sr.apply(lambda x: (1+x).prod()-1)
    rows[lab+'idx'] = s.groupby(s.date.dt.year).px.apply(lambda x: x.iloc[-1]/x.iloc[0]-1)
yrs_ = sorted(rows['v3.0 (4%)'].index)
w = 0.26
ax.bar(np.arange(len(yrs_))-w, rows['v3.0 (4%)']*100, w, color='#f39c12', label='v3.0 (4%)')
ax.bar(np.arange(len(yrs_)), rows['v4.0 (5%)']*100, w, color='#c0392b', label='v4.0 (5%)')
ax.bar(np.arange(len(yrs_))+w, rows['v3.0 (4%)idx']*100, w, color='#95a5a6', label='创业板指')
ax.axhline(0, color='k', lw=.7); ax.grid(alpha=.25, axis='y'); ax.legend(fontsize=8)
ax.set_xticks(np.arange(len(yrs_))); ax.set_xticklabels(yrs_, fontsize=8.5, rotation=45)
ax.set_title('分年度收益', fontsize=10); ax.set_ylabel('%')

ax = fig.add_subplot(gs[2, :])
ax.plot(s.date, s.c, lw=0.9, color='#34495e', label='活跃市值 0AMV')
for thr, lab, c in [(0.04, 'v3.0 入场信号 (≥4%)', '#f39c12'), (0.05, 'v4.0 入场信号 (≥5%)', '#c0392b')]:
    sp = s[s.amv_r >= thr]
    ax.scatter(sp.date, sp.c, s=16, color=c, zorder=4, label=f'{lab}  ({len(sp)} 次)')
ax.set_yscale('log'); ax.grid(alpha=.25); ax.legend(fontsize=9)
ax.set_title('两版入场信号在 AMV 序列上的位置', fontsize=10)

plt.savefig('amv-strategy/charts/backtest_v4.png', dpi=140, bbox_inches='tight', facecolor='white')
print('\n已保存 amv-strategy/charts/backtest_v4.png')

print('\nv4.0 最近 8 笔（创业板）:')
for _, r in res['v4.0 (5%)']['trades'].tail(8).iterrows():
    print('  %s → %s  %+.2f%%  (%d 天)' % (r.b, r.s, r.r*100, r.d))
