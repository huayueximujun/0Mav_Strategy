# -*- coding: utf-8 -*-
"""AMV（指南针活跃市值）择时有效性检验 vs 上证 / 创业板"""
import numpy as np
import pandas as pd
from scipy import stats
pd.set_option('display.width', 250)

# ---------- 数据 ----------
amv = pd.read_csv('0amv_daily_261113.csv', encoding='utf-8-sig', parse_dates=['date'])
amv = amv[['date','close','volume','amount']].rename(columns={'close':'amv'}).sort_values('date')
sh = pd.read_csv('idx_sh000001.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'sh'})
cy = pd.read_csv('idx_sz399006.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'cy'})

d = amv.merge(sh, on='date', how='inner').merge(cy, on='date', how='left')
d = d.sort_values('date').reset_index(drop=True)
print('对齐后样本: %d 行  %s -> %s' % (len(d), d.date.iloc[0].date(), d.date.iloc[-1].date()))
print('有创业板数据的行数:', d.cy.notna().sum(), '起始', d[d.cy.notna()].date.iloc[0].date())

d['r_amv'] = d.amv.pct_change()
d['r_sh'] = d.sh.pct_change()
d['r_cy'] = d.cy.pct_change()

print('\n' + '='*74)
print('一、AMV 与指数的同期关系')
print('='*74)
for c, nm in [('r_sh','上证'), ('r_cy','创业板')]:
    m = d[c].notna()
    print('  AMV日收益 ~ %s 日收益: 相关 %+.3f  (n=%d)' % (nm, d.r_amv[m].corr(d[c][m]), m.sum()))

# 滚动 beta 稳定性
print('\n  分年代 同期相关（AMV 收益 vs 上证收益）:')
for seg in range(1995, 2030, 5):
    s = d[(d.date.dt.year >= seg) & (d.date.dt.year < seg+5)].dropna(subset=['r_amv','r_sh'])
    if len(s) < 100: continue
    beta = np.polyfit(s.r_sh, s.r_amv, 1)[0]
    print('    %d-%d: corr=%+.3f  beta=%.2f  n=%4d' % (seg, seg+4, s.r_amv.corr(s.r_sh), beta, len(s)))

print('\n' + '='*74)
print('二、领先性检验：AMV 增速 → 指数未来收益（Spearman IC）')
print('='*74)
print('   行=AMV 过去 N 日增速, 列=指数未来 M 日收益')
for idx_name, idx_col in [('上证', 'sh'), ('创业板', 'cy')]:
    print('\n  【%s】' % idx_name)
    print('        ' + ''.join('   M=%2d  ' % M for M in [1, 5, 20, 60]))
    for N in [1, 5, 20, 60, 120, 250]:
        g = d[idx_col].pct_change()
        sig = d.amv.pct_change(N)
        row = []
        for M in [1, 5, 20, 60]:
            fwd = d[idx_col].shift(-M)/d[idx_col] - 1
            x = pd.concat([sig, fwd], axis=1).dropna()
            if len(x) < 200:
                row.append('   n/a  '); continue
            ic = stats.spearmanr(x.iloc[:,0], x.iloc[:,1])[0]
            row.append('%+8.3f' % ic)
        print('   N=%3d ' % N + ''.join(row))

print('\n' + '='*74)
print('三、AMV 分位分组：AMV 相对 250 日区间的位置 → 未来 20 日收益')
print('='*74)
d['amv_pct'] = (d.amv - d.amv.rolling(250).min()) / (d.amv.rolling(250).max() - d.amv.rolling(250).min())
for idx_name, idx_col in [('上证', 'sh'), ('创业板', 'cy')]:
    print('\n  【%s】' % idx_name)
    x = d.dropna(subset=['amv_pct', idx_col]).copy()
    x['fwd20'] = x[idx_col].shift(-20)/x[idx_col]-1
    x = x.dropna(subset=['fwd20'])
    x['grp'] = pd.qcut(x.amv_pct, 5, labels=['最低20%','次低','中间','次高','最高20%'])
    t = x.groupby('grp', observed=True).fwd20.agg(['mean','median','count'])
    t['mean'] *= 100; t['median'] *= 100; t['胜率'] = x.groupby('grp', observed=True).fwd20.apply(lambda s: (s>0).mean())
    print(t.to_string(float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*74)
print('四、择时策略回测（T 日收盘出信号，T+1 收盘执行，含成本）')
print('='*74)

def backtest(signal, ret, cost_bp=2.0, name=''):
    """signal: 0/1 序列（T日收盘可得），收益用 T+1 日的 ret"""
    pos = signal.shift(1).fillna(0)
    pnl = pos*ret - pos.diff().abs().fillna(0)*cost_bp/10000
    pnl = pnl.dropna()
    if len(pnl) < 200 or pnl.std() == 0: return None
    cum = (1+pnl).cumprod()
    years = len(pnl)/252
    ann = cum.iloc[-1]**(1/years)-1
    sharpe = pnl.mean()/pnl.std()*np.sqrt(252)
    dd = (cum/cum.cummax()-1).min()
    expo = pos.mean()
    return dict(name=name, 年化=ann*100, Sharpe=sharpe, 最大回撤=dd*100, 仓位=expo*100,
                交易次数=int(pos.diff().abs().sum()), n=len(pnl))

for idx_name, idx_col in [('上证', 'sh'), ('创业板', 'cy')]:
    sub = d.dropna(subset=[idx_col]).copy()
    ret = sub[idx_col].pct_change()
    print('\n  ┌─ %s（%s ~ %s, n=%d）' % (idx_name, sub.date.iloc[0].date(), sub.date.iloc[-1].date(), len(sub)))
    res = [backtest(pd.Series(1, index=sub.index), ret, 0, '买入持有')]
    # 基准：指数自身均线择时
    for w in [20, 60, 120]:
        res.append(backtest((sub[idx_col] > sub[idx_col].rolling(w).mean()).astype(float), ret, 2, f'指数MA{w}择时'))
    # AMV 均线择时
    for w in [5, 10, 20, 60, 120]:
        res.append(backtest((sub.amv > sub.amv.rolling(w).mean()).astype(float), ret, 2, f'AMV-MA{w}上穿持有'))
    # AMV 增速择时
    for w in [5, 20, 60]:
        res.append(backtest((sub.amv.pct_change(w) > 0).astype(float), ret, 2, f'AMV {w}日增速>0'))
    # 背离：AMV 增速 - 指数增速
    for w in [20, 60]:
        feats = sub.amv.pct_change(w) - sub[idx_col].pct_change(w)
        res.append(backtest((feats > 0).astype(float), ret, 2, f'背离 AMV增速>指数增速({w}日)'))
    # 双确认：AMV 均线 且 指数均线
    res.append(backtest(((sub.amv > sub.amv.rolling(20).mean()) & (sub[idx_col] > sub[idx_col].rolling(60).mean())).astype(float), ret, 2, 'AMV-MA20 且 指数MA60'))
    # 逆向：AMV 分位低
    res.append(backtest((sub.amv_pct < 0.2).astype(float), ret, 2, 'AMV 250日分位<20% 逆向买入'))
    res.append(backtest((sub.amv_pct > 0.8).astype(float), ret, 2, 'AMV 250日分位>80% 顺势买入'))

    dfr = pd.DataFrame([r for r in res if r])
    print(dfr.to_string(index=False, float_format=lambda v: f'{v:,.2f}'))
    print('  └─' + '─'*60)
