# -*- coding: utf-8 -*-
"""科创50 回测曲线（与创业板同口径）"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import akshare as ak
import warnings
warnings.filterwarnings('ignore')
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei','SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 更新科创50
try:
    kc = ak.index_zh_daily_sina(symbol='sh000688')
    kc['date'] = pd.to_datetime(kc['date'])
    kc[['date','close']].rename(columns={'close':'kc'}).to_csv('latest_kc.csv', index=False, encoding='utf-8-sig')
    print('科创50 更新至 %s，收盘 %.2f' % (kc.date.iloc[-1].date(), kc.close.iloc[-1]))
except Exception as e:
    print('更新失败', e)
    kc = pd.read_csv('idx_sh000688.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'kc'})

amv = pd.read_csv('amv_xlsx_clean.csv', parse_dates=['date']).sort_values('date').reset_index(drop=True)
amv['amv_r'] = amv.c.pct_change()
kc = pd.read_csv('latest_kc.csv', parse_dates=['date'])
cy = pd.read_csv('latest_cy.csv', parse_dates=['date'])
d = amv.merge(kc, on='date', how='inner').merge(cy, on='date', how='left').sort_values('date').reset_index(drop=True)
d = d[d.date >= '2020-01-01'].reset_index(drop=True)

def backtest(df, col, hold=20, stop=-0.03, lag=1, cost_bp=2.0):
    px = df[col].values; sig = (df.amv_r >= 0.04).values; n = len(df)
    pos = np.zeros(n); trades = []; i = 0
    while i < n:
        if not np.isnan(sig[i]) and sig[i]:
            bi = min(i+lag, n-1); si = min(bi+hold, n-1)
            if stop is not None:
                for j in range(bi+1, si+1):
                    if px[j]/px[bi]-1 <= stop: si = j; break
            if si <= bi: si = min(bi+2, n-1)
            pos[bi:si] = 1
            trades.append(dict(sig_i=i, buy=bi, sell=si, ret=px[si]/px[bi]-1, days=si-bi))
            i = si+1
        else:
            i += 1
    r = np.r_[0, px[1:]/px[:-1]-1]
    pnl = pos*r - np.abs(np.diff(np.r_[0, pos]))*cost_bp/10000
    cum = np.cumprod(1+pnl); bh = np.cumprod(1+r)
    return pos, pnl, cum, bh, pd.DataFrame(trades)

pos, pnl, cum, bh, tr = backtest(d, 'kc')
yrs = len(d)/252
dd_s = cum/np.maximum.accumulate(cum)-1
dd_b = bh/np.maximum.accumulate(bh)-1

print('\n' + '='*76)
print('科创50 策略汇总（%s ~ %s，%.1f 年）' % (d.date.iloc[0].date(), d.date.iloc[-1].date(), yrs))
print('='*76)
print('  策略年化   %+.2f%%      买入持有 %+.2f%%' % (((cum[-1]**(1/yrs))-1)*100, ((bh[-1]**(1/yrs))-1)*100))
print('  Sharpe     %.2f         最大回撤 %.1f%% (买入持有 %.1f%%)' % (pnl.mean()/pnl.std()*np.sqrt(252), dd_s.min()*100, dd_b.min()*100))
print('  交易次数   %d 次（AMV 信号 %d 次，平均持仓 %.1f 天）' % (len(tr), (d.amv_r>=0.04).sum(), tr.days.mean()))
print('  胜率       %.1f%%        平均单笔 %+.2f%%' % ((tr.ret>0).mean()*100, tr.ret.mean()*100))
print('  仓位占用   %.1f%%' % (pos.mean()*100))
print('\n  最近 5 笔交易:')
for _, t in tr.tail(5).iterrows():
    print('    %s 买入 → %s 卖出  %+.2f%%  (%d 天)'
          % (d.date.iloc[int(t.buy)].date(), d.date.iloc[int(t.sell)].date(), t.ret*100, int(t.days)))

# ---------- 图 ----------
fig = plt.figure(figsize=(15.5, 10.5))
gs = fig.add_gridspec(3, 2, height_ratios=[1.5, 1, 1], hspace=0.32, wspace=0.22)

ax = fig.add_subplot(gs[0, :])
ax.plot(d.date, bh, lw=1.3, color='#95a5a6', label=f'科创50 买入持有  年化 {((bh[-1]**(1/yrs))-1)*100:+.1f}%')
ax.plot(d.date, cum, lw=2.0, color='#8e44ad',
        label=f'AMV策略  年化 {((cum[-1]**(1/yrs))-1)*100:+.1f}%  Sharpe {pnl.mean()/pnl.std()*np.sqrt(252):.2f}  仓位 {pos.mean()*100:.0f}%')
ax.scatter([d.date.iloc[int(t.buy)] for _, t in tr.iterrows()], [cum[int(t.buy)] for _, t in tr.iterrows()],
           marker='^', s=34, color='#e74c3c', zorder=5, label=f'买入 {len(tr)} 次')
ax.scatter([d.date.iloc[int(t.sell)] for _, t in tr.iterrows()], [cum[int(t.sell)] for _, t in tr.iterrows()],
           marker='v', s=28, color='#27ae60', zorder=5, label='卖出')
ax.set_yscale('log'); ax.grid(alpha=.25); ax.legend(fontsize=9, loc='upper left')
ax.set_title('AMV 策略净值（科创50，2020-01 ~ 2026-11，含 2bp 成本）', fontsize=12, pad=10)
ax.set_ylabel('净值（对数轴）')

ax = fig.add_subplot(gs[1, 0])
ax.fill_between(d.date, dd_s*100, 0, color='#8e44ad', alpha=.55, label=f'策略 {dd_s.min()*100:.1f}%')
ax.fill_between(d.date, dd_b*100, 0, color='#95a5a6', alpha=.35, label=f'买入持有 {dd_b.min()*100:.1f}%')
ax.legend(fontsize=8.5, loc='lower left'); ax.grid(alpha=.25)
ax.set_title('回撤对比', fontsize=10); ax.set_ylabel('%')

ax = fig.add_subplot(gs[1, 1])
d['strat_r'] = pnl
ann = pd.DataFrame({'s': d.groupby(d.date.dt.year).strat_r.apply(lambda x: (1+x).prod()-1)})
ann['b'] = d.groupby(d.date.dt.year).kc.apply(lambda x: x.iloc[-1]/x.iloc[0]-1)
yrs_ = ann.index.astype(int); w = 0.38
ax.bar(yrs_-w/2, ann.s*100, w, color='#8e44ad', label='策略')
ax.bar(yrs_+w/2, ann.b*100, w, color='#95a5a6', label='科创50')
ax.axhline(0, color='k', lw=.7); ax.grid(alpha=.25, axis='y')
ax.legend(fontsize=8.5); ax.set_title('分年度收益', fontsize=10); ax.set_ylabel('%')
ax.tick_params(axis='x', rotation=45)

ax = fig.add_subplot(gs[2, :])
ax.plot(d.date, d.c, lw=0.9, color='#34495e', label='活跃市值 0AMV')
sp = d[d.amv_r >= 0.04]
ax.scatter(sp.date, sp.c, s=24, color='#e67e22', zorder=4, label=f'AMV 单日 ≥+4%（{len(sp)} 次）')
ax.set_yscale('log'); ax.grid(alpha=.25); ax.legend(fontsize=9)
ax.set_title('入场信号位置', fontsize=10)
ax2 = ax.twinx(); ax2.plot(d.date, pos, lw=0.6, color='#8e44ad', alpha=.35)
ax2.set_ylim(-0.05, 1.05); ax2.set_yticks([0,1]); ax2.set_yticklabels(['空仓','持仓'], fontsize=8)

plt.savefig('backtest_kc.png', dpi=140, bbox_inches='tight', facecolor='white')
print('\n已保存 backtest_kc.png')

# ---------- 对比 ----------
print('\n' + '='*76)
print('科创50 vs 创业板 vs 上证（同为 2020-01 起，同一套规则）')
print('='*76)
sh = pd.read_csv('latest_sh.csv', parse_dates=['date'])
d2 = amv.merge(kc, on='date', how='inner').merge(cy, on='date', how='left').merge(sh, on='date', how='left')
d2 = d2[d2.date >= '2020-01-01'].reset_index(drop=True)
rows = []
for nm, col in [('科创50','kc'), ('创业板','cy'), ('上证','sh')]:
    s = d2.dropna(subset=[col]).reset_index(drop=True)
    p, pn, cm, bhh, tt = backtest(s, col)
    y = len(s)/252
    rows.append(dict(标的=nm, 样本天数=len(s), 年化=(cm[-1]**(1/y)-1)*100,
                     Sharpe=pn.mean()/pn.std()*np.sqrt(252),
                     回撤=(cm/np.maximum.accumulate(cm)-1).min()*100,
                     买持年化=(bhh[-1]**(1/y)-1)*100, 笔数=len(tt),
                     胜率=(tt.ret>0).mean()*100, 仓位=p.mean()*100))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))
