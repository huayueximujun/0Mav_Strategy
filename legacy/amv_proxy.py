# -*- coding: utf-8 -*-
"""能不能不用指南针？用公开的成交额替代 AMV 做信号"""
import numpy as np
import pandas as pd
from scipy import stats
pd.set_option('display.width', 260)

raw = pd.read_csv('0amv_daily_261113.csv', encoding='utf-8-sig', parse_dates=['date']).sort_values('date')
raw['amv_r'] = raw.close.pct_change()
raw['amt_r'] = raw.amount.pct_change()
raw['vol_r'] = raw.volume.pct_change()

cy = pd.read_csv('idx_sz399006.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'cy'}).sort_values('date')
d = raw.merge(cy, on='date', how='inner').sort_values('date').reset_index(drop=True)
d = d[d.date >= '2016-01-01'].reset_index(drop=True)

print('='*84)
print('1. AMV 与公开指标的关系（2016-2026）')
print('='*84)
for c, nm in [('amt_r','全市场成交额日变化'), ('vol_r','全市场成交量日变化')]:
    print('  AMV日收益 ~ %s: 相关 %+.3f' % (nm, d.amv_r.corr(d[c])))
print('  AMV 日收益 σ = %.2f%%   成交额 σ = %.2f%%' % (d.amv_r.std()*100, d.amt_r.std()*100))

# 同日同向率
print('  同向天数占比: %.1f%%' % ((np.sign(d.amv_r)==np.sign(d.amt_r)).mean()*100))
# 交集（两个都大涨）
print('  AMV≥+4%% 的天数: %d   成交额≥+10%% 的天数: %d   两者同时: %d'
      % ((d.amv_r>=0.04).sum(), (d.amt_r>=0.10).sum(), ((d.amv_r>=0.04)&(d.amt_r>=0.10)).sum()))

def sim(ent, hold=20, stop=-0.03, lag=1, cost=2.0):
    px = d.cy.values; n = len(d); pos = np.zeros(n); trades = []; i = 0
    while i < n:
        if ent[i]:
            bi = min(i+lag, n-1); si = min(bi+hold, n-1)
            if stop is not None:
                for j in range(bi+1, si+1):
                    if px[j]/px[bi]-1 <= stop: si = j; break
            if si <= bi: si = min(bi+2, n-1)
            pos[bi:si] = 1; trades.append((bi, si)); i = si+1
        else: i += 1
    r = np.r_[0, px[1:]/px[:-1]-1]
    pnl = pos*r - np.abs(np.diff(np.r_[0, pos]))*cost/10000
    cum = np.cumprod(1+pnl); yrs = n/252
    tr = np.array([px[si]/px[bi]-1 for bi, si in trades]) if trades else np.array([0])
    return dict(年化=(cum[-1]**(1/yrs)-1)*100, Sharpe=pnl.mean()/pnl.std()*np.sqrt(252),
                回撤=(cum/np.maximum.accumulate(cum)-1).min()*100, 笔数=len(trades),
                胜率=(tr>0).mean()*100, 平均单笔=tr.mean()*100)

print('\n' + '='*84)
print('2. 用成交额替代 AMV 做入场信号，扫阈值（创业板，持20天+止损-3%）')
print('='*84)
rows = [dict(信号='AMV ≥+4%（原始）', **sim((d.amv_r>=0.04).values))]
for th in [0.05, 0.08, 0.10, 0.15, 0.20, 0.25]:
    rows.append(dict(信号=f'成交额 ≥+{th*100:.0f}%', **sim((d.amt_r>=th).values)))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*84)
print('3. 信号重合度：成交额信号的入场日，有多少也是 AMV 信号日？')
print('='*84)
amv_sig = (d.amv_r>=0.04).values
for th in [0.08, 0.10, 0.15, 0.20]:
    amt_sig = (d.amt_r>=th).values
    inter = (amv_sig & amt_sig).sum()
    print('  成交额≥+%2.0f%%: %3d 次，其中 %2d 次也是 AMV 信号（重合 %2.0f%%）；AMV 信号被覆盖 %.0f%%'
          % (th*100, amt_sig.sum(), inter, inter/max(amt_sig.sum(),1)*100, inter/max(amv_sig.sum(),1)*100))

print('\n' + '='*84)
print('4. 组合信号：AMV 或 成交额 任一触发（扩大样本）')
print('='*84)
rows = []
for th in [0.10, 0.15, 0.20]:
    ent = amv_sig | (d.amt_r>=th).values
    rows.append(dict(信号=f'AMV≥4% 或 成交额≥{th*100:.0f}%', **sim(ent)))
rows.append(dict(信号='仅 AMV≥+4%', **sim(amv_sig)))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*84)
print('5. 更贴近 AMV 的代理：成交额 / 换手（用成交额20日均值的偏离度）')
print('='*84)
d['amt_z'] = (d.amount - d.amount.rolling(60).mean())/d.amount.rolling(60).std()
rows = []
for z in [1.0, 1.5, 2.0, 2.5]:
    rows.append(dict(信号=f'成交额偏离60日均值 {z}σ', **sim((d.amt_z>=z).fillna(False).values)))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))
