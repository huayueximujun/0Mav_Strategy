# -*- coding: utf-8 -*-
"""阶段四：可交易性拆解 + 稳健性"""
import numpy as np
import pandas as pd
from scipy import stats

pd.set_option('display.width', 260)
df = pd.read_csv(r'./0amv_daily_261113.csv',
                 encoding='utf-8-sig', parse_dates=['date']).sort_values('date').reset_index(drop=True)
df['ret'] = df.close.pct_change()
df['on'] = df.open/df.close.shift(1)-1        # 隔夜
df['id'] = df.close/df.open-1                 # 日内

m = df.date >= '2016-01-01'

def acf1(x):
    x = pd.Series(x).dropna().values; x = x - x.mean()
    return (x[1:]*x[:-1]).mean()/(x*x).mean()

print('='*72)
print('1. 近10年：隔夜 / 日内 自相关与动量可交易性')
print('='*72)
for name, s in [('全日收益 ret', df.ret[m]), ('隔夜 on', df.on[m]), ('日内 id', df.id[m])]:
    x = s.dropna()
    print('  %-12s n=%4d  σ=%.3f%%  ρ1=%+.3f  ρ2=%+.3f' % (name, len(x), x.std()*100, acf1(x), acf1(x.shift(1))))

print('\n  信号=昨收涨跌，持仓=今日:')
for seg in ['隔夜段', '日内段', '全日段']:
    if seg == '隔夜段':
        pnl = np.sign(df.ret.shift(1)) * df.on
    elif seg == '日内段':
        pnl = np.sign(df.ret.shift(1)) * df.id
    else:
        pnl = np.sign(df.ret.shift(1)) * df.ret
    p = pnl[m].dropna()
    print('    %-6s Sharpe=%+.3f  日均=%+.4f%%  t=%+.2f' % (seg, p.mean()/p.std()*np.sqrt(252), p.mean()*100, stats.ttest_1samp(p,0)[0]))

print('\n  ★ 只看日内（可实际交易部分）的 1 日动量，全样本:')
for label, mask in [('1993-2005', df.date<'2006-01-01'), ('2006-2015', (df.date>='2006-01-01')&(df.date<='2015-12-31')), ('2016-2026', df.date>='2016-01-01')]:
    p = (np.sign(df.ret.shift(1))*df.id)[mask].dropna()
    print('    %-10s n=%4d Sharpe=%+.3f 日均%+.4f%%' % (label, len(p), p.mean()/p.std()*np.sqrt(252), p.mean()*100))

print('\n' + '='*72)
print('2. 严格可交易版：t日收盘信号 → t+1开盘买入 → t+1收盘卖出，扣双边成本')
print('='*72)
for cost_bp in [0, 3, 5, 10]:
    pnl = np.sign(df.ret.shift(1))*df.id - cost_bp/10000
    p = pnl[m].dropna()
    print('  成本%2dbp: 年化Sharpe=%+.3f  年化收益=%+.2f%%' % (cost_bp, p.mean()/p.std()*np.sqrt(252), p.mean()*252*100))

print('\n' + '='*72)
print('3. 波动率可预测性（GARCH 效应）')
print('='*72)
for label, mask in [('全样本', df.date.notna()), ('2016-2026', df.date>='2016-01-01')]:
    r = df.ret[mask].dropna()
    print('%s: |r| ρ1=%+.3f ρ5=%+.3f   r² ρ1=%+.3f   ARCH-LM(5) 见下'
          % (label, acf1(r.abs()), acf1(r.abs().shift(4)), acf1(r**2)))
    # ARCH-LM
    r2 = r**2
    X = np.column_stack([np.ones(len(r2)-5)] + [r2.shift(k).iloc[5:].values for k in range(1,6)])
    y = r2.iloc[5:].values
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X@beta
    r2stat = 1 - resid.var()/y.var()
    print('        ARCH-LM R²=%.3f  nR²=%.1f (χ²(5) 临界 11.07)' % (r2stat, r2stat*len(y)))

print('\n' + '='*72)
print('4. 波动率预测：HAR-RV 滚动样本外（用过去预测未来20日波动）')
print('='*72)
d = df.dropna(subset=['ret']).copy()
d['rv'] = d.ret.abs()*np.sqrt(np.pi/2)   # 近似日波动
d['rv5'] = d.ret.rolling(5).std()
d['rv22'] = d.ret.rolling(22).std()
d['fwd22'] = d.ret[::-1].rolling(22).std()[::-1]
d2 = d.dropna(subset=['rv','rv5','rv22','fwd22'])
X = np.column_stack([np.ones(len(d2)), d2.rv, d2.rv5, d2.rv22])
y = d2.fwd22.values
beta, *_ = np.linalg.lstsq(X, y, rcond=None)
pred = X@beta
print('  HAR 回归 R²=%.3f  （R² 越高说明波动越可预测）' % (1-((y-pred)**2).sum()/((y-y.mean())**2).sum()))
print('  对照：用"过去均值"预测的 R²=%.3f' % (1-((y-y.mean())**2).sum()/((y-y.mean())**2).sum()))
# 样本外
split = int(len(d2)*0.7)
b2, *_ = np.linalg.lstsq(X[:split], y[:split], rcond=None)
po = X[split:]@b2
print('  样本外(后30%%) R²=%.3f  vs 全样本均值基准 R²=%.3f'
      % (1-((y[split:]-po)**2).sum()/((y[split:]-y[split:].mean())**2).sum(),
         1-((y[split:]-y[:split].mean())**2).sum()/((y[split:]-y[split:].mean())**2).sum()))

print('\n' + '='*72)
print('5. 方向预测的样本外检验：逻辑回归（特征=过去1/5/10/20日收益+波动+量能）')
print('='*72)
def logit_fit(X, y, l2=1.0, iters=2000, lr=0.1):
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        z = X@w; p = 1/(1+np.exp(-np.clip(z,-30,30)))
        g = X.T@(p-y)/len(y) + l2*w/len(y)
        w -= lr*g
    return w

f = pd.DataFrame(index=df.index)
f['r1'] = df.ret.shift(1)
f['r5'] = df.ret.rolling(5).sum().shift(1)
f['r10'] = df.ret.rolling(10).sum().shift(1)
f['r20'] = df.ret.rolling(20).sum().shift(1)
f['vol20'] = df.ret.rolling(20).std().shift(1)
f['volchg'] = (df.ret.rolling(5).std()/df.ret.rolling(60).std()).shift(1)
f['gap'] = df.on.shift(1)
f['amtchg'] = df.amount.pct_change().rolling(5).mean().shift(1)
f['y'] = (df.ret > 0).astype(float)
d3 = pd.concat([df[['date','ret']], f], axis=1).dropna()

cols = ['r1','r5','r10','r20','vol20','volchg','gap','amtchg']
Xa = d3[cols].values
mu, sd = Xa.mean(0), Xa.std(0)
Xa = (Xa-mu)/sd
ya = d3.y.values
# walk-forward：前 60% 训练，之后每年滚动重训
n = len(d3); start = int(n*0.6)
preds, actual, dates = [], [], []
for i in range(start, n, 250):
    tr_end = i; tr_start = max(0, i-2500)
    w = logit_fit(np.column_stack([np.ones(tr_end-tr_start), Xa[tr_start:tr_end]]),
                  ya[tr_start:tr_end], l2=10.0, lr=0.5, iters=1500)
    seg = slice(i, min(i+250, n))
    Xs = np.column_stack([np.ones(seg.stop-seg.start), Xa[seg]])
    preds.extend(1/(1+np.exp(-np.clip(Xs@w, -30, 30))))
    actual.extend(ya[seg]); dates.extend(d3.date.iloc[seg])

preds = np.array(preds); actual = np.array(actual)
acc = ((preds>0.5)==actual).mean()
base = max(actual.mean(), 1-actual.mean())
auc = stats.mannwhitneyu(preds[actual==1], preds[actual==0]).statistic/((actual==1).sum()*(actual==0).sum())
print('  样本外 n=%d  准确率=%.4f  基准(多数类)=%.4f  AUC=%.4f' % (len(preds), acc, base, auc))
hi = preds > np.quantile(preds, 0.8)
print('  模型最看多20%%: 实际上涨率=%.4f   最看空20%%: 实际上涨率=%.4f   全样本基准=%.4f'
      % (actual[hi].mean(), actual[preds<=np.quantile(preds,0.2)].mean(), actual.mean()))

print('\n' + '='*72)
print('6. 极端下跌后的反弹（逆向视角）——近10年')
print('='*72)
r10 = df.ret[m]
print('基准: 次日上涨率 %.3f, 10日累计均值 %+.2f%%, 20日均值 %+.2f%%'
      % ((r10.dropna()>0).mean(), (r10.rolling(10).sum().shift(-10))[m].mean()*100,
         (r10.rolling(20).sum().shift(-20))[m].mean()*100))
for q in [0.02, 0.05, 0.10]:
    thr = r10.quantile(q)
    idx = r10[r10<=thr].index
    idx = [i for i in idx if i+21 < len(df)]
    nxt = np.array([df.ret.iloc[i+1] for i in idx])
    f10 = np.array([df.close.iloc[i+10]/df.close.iloc[i]-1 for i in idx])
    f20 = np.array([df.close.iloc[i+20]/df.close.iloc[i]-1 for i in idx])
    print('  跌幅前%2.0f%%(≤%.2f%%) n=%3d: 次日%+.2f%%(胜率%.2f)  10日%+.2f%%(胜率%.2f)  20日%+.2f%%(胜率%.2f)'
          % (q*100, thr*100, len(idx), nxt.mean()*100, (nxt>0).mean(), f10.mean()*100, (f10>0).mean(), f20.mean()*100, (f20>0).mean()))
