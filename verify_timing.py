# -*- coding: utf-8 -*-
"""核对：各种回测的执行时点是否真的做到了「T日收盘确认 → T+1 买入」"""
import numpy as np
import pandas as pd
pd.set_option('display.width', 250)

x = pd.read_csv('data/amv_daily.csv', parse_dates=['date']).sort_values('date').reset_index(drop=True)
cy = pd.read_csv('data/index_cyb_ohlcv.csv', parse_dates=['date'])
cy.columns = [c.strip().lower() for c in cy.columns]
cy = cy[['date','open','high','low','close']].sort_values('date').reset_index(drop=True)
d = x.merge(cy, on='date', how='inner').sort_values('date').reset_index(drop=True)
d = d[d.date >= '2016-01-01'].reset_index(drop=True)
d['amv_r'] = d['c'].pct_change()
d['cy_r'] = d['close'].pct_change()
d['cy_intra'] = d['close'] / d['open'] - 1
d['cy_gap'] = d['open'] / d['close'].shift(1) - 1
yrs = len(d) / 252
px = d['close'].values
po = d['open'].values
r_cc = d['cy_r'].values
r_io = d['cy_intra'].values


def bt(mode, hold=20, stop=-0.03, entry_col=None):
    sig_v = d[entry_col if entry_col else 'amv_r'].values
    n = len(d)
    day = np.zeros(n)
    tr = []
    i = 0
    while i < n:
        if np.isnan(sig_v[i]) or sig_v[i] < 0.04:
            i += 1; continue
        if mode == 'close_T':
            if i + 1 >= n: break
            buy = px[i]; start = i + 1
        elif mode == 'open_T1':
            if i + 1 >= n: break
            buy = po[i + 1]; start = i + 1
        else:
            if i + 1 >= n: break
            buy = px[i + 1]; start = i + 2
        end = min(start + hold - 1, n - 1)
        si = end
        for t in range(start, end + 1):
            if px[t] / buy - 1 <= stop:
                si = t; break
        if si < start: si = start
        if mode == 'close_T':
            for t in range(start, si + 1):
                day[t] = r_cc[t]
        elif mode == 'open_T1':
            day[i + 1] = r_io[i + 1]
            for t in range(i + 2, si + 1):
                day[t] = r_cc[t]
        else:
            for t in range(start, si + 1):
                day[t] = r_cc[t]
        tr.append(dict(信号日=d.date.iloc[i].date(), 买入=d.date.iloc[min(i+1,n-1)].date(),
                       卖出=d.date.iloc[si].date(), 收益=px[si]/buy-1))
        i = si + 1
    nav = np.cumprod(1 + day)
    tt = pd.DataFrame(tr)
    s = dict(年化=(nav[-1] ** (1 / yrs) - 1) * 100,
             Sharpe=(day.mean() / day.std() * np.sqrt(252)) if day.std() > 0 else 0,
             回撤=(nav / np.maximum.accumulate(nav) - 1).min() * 100,
             笔数=len(tt), 胜率=(tt.收益 > 0).mean() * 100, 平均单笔=tt.收益.mean() * 100)
    return s, day


print('=' * 96)
print('核对一：AMV ≥+4% 信号，三种买入时点（创业板 2016-2026，零成本口径便于横向比较）')
print('=' * 96)
print('  A T日收盘买  → 不可执行（收盘后才知道结果），仅作上限参考')
print('  B T+1开盘买  → 可执行（次日开盘就买，吃到隔夜跳空）')
print('  C T+1收盘买  → 可执行且最保守（次日收盘才买）')
rows = []
for m, lab in [('close_T', 'A T日收盘买（前视）'), ('open_T1', 'B T+1开盘买'), ('close_T1', 'C T+1收盘买')]:
    s, _ = bt(m)
    rows.append(dict(口径=lab, **s))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '=' * 96)
print('核对二：legacy 脚本口径诊断')
print('=' * 96)
print('''  1. amv_test.py（均线择时）:  pos = signal.shift(1); pnl = pos * ret
     pnl[T+1] = close[T+1]/close[T] - 1
     → 等价于「T 日收盘买入」← 前视偏差（T 日收盘后才知道是否上穿均线）
     → 该脚本给出的均线战法数字（年化 12.03%/5.96% 等）全部虚高

  2. rule_full / rule_decompose / rule_test（大哥规则与改进版）:
     单笔收益 ret = px[si]/px[bi]，bi = T+1 → 单笔口径正确
     但净值 pos[bi:si]=1 有切片 bug → 把买入日涨幅计入，净值虚高
     （已在 src/backtest.py 修正为 pos[bi+1:si+1]=1）''')

print('\n' + '=' * 96)
print('核对三：严格口径 C（T+1收盘买）下，阈值信号 vs 官方均线战法')
print('=' * 96)
d['ma5'] = (d['c'] > d['c'].rolling(5).mean()).astype(float)
d['ma10'] = (d['c'] > d['c'].rolling(10).mean()).astype(float)
d['ma20'] = (d['c'] > d['c'].rolling(20).mean()).astype(float)
d['ma60'] = (d['c'] > d['c'].rolling(60).mean()).astype(float)
rows = []
for col, lab in [('amv_r', 'AMV ≥+4%（Z哥阈值）'), ('ma5', '官方均线 MA5'), ('ma10', '官方均线 MA10'),
                 ('ma20', '官方均线 MA20'), ('ma60', '官方均线 MA60')]:
    s, _ = bt('close_T1', entry_col=col)
    rows.append(dict(信号=lab, **s))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '=' * 96)
print('核对四：隔夜跳空 vs 当日日内（B 与 C 的收益差构成）')
print('=' * 96)
sig_idx = d[d.amv_r >= 0.04].index
on = d['cy_gap'].reindex([i+1 for i in sig_idx if i+1 < len(d)]).dropna()
ino = d['cy_intra'].reindex([i+1 for i in sig_idx if i+1 < len(d)]).dropna()
print('  T+1 隔夜跳空（开盘/昨收）: 均值 %+.2f%%  中位 %+.2f%%  为正占 %.0f%%'
      % (on.mean() * 100, on.median() * 100, (on > 0).mean() * 100))
print('  T+1 当日日内（收/开）:      均值 %+.2f%%  中位 %+.2f%%  为正占 %.0f%%'
      % (ino.mean() * 100, ino.median() * 100, (ino > 0).mean() * 100))
print('  → B(开盘买) 与 C(收盘买) 的差 = 当日日内涨幅')
