# -*- coding: utf-8 -*-
"""四种信号的实盘稳健性对比"""
import numpy as np
import pandas as pd
pd.set_option('display.width', 280)

raw = pd.read_csv('0amv_daily_261113.csv', encoding='utf-8-sig', parse_dates=['date']).sort_values('date')
raw['real_r'] = raw.close.pct_change()
raw['amt_r'] = raw.amount.pct_change()
raw['ema9'] = raw.amount.ewm(span=9, adjust=False).mean()
raw['ema_r'] = raw.ema9.pct_change()

cy = pd.read_csv('cy_with_vol.csv', parse_dates=['date'])[['date','close','volume']].rename(columns={'close':'cy','volume':'cyvol'})
sh = pd.read_csv('idx_sh000001.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'sh'})
d = raw.merge(cy, on='date', how='inner').merge(sh, on='date', how='left').sort_values('date').reset_index(drop=True)
d['cyvol_r'] = d.cyvol.pct_change()

def sim(df, col, sig, hold=20, stop=-0.03, lag=1, cost=2.0):
    px = df[col].values; s = sig.values; n = len(df)
    pos = np.zeros(n); tr = []; i = 0
    while i < n:
        if not np.isnan(s[i]) and s[i]:
            bi = min(i+lag, n-1); si = min(bi+hold, n-1)
            for j in range(bi+1, si+1):
                if px[j]/px[bi]-1 <= stop: si = j; break
            if si <= bi: si = min(bi+2, n-1)
            pos[bi:si] = 1; tr.append((bi, si)); i = si+1
        else:
            i += 1
    r = np.r_[0, px[1:]/px[:-1]-1]
    pnl = pos*r - np.abs(np.diff(np.r_[0, pos]))*cost/10000
    cum = np.cumprod(1+pnl); yrs = max(n/252, 0.5)
    t = np.array([px[si]/px[bi]-1 for bi, si in tr]) if tr else np.array([0])
    return dict(年化=(cum[-1]**(1/yrs)-1)*100 if cum[-1] > 0 else -99,
                Sharpe=pnl.mean()/pnl.std()*np.sqrt(252) if pnl.std() > 0 else 0,
                回撤=(cum/np.maximum.accumulate(cum)-1).min()*100,
                笔数=len(tr), 胜率=(t>0).mean()*100, 仓位=pos.mean()*100)

SIGS = {
    'A 真实AMV ≥+4%':      ('real_r', 0.04),
    'B 代理EMA9 ≥+4%':     ('ema_r', 0.04),
    'C 创业板量 ≥+20%':    ('cyvol_r', 0.20),
    'D 全市场成交额 ≥+5%': ('amt_r', 0.05),
}

print('='*104)
print('一、分时段稳定性（创业板，每段 3-4 年）—— 稳不稳就看这个')
print('='*104)
segs = [('2016-2019','2016-01-01','2019-12-31'), ('2020-2022','2020-01-01','2022-12-31'),
        ('2023-2026','2023-01-01','2026-12-31')]
hdr = '%-20s' % '信号'
for lab, _, _ in segs: hdr += '%22s' % lab
print(hdr)
print('%-20s' % '' + ''.join('%22s' % '年化/Sharpe/笔数' for _ in segs))
res = {}
for nm, (col, th) in SIGS.items():
    line = '%-20s' % nm
    vals = []
    for lab, s0, s1 in segs:
        s = d[(d.date>=s0)&(d.date<=s1)].dropna(subset=['cy']).reset_index(drop=True)
        if len(s) < 150: line += '%22s' % 'n/a'; continue
        r = sim(s, 'cy', (s[col] >= th))
        vals.append(r)
        line += '%22s' % ('%+.1f%%/%.2f/%d' % (r['年化'], r['Sharpe'], r['笔数']))
    res[nm] = vals
    print(line)

print('\n  ★ 稳健性判据：三段年化的最小值（Min）与离散度')
print('%-22s%12s%12s%12s%14s' % ('信号', '最差段年化', '最好段年化', '均值', '标准差(越小越稳)'))
for nm, vals in res.items():
    if len(vals) < 3: continue
    a = np.array([v['年化'] for v in vals])
    print('%-22s%11.1f%%%11.1f%%%11.1f%%%13.1f' % (nm, a.min(), a.max(), a.mean(), a.std()))

print('\n' + '='*104)
print('二、参数敏感性：阈值上下浮动 20%/50%，年化变化多少（创业板 2016-2026）')
print('='*104)
s = d[d.date>='2016-01-01'].dropna(subset=['cy']).reset_index(drop=True)
base_th = {'A 真实AMV ≥+4%': ('real_r', 0.04), 'B 代理EMA9 ≥+4%': ('ema_r', 0.04),
           'C 创业板量 ≥+20%': ('cyvol_r', 0.20), 'D 全市场成交额 ≥+5%': ('amt_r', 0.05)}
print('%-20s%10s%10s%10s%10s%10s' % ('信号', '×0.6', '×0.8', '基准', '×1.2', '×1.5'))
for nm, (col, th) in base_th.items():
    cells = []
    for k in [0.6, 0.8, 1.0, 1.2, 1.5]:
        r = sim(s, 'cy', (s[col] >= th*k))
        cells.append('%9.1f%%' % r['年化'])
    print('%-20s' % nm + ''.join(cells))

print('\n' + '='*104)
print('三、跨标的稳健性（同一方案用在三个指数上，2016-2026）')
print('='*104)
print('%-20s%26s%26s%26s' % ('信号', '上证', '创业板', '科创50'))
kc = pd.read_csv('idx_sh000688.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'kc'})
dk = d.merge(kc, on='date', how='left')
for nm, (col, th) in base_th.items():
    line = '%-20s' % nm
    for tgt in ['sh','cy','kc']:
        ss = dk[dk.date>='2016-01-01'].dropna(subset=[tgt]).reset_index(drop=True)
        if len(ss) < 300: line += '%26s' % 'n/a'; continue
        r = sim(ss, tgt, (ss[col] >= th))
        line += '%26s' % ('%+.1f%%/S%.2f' % (r['年化'], r['Sharpe']))
    print(line)

print('\n' + '='*104)
print('四、实盘可执行性')
print('='*104)
rows = []
for nm, (col, th) in base_th.items():
    r = sim(s, 'cy', (s[col] >= th))
    rows.append(dict(信号=nm, 笔数=r['笔数'], 每年笔数=round(r['笔数']/(len(s)/252),1),
                     仓位占用=r['仓位'], 回撤=r['回撤']))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.1f}'))
