# -*- coding: utf-8 -*-
"""v4.0 验证：统一口径 + 参数平台 + 跨标的 + 逐年"""
import numpy as np
import pandas as pd
from scipy import stats
pd.set_option('display.width', 280)

# ---- 数据：涨跌幅在全量 AMV 上算，再与指数合并 ----
amv = pd.read_csv('data/amv_daily.csv', parse_dates=['date']).sort_values('date').reset_index(drop=True)
amv['amv_r'] = amv['c'].pct_change()
amv['amv_sd60'] = amv['amv_r'].rolling(60).std()
amv['amv_3d'] = amv['amv_r'].rolling(3).sum()

cy = pd.read_csv('data/index_cyb_ohlcv.csv', parse_dates=['date'])
cy.columns = [c.strip().lower() for c in cy.columns]
cy = cy[['date','open','high','low','close']].sort_values('date').reset_index(drop=True)
kc = pd.read_csv('data/index_kc50.csv', parse_dates=['date']).rename(columns={'close':'kc'})
sh = pd.read_csv('data/index_sse.csv', parse_dates=['date']).rename(columns={'close':'sh'})

d = amv.merge(cy, on='date', how='inner').merge(kc, on='date', how='left').merge(sh, on='date', how='left')
d = d.sort_values('date').reset_index(drop=True)
d['dd250'] = d['close']/d['close'].rolling(250).max() - 1


def sim(s, price, entry, hold=20, stop=-0.03, mode='open_T1', w=None, cost_bp=2.0):
    """统一口径：T日信号 → T+1开盘买 → 持 hold 个交易日（T+1..T+hold）→ 卖出
       mode='close_T1' 时 T+1 收盘买，收益从 T+2 起算"""
    px = s[price].values
    op = s['open'].values
    n = len(s)
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
            last = min(t0 + hold - 1, n-1); si = last
            for t in range(t0, last+1):
                if px[t]/buy - 1 <= stop:
                    si = t; break
            if si < t0: si = t0
            wgt = ww[i]
            if mode == 'open_T1':
                day[i+1] = (px[i+1]/buy-1)*wgt - cost_bp/10000
                for t in range(i+2, si+1):
                    day[t] = (px[t]/px[t-1]-1)*wgt - (cost_bp/10000 if t == si else 0)
            else:
                for t in range(t0, si+1):
                    day[t] = (px[t]/px[t-1]-1)*wgt - (cost_bp/10000 if t == si else 0)
            tr.append((s.date.iloc[i+1].date(), s.date.iloc[si].date(), px[si]/buy-1, si-i))
            i = si + 1
        else:
            i += 1
    nav = np.cumprod(1+day); tt = pd.DataFrame(tr, columns=['b','s','r','d'])
    yrs = n/252
    return dict(年化=(nav[-1]**(1/yrs)-1)*100,
                Sharpe=day.mean()/day.std()*np.sqrt(252) if day.std()>0 else 0,
                回撤=(nav/np.maximum.accumulate(nav)-1).min()*100,
                笔数=len(tt), 胜率=(tt.r>0).mean()*100 if len(tt) else np.nan,
                平均单笔=tt.r.mean()*100 if len(tt) else np.nan,
                仓位=(day!=0).mean()*100, 复利=nav[-1], nav=nav, trades=tt)


def sig_fixed(s, th=0.04): return (s.amv_r >= th).astype(float)
def sig_z(s, k=1.8):      return (s.amv_r >= k*s.amv_sd60).astype(float)
def sig_cum(s, th=0.08):  return (s.amv_3d >= th).astype(float)
def wt_tier(s):
    w = pd.Series(1.0, index=s.index)
    w[(s.dd250 > -0.25) & (s.dd250 <= -0.15)] = 0.5
    w[(s.dd250 > -0.15) & (s.dd250 <= -0.08)] = 0.5
    w[(s.dd250 > -0.08) & (s.dd250 <= -0.02)] = 0.0
    return w
def wt_deep(s): return (s.dd250 <= -0.25).astype(float)


print('='*112)
print('一、统一口径后：v3.0 基线真实数字（创业板 2016-2026）')
print('='*112)
s = d[d.date >= '2016-01-01'].reset_index(drop=True)
for lab, mode in [('T+1 开盘买', 'open_T1'), ('T+1 收盘买', 'close_T1')]:
    r = sim(s, 'close', sig_fixed(s), hold=20, stop=-0.03, mode=mode)
    print('  %-12s 年化 %+.2f%%  Sharpe %.2f  回撤 %.1f%%  笔数 %d  胜率 %.1f%%  平均单笔 %+.2f%%  复利 %.2f 倍'
          % (lab, r['年化'], r['Sharpe'], r['回撤'], r['笔数'], r['胜率'], r['平均单笔'], r['复利']))

print('\n' + '='*112)
print('二、参数平台矩阵（创业板全样本 2016-2026，T+1开盘买，Sharpe）')
print('='*112)
rows = []
for kind, fn, params in [('固定阈值', sig_fixed, [0.03,0.04,0.05,0.06]),
                          ('自适应z', sig_z, [1.2,1.5,1.8,2.0,2.5]),
                          ('3日累计', sig_cum, [0.04,0.06,0.08,0.10])]:
    for p in params:
        for hold in [15, 20, 30, 40]:
            for stop in [-0.03, -0.05]:
                r = sim(s, 'close', fn(s, p), hold=hold, stop=stop, mode='open_T1')
                rows.append(dict(信号=f'{kind}{p}', 持有=hold, 止损=stop, 年化=r['年化'],
                                 Sharpe=r['Sharpe'], 回撤=r['回撤'], 笔数=r['笔数'], 胜率=r['胜率']))
grid = pd.DataFrame(rows)
for kind in ['固定阈值','自适应z','3日累计']:
    sub = grid[grid.信号.str.startswith(kind)]
    piv = sub.pivot_table(index='信号', columns=['持有','止损'], values='Sharpe')
    print(f'\n【{kind}】Sharpe 矩阵')
    print(piv.to_string(float_format=lambda v: f'{v:.2f}'))

print('\n' + '='*112)
print('三、样本内/样本外（2016-2021 / 2022-2026）')
print('='*112)
rows = []
for kind, fn, params in [('固定阈值', sig_fixed, [0.03,0.04,0.05,0.06]),
                          ('自适应z', sig_z, [1.2,1.5,1.8,2.0,2.5]),
                          ('3日累计', sig_cum, [0.04,0.06,0.08,0.10])]:
    for p in params:
        for hold in [15, 20, 30, 40]:
            for stop in [-0.03, -0.05]:
                out = {}
                for lab, st, en in [('IS','2016-01-01','2021-12-31'), ('OOS','2022-01-01','2026-12-31')]:
                    sub = d[(d.date>=st)&(d.date<=en)].reset_index(drop=True)
                    out[lab] = sim(sub, 'close', fn(sub, p), hold=hold, stop=stop, mode='open_T1')
                rows.append(dict(信号=f'{kind}{p}', 持有=hold, 止损=stop,
                                 IS年化=out['IS']['年化'], IS夏普=out['IS']['Sharpe'],
                                 OOS年化=out['OOS']['年化'], OOS夏普=out['OOS']['Sharpe'],
                                 OOS回撤=out['OOS']['回撤'], OOS笔数=out['OOS']['笔数']))
sp = pd.DataFrame(rows)
print(sp.sort_values('OOS夏普', ascending=False).head(12).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))
print('\n固定阈值 4% 的样本外表现:')
print(sp[(sp.信号=='固定阈值0.04')].to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*112)
print('四、候选方案：跨标的 + 仓位分层')
print('='*112)
CANDS = [
    ('v3.0 固定4%/持20/止损3%/满仓', sig_fixed, 0.04, 20, -0.03, None),
    ('v4.1 自适应1.8σ/持30/止损5%/满仓', sig_z, 1.8, 30, -0.05, None),
    ('v4.2 自适应1.8σ/持30/止损5%/分层', sig_z, 1.8, 30, -0.05, 'tier'),
    ('v4.3 3日累计8%/持30/止损3%/满仓', sig_cum, 0.08, 30, -0.03, None),
    ('v4.4 3日累计8%/持30/止损3%/分层', sig_cum, 0.08, 30, -0.03, 'tier'),
    ('v4.5 自适应2.0σ/持30/止损3%/分层', sig_z, 2.0, 30, -0.03, 'tier'),
]
for nm, fn, p, hold, stop, wm in CANDS:
    line = '%-32s' % nm
    for tgt, tname in [('close','创业板'), ('kc','科创50'), ('sh','上证')]:
        if tgt != 'close':
            sub = d[(d.date>='2020-01-01')].dropna(subset=[tgt]).reset_index(drop=True)
        else:
            sub = d[d.date>='2016-01-01'].reset_index(drop=True)
        w = wt_tier(sub) if wm == 'tier' else None
        r = sim(sub, tgt, fn(sub, p), hold=hold, stop=stop, mode='open_T1', w=w)
        line += ' | %s %+.1f%%/S%.2f' % (tname, r['年化'], r['Sharpe'])
    print(line)

print('\n' + '='*112)
print('五、候选方案逐年收益（创业板）')
print('='*112)
for nm, fn, p, hold, stop, wm in CANDS:
    s2 = d[d.date>='2016-01-01'].reset_index(drop=True)
    w = wt_tier(s2) if wm=='tier' else None
    r = sim(s2, 'close', fn(s2,p), hold=hold, stop=stop, mode='open_T1', w=w)
    dd = s2.copy(); dd['sr'] = r['nav'].pct_change().fillna(0).values
    ann = dd.groupby(dd.date.dt.year).sr.apply(lambda x:(1+x).prod()-1)
    print('  %-32s %s' % (nm, ' '.join('%d:%+.0f%%'%(y,v*100) for y,v in ann.items())))
