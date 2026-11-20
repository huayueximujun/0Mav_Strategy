# -*- coding: utf-8 -*-
"""阶段一：序列结构诊断 + 经典可预测性检验"""
import numpy as np
import pandas as pd
from scipy import stats

np.set_printoptions(suppress=True)
pd.set_option('display.width', 200)

df = pd.read_csv(r'./0amv_daily_261113.csv',
                 encoding='utf-8-sig', parse_dates=['date']).sort_values('date').reset_index(drop=True)
df['ret'] = df.close.pct_change()
df['overnight'] = df.open / df.close.shift(1) - 1
df['intraday'] = df.close / df.open - 1
df['hl_range'] = df.high / df.low - 1

print('='*70)
print('A. 结构诊断')
print('='*70)
print('隔夜收益 年化波动: %.1f%%   日内收益 年化波动: %.1f%%'
      % (df.overnight.std()*np.sqrt(252)*100, df.intraday.std()*np.sqrt(252)*100))
print('隔夜贡献方差占比: %.1f%%' % (100*df.overnight.var()/(df.overnight.var()+df.intraday.var())))
print('隔夜/日内 波动比: %.2f' % (df.overnight.std()/df.intraday.std()))
print('日内振幅(high/low-1) 中位数: %.2f%%   均值: %.2f%%' % (df.hl_range.median()*100, df.hl_range.mean()*100))
print('成交额/成交量 隐含均价 中位数: %.2f 元' % (df.amount/df.volume).median())

# 分段：隔夜 vs 日内波动
print('\n分年代 隔夜/日内波动比:')
for seg, sub in df.dropna(subset=['overnight']).groupby(df.date.dt.year//5*5):
    if len(sub) < 50: continue
    print('  %d-%d  n=%4d  隔夜σ=%.2f%%  日内σ=%.2f%%  比=%.2f'
          % (seg, seg+4, len(sub), sub.overnight.std()*100, sub.intraday.std()*100,
             sub.overnight.std()/sub.intraday.std()))

r = df.ret.dropna()
print('\n收益分布: 偏度 %.3f  峰度 %.2f  JB=%.1f (p=%.2e)'
      % (stats.skew(r), stats.kurtosis(r, fisher=False), *stats.jarque_bera(r)))

print('\n' + '='*70)
print('B. 线性自相关检验 (ACF + Ljung-Box)')
print('='*70)

def acf(x, k):
    x = np.asarray(x, float); x = x - x.mean()
    c0 = (x*x).mean()
    return np.array([(x[k_:]*x[:-k_]).mean()/c0 if k_ < len(x) else np.nan for k_ in k])

def ljung_box(x, lags):
    x = np.asarray(x, float); n = len(x); x = x - x.mean()
    c0 = (x*x).mean()
    out = []
    q = 0.0
    for k in range(1, lags+1):
        rk = (x[k:]*x[:-k]).mean()/c0
        q += rk*rk/(n-k)
        out.append((k, rk, n*(n+2)*q))
    return out

lags = [1,2,3,5,10,20]
for name, series in [('原始收益 ret', r), ('绝对收益 |ret|', r.abs()), ('平方收益 ret^2', r**2)]:
    a = acf(series.values, lags)
    print('%-16s' % name, '  '.join('ρ%d=%+.3f' % (l, v) for l, v in zip(lags, a)))
    lb = ljung_box(series.values, 20)
    print('%20s Ljung-Box(20): Q=%.1f  p=%.4g  |  (5阶) Q=%.1f p=%.4g'
          % ('', lb[-1][2], stats.chi2.sf(lb[-1][2], 20), lb[4][2], stats.chi2.sf(lb[4][2], 5)))

print('\n--- 分样本 ---')
for label, s in [('1993-2005', r[r.index < df.index[df.date.searchsorted("2006-01-01")]]),
                 ('2006-2015', r[(df.date>='2006-01-01') & (df.date<='2015-12-31')]),
                 ('2016-2026', r[df.date>='2016-01-01'])]:
    a = acf(s.values, [1,2,3,5])
    lb = ljung_box(s.values, 10)
    print('%-10s n=%4d  ρ1=%+.3f ρ2=%+.3f ρ3=%+.3f ρ5=%+.3f  LB(10) Q=%.1f p=%.3f'
          % (label, len(s), a[0], a[1], a[2], a[3], lb[-1][2], stats.chi2.sf(lb[-1][2], 10)))

print('\n' + '='*70)
print('C. 方差比检验 (Lo-MacKinlay, 异方差稳健)')
print('='*70)

def variance_ratio(x, q):
    x = np.asarray(x, float); n = len(x)
    mu = x.mean()
    var1 = ((x-mu)**2).sum()/(n-1)
    # q 期重叠收益
    xq = np.convolve(x, np.ones(q), 'valid')
    varq = ((xq-q*mu)**2).sum()/((n-q+1)*q)
    vr = varq/var1
    # 异方差稳健标准误
    d = np.array([((x[k:]-mu)**2).sum() for k in range(1, q)]) / (((x-mu)**2).sum())
    theta = sum((2*(q-k)/q)**2 * d[k-1] for k in range(1, q))
    z = (vr-1)/np.sqrt(theta) if theta > 0 else np.nan
    return vr, z

for label, s in [('全样本 1993-2026', r), ('近10年 2016-2026', r[df.date>='2016-01-01'])]:
    print('%-18s' % label, end='')
    for q in [2, 5, 10, 20, 60]:
        vr, z = variance_ratio(s.values, q)
        print('  q=%2d VR=%.3f(z=%+.2f)' % (q, vr, z), end='')
    print()
print('注: VR>1 趋势/动量, VR<1 均值回复, |z|>1.96 显著')

print('\n' + '='*70)
print('D. Hurst 指数 (R/S)')
print('='*70)

def hurst_rs(x, min_n=8):
    x = np.asarray(x, float); N = len(x)
    ns, rs = [], []
    n = min_n
    while n <= N//2:
        k = N//n
        vals = []
        for i in range(k):
            seg = x[i*n:(i+1)*n]
            seg = seg - seg.mean()
            cum = np.cumsum(seg)
            R = cum.max()-cum.min()
            S = seg.std(ddof=1)
            if S > 0: vals.append(R/S)
        if vals:
            ns.append(n); rs.append(np.mean(vals))
        n = int(n*1.6)
    lx, ly = np.log(ns), np.log(rs)
    return stats.linregress(lx, ly).slope

for label, s in [('全样本', r), ('2006-2015', r[(df.date>='2006-01-01')&(df.date<='2015-12-31')]),
                 ('2016-2026', r[df.date>='2016-01-01'])]:
    print('%-10s H(收益)=%.3f   H(|收益|)=%.3f' % (label, hurst_rs(s.values), hurst_rs(s.abs().values)))

print('\n' + '='*70)
print('E. 游程检验 + 方向转移')
print('='*70)
sign = np.sign(r.values); sign = sign[sign != 0]
N = len(sign); n1 = (sign > 0).sum(); n2 = (sign < 0).sum()
runs = 1 + (np.diff(sign) != 0).sum()
er = 2*n1*n2/N + 1
vr_ = 2*n1*n2*(2*n1*n2-N)/(N*N*(N-1))
zr = (runs-er)/np.sqrt(vr_)
print('涨 %d 天 / 跌 %d 天  runs=%d  期望=%.1f  z=%+.2f  p=%.4f' % (n1, n2, runs, er, zr, 2*stats.norm.sf(abs(zr))))
print('解读: z>0 游程多→反转倾向; z<0 游程少→惯性倾向')

p_up = n1/N
print('无条件 P(涨)=%.4f' % p_up)
print('\n条件概率 P(次日涨 | 前n日状态):')
for k in [1,2,3,4,5]:
    up_after_up, up_after_dn = [], []
    for i in range(k, N):
        past_up = (sign[i-k:i] > 0).all()
        past_dn = (sign[i-k:i] < 0).all()
        if past_up: up_after_up.append(sign[i] > 0)
        if past_dn: up_after_dn.append(sign[i] > 0)
    print('  连涨%d日后 P(涨)=%.3f (n=%d)   连跌%d日后 P(涨)=%.3f (n=%d)'
          % (k, np.mean(up_after_up) if up_after_up else np.nan, len(up_after_up),
             k, np.mean(up_after_dn) if up_after_dn else np.nan, len(up_after_dn)))

print('\n' + '='*70)
print('F. 动量/反转策略 (信号 t 日收盘 → t+1 日持仓)')
print('='*70)
sig_df = pd.DataFrame({'date': df.date, 'ret': df.ret})
for m in [1, 5, 10, 20, 60, 120, 250]:
    mom = df.close.pct_change(m)
    pos = np.sign(mom.shift(1))
    pnl = pos * df.ret
    pnl = pnl.dropna()
    if len(pnl) < 100: continue
    t, p = stats.ttest_1samp(pnl, 0)
    sharpe = pnl.mean()/pnl.std()*np.sqrt(252)
    hit = (np.sign(pnl) > 0).mean()
    # 近十年
    sub = pnl[df.date.reindex(pnl.index) >= '2016-01-01']
    sharpe10 = sub.mean()/sub.std()*np.sqrt(252) if len(sub) > 50 else np.nan
    print('动量%3d日: 年化Sharpe全样本=%+.3f (t=%+.2f)  近10年Sharpe=%+.3f  日均=%+.4f%%'
          % (m, sharpe, t, sharpe10, pnl.mean()*100))

print('\n' + '='*70)
print('G. 日历效应')
print('='*70)
r_df = df.dropna(subset=['ret']).copy()
r_df['dow'] = r_df.date.dt.dayofweek
r_df['month'] = r_df.date.dt.month
print('星期效应(日均收益%, 胜率):')
for d, g in r_df.groupby('dow'):
    print('  周%d: 均值%+.4f%%  胜率%.2f  n=%d' % (d+1, g.ret.mean()*100, (g.ret>0).mean(), len(g)))
print('\n月份效应(日均收益%):')
print('  ' + '  '.join('%d月:%+.4f' % (m, g.ret.mean()*100) for m, g in r_df.groupby('month')))

print('\n' + '='*70)
print('H. 极端日后的表现 (分位数 / 均值回复)')
print('='*70)
r_s = df.ret
for q in [0.01, 0.02, 0.05, 0.10]:
    thr = r_s.quantile(q)
    idx = r_s[r_s <= thr].index
    idx = idx[idx < len(df)-1]
    nxt = np.array([r_s.iloc[i+1] for i in idx if i+1 < len(df)])
    nxt5 = np.array([df.close.iloc[min(i+5, len(df)-1)]/df.close.iloc[i]-1 for i in idx])
    nxt20 = np.array([df.close.iloc[min(i+20, len(df)-1)]/df.close.iloc[i]-1 for i in idx])
    print('最差%.0f%%日(≤%.2f%%, n=%d): 次日均值%+.2f%% 胜率%.2f | 5日均%+.2f%% | 20日均%+.2f%%'
          % (q*100, thr*100, len(idx), nxt.mean()*100, (nxt>0).mean(), nxt5.mean()*100, nxt20.mean()*100))
print('\n无条件基准: 日均%+.4f%%  次日胜率%.3f' % (r_s.mean()*100, (r_s.dropna()>0).mean()))
