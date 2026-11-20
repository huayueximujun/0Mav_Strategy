# -*- coding: utf-8 -*-
import base64
IMG = base64.b64encode(open('cross_result.png','rb').read()).decode()

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>AMV 规则的跨市场检验：A股 / 美股 / 创业板 / 科创50</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#f4f6f9;color:#1c2430;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;line-height:1.65;font-size:14.5px}}
.wrap{{max-width:1080px;margin:0 auto;padding:36px 28px 80px}}
header{{border-left:5px solid #c0392b;padding-left:18px;margin-bottom:26px}}
h1{{font-size:25px;margin:0 0 8px;letter-spacing:-.3px}}
.sub{{color:#66707d;font-size:13.5px}}
h2{{font-size:19px;margin:40px 0 14px;padding-bottom:8px;border-bottom:1px solid #e3e7ee}}
h3{{font-size:15.5px;margin:24px 0 10px;color:#2c3e50}}
p{{margin:10px 0}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:22px 0}}
.kpi{{background:#fff;border:1px solid #e3e7ee;border-radius:10px;padding:15px 14px}}
.kpi .lab{{font-size:11.5px;color:#7b8695}}
.kpi .val{{font-size:20px;font-weight:700;margin:5px 0 2px;letter-spacing:-.5px}}
.kpi .note{{font-size:11.5px;color:#8b95a3}}
.red{{color:#c0392b}}.green{{color:#1e8449}}.blue{{color:#2471a3}}.amber{{color:#b9770e}}
.card{{background:#fff;border:1px solid #e3e7ee;border-radius:12px;padding:20px 22px;margin:16px 0}}
.verdict{{background:linear-gradient(135deg,#fdf3f2,#fbe9e7);border:1px solid #f0c4bd;border-radius:12px;padding:20px 24px;margin:20px 0}}
.verdict ol{{margin:8px 0 0;padding-left:22px}}.verdict li{{margin:9px 0}}
table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:13px;background:#fff}}
th{{background:#eef1f6;text-align:left;padding:9px 10px;font-weight:600;border-bottom:2px solid #dde3ec;font-size:12.5px;white-space:nowrap}}
td{{padding:8px 10px;border-bottom:1px solid #eef1f5}}
tr:hover td{{background:#fafbfd}}
code{{background:#eef1f6;padding:1.5px 5px;border-radius:4px;font-size:12.5px;font-family:ui-monospace,Consolas,monospace}}
.tag{{display:inline-block;padding:1.5px 7px;border-radius:20px;font-size:11.5px;font-weight:600}}
.t-bad{{background:#fbe3e0;color:#a93226}}.t-ok{{background:#dff0e4;color:#1e7b3e}}.t-mid{{background:#fdf0d5;color:#96690f}}
img{{width:100%;border:1px solid #e3e7ee;border-radius:10px;margin:10px 0;background:#fff}}
.cap{{font-size:12px;color:#7b8695;margin:-4px 0 18px}}
ul,ol{{padding-left:22px}}li{{margin:6px 0}}
.warn{{border-left:3px solid #e67e22;background:#fffbf3;padding:12px 16px;margin:14px 0;border-radius:0 8px 8px 0}}
.good{{border-left:3px solid #27ae60;background:#f5fbf7;padding:12px 16px;margin:14px 0;border-radius:0 8px 8px 0}}
.foot{{margin-top:44px;padding-top:16px;border-top:1px solid #e3e7ee;font-size:12px;color:#8b95a3}}
@media(max-width:760px){{.kpis{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body><div class="wrap">

<header>
  <h1>AMV 规则的跨市场检验：有没有 alpha？</h1>
  <div class="sub">标的：上证 · 创业板 · 科创50 · 标普500 · 纳斯达克 · 纳指100<br>
  共同区间 2020-01 ~ 2026-11（1,606–1,663 个交易日）· 规则：AMV 单日 ≥+4% 入场 / 持 20 天 / 止损 −3% · 含 2bp 成本</div>
</header>

<div class="verdict">
  <strong style="font-size:16px;">直接回答</strong>
  <ol>
    <li><b>没有跨市场的 alpha。</b>AMV 对美股未来 20 日的超额只有 <b class="red">+0.12% ~ +0.33%</b>（约等于零），全区间跑下来年化 <b>跑输</b>买入持有（11.1% vs 14.1%）。</li>
    <li><b>根因很简单：AMV 只测 A 股的钱。</b>它和 A 股日收益的相关性是 <b class="green">0.73–0.77</b>，和美股只有 <b class="red">0.13</b>。它不是全球风险偏好指标，拿它预判美股等于隔着一条河看别人家的水位。</li>
    <li><b>但 A 股这边确实有效，而且中小盘更强。</b>2020 年以来：创业板年化 <b class="green">21.4%</b>（买入持有 4.3%）、科创50 <b class="green">19.1%</b>（3.5%）、上证 10.6%（2.5%）。<b>弹性越大的板块，对 AMV 异动越敏感。</b></li>
  </ol>
</div>

<div class="kpis">
  <div class="kpi"><div class="lab">AMV ~ A股 相关性</div><div class="val green">0.73–0.77</div><div class="note">信号有效的基础</div></div>
  <div class="kpi"><div class="lab">AMV ~ 美股 相关性</div><div class="val red">0.13</div><div class="note">几乎无关</div></div>
  <div class="kpi"><div class="lab">美股 20 日超额</div><div class="val red">+0.2%</div><div class="note">等于没有</div></div>
  <div class="kpi"><div class="lab">A股 20 日超额</div><div class="val green">+1.6~3.5%</div><div class="note">创业板最高</div></div>
</div>

<h2>一、同台对比（2020-01 ~ 2026-11，全部标的同一区间）</h2>
<table>
<tr><th>标的</th><th>样本</th><th colspan="3" style="text-align:center">买入持有</th><th colspan="3" style="text-align:center">AMV 改进版</th><th>笔数</th></tr>
<tr><th></th><th></th><th>年化</th><th>Sharpe</th><th>回撤</th><th>年化</th><th>Sharpe</th><th>回撤</th><th></th></tr>
<tr><td colspan="9" style="background:#f7f9fc;font-weight:600;">A 股（T+1 收盘执行）</td></tr>
<tr><td>上证指数</td><td>1,663</td><td>2.51%</td><td>0.23</td><td>−27.3%</td><td class="green">10.56%</td><td class="green">1.07</td><td class="green">−9.2%</td><td>35</td></tr>
<tr><td><b>创业板指</b></td><td>1,663</td><td>4.34%</td><td>0.29</td><td>−57.1%</td><td class="green"><b>21.43%</b></td><td class="green"><b>1.19</b></td><td class="green">−20.8%</td><td>37</td></tr>
<tr><td><b>科创50</b></td><td>1,663</td><td>3.50%</td><td>0.27</td><td>−62.7%</td><td class="green"><b>19.12%</b></td><td class="green">0.91</td><td class="green">−22.1%</td><td>37</td></tr>
<tr><td colspan="9" style="background:#f7f9fc;font-weight:600;">美股（T+1 收盘执行，保守口径）</td></tr>
<tr><td>标普500</td><td>1,606</td><td class="green">14.12%</td><td>0.75</td><td>−33.9%</td><td class="red">11.14%</td><td class="green">1.16</td><td class="green">−7.6%</td><td>32</td></tr>
<tr><td>纳斯达克</td><td>1,606</td><td class="green">17.30%</td><td>0.76</td><td>−36.4%</td><td class="red">11.94%</td><td class="green">0.97</td><td class="green">−14.5%</td><td>34</td></tr>
<tr><td>纳指100</td><td>1,606</td><td class="green">19.72%</td><td>0.83</td><td>−35.6%</td><td class="red">13.74%</td><td class="green">1.06</td><td class="green">−11.5%</td><td>34</td></tr>
</table>
<div class="cap">A 股用 T+1 收盘执行；美股时间上 AMV（北京 T 日 15:00）早于美股 T 日开盘（北京 T 日 21:30），主要结果也给了 T+1 保守口径，见第三节。</div>

<p><b>读这张表的方法：</b></p>
<ul>
<li><b>A 股：年化、Sharpe、回撤三项全面提升。</b>创业板从 4.3% 干到 21.4%，回撤从 −57% 压到 −21%。</li>
<li><b>美股：年化输、Sharpe 赢、回撤大赢。</b>标普年化少了 3 个点，但 Sharpe 从 0.75 提到 1.16，回撤从 −34% 压到 −7.6%。<b>这是"少赚换少亏"，不是 alpha。</b></li>
</ul>

<div class="warn">
<b>这个区别很重要：</b>如果你问"能不能靠它多赚钱"，美股答案是<b>不能</b>；如果你问"能不能用它把回撤按住"，美股答案是<b>能，而且效果很好</b>。<br>
因为 AMV 异动时全球风险偏好往往同步，你持仓的那 20 天美股上涨概率确实高（标普 20 日胜率 70.4%），<b>但这是因为美股自己长期上涨 + 你减少了暴露时间，不是因为 AMV 看懂了美股。</b>
</div>

<h2>二、Alpha 检验：超额到底有多大</h2>
<table>
<tr><th>标的</th><th>方案</th><th>年化超额</th><th>日均超额</th><th>t 值</th><th>p 值</th><th>Sharpe 差</th><th>判定</th></tr>
<tr><td>上证</td><td>改进版</td><td class="green">+8.05%</td><td>+2.65 bp</td><td>1.30</td><td>0.194</td><td>+0.84</td><td><span class="tag t-mid">正但不显著</span></td></tr>
<tr><td>创业板</td><td>改进版</td><td class="green">+17.09%</td><td>+4.75 bp</td><td>1.22</td><td>0.223</td><td>+0.90</td><td><span class="tag t-mid">正但不显著</span></td></tr>
<tr><td>科创50</td><td>改进版</td><td class="green">+15.62%</td><td>+4.18 bp</td><td>1.02</td><td>0.308</td><td>+0.64</td><td><span class="tag t-mid">正但不显著</span></td></tr>
<tr><td>标普500</td><td>改进版</td><td class="red">−2.98%</td><td>−1.71 bp</td><td>−0.60</td><td>0.549</td><td>+0.41</td><td><span class="tag t-bad">负</span></td></tr>
<tr><td>纳斯达克</td><td>改进版</td><td class="red">−5.36%</td><td>−2.79 bp</td><td>−0.82</td><td>0.412</td><td>+0.21</td><td><span class="tag t-bad">负</span></td></tr>
<tr><td>纳指100</td><td>改进版</td><td class="red">−5.98%</td><td>−3.00 bp</td><td>−0.87</td><td>0.386</td><td>+0.23</td><td><span class="tag t-bad">负</span></td></tr>
</table>
<p><b>所有 t 值都在 ±1.3 以内，没有一个显著。</b>这不能证明 A 股有效，也不能证明美股无效——只能说明<b>"在 2020 年以来这 1,600 个交易日、30 多笔交易里，分不出真假"</b>。样本太小了。</p>

<h3>信号本身值多少：AMV ≥+4% 之后的 20 日超额</h3>
<table>
<tr><th>标的</th><th>信号数</th><th>20 日收益</th><th>无条件基准</th><th>超额</th><th>胜率</th></tr>
<tr><td>上证</td><td>74</td><td>+1.94%</td><td>+0.33%</td><td class="green">+1.61%</td><td>62.2%</td></tr>
<tr><td>创业板</td><td>74</td><td>+4.22%</td><td>+0.76%</td><td class="green"><b>+3.46%</b></td><td>59.5%</td></tr>
<tr><td>科创50</td><td>74</td><td>+4.02%</td><td>+0.65%</td><td class="green"><b>+3.37%</b></td><td>54.1%</td></tr>
<tr><td>标普500</td><td>71</td><td>+1.32%</td><td>+1.20%</td><td class="red">+0.12%</td><td>70.4%</td></tr>
<tr><td>纳斯达克</td><td>71</td><td>+1.84%</td><td>+1.50%</td><td class="red">+0.33%</td><td>64.8%</td></tr>
<tr><td>纳指100</td><td>71</td><td>+1.92%</td><td>+1.67%</td><td class="red">+0.25%</td><td>66.2%</td></tr>
</table>
<img src="data:image/png;base64,{IMG}" alt="跨市场对比">
<div class="cap">① A股净值；② 美股净值（实线=改进版，虚线=买入持有）；③ 20日超额：A股红、美股蓝；④ 根因：相关性 0.73–0.77 vs 0.13–0.14。</div>

<p><b>注意美股那 70% 的胜率——那是陷阱。</b>美股无条件 20 日胜率本来就有 60% 左右（长期上涨），信号只把它抬到 70%，超额 +0.12% 基本是噪音。<b>判断信号价值要看超额，不能看胜率</b>，否则你在任何牛市里都会觉得自己发现了圣杯。</p>

<h2>三、时间上的真相：AMV 对美股只是"当日联动"</h2>
<table>
<tr><th>执行方式</th><th>标普500 年化</th><th>Sharpe</th><th>纳斯达克 年化</th><th>Sharpe</th></tr>
<tr><td>同日执行（AMV 收盘 → 当晚美股开盘买）</td><td>13.57%</td><td>1.28</td><td>15.69%</td><td>1.21</td></tr>
<tr><td>滞后一日</td><td>11.14%</td><td>1.16</td><td>11.94%</td><td>0.97</td></tr>
<tr><td>滞后两日</td><td>8.43%</td><td>0.93</td><td>8.84%</td><td>0.77</td></tr>
</table>
<p>如果是真信号，滞后应该衰减——<b>确实在衰减，但衰减得太快太线性</b>：每滞后一天掉 2.5 个点。这说明收益主要来自"AMV 异动当天晚上的那波全球 risk-on"，而不是"AMV 预判了美股未来 20 天"。<b>本质是同步，不是领先。</b></p>

<h2>四、决定性对照：换成美股自己的动量，效果翻几倍</h2>
<p>同样的规则（单日大涨入场、持 20 天、止损 −3%），把入场条件从"AMV ≥+4%"换成"该指数自身单日 ≥1.5σ"：</p>
<table>
<tr><th>标的</th><th>AMV ≥+4% 入场</th><th>自身单日 ≥1.5σ 入场</th><th>买入持有</th><th>结论</th></tr>
<tr><td>上证</td><td>21.3% / S1.82</td><td>20.9% / S1.68</td><td>2.5% / S0.23</td><td><span class="tag t-mid">两者相当</span></td></tr>
<tr><td>创业板</td><td>40.7% / S1.77</td><td class="green">56.9% / S2.08</td><td>4.3% / S0.29</td><td><span class="tag t-ok">自身动量更好</span></td></tr>
<tr><td>科创50</td><td>44.3% / S1.68</td><td class="green">73.4% / S2.37</td><td>3.5% / S0.27</td><td><span class="tag t-ok">自身动量更好</span></td></tr>
<tr><td>标普500</td><td>13.6% / S1.28</td><td class="green">34.6% / S2.64</td><td>14.1% / S0.75</td><td><span class="tag t-bad">AMV 基本无用</span></td></tr>
<tr><td>纳斯达克</td><td>15.7% / S1.21</td><td class="green">49.0% / S2.60</td><td>17.3% / S0.76</td><td><span class="tag t-bad">AMV 基本无用</span></td></tr>
<tr><td>纳指100</td><td>17.0% / S1.29</td><td class="green">49.4% / S2.57</td><td>19.7% / S0.83</td><td><span class="tag t-bad">AMV 基本无用</span></td></tr>
</table>
<div class="cap">注：本表统一用同日执行（lag=0）以便横向比较；A 股 lag=0 偏乐观，严格口径见第一节。</div>

<div class="good">
<b>这张表是整个测试里信息量最大的：</b><br>
这套规则的"内核"其实是<b>波动突破 / 动量启动</b>，不是"活跃市值"。<b>在美股，把 AMV 换成美股自己的 1.5σ 大涨，年化从 13.6% 跳到 34.6%，Sharpe 从 1.28 跳到 2.64。</b><br>
所以在美股，你需要的不是 AMV，是一个能测美股自身资金/波动的指标（VIX 分位、成交量突破、板块宽度都行）。<b>AMV 在美股上唯一的作用，是被动地当了一个"全球 risk-on 的粗糙代理"。</b>
</div>

<h2>五、结论与落地</h2>
<div class="card">
<p><b>1. AMV 是 A 股专用指标，不能跨市场用。</b><br>
相关性 0.73（A 股）vs 0.13（美股），这是物理隔离。要么用 A 股的 AMV 做 A 股，要么用美股的指标做美股。混着用只会得到一堆 p 值 0.4–0.5 的结果。</p>

<p><b>2. A 股里，板块弹性决定效果：创业板 &gt; 科创50 &gt; 上证。</b><br>
2020 年以来：创业板 21.4%（回撤 −21%）、科创50 19.1%（−22%）、上证 10.6%（−9%）。<b>要弹性就选创业板/科创50，要稳就选上证。</b></p>

<p><b>3. 美股要用，只能当"减仓开关"，不能当"选时赚钱"。</b><br>
标普：Sharpe 0.75 → 1.16，回撤 −34% → −7.6%，但年化 14.1% → 11.1%。<b>适合"我本来就想降杠杆"的场景，不适合"我想跑赢标普"。</b></p>

<p><b>4. 如果要在美股做同类策略，换指标。</b><br>
用该指数自身的 1.5σ 单日大涨入场 + 持 20 天 + 止损 −3%，标普 34.6%、纳指 49.0%（2020 以来）。这个方向比 AMV 靠谱得多，值得单独测。</p>
</div>

<div class="warn">
<b>四条必须打折的：</b>
<ol>
<li><b>样本严重不足。</b>2020 年以来只有 31–37 笔交易，所有 t 值都在 ±1.3 内，<b>没有一个是统计显著的</b>。这张表能告诉你"方向"，不能告诉你"结论"。</li>
<li><b>科创50 只有 2020 年起的数据</b>（1,663 天），且 2020-2021 有一波极端行情，结果受这一段影响很大。</li>
<li><b>lag=0 对 A 股偏乐观。</b>严格口径（T+1 执行）下 A 股数字要打七折：上证 21.3% → 10.6%，创业板 40.7% → 21.4%。美股用 lag=0 是合理的（时序在前）。</li>
<li><b>多重检验。</b>我在这份报告里跑了 6 个标的 × 3 种执行 × 2 种方案，挑出来的"最好结果"天然有过拟合成分。真正该看的是"方向是否一致"，而不是某个具体数字。</li>
</ol>
</div>

<h2>六、一句话</h2>
<div class="card" style="border-left:4px solid #c0392b;">
<p style="font-size:15.5px;margin:6px 0;"><b>AMV 是 A 股的资金温度计，出了 A 股就失灵。</b></p>
<p>A 股：创业板 21.4% / 科创50 19.1%，回撤砍一半以上，但统计不显著。<br>
美股：超额 +0.12%~+0.33%，年化跑输买入持有 3–6 个点，唯一价值是把回撤从 −34% 压到 −8%。<br>
<b>想在美国市场用这套逻辑，把 AMV 换成"该指数自身 1.5σ 单日大涨"——效果是 AMV 的三倍。</b></p>
</div>

<div class="foot">
脚本：cross_market.py / plot_cross.py（同目录）<br>
数据：AMV 日线（用户提供）· 上证/创业板/科创50（新浪财经）· 标普500/纳斯达克/纳指100（新浪美股，2004/2014 年起）· 生成 2026-11-18
</div>

</div></body></html>"""

open('AMV跨市场alpha检验.html','w',encoding='utf-8').write(html)
print('OK', len(html))
