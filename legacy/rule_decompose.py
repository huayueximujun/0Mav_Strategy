# -*- coding: utf-8 -*-
"""拆解：出场规则到底是帮忙还是帮倒忙"""
import numpy as np
import pandas as pd
from scipy import stats
pd.set_option('display.width', 250)

amv = pd.read_csv('0amv_daily_261113.csv', encoding='utf-8-sig', parse_dates=['date'])
amv = amv[['date','close']].rename(columns={'close':'amv'}).sort_values('date')
sh = pd.read_csv('idx_sh000001.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'sh'})
cy = pd.read_csv('idx_sz399006.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'cy'})
d = amv.merge(sh, on='date', how='inner').merge(cy, on='date', how='left').sort_values('date').reset_index(drop=True)
d['amv_r'] = d.amv.pct_change()

# ---------- 1. 固定持有 N 天 vs -2.3% 出场 ----------
print('='*84)
print('1. 入场后"固定持有 N 天" vs "跌到 -2.3% 就卖"（近10年，T+1 收盘买入）')
print('='*84)
for nm, col in [('上证','sh'), ('创业板','cy')]:
    for lab, s0 in [('1993-2026','1993-01-01'), ('2016-2026','2016-01-01')]:
        s = d[(d.date>=s0)].dropna(subset=[col]).reset_index(drop=True)
        ent = s[s.amv_r >= 0.04].index
        ent = [i for i in ent if i+1 < len(s)]
        print('\n【%s / %s】入场信号 %d 次' % (nm, lab, len(ent)))
        rows = []
        for N in [1, 3, 5, 10, 20, 30, 40, 60]:
            r = []
            for i in ent:
                bi = i+1; si = min(bi+N, len(s)-1)
                r.append(s[col].iloc[si]/s[col].iloc[bi]-1)
            r = np.array(r)
            rows.append(dict(持有=N, 平均收益=r.mean()*100, 中位=np.median(r)*100,
                             胜率=(r>0).mean()*100, n=len(r)))
        print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

# ---------- 2. 出场信号后指数继续跌吗 ----------
print('\n' + '='*84)
print('2. 出场信号（AMV ≤ -2.3%）之后，指数是继续跌还是涨回来？')
print('='*84)
for nm, col in [('上证','sh'), ('创业板','cy')]:
    for lab, s0 in [('1993-2026','1993-01-01'), ('2016-2026','2016-01-01')]:
        s = d[(d.date>=s0)].dropna(subset=[col]).reset_index(drop=True)
        ev = s[s.amv_r <= -0.023].index
        ev = [i for i in ev if i+1 < len(s)]
        out = []
        for N in [1, 5, 10, 20]:
            r = [s[col].iloc[min(i+N, len(s)-1)]/s[col].iloc[i]-1 for i in ev]
            out.append('%d日 %+.2f%%' % (N, np.mean(r)*100))
        print('  %s %-10s n=%4d  %s' % (nm, lab, len(ev), '  '.join(out)))

# ---------- 3. 完整参数表 ----------
print('\n' + '='*84)
print('3. 参数敏感性：入场阈值（行）× 出场阈值（列），全样本 年化% / 胜率% / 笔数')
print('='*84)

def simulate(df, col, entry_th, exit_th, lag=1, max_hold=250, cost_bp=2.0):
    px = df[col].values; ar = df.amv_r.values; n = len(df)
    trades = []; i = 0
    while i < n:
        if not np.isnan(ar[i]) and ar[i] >= entry_th:
            bi = i+lag
            if bi >= n: break
            j = bi+1; si = None
            while j < n:
                if not np.isnan(ar[j]) and ar[j] <= exit_th:
                    si = min(j+lag, n-1); break
                if j-bi >= max_hold:
                    si = min(j+lag, n-1); break
                j += 1
            if si is None: si = n-1
            trades.append(px[si]/px[bi]-1-cost_bp/10000)
            i = si+1
        else:
            i += 1
    return np.array(trades)

for nm, col in [('上证','sh'), ('创业板','cy')]:
    s = d.dropna(subset=[col]).reset_index(drop=True)
    yrs = len(s)/252
    print('\n【%s】' % nm)
    print('        ' + ''.join('%18s' % f'出场{e*100:.1f}%' for e in [-0.01,-0.015,-0.023,-0.03,-0.04,-100]))
    for en in [0.02, 0.03, 0.04, 0.05, 0.06]:
        cells = []
        for ex in [-0.01,-0.015,-0.023,-0.03,-0.04,-100]:
            tr = simulate(s, col, en, ex)
            if len(tr) < 5: cells.append('%18s' % 'n/a'); continue
            cum = (1+tr).prod()
            ann = (cum**(1/yrs)-1)*100 if cum>0 else -100
            cells.append('%18s' % f'{ann:+.1f}%/{(tr>0).mean()*100:.0f}/n={len(tr)}')
        print(' 入场%+.0f%%' % (en*100) + ''.join(cells))
    print(' 注：最后一行 ex=-100%% 表示"不出场，一直拿到期末"')

# ---------- 4. 对照：入场后持有 20 天的策略整体表现 ----------
print('\n' + '='*84)
print('4. 如果只用入场信号、固定持有 20 天（不加出场），整体年化')
print('='*84)
for nm, col in [('上证','sh'), ('创业板','cy')]:
    s = d.dropna(subset=[col]).reset_index(drop=True)
    r = s[col].pct_change().values
    sig = (s.amv_r >= 0.04).values
    pos = np.zeros(len(s))
    for i in np.where(sig)[0]:
        if i+1 < len(s):
            pos[i+1:min(i+22, len(s))] = 1     # 持有 20 个交易日
    pnl = pd.Series(pos*r).fillna(0) - pd.Series(np.abs(np.diff(np.r_[0,pos]))*2/10000)
    cum = (1+pnl).cumprod()
    yrs = len(s)/252
    print('  %s: 年化 %+.2f%%  仓位占用 %.0f%%  Sharpe %.2f  最大回撤 %.1f%%  交易 %d 次'
          % (nm, (cum.iloc[-1]**(1/yrs)-1)*100, pos.mean()*100,
             pnl.mean()/pnl.std()*np.sqrt(252), (cum/cum.cummax()-1).min()*100, int(np.abs(np.diff(np.r_[0,pos])).sum()/2)))
