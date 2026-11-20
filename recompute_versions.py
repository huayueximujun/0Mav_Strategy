# -*- coding: utf-8 -*-
"""各版本策略数字重算（用修复后的引擎，统一口径）"""
import numpy as np
import pandas as pd
pd.set_option('display.width', 240)

from src.data import merge_all
from src.signals import amv_surge, amv_drop
from src.backtest import run

print('='*96)
print('各版本统一重算（T 日收盘确认信号，T+1 执行，含 2bp 成本）')
print('='*96)

# ---------- 创业板 2016-2026 ----------
df = merge_all('2016-01-01').dropna(subset=['cyb']).reset_index(drop=True)
yrs = len(df)/252
print('\n【创业板 2016-01 ~ 2026-11，n=%d】' % len(df))
rows = []
# v1.0 大哥原版：+4%进 / -2.3%出
r = run(df, 'cyb', entry=amv_surge(df), exit_sig=amv_drop(df), stop=None).stats
rows.append(dict(版本='v1.0 大哥原版', 规则='+4%进 / -2.3%出', 年化=r['年化'], Sharpe=r['Sharpe'],
                 回撤=r['最大回撤'], 笔数=r['笔数'], 胜率=r['胜率'], 仓位=r['仓位']))
# v1.1 改进版：+4%进 / 持20天 / -3%止损（T+1收盘执行）
r = run(df, 'cyb', entry=amv_surge(df), hold=20, stop=-0.03, lag=1).stats
rows.append(dict(版本='v1.1 改进出场', 规则='+4%进 / 持20天 / 止损-3%（T+1收盘买）', 年化=r['年化'], Sharpe=r['Sharpe'],
                 回撤=r['最大回撤'], 笔数=r['笔数'], 胜率=r['胜率'], 仓位=r['仓位']))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

# ---------- 开盘买版本（v2.0 执行修正） ----------
print('\n【v2.0 执行修正：T+1 开盘买（用创业板 OHLC）】')
cy = pd.read_csv('data/index_cyb_ohlcv.csv', parse_dates=['date'])
cy.columns = [c.strip().lower() for c in cy.columns]
cy = cy[['date','open','high','low','close']].sort_values('date').reset_index(drop=True)
dd = df.merge(cy, on='date', how='inner').sort_values('date').reset_index(drop=True)
px_close = dd.close.values; px_open = dd.open.values
sig = dd.amv_ret.values if 'amv_ret' in dd.columns else dd.c.pct_change().values
n = len(dd)
HOLD, STOP, COST = 20, -0.03, 2.0

def sim_open(stop=STOP, hold=HOLD):
    day = np.zeros(n); tr = []; i = 0
    while i < n:
        if not np.isnan(sig[i]) and sig[i] >= 0.04:
            if i+1 >= n: break
            buy = px_open[i+1]; start = i+1
            end = min(start+hold-1, n-1); si = end
            for t in range(start, end+1):
                if px_close[t]/buy-1 <= stop: si = t; break
            if si < start: si = start
            day[i+1] = (px_close[i+1]/buy-1) - COST/10000   # T+1 日内
            for t in range(i+2, si+1):
                day[t] = (px_close[t]/px_close[t-1]-1) - (COST/10000 if t==si else 0)
            tr.append((dd.date.iloc[i+1].date(), dd.date.iloc[si].date(), px_close[si]/buy-1))
            i = si+1
        else: i += 1
    nav = np.cumprod(1+day); tt = pd.DataFrame(tr, columns=['buy','sell','ret'])
    return dict(年化=(nav[-1]**(1/yrs)-1)*100,
                Sharpe=day.mean()/day.std()*np.sqrt(252) if day.std()>0 else 0,
                回撤=(nav/np.maximum.accumulate(nav)-1).min()*100,
                笔数=len(tt), 胜率=(tt.ret>0).mean()*100,
                平均单笔=tt.ret.mean()*100, 仓位=(day!=0).mean()*100,
                复利=nav[-1])
r = sim_open()
print('  年化 %+.2f%%  Sharpe %.2f  回撤 %.1f%%  笔数 %d  胜率 %.1f%%  平均单笔 %+.2f%%  仓位 %.0f%%  复利 %.2f 倍'
      % (r['年化'], r['Sharpe'], r['回撤'], r['笔数'], r['胜率'], r['平均单笔'], r['仓位'], r['复利']))
r5 = sim_open(stop=-0.05)
print('  （止损-5%%口径：年化 %+.2f%%  回撤 %.1f%%）' % (r5['年化'], r5['回撤']))

# ---------- 科创50 / 上证 ----------
print('\n【科创50 / 上证（T+1 收盘执行口径）】')
rows = []
for nm, col, s in [('科创50','kc50','2020-01-01'), ('上证','sse','2016-01-01')]:
    d2 = merge_all(s).dropna(subset=[col]).reset_index(drop=True)
    r = run(d2, col, entry=amv_surge(d2), hold=20, stop=-0.03, lag=1).stats
    rows.append(dict(标的=nm, 区间=f"{d2.date.iloc[0].year}-{d2.date.iloc[-1].year}",
                     年化=r['年化'], Sharpe=r['Sharpe'], 回撤=r['最大回撤'],
                     笔数=r['笔数'], 胜率=r['胜率'], 仓位=r['仓位']))
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

# ---------- 位置分层（事件研究，不受 bug 影响） ----------
print('\n【位置分层（事件研究：信号后 N 日指数涨幅，2011-2026）】')
d = merge_all('2011-01-01').dropna(subset=['cyb']).reset_index(drop=True)
d['bucket'] = pd.cut(d.cyb/d.cyb.rolling(250).max()-1, bins=[-1,-0.25,-0.15,-0.08,-0.02,1],
                     labels=['深跌<-25%','中度-25~-15%','轻度-15~-8%','近高点-8~-2%','创新高附近'])
sig = d[amv_surge(d)].dropna(subset=['bucket'])
for k in ['深跌<-25%','中度-25~-15%','轻度-15~-8%','近高点-8~-2%','创新高附近']:
    g = sig[sig.bucket==k]
    if len(g) < 3: continue
    r20 = [d.cyb.iloc[i+20]/d.cyb.iloc[i]-1 for i in g.index if i+20 < len(d)]
    r60 = [d.cyb.iloc[i+60]/d.cyb.iloc[i]-1 for i in g.index if i+60 < len(d)]
    print('  %-12s n=%2d  20日 %+.2f%%(胜%.0f%%)  60日 %+.2f%%(胜%.0f%%)'
          % (k, len(g), np.mean(r20)*100, (np.array(r20)>0).mean()*100,
             np.mean(r60)*100, (np.array(r60)>0).mean()*100))

# ---------- 依赖度 ----------
print('\n【收益依赖度（创业板 v1.1）】')
res = run(df, 'cyb', entry=amv_surge(df), hold=20, stop=-0.03, lag=1)
t = res.trades.ret.values
print('  复利 %.2f 倍' % (1+t).prod())
print('  剔除最好一笔(%.1f%%) → 年化 %.2f%%' % (t.max()*100, (((1+np.delete(t, np.argmax(t))).prod())**(252/len(df))-1)*100))
print('  前5笔贡献: %.0f%%' % (np.sort(t)[::-1][:5].sum()/np.abs(t).sum()*100))
