# -*- coding: utf-8 -*-
"""完整风险指标 + 自适应阈值改造"""
import numpy as np
import pandas as pd
pd.set_option('display.width', 260)

amv = pd.read_csv('0amv_daily_261113.csv', encoding='utf-8-sig', parse_dates=['date'])
amv = amv[['date','close']].rename(columns={'close':'amv'}).sort_values('date')
sh = pd.read_csv('idx_sh000001.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'sh'})
cy = pd.read_csv('idx_sz399006.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'cy'})
d = amv.merge(sh, on='date', how='inner').merge(cy, on='date', how='left').sort_values('date').reset_index(drop=True)
d['amv_r'] = d.amv.pct_change()
d['amv_sd'] = d.amv_r.rolling(60).std()

def run(df, col, entry_sig, exit_sig, lag=1, max_hold=250, cost_bp=2.0):
    """逐日状态机，返回日频净值序列与交易列表"""
    px = df[col].values; n = len(df)
    pos = np.zeros(n); trades = []
    i = 0; holding = False; bi = None
    for i in range(n):
        if not holding:
            if entry_sig[i]:
                bi = i + lag
                if bi >= n: break
                holding = True; pos[bi] = 1; hold_start = bi
        else:
            if (exit_sig[i] and i > hold_start) or (i - hold_start) >= max_hold:
                si = min(i + lag, n-1)
                pos[si] = 1 if si > i else 1   # 卖出日在场
                trades.append((bi, si))
                holding = False
                # 卖出后清空
                pos[si] = 0
    # 重建 pos（简单法：按 trades 填充）
    pos = np.zeros(n)
    for bi, si in trades:
        pos[bi:si] = 1
    r = np.r_[0, px[1:]/px[:-1]-1]
    pnl = pos*r - np.abs(np.diff(np.r_[0, pos]))*cost_bp/10000
    cum = np.cumprod(1+pnl)
    yrs = n/252
    ret_tr = [px[si]/px[bi]-1-cost_bp*2/10000 for bi, si in trades]
    return dict(年化=(cum[-1]**(1/yrs)-1)*100, Sharpe=pnl.mean()/pnl.std()*np.sqrt(252),
                回撤=(cum/np.maximum.accumulate(cum)-1).min()*100, 仓位=pos.mean()*100,
                笔数=len(trades), 胜率=(np.array(ret_tr)>0).mean()*100 if trades else np.nan,
                平均单笔=np.mean(ret_tr)*100 if trades else np.nan,
                平均持仓=np.mean([si-bi for bi,si in trades]) if trades else np.nan), cum

print('='*92)
print('A. 三种方案完整对比（上证）')
print('='*92)
for lab, s0 in [('1993-2026','1993-01-01'), ('2016-2026','2016-01-01')]:
    s = d[d.date>=s0].dropna(subset=['sh']).reset_index(drop=True)
    ar = s.amv_r.values; n = len(s)
    print('\n【%s】n=%d' % (lab, n))
    rows = []

    # 1 买入持有
    r = s.sh.pct_change().fillna(0).values
    cum = np.cumprod(1+r)
    rows.append(dict(方案='买入持有', 年化=((cum[-1]**(252/n))-1)*100, Sharpe=r.mean()/r.std()*np.sqrt(252),
                     回撤=(cum/np.maximum.accumulate(cum)-1).min()*100, 仓位=100, 笔数=1,
                     胜率=np.nan, 平均单笔=np.nan, 平均持仓=np.nan))

    # 2 大哥规则
    ent = (ar >= 0.04); ext = (ar <= -0.023)
    st, cum = run(s, 'sh', ent, ext, max_hold=250)
    rows.append(dict(方案='大哥规则 4%/-2.3%', **st))

    # 3 只入场 + 固定持有 20 天
    st, cum = run(s, 'sh', ent, np.zeros(n, bool), max_hold=20)
    rows.append(dict(方案='只入场+持有20天', **st))

    # 4 只入场 + 固定持有 10 天
    st, cum = run(s, 'sh', ent, np.zeros(n, bool), max_hold=10)
    rows.append(dict(方案='只入场+持有10天', **st))

    # 5 自适应阈值（1.8σ 入场 / -1.0σ 出场）
    ent2 = (ar >= 1.8*s.amv_sd.values); ext2 = (ar <= -1.0*s.amv_sd.values)
    st, cum = run(s, 'sh', ent2, ext2, max_hold=250)
    rows.append(dict(方案='自适应 1.8σ/-1.0σ', **st))

    # 6 自适应 + 持有20天
    st, cum = run(s, 'sh', ent2, np.zeros(n, bool), max_hold=20)
    rows.append(dict(方案='自适应入场+持有20天', **st))

    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*92)
print('B. 三种方案完整对比（创业板）')
print('='*92)
for lab, s0 in [('2011-2026','2011-01-01'), ('2016-2026','2016-01-01')]:
    s = d[d.date>=s0].dropna(subset=['cy']).reset_index(drop=True)
    ar = s.amv_r.values; n = len(s)
    print('\n【%s】n=%d' % (lab, n))
    rows = []
    r = s.cy.pct_change().fillna(0).values
    cum = np.cumprod(1+r)
    rows.append(dict(方案='买入持有', 年化=((cum[-1]**(252/n))-1)*100, Sharpe=r.mean()/r.std()*np.sqrt(252),
                     回撤=(cum/np.maximum.accumulate(cum)-1).min()*100, 仓位=100, 笔数=1,
                     胜率=np.nan, 平均单笔=np.nan, 平均持仓=np.nan))
    ent = (ar >= 0.04); ext = (ar <= -0.023)
    st, cum = run(s, 'cy', ent, ext); rows.append(dict(方案='大哥规则 4%/-2.3%', **st))
    st, cum = run(s, 'cy', ent, np.zeros(n, bool), max_hold=20); rows.append(dict(方案='只入场+持有20天', **st))
    ent2 = (ar >= 1.8*s.amv_sd.values); ext2 = (ar <= -1.0*s.amv_sd.values)
    st, cum = run(s, 'cy', ent2, ext2); rows.append(dict(方案='自适应 1.8σ/-1.0σ', **st))
    st, cum = run(s, 'cy', ent2, np.zeros(n, bool), max_hold=20); rows.append(dict(方案='自适应入场+持有20天', **st))
    print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*92)
print('C. 为什么 4% 越来越难触发：4% 相当于多少个标准差')
print('='*92)
d['z'] = d.amv_r / d.amv_sd
for seg in range(1995, 2030, 5):
    s = d[(d.date.dt.year>=seg)&(d.date.dt.year<seg+5)]
    if len(s)<100: continue
    print('  %d-%d: AMV 日波动 %.2f%%   4%% 相当于 %.1fσ   触发频率 %.1f%%'
          % (seg, seg+4, s.amv_r.std()*100, 0.04/s.amv_r.std(), (s.amv_r>=0.04).mean()*100))
