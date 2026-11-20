# -*- coding: utf-8 -*-
"""两种止损的实证对比：AMV 信号出场 vs 持仓浮亏止损"""
import numpy as np
import pandas as pd
pd.set_option('display.width', 260)

amv = pd.read_csv('0amv_daily_261113.csv', encoding='utf-8-sig', parse_dates=['date'])[['date','close']]
amv = amv.rename(columns={'close':'amv'}).sort_values('date')
amv['amv_r'] = amv.amv.pct_change()
cy = pd.read_csv('idx_sz399006.csv', parse_dates=['date'])[['date','close']].rename(columns={'close':'cy'}).sort_values('date')
d = amv.merge(cy, on='date', how='inner').sort_values('date').reset_index(drop=True)
d = d[d.date >= '2016-01-01'].reset_index(drop=True)

# 逐笔模拟，同时记录两种出场条件的状态
px = d.cy.values; ar = d.amv_r.values; n = len(d)
records = []
i = 0
while i < n:
    if not np.isnan(ar[i]) and ar[i] >= 0.04:
        bi = min(i+1, n-1)
        # 遍历持仓期，记录每天的 AMV 涨跌 与 持仓浮亏
        path = []
        si_exit = None
        end = min(bi+20, n-1)
        for j in range(bi+1, end+1):
            ret_pos = px[j]/px[bi]-1          # 持仓浮亏
            path.append(dict(j=j, date=d.date.iloc[j], amv_r=ar[j], pos_ret=ret_pos))
            if ret_pos <= -0.03:
                si_exit = j; break
        if si_exit is None:
            si_exit = end
        records.append(dict(bi=bi, si=si_exit, path=path))
        i = si_exit + 1
    else:
        i += 1

print('='*86)
print('1. 核心问题：AMV 跌 2.3% 的那天，你的仓位实际亏了多少？')
print('='*86)
# 在全部持仓日中，找 AMV 单日 ≤ -2.3% 的日子，统计当时持仓浮亏
hits = []
for rec in records:
    for p in rec['path']:
        if not np.isnan(p['amv_r']) and p['amv_r'] <= -0.023:
            hits.append(p['pos_ret'])
hits = np.array(hits)
print('  持仓期内 AMV 单日 ≤ -2.3%% 的情况共 %d 次' % len(hits))
if len(hits):
    print('  当时持仓浮亏: 均值 %+.2f%%  中位 %+.2f%%' % (hits.mean()*100, np.median(hits)*100))
    print('  分位: 最小 %.1f%%  25%% %.1f%%  50%% %.1f%%  75%% %.1f%%  最大 %.1f%%'
          % (hits.min()*100, np.percentile(hits,25)*100, np.percentile(hits,50)*100,
             np.percentile(hits,75)*100, hits.max()*100))
    print('  其中「仓位其实还在赚」的比例: %.1f%%' % ((hits>0).mean()*100))
    print('  其中「仓位已亏超 3%%(本该止损)」的比例: %.1f%%' % ((hits<=-0.03).mean()*100))

print('\n' + '='*86)
print('2. 反向：持仓浮亏触及 -3% 时，AMV 当天在干什么？')
print('='*86)
tri = []
for rec in records:
    for p in rec['path']:
        if p['pos_ret'] <= -0.03:
            tri.append(p['amv_r']); break
tri = np.array([x for x in tri if not np.isnan(x)])
if len(tri):
    print('  -3%% 止损触发 %d 次，触发日 AMV 涨跌幅: 均值 %+.2f%%  中位 %+.2f%%'
          % (len(tri), tri.mean()*100, np.median(tri)*100))
    print('  其中 AMV 当天是「上涨」的比例: %.1f%%  ← 说明 AMV 完全没预警' % ((tri>0).mean()*100))

print('\n' + '='*86)
print('3. -3%% 止损到底是在「躲刀」还是「被震出来」？止损后指数继续跌吗')
print('='*86)
stop_events = []
for rec in records:
    if rec['si'] - rec['bi'] < 20:   # 提前离场 = 止损触发
        si = rec['si']
        if si+20 < n:
            stop_events.append(dict(
                日期=d.date.iloc[si],
                止损时浮亏=(px[si]/px[rec['bi']]-1)*100,
                之后5日=(px[si+5]/px[si]-1)*100,
                之后10日=(px[si+10]/px[si]-1)*100,
                之后20日=(px[si+20]/px[si]-1)*100,
                若不止损则最终=(px[rec['bi']+20]/px[rec['bi']]-1)*100))
se = pd.DataFrame(stop_events)
print('  提前止损 %d 笔（占 %d 笔的 %.0f%%），其余为持有满 20 天自然到期'
      % (len(se), len(records), len(se)/len(records)*100))
if len(se):
    print('  止损后 5 日:  均值 %+.2f%%  中位 %+.2f%%' % (se.之后5日.mean(), se.之后5日.median()))
    print('  止损后 10 日: 均值 %+.2f%%  中位 %+.2f%%' % (se.之后10日.mean(), se.之后10日.median()))
    print('  止损后 20 日: 均值 %+.2f%%  中位 %+.2f%%' % (se.之后20日.mean(), se.之后20日.median()))
    print('  「止损后又跌」的比例: 5日 %.0f%%  10日 %.0f%%  20日 %.0f%%'
          % ((se.之后5日<0).mean()*100, (se.之后10日<0).mean()*100, (se.之后20日<0).mean()*100))
    print('\n  止损到底是赚了还是亏了（止损 vs 死扛到第20天）:')
    edge = se.若不止损则最终 - se.止损时浮亏
    print('    止损时平均浮亏 %.2f%%，若扛到第20天平均 %.2f%%' % (se.止损时浮亏.mean(), se.若不止损则最终.mean()))
    print('    → 止损平均少亏/多亏 %.2f 个百分点；止损「救了」的比例 %.0f%%'
          % (edge.mean(), (edge<0).mean()*100))

print('\n' + '='*86)
print('4. 两种出场方式的直接对比（同区间 2016-2026）')
print('='*86)
def run(mode, stop=None, hold=20, exit_th=-0.023):
    pos = np.zeros(n); i = 0; trades = []
    while i < n:
        if not np.isnan(ar[i]) and ar[i] >= 0.04:
            bi = min(i+1, n-1)
            if mode == 'time':
                si = min(bi+hold, n-1)
                if stop is not None:
                    for j in range(bi+1, si+1):
                        if px[j]/px[bi]-1 <= stop: si = j; break
            else:  # AMV 信号出场
                j = bi+1; si = None
                while j < n:
                    if not np.isnan(ar[j]) and ar[j] <= exit_th:
                        si = min(j+1, n-1); break
                    if j-bi >= 250: si = n-1; break
                    j += 1
                if si is None: si = n-1
            pos[bi:si] = 1; trades.append((bi, si)); i = si+1
        else: i += 1
    r = np.r_[0, px[1:]/px[:-1]-1]
    pnl = pos*r - np.abs(np.diff(np.r_[0, pos]))*2/10000
    cum = np.cumprod(1+pnl); yrs = n/252
    tr = np.array([px[si]/px[bi]-1 for bi, si in trades])
    return dict(年化=(cum[-1]**(1/yrs)-1)*100, Sharpe=pnl.mean()/pnl.std()*np.sqrt(252),
                回撤=(cum/np.maximum.accumulate(cum)-1).min()*100, 笔数=len(trades),
                胜率=(tr>0).mean()*100, 中位单笔=np.median(tr)*100,
                平均持仓=np.mean([si-bi for bi, si in trades]))

rows = [
    dict(出场方式='① 仅时间（持满20天）', **run('time')),
    dict(出场方式='② 时间 + 价格止损-3%', **run('time', stop=-0.03)),
    dict(出场方式='③ 时间 + 价格止损-5%', **run('time', stop=-0.05)),
    dict(出场方式='④ AMV单日-2.3%（大哥原版）', **run('amv')),
]
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda v: f'{v:,.2f}'))
print('\n  ★ 关键：②的止损是「买入价 × 0.97」，看的是你自己的账；④看的是 AMV 这个指标。')
