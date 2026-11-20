# -*- coding: utf-8 -*-
"""v4.0 最终确认：跨标的（含各自OHLC）+ 逐年 + 邻域稳定性"""
import numpy as np
import pandas as pd
pd.set_option('display.width', 280)

amv = pd.read_csv('data/amv_daily.csv', parse_dates=['date']).sort_values('date').reset_index(drop=True)
amv['amv_r'] = amv['c'].pct_change()
amv['amv_sd60'] = amv['amv_r'].rolling(60).std()

def prep_ohlc(path, col):
    df = pd.read_csv(path, parse_dates=['date'])
    df.columns = [c.strip().lower() for c in df.columns]
    df = df[['date','open','high','low','close']].copy()
    df['px'] = df['close']; df[col] = df['close']
    return df.sort_values('date').reset_index(drop=True)

cy = prep_ohlc('data/index_cyb_ohlcv.csv', 'cy')
kc = prep_ohlc('data/index_kc50_ohlcv.csv', 'kc')
sh = prep_ohlc('data/index_sse_ohlcv.csv', 'sh')

def build(tgt, start='2016-01-01'):
    a = amv.merge(tgt, on='date', how='inner').sort_values('date').reset_index(drop=True)
    a = a[a.date >= start].reset_index(drop=True)
    a['dd250'] = a['px']/a['px'].rolling(250).max() - 1
    return a

def sim(s, entry, hold=20, stop=-0.03, mode='open_T1', w=None, cost_bp=2.0):
    px = s['px'].values; op = s['open'].values; n = len(s)
    sig = entry.values if hasattr(entry, 'values') else np.asarray(entry)
    ww = (w.values if hasattr(w, 'values') else np.asarray(w)) if w is not None else np.ones(n)
    day = np.zeros(n); tr = []; i = 0
    while i < n:
        if not np.isnan(sig[i]) and sig[i]:
            if mode == 'open_T1':
                if i+1 >= n: break
                buy = op[i+1]; t0 = i+1
            else:
                if i+1 >= n: break
                buy = px[i+1]; t0 = i+2
            last = min(t0+hold-1, n-1); si = last
            for t in range(t0, last+1):
                if px[t]/buy-1 <= stop: si = t; break
            if si < t0: si = t0
            wg = ww[i]
            if mode == 'open_T1':
                day[i+1] = (px[i+1]/buy-1)*wg - cost_bp/10000
                for t in range(i+2, si+1):
                    day[t] = (px[t]/px[t-1]-1)*wg - (cost_bp/10000 if t == si else 0)
            else:
                for t in range(t0, si+1):
                    day[t] = (px[t]/px[t-1]-1)*wg - (cost_bp/10000 if t == si else 0)
            tr.append((s.date.iloc[i+1].date(), s.date.iloc[si].date(), px[si]/buy-1))
            i = si + 1
        else: i += 1
    nav = np.cumprod(1+day); tt = pd.DataFrame(tr, columns=['b','s','r'])
    yrs = n/252
    return dict(年化=(nav[-1]**(1/yrs)-1)*100,
                Sharpe=day.mean()/day.std()*np.sqrt(252) if day.std()>0 else 0,
                回撤=(nav/np.maximum.accumulate(nav)-1).min()*100,
                笔数=len(tt), 胜率=(tt.r>0).mean()*100 if len(tt) else np.nan,
                平均单笔=tt.r.mean()*100 if len(tt) else np.nan,
                仓位=(day!=0).mean()*100, 复利=nav[-1], nav=nav, trades=tt)

def wt_tier(s):
    w = pd.Series(1.0, index=s.index)
    w[(s.dd250 > -0.25) & (s.dd250 <= -0.15)] = 0.5
    w[(s.dd250 > -0.15) & (s.dd250 <= -0.08)] = 0.5
    w[(s.dd250 > -0.08) & (s.dd250 <= -0.02)] = 0.0
    return w

print('='*112)
print('一、跨标的对比（各自指数的开盘价，含 2bp 成本，T+1开盘买）')
print('='*112)
print('  %-34s %-22s %-22s %-22s' % ('方案','创业板 2016-2026','科创50 2020-2026','上证 2016-2026'))
CANDS = [
    ('v3.0  4% / 持20 / 止损3% / 满仓', 0.04, 20, -0.03, None),
    ('v4.1  5% / 持20 / 止损3% / 满仓', 0.05, 20, -0.03, None),
    ('v4.2  5% / 持20 / 止损3% / 分层仓位', 0.05, 20, -0.03, 'tier'),
    ('v4.3  5% / 持30 / 止损3% / 分层仓位', 0.05, 30, -0.03, 'tier'),
    ('v4.4  5% / 持20 / 止损5% / 分层仓位', 0.05, 20, -0.05, 'tier'),
    ('v4.5  z2.0σ / 持20 / 止损3% / 满仓', 'z2.0', 20, -0.03, None),
    ('v4.6  z2.5σ / 持20 / 止损3% / 满仓', 'z2.5', 20, -0.03, None),
    ('v4.7  z2.5σ / 持15 / 止损3% / 满仓', 'z2.5', 15, -0.03, None),
]
for nm, th, hold, stop, wm in CANDS:
    line = '  %-34s' % nm
    for tgt, tname, st in [(cy,'创业板','2016-01-01'), (kc,'科创50','2020-01-01'), (sh,'上证','2016-01-01')]:
        s = build(tgt, st)
        if isinstance(th, str):
            e = (s.amv_r >= float(th[1:])*s.amv_sd60).astype(float)
        else:
            e = (s.amv_r >= th).astype(float)
        w = wt_tier(s) if wm == 'tier' else None
        r = sim(s, e, hold=hold, stop=stop, mode='open_T1', w=w)
        line += ' %+6.1f%%/S%.2f' % (r['年化'], r['Sharpe'])
    print(line)

print('\n' + '='*112)
print('二、v4.1 (5%/持20/止损3%) 逐年收益（创业板）')
print('='*112)
s = build(cy, '2016-01-01')
for th, lab in [(0.04, 'v3.0 4%'), (0.05, 'v4.1 5%')]:
    e = (s.amv_r >= th).astype(float)
    r = sim(s, e, hold=20, stop=-0.03, mode='open_T1')
    dd = s.copy(); dd['sr'] = pd.Series(r['nav']).pct_change().fillna(0).values
    bh = s.groupby(s.date.dt.year).close.apply(lambda x: x.iloc[-1]/x.iloc[0]-1)
    ann = dd.groupby(dd.date.dt.year).sr.apply(lambda x: (1+x).prod()-1)
    print('  %-8s %s' % (lab, ' '.join('%d:%+5.1f%%'%(y,v*100) for y,v in ann.items())))
    print('  %-8s 指数 %s' % ('', ' '.join('%d:%+5.1f%%'%(y,v*100) for y,v in bh.items())))
    print('  %-8s 跑赢年数 %d/11   策略总复利 %.2f 倍  年化 %.2f%%' % ('', int((ann>bh).sum()), r['复利'], r['年化']))

print('\n' + '='*112)
print('三、阈值邻域稳定性（创业板全样本，持有20，止损-3%）')
print('='*112)
rows = []
for th in [0.03,0.035,0.04,0.045,0.05,0.055,0.06,0.07]:
    e = (s.amv_r >= th).astype(float)
    r = sim(s, e, hold=20, stop=-0.03, mode='open_T1')
    # 样本外
    so = build(cy, '2022-01-01')
    eo = (so.amv_r >= th).astype(float)
    ro = sim(so, eo, hold=20, stop=-0.03, mode='open_T1')
    rows.append(dict(阈值=f'{th*100:.1f}%', 全样本年化=r['年化'], 全样本Sharpe=r['Sharpe'],
                     全样本笔数=r['笔数'], 样本外年化=ro['年化'], 样本外Sharpe=ro['Sharpe'],
                     样本外笔数=ro['笔数'], 样本外回撤=ro['回撤']))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*112)
print('四、AMV 日波动率演变 → 阈值该定多少')
print('='*112)
for yr in range(1996, 2026, 3):
    sub = s[(s.date.dt.year>=yr)&(s.date.dt.year<yr+3)]
    if len(sub)<100: continue
    sd = sub.amv_r.std()
    print('  %d-%d  σ=%.2f%%   4%%=%.1fσ  5%%=%.1fσ  触发率(4%%)=%.1f%%  触发率(5%%)=%.1f%%'
          % (yr, yr+2, sd*100, 0.04/sd, 0.05/sd, (sub.amv_r>=0.04).mean()*100, (sub.amv_r>=0.05).mean()*100))
