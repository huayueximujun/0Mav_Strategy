# -*- coding: utf-8 -*-
"""回测曲线 + 执行时点校验"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei','SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ---------- 数据 ----------
amv = pd.read_csv('amv_xlsx_clean.csv', parse_dates=['date']).sort_values('date').reset_index(drop=True)
amv['amv_r'] = amv.c.pct_change()
cy = pd.read_csv('latest_cy.csv', parse_dates=['date'])
sh = pd.read_csv('latest_sh.csv', parse_dates=['date'])
d = amv.merge(cy, on='date', how='inner').merge(sh, on='date', how='left').sort_values('date').reset_index(drop=True)
d = d[d.date >= '2016-01-01'].reset_index(drop=True)

START_EQ = 1.0

def backtest(df, col, hold=20, stop=-0.03, lag=1, cost_bp=2.0):
    px = df[col].values; sig = (df.amv_r >= 0.04).values; n = len(df)
    pos = np.zeros(n); trades = []; i = 0
    while i < n:
        if not np.isnan(sig[i]) and sig[i]:
            bi = min(i + lag, n-1); si = min(bi + hold, n-1)
            if stop is not None:
                for j in range(bi+1, si+1):
                    if px[j]/px[bi] - 1 <= stop:
                        si = j; break
            if si <= bi: si = min(bi+2, n-1)
            pos[bi:si] = 1
            trades.append(dict(sig_i=i, buy=bi, sell=si,
                               sig_date=df.date.iloc[i], buy_date=df.date.iloc[bi], sell_date=df.date.iloc[si],
                               ret=px[si]/px[bi]-1, days=si-bi))
            i = si + 1
        else:
            i += 1
    r = np.r_[0, px[1:]/px[:-1]-1]
    pnl = pos*r - np.abs(np.diff(np.r_[0, pos]))*cost_bp/10000
    cum = np.cumprod(1+pnl)
    bh = np.cumprod(1+r)
    return pos, pnl, cum, bh, pd.DataFrame(trades)

pos, pnl, cum, bh, tr = backtest(d, 'cy')
yrs = len(d)/252

# ---------- 执行时点诊断 ----------
print('='*80)
print('执行时点校验：T 日 AMV ≥+4% → 第二天(T+1)进场')
print('='*80)
lag_ret = []
for _, t in tr.iterrows():
    i = int(t.sig_i); bi = int(t.buy)
    lag_ret.append(d.cy.iloc[bi]/d.cy.iloc[i]-1)
lag_ret = np.array(lag_ret)
print('  信号日(T) → 买入日(T+1) 创业板涨跌: 均值 %+.2f%%  中位 %+.2f%%  为正的占 %.0f%%'
      % (lag_ret.mean()*100, np.median(lag_ret)*100, (lag_ret>0).mean()*100))
print('  → 第二天进场时,价格平均已经比信号日高 %.2f%%（这是"隔夜追高"成本）' % (lag_ret.mean()*100))

# 对比三种执行
def bt_lag(lag, price_mode='close'):
    px = d.cy.values; sig = (d.amv_r >= 0.04).values; n = len(d)
    op = d.cy.values  # 用 close 近似,若要开盘价需另取
    pos = np.zeros(n); tlist = []; i = 0
    while i < n:
        if not np.isnan(sig[i]) and sig[i]:
            bi = min(i+lag, n-1); si = min(bi+20, n-1)
            for j in range(bi+1, si+1):
                if px[j]/px[bi]-1 <= -0.03: si = j; break
            if si <= bi: si = min(bi+2, n-1)
            pos[bi:si] = 1; tlist.append(px[si]/px[bi]-1); i = si+1
        else: i += 1
    r = np.r_[0, px[1:]/px[:-1]-1]
    p = pos*r - np.abs(np.diff(np.r_[0, pos]))*2/10000
    c = np.cumprod(1+p)
    return dict(年化=(c[-1]**(1/yrs)-1)*100, Sharpe=p.mean()/p.std()*np.sqrt(252),
                回撤=(c/np.maximum.accumulate(c)-1).min()*100, 笔数=len(tlist),
                胜率=(np.array(tlist)>0).mean()*100)

print('\n  不同执行时点对比:')
cmp = [dict(执行='T日收盘就买(lag=0，偏乐观)', **bt_lag(0)),
       dict(执行='T+1收盘买(lag=1，回测口径)', **bt_lag(1)),
       dict(执行='T+2收盘买(lag=2)', **bt_lag(2))]
print(pd.DataFrame(cmp).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

# ---------- 主图 ----------
fig = plt.figure(figsize=(15.5, 10.5))
gs = fig.add_gridspec(3, 2, height_ratios=[1.5, 1, 1], hspace=0.32, wspace=0.22)

# ① 净值曲线 + 买卖点
ax = fig.add_subplot(gs[0, :])
ax.plot(d.date, bh, lw=1.3, color='#95a5a6', label=f'创业板指买入持有  年化 {((bh[-1]**(1/yrs))-1)*100:+.1f}%')
ax.plot(d.date, cum, lw=2.0, color='#c0392b',
        label=f'AMV策略（+4%进 / 持20天 / 止损-3%）  年化 {((cum[-1]**(1/yrs))-1)*100:+.1f}%  仓位 {pos.mean()*100:.0f}%')
# 买卖点
bx = [d.date.iloc[int(t.buy)] for _, t in tr.iterrows()]
by = [cum[int(t.buy)] for _, t in tr.iterrows()]
sx = [d.date.iloc[int(t.sell)] for _, t in tr.iterrows()]
sy = [cum[int(t.sell)] for _, t in tr.iterrows()]
ax.scatter(bx, by, marker='^', s=26, color='#e74c3c', zorder=5, label=f'买入 {len(tr)} 次')
ax.scatter(sx, sy, marker='v', s=22, color='#27ae60', zorder=5, label='卖出')
ax.set_yscale('log'); ax.grid(alpha=.25); ax.legend(fontsize=9, loc='upper left')
ax.set_title('AMV 策略净值（创业板指，2016-01 ~ 2026-11，含 2bp 成本）', fontsize=12, pad=10)
ax.set_ylabel('净值（对数轴）')

# ② 回撤
ax = fig.add_subplot(gs[1, 0])
dd_s = cum/np.maximum.accumulate(cum)-1
dd_b = bh/np.maximum.accumulate(bh)-1
ax.fill_between(d.date, dd_s*100, 0, color='#c0392b', alpha=.55, label=f'策略 {dd_s.min()*100:.1f}%')
ax.fill_between(d.date, dd_b*100, 0, color='#95a5a6', alpha=.35, label=f'买入持有 {dd_b.min()*100:.1f}%')
ax.legend(fontsize=8.5, loc='lower left'); ax.grid(alpha=.25)
ax.set_title('回撤对比', fontsize=10); ax.set_ylabel('%')

# ③ 分年度收益
ax = fig.add_subplot(gs[1, 1])
d['strat_r'] = pnl
ann = d.groupby(d.date.dt.year).agg(s=('strat_r', lambda x: (1+x).prod()-1),
                                     b=('cy', 'last'))
ann['b'] = d.groupby(d.date.dt.year).cy.apply(lambda x: x.iloc[-1]/x.iloc[0]-1)
yrs_ = ann.index.astype(int)
w = 0.38
ax.bar(yrs_-w/2, ann.s*100, w, color='#c0392b', label='策略')
ax.bar(yrs_+w/2, ann.b*100, w, color='#95a5a6', label='创业板指')
ax.axhline(0, color='k', lw=.7); ax.grid(alpha=.25, axis='y')
ax.legend(fontsize=8.5); ax.set_title('分年度收益', fontsize=10); ax.set_ylabel('%')
ax.tick_params(axis='x', rotation=45)

# ④ AMV 与信号点
ax = fig.add_subplot(gs[2, :])
ax.plot(d.date, d.c, lw=0.9, color='#34495e', label='活跃市值 0AMV')
sig_pts = d[d.amv_r >= 0.04]
ax.scatter(sig_pts.date, sig_pts.c, s=22, color='#e67e22', zorder=4, label=f'AMV 单日 ≥+4%（{len(sig_pts)} 次）')
ax.set_yscale('log'); ax.grid(alpha=.25); ax.legend(fontsize=9)
ax.set_title('入场信号位置：AMV 单日涨幅 ≥+4%', fontsize=10)
ax2 = ax.twinx()
ax2.plot(d.date, pos, lw=0.6, color='#c0392b', alpha=.35)
ax2.set_ylim(-0.05, 1.05); ax2.set_yticks([0,1]); ax2.set_yticklabels(['空仓','持仓'], fontsize=8)

plt.savefig('backtest_curve.png', dpi=140, bbox_inches='tight', facecolor='white')
print('\n已保存 backtest_curve.png')

# ---------- 汇总 ----------
print('\n' + '='*80)
print('策略汇总（2016-01 ~ 2026-11-19，创业板指）')
print('='*80)
print('  策略年化   %+.2f%%' % (((cum[-1]**(1/yrs))-1)*100))
print('  买入持有   %+.2f%%' % (((bh[-1]**(1/yrs))-1)*100))
print('  Sharpe     %.2f' % (pnl.mean()/pnl.std()*np.sqrt(252)))
print('  最大回撤   %.1f%%' % (dd_s.min()*100))
print('  交易次数   %d  （平均持仓 %.1f 天）' % (len(tr), tr.days.mean()))
print('  胜率       %.1f%%   平均单笔 %+.2f%%' % ((tr.ret>0).mean()*100, tr.ret.mean()*100))
print('  仓位占用   %.1f%%' % (pos.mean()*100))
