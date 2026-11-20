# -*- coding: utf-8 -*-
"""xlsx 导出全量核对 + 最新数据解读"""
import numpy as np
import pandas as pd
import openpyxl
pd.set_option('display.width', 260)

XLSX = r'D:\Compass\_export\活跃市值_日线历史_1993-2026.xlsx'
CSV = '0amv_daily_261113.csv'

# ---------- 读 xlsx ----------
wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
ws = wb['活跃市值_日线']
rows = list(ws.iter_rows(min_row=2, values_only=True))
wb.close()
x = pd.DataFrame(rows, columns=['date','o','h','l','c'])
x['date'] = pd.to_datetime(x['date'])
for col in ['o','h','l','c']:
    x[col] = pd.to_numeric(x[col])
x = x.dropna(subset=['date']).sort_values('date').reset_index(drop=True)

# ---------- 读 CSV ----------
y = pd.read_csv(CSV, encoding='utf-8-sig', parse_dates=['date']).sort_values('date').reset_index(drop=True)

print('='*86)
print('一、结构核对')
print('='*86)
print('  xlsx 数据行: %d   范围 %s ~ %s' % (len(x), x.date.iloc[0].date(), x.date.iloc[-1].date()))
print('  CSV  数据行: %d   范围 %s ~ %s' % (len(y), y.date.iloc[0].date(), y.date.iloc[-1].date()))
print('  xlsx 多出: %d 行' % (len(x)-len(y)))
extra = x[x.date > y.date.max()]
print('  多出日期: %s' % ', '.join(str(d.date()) for d in extra.date))
print('  重复日期 xlsx: %d   CSV: %d' % (x.date.duplicated().sum(), y.date.duplicated().sum()))
print('  严格升序 xlsx: %s' % x.date.is_monotonic_increasing)

print('\n' + '='*86)
print('二、全量数值核对（8245 个共同交易日 × 4 字段 = 32,980 个值）')
print('='*86)
m = x.merge(y, on='date', suffixes=('_x','_y'))
print('  匹配行数: %d' % len(m))
tot_fields = 0; diff_rows = 0; max_abs = 0; worst = None
for a, b in [('o','open'), ('h','high'), ('l','low'), ('c','close')]:
    d = (m[a]-m[b]).abs()
    tot_fields += len(d)
    n_bad = (d > 1e-6).sum()
    if n_bad: diff_rows += 1
    if d.max() > max_abs:
        max_abs = d.max(); worst = (a, m.loc[d.idxmax(),'date'].date(), m.loc[d.idxmax(),a], m.loc[d.idxmax(),b])
    print('  %-6s 最大绝对差 %.6f  超 1e-6 的值 %d 个' % (a, d.max(), n_bad))
print('  合计比对 %d 个值，最大绝对差 %.6f' % (tot_fields, max_abs))
if worst: print('  最大差异点: %s 字段=%s xlsx=%.4f csv=%.4f' % (worst[1], worst[0], worst[2], worst[3]))

# round 校验
for a, b in [('o','open'),('h','high'),('l','low'),('c','close')]:
    ok = np.isclose(m[a], m[b].round(2), atol=1e-9)
    print('  %s 是否等于 round(csv,2): %s (%.2f%% 吻合)' % (a, ok.all(), ok.mean()*100))

print('\n' + '='*86)
print('三、精度损失的实际影响（2 位小数 vs 4 位小数）')
print('='*86)
for seg, s0, s1 in [('1993-1997', '1993-01-01','1997-12-31'), ('2010-2014','2010-01-01','2014-12-31'),
                    ('2024-2026','2024-01-01','2026-12-31')]:
    s = m[(m.date>=s0)&(m.date<=s1)]
    r_x = s.c.pct_change(); r_y = s.close.pct_change()
    dd = (r_x-r_y).abs()
    print('  %-10s 收益差: 均值 %.2e  最大 %.2e (=%.4f 个百分点)  年化影响 ≈ %.4f%%'
          % (seg, dd.mean(), dd.max(), dd.max()*100, dd.mean()*252*100))

print('\n' + '='*86)
print('四、数据质量')
print('='*86)
print('  OHLC 违规: high<max(o,c) %d 行; low>min(o,c) %d 行'
      % ((x.h < x[['o','c']].max(axis=1)).sum(), (x.l > x[['o','c']].min(axis=1)).sum()))
x['ret'] = x.c.pct_change()
big = x[x.ret.abs() > 0.15]
print('  |单日涨跌| > 15%% 共 %d 行:' % len(big))
for _, r in big.iterrows():
    print('    %s  %+.2f%%' % (r.date.date(), r.ret*100))
gaps = x.date.diff().dt.days
print('  最大日期间隔: %d 天 (%s → %s)' % (gaps.max(), x.date.iloc[gaps.idxmax()-1].date(), x.date.iloc[gaps.idxmax()].date()))

print('\n' + '='*86)
print('五、最新 4 个交易日（CSV 之后的新数据）')
print('='*86)
last = x.tail(12).copy()
last['涨跌%'] = last.c.pct_change()*100
print(last[['date','o','h','l','c','涨跌%']].to_string(index=False, float_format=lambda v: f'{v:,.2f}'))

print('\n' + '='*86)
print('六、最新数据的位置与状态')
print('='*86)
cur = x.c.iloc[-1]
print('  当前读数: %.2f (%s)' % (cur, x.date.iloc[-1].date()))
print('  距 2026-07-01 峰值 268,357.22: %.1f%%' % ((cur/268357.2188-1)*100))
print('  250 日区间分位: %.1f%%' % ((cur - x.c.tail(250).min())/(x.c.tail(250).max()-x.c.tail(250).min())*100))
allpct = (x.c < cur).mean()*100
print('  全历史分位: %.1f%%（1993 年以来只有 %.0f%% 的交易日比现在低）' % (allpct, allpct))
print('  近 250 日: 最高 %.0f  最低 %.0f' % (x.c.tail(250).max(), x.c.tail(250).min()))
# 连续下跌
drops = (x.c.pct_change() < 0).iloc[::-1]
cnt = 0
for v in drops:
    if v: cnt += 1
    else: break
print('  当前连续下跌: %d 天' % cnt)
print('  近 4 日累计: %.2f%%' % ((x.c.iloc[-1]/x.c.iloc[-5]-1)*100))
print('  近 20 日累计: %.2f%%' % ((x.c.iloc[-1]/x.c.iloc[-21]-1)*100))
x.to_csv('amv_xlsx_clean.csv', index=False, encoding='utf-8-sig')
print('\n  已另存 amv_xlsx_clean.csv（仅 5 列，供后续使用）')
