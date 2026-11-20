# -*- coding: utf-8 -*-
"""创业板专项：实盘化检查（分年、成本、信号明细、风险特征）"""
import numpy as np
import pandas as pd
pd.set_option('display.width', 260)
pd.set_option('display.max_rows', 200)

amv = pd.read_csv('0amv_daily_261113.csv', encoding='utf-8-sig', parse_dates=['date'])[['date','close']]
amv = amv.rename(columns={'close':'amv'}).sort_values('date')
amv['amv_r'] = amv.amv.pct_change()
cy = pd.read_csv('idx_sz399006.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'cy'}).sort_values('date')
d = amv.merge(cy, on='date', how='inner').sort_values('date').reset_index(drop=True)
d = d[d.date >= '2011-01-01'].reset_index(drop=True)

def sim(df, hold=20, stop=-0.03, cost=2.0, lag=1):
    px = df.cy.values; ar = df.amv_r.values; n = len(df)
    pos = np.zeros(n); trades = []; i = 0
    while i < n:
        if not np.isnan(ar[i]) and ar[i] >= 0.04:
            bi = min(i+lag, n-1); si = min(bi+hold, n-1)
            if stop is not None:
                for j in range(bi+1, si+1):
                    if px[j]/px[bi]-1 <= stop: si = j; break
            if si <= bi: si = min(bi+1, n-1)
            pos[bi:si] = 1; trades.append((bi, si)); i = si+1
        else: i += 1
    r = np.r_[0, px[1:]/px[:-1]-1]
    pnl = pos*r - np.abs(np.diff(np.r_[0, pos]))*cost/10000
    cum = np.cumprod(1+pnl); yrs = n/252
    return dict(年化=(cum[-1]**(1/yrs)-1)*100, Sharpe=pnl.mean()/pnl.std()*np.sqrt(252),
                回撤=(cum/np.maximum.accumulate(cum)-1).min()*100, 仓位=pos.mean()*100,
                笔数=len(trades)), pnl, cum, trades

print('='*88)
print('1. 创业板：分段表现（策略 vs 买入持有）')
print('='*88)
seg = [('2011-2015','2011-01-01','2015-12-31'), ('2016-2020','2016-01-01','2020-12-31'),
       ('2021-2026','2021-01-01','2026-12-31'), ('全样本','2011-01-01','2026-12-31')]
rows = []
for lab, s0, s1 in seg:
    s = d[(d.date>=s0)&(d.date<=s1)].reset_index(drop=True)
    if len(s) < 200: continue
    st, pnl, cum, tr = sim(s)
    r = s.cy.pct_change().fillna(0).values
    cum_bh = np.cumprod(1+r); yrs = len(s)/252
    rows.append(dict(区间=lab, 样本=len(s), 策略年化=st['年化'], 策略Sharpe=st['Sharpe'],
                     策略回撤=st['回撤'], 笔数=st['笔数'],
                     买持年化=(cum_bh[-1]**(1/yrs)-1)*100, 买持Sharpe=r.mean()/r.std()*np.sqrt(252),
                     买持回撤=(cum_bh/np.maximum.accumulate(cum_bh)-1).min()*100))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*88)
print('2. 成本敏感性（近10年 2016-2026）')
print('='*88)
s = d[d.date>='2016-01-01'].reset_index(drop=True)
rows = []
for c in [2, 5, 10, 15, 20, 30]:
    st, _, _, _ = sim(s, cost=c)
    rows.append(dict(单边成本bp=c, 年化=st['年化'], Sharpe=st['Sharpe'], 回撤=st['回撤'], 笔数=st['笔数']))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*88)
print('3. 参数稳健性网格（创业板 2016-2026）：年化% / Sharpe')
print('='*88)
opts = [-0.03, -0.05, -0.08, -0.12, None]
labs = ['止损3%','止损5%','止损8%','止损12%','无止损']
print('        ' + ''.join('%18s' % x for x in labs))
for h in [5, 10, 15, 20, 25, 30, 40]:
    cells = []
    for z in opts:
        st, _, _, _ = sim(s, hold=h, stop=z)
        cells.append('%18s' % f'{st["年化"]:+.1f}/{st["Sharpe"]:.2f}')
    print('  持有%2d天' % h + ''.join(cells))

print('\n' + '='*88)
print('4. 近3年逐笔明细（2023 至今）')
print('='*88)
s = d[d.date>='2016-01-01'].reset_index(drop=True)
st, pnl, cum, tr = sim(s)
sub = d.reset_index(drop=True)
rows = []
for bi, si in tr:
    if sub.date.iloc[bi] >= pd.Timestamp('2023-01-01'):
        rows.append(dict(买=sub.date.iloc[bi].date(), 卖=sub.date.iloc[si].date(),
                         天数=si-bi, 收益=(sub.cy.iloc[si]/sub.cy.iloc[bi]-1)*100,
                         期间指数最高=(sub.cy.iloc[bi:si+1].max()/sub.cy.iloc[bi]-1)*100,
                         策略卖出后20日=(sub.cy.iloc[min(si+20,len(sub)-1)]/sub.cy.iloc[si]-1)*100))
if rows:
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*88)
print('5. 实盘特征：空仓时长、连续亏损、单笔分布')
print('='*88)
st, pnl, cum, tr = sim(s)
hold = np.array([si-bi for bi, si in tr])
ret = np.array([sub.cy.iloc[si]/sub.cy.iloc[bi]-1 for bi, si in tr])
gaps = np.array([tr[i+1][0]-tr[i][1] for i in range(len(tr)-1)])
print('  交易笔数 %d（%.1f 笔/年）' % (len(tr), len(tr)/(len(s)/252)))
print('  持仓天数: 中位 %d, 均值 %.1f, 最长 %d' % (np.median(hold), hold.mean(), hold.max()))
print('  空仓间隔: 中位 %d 天, 均值 %.1f, 最长 %d 天' % (np.median(gaps), gaps.mean(), gaps.max()))
print('  单笔收益: 中位 %+.2f%%, 均值 %+.2f%%, 最好 %+.1f%%, 最差 %.1f%%'
      % (np.median(ret)*100, ret.mean()*100, ret.max()*100, ret.min()*100))
print('  胜率 %.1f%%  盈亏比 %.2f' % ((ret>0).mean()*100, ret[ret>0].sum()/abs(ret[ret<0].sum())))
# 连续亏损
mx = 0; cur = 0
for x in ret:
    cur = cur+1 if x <= 0 else 0
    mx = max(mx, cur)
print('  最长连续亏损 %d 笔' % mx)
# 空仓期错过的涨幅
print('  仓位占用 %.1f%%（即约 %.0f%% 时间空仓）' % (st['仓位'], 100-st['仓位']))

print('\n' + '='*88)
print('6. 兜底问题：策略在最大回撤期间做了什么')
print('='*88)
cum_s = pd.Series(cum, index=s.date)
peak = cum_s.cummax()
dd = cum_s/peak-1
idx = dd.idxmin()
print('  策略最大回撤 %.1f%%，谷底日期 %s' % (dd.min()*100, idx.date()))
print('  同期指数跌幅 %.1f%%' % ((s[s.date==idx].cy.iloc[0]/s[s.date<=idx].cy.max()-1)*100))
