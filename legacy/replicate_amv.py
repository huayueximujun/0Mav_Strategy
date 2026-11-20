# -*- coding: utf-8 -*-
"""复刻 0AMV：多种构造方案与真实序列的对比"""
import numpy as np
import pandas as pd
from scipy import stats
pd.set_option('display.width', 250)

d = pd.read_csv('0amv_daily_261113.csv', encoding='utf-8-sig', parse_dates=['date']).sort_values('date').reset_index(drop=True)
d['amv_r'] = d.close.pct_change()
d['amt_r'] = d.amount.pct_change()
# 只用 1996 年后（文章也说 1995 年前数据不可靠）
d = d[d.date >= '1996-01-01'].reset_index(drop=True)
print('样本: %d 行  %s ~ %s' % (len(d), d.date.iloc[0].date(), d.date.iloc[-1].date()))

amt = d.amount.values
vol = d.volume.values
vwap = d.amount.values/d.volume.values

cands = {}
# A: 前人方案 EMA(amount, 9)
for sp in [5, 9, 15, 30]:
    cands[f'EMA(成交额,{sp})'] = pd.Series(amt).ewm(span=sp, adjust=False).mean().values
# B: EMA(成交量,9) × 均价  —— 把量价分开建模
cands['EMA(量,9)×均价'] = pd.Series(vol).ewm(span=9, adjust=False).mean().values * vwap
# C: 带下限的 EMA（活跃筹码有惯性）
e9 = pd.Series(amt).ewm(span=9, adjust=False).mean().values
floor = np.percentile(e9, 10)
cands['EMA(成交额,9) 带下限'] = np.maximum(e9, floor*0.8)
# D: 双指数平滑（更平滑）
cands['EMA9 再 EMA9'] = pd.Series(e9).ewm(span=9, adjust=False).mean().values
# E: 成交额的 9 日滚动和（存量视角）
cands['成交额9日和'] = pd.Series(amt).rolling(9).sum().values
# F: 成交额 ÷ 换手率代理（用量的相对波动估计活跃度）
act = pd.Series(vol).rolling(20).mean()/pd.Series(vol).rolling(250).mean()
cands['成交额×活跃度'] = amt * act.values

def evaluate(name, s):
    x = pd.Series(s, index=d.index).replace([np.inf, -np.inf], np.nan)
    ok = x.notna() & (x > 0)
    lr = np.log(d.close[ok]) 
    lx = np.log(x[ok])
    lvl_corr = np.corrcoef(lr, lx)[0,1]
    xr = x.pct_change()
    m = xr.notna() & d.amv_r.notna()
    ret_corr = np.corrcoef(xr[m], d.amv_r[m])[0,1]
    # 动态范围
    dr_real = d.close.max()/d.close.min()
    dr_x = x[ok].max()/x[ok].min()
    # +4% 信号重合
    sig_real = (d.amv_r >= 0.04)
    sig_x = (xr >= 0.04)
    inter = (sig_real & sig_x).sum()
    recall = inter/max(sig_real.sum(), 1)
    prec = inter/max(sig_x.sum(), 1)
    return dict(方案=name, 水平log相关=lvl_corr, **{'日收益相关': ret_corr},
                动态范围_代理=dr_x, 动态范围_真实=dr_real,
                信号数_代理=int(sig_x.sum()), 信号召回=recall*100, 信号精确=prec*100)

rows = [evaluate(k, v) for k, v in cands.items()]
print('\n真实序列动态范围: %.2f 倍' % (d.close.max()/d.close.min()))
print('\n' + '='*104)
print('复刻方案对比（关键看「日收益相关」，策略信号依赖它）')
print('='*104)
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.3f}'))

print('\n' + '='*104)
print('最优方案的细节诊断')
print('='*104)
best_name = max(rows, key=lambda r: r['日收益相关'])['方案']
best = pd.Series(cands[best_name], index=d.index)
print('最优: %s  日收益相关 %.3f' % (best_name, max(r['日收益相关'] for r in rows)))
br = best.pct_change()
print('  代理日收益 σ=%.2f%%  真实 σ=%.2f%%' % (br.std()*100, d.amv_r.std()*100))
print('  +4%% 信号: 真实 %d 次 / 代理 %d 次' % ((d.amv_r>=0.04).sum(), (br>=0.04).sum()))

# 关键时点对比
print('\n关键时点（真实 vs 最优代理，均已归一化到 1996 起点=100）:')
for dt in ['2007-10-16','2008-10-28','2015-06-12','2018-10-18','2024-09-18','2026-07-01']:
    row = d[d.date == dt]
    if len(row) == 0: continue
    i = row.index[0]
    v_r = d.close.iloc[i]/d.close.iloc[0]*100
    v_x = best.iloc[i]/best.iloc[0]*100
    print('  %s  真实 %8.1f  代理 %8.1f  偏差 %+.0f%%' % (dt, v_r, v_x, (v_x/v_r-1)*100))

print('\n' + '='*104)
print('用代理指标跑策略，看结论是否还成立（创业板 2016-2026）')
print('='*104)
cy = pd.read_csv('idx_sz399006.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'cy'})
dd = d.merge(cy, on='date', how='inner').sort_values('date').reset_index(drop=True)
dd = dd[dd.date >= '2016-01-01'].reset_index(drop=True)
px = dd.cy.values; n = len(dd)

def sim(sig, hold=20, stop=-0.03, lag=1, cost=2.0):
    pos = np.zeros(n); tr = []; i = 0
    while i < n:
        if sig[i]:
            bi = min(i+lag, n-1); si = min(bi+hold, n-1)
            for j in range(bi+1, si+1):
                if px[j]/px[bi]-1 <= stop: si = j; break
            if si <= bi: si = min(bi+2, n-1)
            pos[bi:si] = 1; tr.append((bi, si)); i = si+1
        else: i += 1
    r = np.r_[0, px[1:]/px[:-1]-1]
    pnl = pos*r - np.abs(np.diff(np.r_[0, pos]))*cost/10000
    cum = np.cumprod(1+pnl); yrs = n/252
    t = np.array([px[si]/px[bi]-1 for bi, si in tr]) if tr else np.array([0])
    return dict(年化=(cum[-1]**(1/yrs)-1)*100, Sharpe=pnl.mean()/pnl.std()*np.sqrt(252),
                回撤=(cum/np.maximum.accumulate(cum)-1).min()*100, 笔数=len(tr),
                胜率=(t>0).mean()*100)

rows = []
rows.append(dict(信号='真实 AMV ≥+4%', **sim((dd.amv_r>=0.04).fillna(False).values)))
bp = pd.Series(dd.amount.values).ewm(span=9, adjust=False).mean()
bp_r = bp.pct_change()
rows.append(dict(信号='EMA(成交额,9) ≥+4%', **sim((bp_r>=0.04).fillna(False).values)))
rows.append(dict(信号='EMA(成交额,9) ≥+8%', **sim((bp_r>=0.08).fillna(False).values)))
rows.append(dict(信号='EMA(成交额,9) ≥+10%', **sim((bp_r>=0.10).fillna(False).values)))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))
