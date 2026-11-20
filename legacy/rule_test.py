# -*- coding: utf-8 -*-
"""大哥规则回测：AMV 单日 ≥ +4% 入场，≤ -2.3% 出场"""
import numpy as np
import pandas as pd
from scipy import stats
pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 200)

amv = pd.read_csv('0amv_daily_261113.csv', encoding='utf-8-sig', parse_dates=['date'])
amv = amv[['date','close']].rename(columns={'close':'amv'}).sort_values('date')
sh = pd.read_csv('idx_sh000001.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'sh'})
cy = pd.read_csv('idx_sz399006.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'cy'})
d = amv.merge(sh, on='date', how='inner').merge(cy, on='date', how='left').sort_values('date').reset_index(drop=True)
d['amv_r'] = d.amv.pct_change()

print('='*80)
print('0. 信号频率：AMV 单日涨跌幅分布')
print('='*80)
print('全样本 AMV 日收益: 均值 %+.3f%%  σ %.2f%%' % (d.amv_r.mean()*100, d.amv_r.std()*100))
for lab, s0, s1 in [('1993-2005','1993-01-01','2005-12-31'),('2006-2015','2006-01-01','2015-12-31'),('2016-2026','2016-01-01','2026-12-31')]:
    s = d[(d.date>=s0)&(d.date<=s1)].amv_r.dropna()
    print('  %-10s σ=%.2f%%   ≥+4%%: %4d 次(%.1f%%)   ≤-2.3%%: %4d 次(%.1f%%)'
          % (lab, s.std()*100, (s>=0.04).sum(), (s>=0.04).mean()*100, (s<=-0.023).sum(), (s<=-0.023).mean()*100))

def simulate(df, col, entry_th=0.04, exit_th=-0.023, lag=1, max_hold=250, cost_bp=2.0):
    """T日收盘出信号，T+lag日收盘执行"""
    px = df[col].values; ar = df.amv_r.values; dt = df.date.values
    n = len(df); trades = []; i = 0
    while i < n:
        if not np.isnan(ar[i]) and ar[i] >= entry_th:
            bi = i + lag
            if bi >= n: break
            j = bi + 1; si = None
            while j < n:
                if not np.isnan(ar[j]) and ar[j] <= exit_th:
                    si = min(j + lag, n-1); break
                if j - bi >= max_hold:
                    si = min(j + lag, n-1); break
                j += 1
            if si is None: si = n-1
            r = px[si]/px[bi] - 1 - cost_bp/10000
            trades.append(dict(买=pd.Timestamp(dt[bi]).date(), 卖=pd.Timestamp(dt[si]).date(),
                               收益=r, 天数=si-bi))
            i = si + 1
        else:
            i += 1
    return pd.DataFrame(trades)

def stats_of(tr, years, label):
    if len(tr) == 0: return None
    win = (tr.收益 > 0).mean()
    cum = (1+tr.收益).prod()
    pos = tr[tr.收益>0].收益; neg = tr[tr.收益<0].收益
    pf = pos.sum()/abs(neg.sum()) if len(neg) else np.inf
    return dict(区间=label, 笔数=len(tr), 胜率=win*100, 平均收益=tr.收益.mean()*100,
                中位=tr.收益.median()*100, 平均持仓天=tr.天数.mean(),
                累计= (cum-1)*100, 年化=((cum**(1/years))-1)*100 if cum>0 else -100,
                盈亏比=pf, 最差单笔=tr.收益.min()*100, 最好单笔=tr.收益.max()*100)

print('\n' + '='*80)
print('1. 大哥规则：AMV ≥+4% 入场 / ≤-2.3% 出场（T+1 收盘执行，2bp 成本）')
print('='*80)
for nm, col in [('上证','sh'), ('创业板','cy')]:
    sub = d.dropna(subset=[col]).reset_index(drop=True)
    print('\n【%s】' % nm)
    rows = []
    for lab, s0, s1 in [('全样本','1993-01-01','2026-12-31'),('1993-2005','1993-01-01','2005-12-31'),
                        ('2006-2015','2006-01-01','2015-12-31'),('2016-2026','2016-01-01','2026-12-31')]:
        s = sub[(sub.date>=s0)&(sub.date<=s1)]
        if len(s) < 200: continue
        tr = simulate(s.reset_index(drop=True), col)
        st = stats_of(tr, len(s)/252, lab)
        if st: rows.append(st)
    # 买入持有对照
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))
    bh = sub[col].iloc[-1]/sub[col].iloc[0]-1
    print('   对照 买入持有: 全样本累计 %+.0f%%  年化 %+.2f%%'
          % (bh*100, ((1+bh)**(252/len(sub))-1)*100))

print('\n' + '='*80)
print('2. 逐笔明细（近10年，上证）')
print('='*80)
sub = d[d.date>='2016-01-01'].dropna(subset=['sh']).reset_index(drop=True)
tr = simulate(sub, 'sh')
if len(tr):
    print(tr.to_string(index=False, float_format=lambda v: f'{v*100:+.2f}%' if abs(v)<1 else f'{v:.0f}'))

print('\n' + '='*80)
print('3. 拆解：入场信号本身有没有 alpha（事件研究，AMV ≥+4% 后）')
print('='*80)
for nm, col in [('上证','sh'), ('创业板','cy')]:
    print('\n【%s】' % nm)
    for lab, s0, s1 in [('全样本','1993-01-01','2026-12-31'), ('2016-2026','2016-01-01','2026-12-31')]:
        s = d[(d.date>=s0)&(d.date<=s1)].dropna(subset=[col]).reset_index(drop=True)
        ev = s[s.amv_r >= 0.04]
        if len(ev) < 20: continue
        out = []
        for N in [1, 5, 10, 20, 60]:
            fwd = s[col].shift(-N)/s[col]-1
            v = fwd[ev.index].dropna()
            out.append('%d日 %+.2f%%(胜%.2f)' % (N, v.mean()*100, (v>0).mean()))
        base = []
        for N in [20]:
            fwd = s[col].shift(-N)/s[col]-1
            base.append('基准20日 %+.2f%%' % (fwd.dropna().mean()*100))
        print('  %-9s n=%4d  %s  | %s' % (lab, len(ev), '  '.join(out), base[0]))

print('\n' + '='*80)
print('4. 参数敏感性：入场阈值 × 出场阈值（全样本，年化% / 胜率%）')
print('='*80)
for nm, col in [('上证','sh'), ('创业板','cy')]:
    sub = d.dropna(subset=[col]).reset_index(drop=True)
    print('\n【%s】 行为入场阈值, 列为出场阈值' % nm)
    print('         ' + ''.join('%16s' % f'{e*100:.1f}%' for e in [-0.01,-0.015,-0.023,-0.03,-0.04]))
    for en in [0.02, 0.03, 0.04, 0.05, 0.06]:
        cells = []
        for ex in [-0.01,-0.015,-0.023,-0.03,-0.04]:
            tr = simulate(sub, col, en, ex)
            if len(tr) < 5: cells.append('%16s' % 'n/a'); continue
            cum = (1+tr.收益).prod(); yrs = len(sub)/252
            ann = (cum**(1/yrs)-1)*100 if cum>0 else -100
            cells.append('%16s' % f'{ann:+.1f}/{((tr.收益>0).mean()*100):.0f}')
        print('  入场 %+.0f%%' % (en*100) + ''.join(cells))
