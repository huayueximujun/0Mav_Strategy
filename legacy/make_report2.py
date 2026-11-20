# -*- coding: utf-8 -*-
import base64
def b64(p): return base64.b64encode(open(p,'rb').read()).decode()
IMG = b64('amv_result.png')

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>指南针 AMV（活跃市值）择时有效性检验</title>
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
.kpi .lab{{font-size:11.5px;color:#7b8695;letter-spacing:.3px}}
.kpi .val{{font-size:21px;font-weight:700;margin:5px 0 2px;letter-spacing:-.5px}}
.kpi .note{{font-size:11.5px;color:#8b95a3}}
.red{{color:#c0392b}}.green{{color:#1e8449}}.blue{{color:#2471a3}}.amber{{color:#b9770e}}
.card{{background:#fff;border:1px solid #e3e7ee;border-radius:12px;padding:20px 22px;margin:16px 0}}
.verdict{{background:linear-gradient(135deg,#fdf3f2,#fbe9e7);border:1px solid #f0c4bd;border-radius:12px;padding:20px 24px;margin:20px 0}}
.verdict ol{{margin:8px 0 0;padding-left:22px}}.verdict li{{margin:9px 0}}
table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:13px;background:#fff}}
th{{background:#eef1f6;text-align:left;padding:9px 11px;font-weight:600;border-bottom:2px solid #dde3ec;font-size:12.5px;white-space:nowrap}}
td{{padding:8px 11px;border-bottom:1px solid #eef1f5;vertical-align:top}}
tr:hover td{{background:#fafbfd}}
code{{background:#eef1f6;padding:1.5px 5px;border-radius:4px;font-size:12.5px;font-family:ui-monospace,Consolas,monospace}}
.tag{{display:inline-block;padding:1.5px 7px;border-radius:20px;font-size:11.5px;font-weight:600}}
.t-bad{{background:#fbe3e0;color:#a93226}}.t-ok{{background:#dff0e4;color:#1e7b3e}}.t-mid{{background:#fdf0d5;color:#96690f}}
img{{width:100%;border:1px solid #e3e7ee;border-radius:10px;margin:10px 0;background:#fff}}
.cap{{font-size:12px;color:#7b8695;margin:-4px 0 18px}}
ul,ol{{padding-left:22px}}li{{margin:6px 0}}
.warn{{border-left:3px solid #e67e22;background:#fffbf3;padding:12px 16px;margin:14px 0;border-radius:0 8px 8px 0}}
.good{{border-left:3px solid #27ae60;background:#f5fbf7;padding:12px 16px;margin:14px 0;border-radius:0 8px 8px 0}}
.fix{{border-left:3px solid #7f8c8d;background:#f7f8fa;padding:12px 16px;margin:14px 0;border-radius:0 8px 8px 0}}
.foot{{margin-top:44px;padding-top:16px;border-top:1px solid #e3e7ee;font-size:12px;color:#8b95a3}}
@media(max-width:760px){{.kpis{{grid-template-columns:repeat(2,1fr)}}}}
</style></head><body><div class="wrap">

<header>
  <h1>指南针 AMV（活跃市值）择时有效性检验</h1>
  <div class="sub">数据：AMV 日线 1993-01-03 → 2026-11-13（8,245 日）· 上证指数 1990-12-19 → 2026-11-17（8,765 日）· 创业板指 2010-06-01 → 2026-11-17（3,997 日）<br>
  方法：Spearman IC / 分位分组 / 事件研究 / 均线择时回测（T 日收盘信号，T+1 执行，含 2bp 成本）</div>
</header>

<div class="verdict">
  <strong style="font-size:16px;">结论先行</strong>
  <ol>
    <li><b>有用，但用法和你想的不一样。</b>AMV <b>不是方向预测器</b>（近 10 年对次日/未来 20 日涨跌的 IC 基本为 0），它是<b>资金活跃度的指标</b>。真正的价值在"识别冰点"和"过滤过热"，不在"猜明天涨跌"。</li>
    <li><b>对大盘有效，对创业板几乎无效。</b>近 10 年上证：AMV-MA10 择时年化 <b class="green">5.96%</b>、回撤 <b class="green">−12.5%</b>，买入持有仅 0.94%、回撤 −30.8%。创业板：AMV 择时 5.97%/0.39，跟指数自身 MA60（5.97%/0.38）<b>打平，没有增量</b>。</li>
    <li><b>最关键的一条：AMV 冰点是"入场事件"，不是"持有状态"。</b>上证进入 AMV 250 日低位后 60 日平均 <b class="green">+3.98%</b>、胜率 60%（t=11.2）；但只要你"因为它在低位就一直拿着"，年化变成 <b class="red">−3.09%</b>，创业板更是 <b class="red">−15.78%</b>。</li>
  </ol>
</div>

<div class="kpis">
  <div class="kpi"><div class="lab">AMV 领先性（近10年 IC）</div><div class="val amber">≈ 0</div><div class="note">未来 1–20 日无信息量</div></div>
  <div class="kpi"><div class="lab">上证择时 Sharpe 提升</div><div class="val green">0.14 → 0.58</div><div class="note">AMV-MA10，近10年</div></div>
  <div class="kpi"><div class="lab">创业板增量</div><div class="val red">无</div><div class="note">打平指数 MA60</div></div>
  <div class="kpi"><div class="lab">统计显著性</div><div class="val red">t = 0.69</div><div class="note">p=0.49，不显著</div></div>
</div>

<div class="fix">
<b>先纠正我上一版的一个误判。</b>最初我把 <code>close</code> 当价格序列分析，发现日收益 ρ1=+0.423、游程 z=−32.6、与成交额对数相关 0.969，判定为"数据异常"。知道它是指南针 AMV 之后，这些特征<b>全部有正解</b>：AMV = 流通市值 × 活跃度的<b>资金规模量</b>，天然是累积型、平滑型变量，惯性是定义决定的，不是缺陷。<br>
唯一需要记住的推论是：<b>用 AMV 做日频动量/机器学习预测方向，得到的高 Sharpe 都是"规模量的自我复制"，不可交易。</b>下面所有检验都建立在"AMV 是资金指标"这个正确前提上。
</div>

<h2>一、它到底有没有领先性：几乎没有</h2>
<p>把 AMV 的过去 N 日增速，对上指数的未来 M 日收益，算 Spearman 秩相关（IC）。这是判断"是不是领先指标"最直接的办法。</p>
<table>
<tr><th>AMV 窗口 → 预测期</th><th>5 日</th><th>20 日</th><th>60 日</th><th>判读</th></tr>
<tr><td>N=5 → 未来</td><td>+0.061 / <b class="red">−0.011</b></td><td>+0.068 / +0.039</td><td>+0.029 / <b class="red">−0.138</b></td><td>短期归零</td></tr>
<tr><td>N=20 → 未来</td><td>+0.071 / +0.034</td><td>+0.036 / −0.025</td><td>+0.023 / <b class="red">−0.184</b></td><td>60 日转负</td></tr>
<tr><td>N=60 → 未来</td><td>+0.049 / −0.062</td><td>+0.013 / <b class="red">−0.139</b></td><td>+0.046 / <b class="red">−0.141</b></td><td>全面转负</td></tr>
</table>
<div class="cap">格式：全样本 IC / 近 10 年 IC。IC 绝对值 &lt;0.05 视为无信息量（灰带）。</div>

<p>三个结论：</p>
<ul>
<li><b>全样本看，IC 只有 +0.01 ~ +0.07</b>，属于"有一点点但不足以覆盖交易成本"的量级。AMV 不是领先指标，它和指数是<b>同步甚至略滞后</b>的。</li>
<li><b>近 10 年短期 IC 归零</b>（−0.01 ~ +0.04）：市场效率提高后，AMV 对未来 1–20 日涨跌已经没有增量信息。</li>
<li><b>但 60 日 IC 显著转负</b>（−0.13 ~ −0.18）：这是唯一还活着的信号——<b>AMV 短期冲得太猛，未来 2–3 个月倾向于回调</b>。方向是"逆向"，不是"顺势"。</li>
</ul>

<h2>二、作为择时器：上证有效，创业板无效</h2>
<img src="data:image/png;base64,{IMG}" alt="AMV 检验结果">
<div class="cap">① 近10年归一化；② 上证策略净值；③ AMV 进入低位后的收益路径（事件研究）；④ 样本内外 IC 对比。</div>

<h3>近 10 年（2016–2026）完整回测</h3>
<table>
<tr><th>策略</th><th colspan="4" style="text-align:center">上证指数</th><th colspan="4" style="text-align:center">创业板指</th></tr>
<tr><th></th><th>年化</th><th>Sharpe</th><th>回撤</th><th>仓位</th><th>年化</th><th>Sharpe</th><th>回撤</th><th>仓位</th></tr>
<tr><td>买入持有</td><td>0.94%</td><td>0.14</td><td>−30.8%</td><td>100%</td><td>−0.25%</td><td>0.14</td><td>−57.1%</td><td>100%</td></tr>
<tr><td>指数 MA20</td><td>−0.53%</td><td>0.01</td><td>−32.6%</td><td>53%</td><td>2.99%</td><td>0.25</td><td>−48.9%</td><td>49%</td></tr>
<tr><td>指数 MA60</td><td>0.73%</td><td>0.12</td><td>−24.2%</td><td>51%</td><td><b>5.97%</b></td><td><b>0.38</b></td><td>−41.3%</td><td>47%</td></tr>
<tr><td><b>AMV-MA10</b></td><td><b class="green">5.96%</b></td><td><b class="green">0.58</b></td><td><b class="green">−12.5%</b></td><td>47%</td><td>5.97%</td><td>0.39</td><td>−39.7%</td><td>47%</td></tr>
<tr><td>AMV-MA20</td><td>3.90%</td><td>0.40</td><td>−15.7%</td><td>46%</td><td>3.97%</td><td>0.29</td><td>−39.1%</td><td>46%</td></tr>
<tr><td>AMV&指数MA60 双确认</td><td>3.04%</td><td>0.37</td><td>−15.0%</td><td>33%</td><td><b>8.29%</b></td><td><b>0.55</b></td><td><b>−25.5%</b></td><td>30%</td></tr>
<tr><td>背离（AMV20日增速 &gt; 指数20日增速）</td><td><b>6.53%</b></td><td><b>0.60</b></td><td>−20.4%</td><td>44%</td><td>4.94%</td><td>0.33</td><td>−50.6%</td><td>46%</td></tr>
</table>

<h3>但优势只出现在 2016 年之后</h3>
<table>
<tr><th>区间</th><th>买入持有</th><th>指数 MA20</th><th>AMV-MA20</th><th>谁更好</th></tr>
<tr><td>上证 1996–2005</td><td>8.4% / 0.43</td><td><b>15.3% / 0.85</b></td><td>14.4% / 0.79</td><td><span class="tag t-bad">指数均线赢</span></td></tr>
<tr><td>上证 2006–2015</td><td>12.1% / 0.54</td><td><b>24.5% / 1.26</b></td><td>16.8% / 0.91</td><td><span class="tag t-bad">指数均线大胜</span></td></tr>
<tr><td>上证 2016–2026</td><td>0.9% / 0.14</td><td>−0.5% / 0.01</td><td><b>3.9% / 0.40</b></td><td><span class="tag t-ok">AMV 赢</span></td></tr>
<tr><td>创业板 2011–2015</td><td>19.4% / 0.69</td><td><b>27.3% / 1.13</b></td><td>15.2% / 0.73</td><td><span class="tag t-bad">指数均线赢</span></td></tr>
<tr><td>创业板 2016–2020</td><td>3.7% / 0.27</td><td>−2.6% / −0.05</td><td>−0.3% / 0.07</td><td><span class="tag t-mid">都不行</span></td></tr>
<tr><td>创业板 2021–2026</td><td>−4.1% / 0.01</td><td>6.8% / 0.42</td><td><b>6.5% / 0.40</b></td><td><span class="tag t-mid">打平</span></td></tr>
</table>
<div class="cap">格式：年化收益 / Sharpe。含 2bp 双边成本。</div>

<div class="warn">
<b>必须说清的两件事：</b>
<ul>
<li><b>统计上不显著。</b>AMV-MA20 相对买入持有的日均超额 +0.0094%（上证），t = 0.69，p = 0.49；创业板 t = 0.35，p = 0.73。<b>10 年样本不足以证明这是 alpha，只能说"看起来有帮助"。</b></li>
<li><b>2016 年前 AMV 是输的。</b>2006–2015 这十年，指数自身 MA20 做到 24.5%/1.26，AMV-MA20 只有 16.8%/0.91。AMV 的优势是"近几年才出现"的，可能来自市场结构变化（资金对行情的解释力上升），也可能是样本噪音。</li>
</ul>
</div>

<h2>三、真正的金矿：冰点是事件，不是状态</h2>
<p>这一节是整份报告最有价值的部分。同样是"AMV 处于 250 日区间最低 20%"，两种用法结果完全相反：</p>

<table>
<tr><th>用法</th><th>上证</th><th>创业板</th></tr>
<tr><td><b>进入低位后买入、持有 N 日</b><br><span style="color:#7b8695;font-size:12px">（事件研究，n=2,064 / 927）</span></td>
<td>5 日 +0.08%<br>10 日 +0.40%（t=2.35）<br>20 日 <b class="green">+1.23%</b>（t=5.40）<br>60 日 <b class="green">+3.98%</b>（胜率 60%，t=11.24）</td>
<td>5 日 −0.10%<br>10 日 0.00%<br>20 日 +0.72%（t=2.11，但<b>中位数 −0.61%</b>）<br>60 日 +2.97%（<b>中位数 −0.09%</b>）</td></tr>
<tr><td><b>只要在低位就一直持有</b><br><span style="color:#7b8695;font-size:12px">（状态持有，占全部交易日 26.3% / 24.2%）</span></td>
<td><b class="red">年化 −3.09%</b><br>胜率 0.492</td><td><b class="red">年化 −15.78%</b><br>胜率 0.483</td></tr>
</table>

<div class="good">
<b>怎么理解这个矛盾：</b>AMV 跌到低位，说明<b>资金正在撤离</b>。撤离过程可能持续很久（低位状态占 26% 的交易日），期间指数继续阴跌——所以你"一直拿着"是负期望。但<b>低位本身是一个高赔率的时点</b>：从上证看，进入低位后 60 日有 60% 概率上涨、平均 +3.98%。<br>
所以正确用法是：<b>AMV 破位 = 开始建仓的闹钟，而不是"全仓押注"的理由</b>。要有时间窗口（20–60 日）和止损。
</div>

<h3>创业板为什么不行</h3>
<p>看中位数就明白了：创业板 AMV 低位后 20 日<b>中位数 −0.61%</b>，60 日<b>中位数 −0.09%</b>——均值被少数几波大涨拉高了，<b>一半以上的情况是继续跌</b>。AMV 反映的是全市场（以大盘蓝筹为主）的资金活跃度，而创业板由产业周期和主题情绪驱动，资金活跃度是<b>结果</b>而不是原因。</p>

<h2>四、还有一个反直觉的发现：极端高位反而继续涨</h2>
<table>
<tr><th>AMV 在 250 日区间的位置</th><th>未来 20 日平均收益（上证）</th><th>上涨概率</th></tr>
<tr><td>最低 20%</td><td>+1.72%</td><td>54%</td></tr>
<tr><td>次低</td><td class="red">−0.63%</td><td>44%</td></tr>
<tr><td>中间</td><td>+0.04%</td><td>51%</td></tr>
<tr><td>次高</td><td>+0.23%</td><td>49%</td></tr>
<tr><td>最高 20%</td><td class="green">+2.28%</td><td>58%</td></tr>
</table>
<p>这是典型的 <b>U 型</b>：<b>两端都好，中间最差</b>。AMV 极高（资金狂热）之后，市场往往还有惯性上冲；AMV 极低（资金冰点）之后，反弹赔率高。<b>最难受的是"次低"和"中间"</b>——资金在撤但没撤透，或者不温不火。</p>
<p>对逆向框架的直接含义：<b>不要在"半山腰"抄底</b>。要么等 AMV 打到区间最低 20% 分位，要么承认资金还在流入、跟着趋势走。中间地带是负期望区。</p>

<h2>五、如果你要用，四个可执行方案</h2>
<div class="card">
<p><b>方案 A · 冰点建仓（首选，适合你的逆向框架）</b><br>
信号：AMV 跌破 250 日区间 20% 分位。动作：建仓，持有窗口 20–60 日。<br>
预期：上证 60 日 +3.98%、胜率 60%。<b>必须设时间止损（60 日不涨就走）</b>，因为持续持有是 −3.09%/年。<br>
<b>只用于上证/沪深300/中证A500，不要用于创业板/科创。</b></p>

<p><b>方案 B · 过热减仓（近 10 年唯一稳定为负的 IC）</b><br>
信号：AMV 过去 20/60 日增速进入历史前 10%，或 AMV 站上 250 日区间 95% 分位。动作：减仓 20–30%，未来 60 日不加仓。<br>
依据：近 10 年 N=60→M=60 的 IC = −0.141，N=20→M=60 的 IC = −0.184。</p>

<p><b>方案 C · 降波动过滤器（想拿住仓位又怕回撤）</b><br>
信号：AMV &gt; MA10 才持有，否则空仓。上证近 10 年：年化 5.96%、回撤 −12.5%（买入持有是 0.94% / −30.8%）。<br>
代价：仓位只有 47%，2024 年 9 月那种急涨会踏空一段。<b>本质是把"择时"换成"控回撤"，别指望它提收益。</b></p>

<p><b>方案 D · 双确认（最稳，但最钝）</b><br>
信号：AMV &gt; AMV-MA20 且 指数 &gt; 指数-MA60。上证回撤压到 −15.0%、创业板 −25.5%（买入持有 −57.1%）。<br>
适合"宁可少赚也不愿大回撤"的仓位管理，年化只有 3–8%。</p>
</div>

<h2>六、四个坑</h2>
<div class="warn">
<ol>
<li><b>别把 AMV 的点位当指数点位。</b>AMV 从 3.1 涨到 145,790（33 年 4.7 万倍），它是资金规模量。看到"AMV 创新高"不等于"市场创新高"。</li>
<li><b>别用日频动量/机器学习预测方向。</b>我用逻辑回归做样本外测试，准确率 66%、AUC 0.70——全是假的，因为 AMV 是平滑累积量，它的"收益"高度自相关（ρ1=0.42）。真实 A 股日收益 ρ1 只有 0.03。</li>
<li><b>别在 AMV 低位"长期埋伏"。</b>上证年化 −3.09%，创业板 −15.78%。低位是入场时点，不是持有理由。</li>
<li><b>别指望统计显著。</b>10 年样本 t=0.69，p=0.49。AMV 择时的改善更像"降波动"而非"真 alpha"。如果你的策略依赖它跑出超额，风险很大；如果只是用它避免大回撤，可以。</li>
</ol>
</div>

<h2>七、一句话总结</h2>
<div class="card" style="border-left:4px solid #c0392b;">
<p style="font-size:15.5px;margin:6px 0;"><b>AMV 是一个"资金温度计"，不是"价格预测器"。</b></p>
<p>它能告诉你<b>现在资金是冰点还是过热</b>，但不能告诉你<b>明天涨还是跌</b>。对大盘（上证）的择时价值体现在"把回撤从 −31% 压到 −12%"；对创业板基本没有增量。<br>
最值得记住的一条：<b>AMV 打到冰点，是让你开始看盘的信号，不是让你满仓的理由。</b></p>
</div>

<div class="foot">
检验脚本：amv_test.py / amv_robust.py / amv_event.py / plot_amv.py（同目录）<br>
数据源：指南针 AMV 日线（用户提供）· 上证 / 创业板日线（新浪财经）· 报告生成 2026-11-18
</div>

</div></body></html>"""

open('AMV择时有效性评估.html','w',encoding='utf-8').write(html)
print('OK', len(html))
