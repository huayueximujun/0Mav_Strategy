# -*- coding: utf-8 -*-
"""按"信号发生时的位置"分层：反转逻辑到底在哪种位置有效"""
import numpy as np
import pandas as pd
pd.set_option('display.width', 280)

x = pd.read_csv('amv_xlsx_clean.csv', parse_dates=['date']).sort_values('date').reset_index(drop=True)
x['ret'] = x.c.pct_change()
cy = pd.read_csv('latest_cy.csv', parse_dates=['date'])
sh = pd.read_csv('latest_sh.csv', parse_dates=['date'])
d = x.merge(cy, on='date', how='inner').merge(sh, on='date', how='left').sort_values('date').reset_index(drop=True)
d = d[d.date >= '2011-01-01'].reset_index(drop=True)   # 创业板 2011 起
d['cy_dd250'] = d.cy/d.cy.rolling(250).max()-1          # 距 250 日高点回撤
d['cy_r20'] = d.cy.pct_change(20)
d['cy_r5'] = d.cy.pct_change(5)
d['amv_pct250'] = (d.c-d.c.rolling(250).min())/(d.c.rolling(250).max()-d.c.rolling(250).min())

sig = d[d.ret >= 0.04].dropna(subset=['cy_dd250']).copy()
print('='*96)
print('一、AMV ≥+4%% 信号发生时，创业板所处位置分布（2011-2026，共 %d 个信号）' % len(sig))
print('='*96)
print(sig.cy_dd250.describe(percentiles=[.1,.25,.5,.75,.9]).to_string())

print('\n' + '='*96)
print('二、按"距250日高点回撤"分层：信号后表现（不等持有期，不加止损）')
print('='*96)
bins = [-1, -0.25, -0.15, -0.08, -0.02, 1]
labels = ['深度回撤 <-25%', '中度 -25~-15%', '轻度 -15~-8%', '近高点 -8~-2%', '创新高附近 >-2%']
sig['bucket'] = pd.cut(sig.cy_dd250, bins=bins, labels=labels)
rows = []
for lab in labels:
    s = sig[sig.bucket == lab]
    if len(s) < 3: continue
    row = dict(位置=lab, 信号数=len(s))
    for N in [5, 20, 40, 60]:
        r = []
        for i in s.index:
            if i+N < len(d): r.append(d.cy.iloc[i+N]/d.cy.iloc[i]-1)
        row[f'{N}日均值%'] = np.mean(r)*100 if r else np.nan
        row[f'{N}日胜率%'] = (np.array(r)>0).mean()*100 if r else np.nan
    rows.append(row)
t = pd.DataFrame(rows)
print(t[['位置','信号数','5日均值%','20日均值%','20日胜率%','40日均值%','60日均值%','60日胜率%']]
      .to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*96)
print('三、关键对比：「指数在跌」时，位置决定成败')
print('='*96)
sub = sig[sig.cy_r5 < 0].copy()
sub['b2'] = np.where(sub.cy_dd250 <= -0.15, '深跌区(<-15%)', '浅跌区(>-15%)')
for lab, g in sub.groupby('b2'):
    out = []
    for N in [20, 40, 60]:
        r = [d.cy.iloc[i+N]/d.cy.iloc[i]-1 for i in g.index if i+N < len(d)]
        out.append('%d日 %+.2f%%(胜%.0f%%)' % (N, np.mean(r)*100, (np.array(r)>0).mean()*100))
    print('  %-14s n=%3d  %s' % (lab, len(g), '  '.join(out)))

print('\n' + '='*96)
print('四、改进后的过滤：不是「5日>0」，而是「位置够低 或 趋势已转」')
print('='*96)

def sim(sig_mask, hold=20, stop=-0.03, lag=1, cost=2.0):
    px = d.cy.values; s = sig_mask.values; n = len(d)
    pos = np.zeros(n); tr = []; i = 0
    while i < n:
        if not np.isnan(s[i]) and s[i]:
            bi = min(i+lag, n-1); si = min(bi+hold, n-1)
            if stop is not None:
                for j in range(bi+1, si+1):
                    if px[j]/px[bi]-1 <= stop: si = j; break
            if si <= bi: si = min(bi+2, n-1)
            pos[bi:si] = 1; tr.append((bi, si)); i = si+1
        else: i += 1
    r = np.r_[0, px[1:]/px[:-1]-1]
    pnl = pos*r - np.abs(np.diff(np.r_[0, pos]))*cost/10000
    cum = np.cumprod(1+pnl); yrs = len(d)/252
    tt = np.array([px[si]/px[bi]-1 for bi, si in tr]) if tr else np.array([0])
    return dict(年化=(cum[-1]**(1/yrs)-1)*100, Sharpe=pnl.mean()/pnl.std()*np.sqrt(252),
                回撤=(cum/np.maximum.accumulate(cum)-1).min()*100, 笔数=len(tr),
                胜率=(tt>0).mean()*100, 平均单笔=tt.mean()*100, 仓位=pos.mean()*100)

base = (d.ret >= 0.04).fillna(False)
deep = (d.cy_dd250 <= -0.15).fillna(False)
shallow_dn = ((d.cy_dd250 > -0.15) & (d.cy_r5 < 0)).fillna(False)
rows = [
    dict(方案='① 原始（不过滤）', **sim(base)),
    dict(方案='② 仅在深跌区(<-15%)', **sim(base & deep)),
    dict(方案='③ 深跌区 或 5日>0（否决浅跌区下跌）', **sim(base & (deep | (d.cy_r5 > 0).fillna(False)))),
    dict(方案='④ 剔除「浅跌区还在跌」（我原先的建议）', **sim(base & (d.cy_r5 > 0).fillna(False))),
]
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*96)
print('五、反转策略该给多少时间和空间：深跌区(<-15%)信号 × 不同持有期/止损')
print('='*96)
print('        ' + ''.join('%16s' % f'止损{z*100:.0f}%' for z in [-0.03,-0.05,-0.08,-0.12]) + '%16s' % '无止损')
for h in [10, 20, 40, 60]:
    cells = []
    for z in [-0.03,-0.05,-0.08,-0.12, None]:
        r = sim(base & deep, hold=h, stop=z)
        cells.append('%16s' % f'{r["年化"]:+.1f}%/{r["Sharpe"]:.2f}')
    print('  持有%2d天' % h + ''.join(cells))

print('\n' + '='*96)
print('六、当前的信号条件检查')
print('='*96)
last = d.iloc[-1]
print('  创业板距250日高点: %+.1f%%  → %s' % (last.cy_dd250*100,
      '深跌区' if last.cy_dd250 <= -0.15 else '浅跌区'))
print('  创业板5日: %+.2f%%  20日: %+.2f%%' % (last.cy_r5*100, last.cy_r20*100))
print('  AMV 今日: %+.2f%%（需要 ≥+4%% 才触发）' % (last.ret*100))
