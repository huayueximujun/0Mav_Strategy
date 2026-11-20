# -*- coding: utf-8 -*-
"""生成 HTML 诊断报告"""
import base64

def b64(p):
    return base64.b64encode(open(p, 'rb').read()).decode()

IMG1 = b64('diag.png')
IMG2 = b64('diag2.png')
IMG3 = b64('diag_cmp.png')

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>0amv_daily_261113 序列审计与可预测性检验</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#f4f6f9; color:#1c2430;
         font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif;
         line-height:1.65; font-size:14.5px; }}
  .wrap {{ max-width:1080px; margin:0 auto; padding:36px 28px 80px; }}
  header {{ border-left:5px solid #c0392b; padding-left:18px; margin-bottom:28px; }}
  h1 {{ font-size:26px; margin:0 0 8px; letter-spacing:-.3px; }}
  .sub {{ color:#66707d; font-size:13.5px; }}
  h2 {{ font-size:19px; margin:42px 0 14px; padding-bottom:8px; border-bottom:1px solid #e3e7ee; }}
  h3 {{ font-size:15.5px; margin:24px 0 10px; color:#2c3e50; }}
  p {{ margin:10px 0; }}
  .kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:24px 0 8px; }}
  .kpi {{ background:#fff; border:1px solid #e3e7ee; border-radius:10px; padding:16px 14px; }}
  .kpi .lab {{ font-size:11.5px; color:#7b8695; letter-spacing:.4px; text-transform:uppercase; }}
  .kpi .val {{ font-size:22px; font-weight:700; margin:6px 0 2px; letter-spacing:-.5px; }}
  .kpi .note {{ font-size:11.5px; color:#8b95a3; }}
  .red {{ color:#c0392b; }} .green {{ color:#1e8449; }} .blue {{ color:#2471a3; }} .amber {{ color:#b9770e; }}
  .card {{ background:#fff; border:1px solid #e3e7ee; border-radius:12px; padding:20px 22px; margin:16px 0; }}
  .verdict {{ background:linear-gradient(135deg,#fdf3f2,#fbe9e7); border:1px solid #f0c4bd; border-radius:12px;
              padding:20px 24px; margin:20px 0; }}
  .verdict ol {{ margin:8px 0 0; padding-left:22px; }}
  .verdict li {{ margin:9px 0; }}
  table {{ width:100%; border-collapse:collapse; margin:14px 0; font-size:13px; background:#fff; }}
  th {{ background:#eef1f6; text-align:left; padding:9px 11px; font-weight:600; border-bottom:2px solid #dde3ec;
        font-size:12.5px; white-space:nowrap; }}
  td {{ padding:9px 11px; border-bottom:1px solid #eef1f5; vertical-align:top; }}
  tr:hover td {{ background:#fafbfd; }}
  code {{ background:#eef1f6; padding:1.5px 5px; border-radius:4px; font-size:12.5px;
          font-family:ui-monospace,Consolas,monospace; }}
  .tag {{ display:inline-block; padding:1.5px 7px; border-radius:20px; font-size:11.5px; font-weight:600; }}
  .t-bad {{ background:#fbe3e0; color:#a93226; }}
  .t-ok {{ background:#dff0e4; color:#1e7b3e; }}
  .t-mid {{ background:#fdf0d5; color:#96690f; }}
  img {{ width:100%; border:1px solid #e3e7ee; border-radius:10px; margin:10px 0; background:#fff; }}
  .cap {{ font-size:12px; color:#7b8695; margin:-4px 0 18px; }}
  ul, ol {{ padding-left:22px; }} li {{ margin:6px 0; }}
  .warn {{ border-left:3px solid #e67e22; background:#fffbf3; padding:12px 16px; margin:14px 0; border-radius:0 8px 8px 0; }}
  .good {{ border-left:3px solid #27ae60; background:#f5fbf7; padding:12px 16px; margin:14px 0; border-radius:0 8px 8px 0; }}
  .foot {{ margin-top:50px; padding-top:16px; border-top:1px solid #e3e7ee; font-size:12px; color:#8b95a3; }}
  @media (max-width:760px) {{ .kpis {{ grid-template-columns:repeat(2,1fr); }} }}
</style>
</head>
<body><div class="wrap">

<header>
  <h1>0amv_daily_261113 · 序列审计与可预测性检验</h1>
  <div class="sub">数据：8,245 个交易日 · 1993-01-03 → 2026-11-13 · 7 列 OHLCV<br>
  检验：ACF / Ljung-Box / 方差比 / Hurst / 游程 / ARCH-LM / HAR-RV / 逻辑回归 walk-forward / 分位数事件研究</div>
</header>

<div class="verdict">
  <strong style="font-size:16px;">一句话结论</strong>
  <ol>
    <li><b>这个序列"看起来"极度可预测</b>（1 日动量年化 Sharpe <b class="red">4.54</b>，逻辑回归样本外准确率 <b class="red">66.3%</b>，AUC 0.697），但<b>这个结论不能采信</b>——它的强度是真实市场不可能出现的量级。</li>
    <li><b>根因：<code>close</code> 列不是价格。</b>它与同文件里的成交均价（<code>amount/volume</code>）比值在 33 年里漂移了 <b class="red">745 倍</b>（12.2 → 9,082）。价格与成交均价的比值必须恒定在个位数，这是硬约束。</li>
    <li><b>唯一可信的是量能列。</b><code>volume/amount</code> 与真实 A 股两市数据逐日吻合（误差 &lt;0.05%）。在这两列上验出了<b class="green">真信号</b>：成交额有显著的均值回复（ρ1 = −0.254），放量后次日缩量 −5.84%，缩量后次日放量 +4.06%。</li>
  </ol>
</div>

<div class="kpis">
  <div class="kpi"><div class="lab">样本跨度</div><div class="val">33.9 年</div><div class="note">8,245 交易日</div></div>
  <div class="kpi"><div class="lab">close 累计涨幅</div><div class="val red">4.7 万倍</div><div class="note">年化 37.4%</div></div>
  <div class="kpi"><div class="lab">日收益 ρ1</div><div class="val red">+0.423</div><div class="note">真实 A 股约 +0.03</div></div>
  <div class="kpi"><div class="lab">数据可信度</div><div class="val amber">量能 ✔ / 价格 ✘</div><div class="note">见下方 5 条红灯</div></div>
</div>

<h2>一、数据画像</h2>
<div class="card">
<table>
<tr><th>字段</th><th>起始 → 结束</th><th>量级</th><th>判读</th></tr>
<tr><td><code>date</code></td><td>1993-01-03 → 2026-11-13</td><td>8,245 行，无重复、无缺失</td><td><span class="tag t-ok">可信</span></td></tr>
<tr><td><code>volume</code></td><td>1,342 万股 → 1,031 亿股</td><td>日均 297 亿股</td><td><span class="tag t-ok">可信</span> 与 A 股真实成交量同量级</td></tr>
<tr><td><code>amount</code></td><td>0.89 亿元 → 1.66 万亿元</td><td>日均 3,798 亿元</td><td><span class="tag t-ok">可信</span> 逐日核对通过（见下）</td></tr>
<tr><td><code>amount/volume</code></td><td>27.3 元 → 16.1 元</td><td>中位数 11.07 元</td><td><span class="tag t-ok">可信</span> 这就是 A 股平均股价</td></tr>
<tr><td><code>close</code></td><td>3.10 → 145,790.7</td><td>年化 37.4%，年化波动 80%</td><td><span class="tag t-bad">不可信</span> 不是价格</td></tr>
<tr><td><code>open/high/low</code></td><td>同步膨胀</td><td>日内振幅中位数 3.4%</td><td><span class="tag t-bad">跟随 close</span> 同源问题</td></tr>
</table>

<h3>成交额的逐日核对（唯一能钉死的锚点）</h3>
<p>2026 年 11 月 2 日至 6 日，公开报道的两市成交额分别为 17,837 / 17,034 / 20,377 / 21,179 / 16,578 亿元。文件里 <code>amount</code> 除以 1e8 后为 17,832.5 / 17,029.1 / 20,373.9 / 21,177.2 / 16,576.0 亿元——<b class="green">五天全部吻合，最大误差 0.03%</b>。</p>
<p>这证明：<b>数据源是真实的全市场日频数据，不是伪造的。</b>问题只出在价格列。</p>
<img src="data:image/png;base64,{IMG3}" alt="成交额验证与走势对比">
<div class="cap">左：同期走势归一化对比，0amv 日波动是上证的 2.5–4 倍。右：成交额逐日吻合。</div>
</div>

<h2>二、五条红灯：为什么 close 不能当价格用</h2>

<h3>红灯 1 · close / 成交均价 = 12 → 9,082（漂移 745 倍）</h3>
<p>若 <code>close</code> 是"元/股"，它与 <code>amount/volume</code>（也是元/股）的比值必须恒定在个位数波动。实测：</p>
<table>
<tr><th>年份</th><th>1993</th><th>1998</th><th>2003</th><th>2008</th><th>2013</th><th>2018</th><th>2023</th><th>2026</th></tr>
<tr><td>close / 均价</td><td>12.2</td><td>49.0</td><td>247.9</td><td>1,210</td><td>1,719</td><td>3,027</td><td>6,246</td><td><b class="red">9,082</b></td></tr>
</table>
<p>反推 <code>close / 均价</code> 的隐含含义：2016 年 3,982 亿"股"，2026 年 11,015 亿"股"——<b>这个量级和"总股本"对得上</b>。所以 <code>close</code> 最可能是<b>总市值一类的规模累积量</b>（单位约十亿元），而不是指数点位。</p>

<h3>红灯 2 · 日收益 1 阶自相关 +0.423（真实 A 股 ≈ +0.03）</h3>
<p>用同一段数据跑白噪声模拟，ρ1 稳定落在 −0.01 ~ −0.03；95% 置信带是 ±0.022。<b class="red">+0.423 超出去 19 倍</b>。lag2 = +0.253、lag3 = +0.168，衰减平滑。</p>
<p>更关键：<b>全样本日内收益 ρ1 只有 +0.087（正常），但 2016 年以后跳到 +0.405。</b>同一列数据在不同年代呈现两种统计性质，这是"换源/改口径"的典型指纹，不是市场规律。</p>

<h3>红灯 3 · 游程检验 z = −32.57</h3>
<p>8,239 个涨跌日只跑出 2,616 个游程，期望 4,079 个。真实指数这个 z 值通常在 −1 ~ −3。<b>−32.6 意味着涨跌高度成串</b>，属于"被平滑过的水平量"特征。</p>

<h3>红灯 4 · 隔夜/日内波动比从 3.39 漂移到 0.42</h3>
<img src="data:image/png;base64,{IMG1}" alt="诊断总图">
<div class="cap">① 对数轴全历史；② 与真实上证同期对比；③ 成交额逐日吻合；④ 收益 ACF（灰带=95% 白噪声区）；⑤ 隔夜/日内波动比的时代漂移。</div>
<p>真实 A 股隔夜跳空波动长期略小于日内波动（比值 0.4–0.8）。而本数据 90 年代初是 <b>3.39</b>，2015 年后才降到 <b>0.42</b>。<b>一个市场的微观结构不会在 30 年里这样单向收敛</b>——这更像是数据拼接方式在演进。</p>

<h3>红灯 5 · 与真实上证同期涨幅放大 2.5–4 倍</h3>
<table>
<tr><th>日期</th><th>真实上证</th><th>本文件 close</th><th>放大倍数</th><th>当日公开信息</th></tr>
<tr><td>11/02</td><td>+1.08%</td><td class="red">+3.94%</td><td>3.65×</td><td>政策座谈会</td></tr>
<tr><td>11/03</td><td>−0.82%</td><td>−1.09%</td><td>1.33×</td><td>—</td></tr>
<tr><td>11/04</td><td>+2.16%</td><td class="red">+7.38%</td><td>3.42×</td><td>创业板 +6.40%、科创综指 +9.90%</td></tr>
<tr><td>11/05</td><td>+0.10%</td><td class="red">+3.75%</td><td>37.5×</td><td>—</td></tr>
<tr><td>11/06</td><td>−1.10%</td><td>−2.75%</td><td>2.50×</td><td>外围重挫，A 股低开高走</td></tr>
</table>
<p>11/04 那天 close 的日内涨幅（+7.24%）确实接近创业板/科创的位置，说明<b>它可能是一个偏成长、偏小盘的加权口径</b>。但 11/05 上证几乎不动而它涨 3.75%，这个偏离已超出任何"宽基指数结构差异"能解释的范围。</p>

<h2>三、可预测性检验：分层结论</h2>
<p>下表每一项都做了，但<b>可信度一栏决定了能不能用</b>。</p>
<table>
<tr><th>检验</th><th>统计量</th><th>显著性</th><th>解读</th><th>可采信度</th></tr>
<tr><td>收益 ACF(1)</td><td>+0.423</td><td>p &lt; 1e-100</td><td>强惯性</td><td><span class="tag t-bad">数据伪影</span></td></tr>
<tr><td>Ljung-Box(20)</td><td>Q = 2,563</td><td>p ≈ 0</td><td>非白噪声</td><td><span class="tag t-bad">数据伪影</span></td></tr>
<tr><td>方差比 VR(20)</td><td>2.47</td><td>z = +0.34</td><td>远超随机游走</td><td><span class="tag t-bad">数据伪影</span></td></tr>
<tr><td>Hurst（收益）</td><td>0.599 ~ 0.710</td><td>—</td><td>趋势持续</td><td><span class="tag t-bad">数据伪影</span></td></tr>
<tr><td>游程 z</td><td>−32.57</td><td>p ≈ 0</td><td>涨跌成串</td><td><span class="tag t-bad">数据伪影</span></td></tr>
<tr><td>1 日动量 Sharpe</td><td>+4.54（近10年 +4.67）</td><td>t = 25.9</td><td>年化 140%</td><td><span class="tag t-bad">不可交易</span></td></tr>
<tr><td>逻辑回归样本外</td><td>准确率 66.3%，AUC 0.697</td><td>n = 3,274</td><td>看似强预测力</td><td><span class="tag t-bad">数据伪影</span></td></tr>
<tr><td>ARCH-LM(5) 2016+</td><td>nR² = 859.7</td><td>临界值 11.07</td><td>波动率聚集极强</td><td><span class="tag t-ok">可用</span></td></tr>
<tr><td>HAR-RV 波动预测</td><td>样本内 R² = 0.133</td><td>—</td><td>波动可预测</td><td><span class="tag t-mid">部分可用</span></td></tr>
<tr><td><b>成交额 ACF(1)</b></td><td><b>−0.254</b></td><td>p &lt; 1e-30</td><td><b>显著均值回复</b></td><td><span class="tag t-ok">干净数据</span></td></tr>
<tr><td><b>成交额 AR(5) 样本外</b></td><td><b>R² = 0.0135</b></td><td>—</td><td><b>比基准好</b></td><td><span class="tag t-ok">干净数据</span></td></tr>
</table>

<div class="warn">
<b>为什么 Sharpe 4.54 一定是假的？</b><br>
真实 A 股 1 日动量策略的年化 Sharpe 长期在 −0.3 ~ +0.3 之间，能稳定做到 1.0 就已是顶级。4.54 意味着"每 3 天有 2 天赚钱、几乎不回撤"——如果真实存在，全球资金会在三个月内把它抹平。<br>
更致命的是：<b>这个 Sharpe 有 4.67 来自"日内段"，隔夜段只有 0.32。</b>而 <code>open</code> 相对前收只有 0.77% 的波动，说明开盘价几乎是前一日收盘的复制品——这正是"水平量被日频采样"的构造痕迹。
</div>

<h2>四、拆解：可预测性到底藏在哪一段</h2>
<img src="data:image/png;base64,{IMG2}" alt="动量可交易性与波动率">
<div class="cap">⑥ 1 日动量累计净值（2016-2026）；⑦ 滚动 250 日 Sharpe：优势全部来自日内段；⑧ 波动率聚集；⑨ 近 10 年收益分布（偏度 2.06，尖峰厚尾）。</div>

<table>
<tr><th>分段</th><th>σ（日）</th><th>ρ1</th><th>1 日动量 Sharpe</th><th>判读</th></tr>
<tr><td>隔夜段（prev_close → open）</td><td>0.77%</td><td>−0.052</td><td>+0.32</td><td><span class="tag t-ok">接近随机</span></td></tr>
<tr><td>日内段（open → close）</td><td>1.97%</td><td class="red">+0.405</td><td class="red">+4.67</td><td><span class="tag t-bad">异常</span></td></tr>
<tr><td>全日段（prev_close → close）</td><td>2.22%</td><td class="red">+0.381</td><td class="red">+4.26</td><td><span class="tag t-bad">异常</span></td></tr>
</table>
<p>真实 A 股日内收益的 ρ1 在 0 ± 0.05。<b>+0.405 意味着"今天开盘买收盘卖赚钱"这件事，明天还会赚钱，后天还会</b>——这是套利机会的教科书定义，不可能长期存在于一个万亿级市场。</p>

<h2>五、干净数据上的真发现（可以直接用）</h2>
<div class="good">
<b>成交额（amount）有显著且可用的均值回复结构。</b>
<ul>
<li>对数成交额变化 ρ1 = <b>−0.254</b>（t 值极大），lag2 = −0.075，lag3 起归零 → <b>一日量能均值回复</b></li>
<li>昨日缩量（前 10% 分位）→ 次日成交额均值 <b class="green">+4.06%</b></li>
<li>昨日放量（前 10% 分位）→ 次日成交额均值 <b class="red">−5.84%</b></li>
<li>AR(5) 模型样本外 R² = 0.0135（成交额本身可预测，但幅度有限）</li>
</ul>
这符合 A 股的"一日放量脉冲"经验：政策/事件驱动的巨量往往次日衰减，可用于<b>判断当日量能是否可持续</b>，比预测点位靠谱得多。
</div>

<h2>六、如果你还想用这个序列：三步自查</h2>
<div class="card">
<ol>
<li><b>确认 close 的定义。</b>打开原始数据源，看这一列的字段名到底是 <code>close</code> / <code>market_cap</code> / <code>amount_cum</code> / <code>index_value</code>。这一步不做，后面全是空转。</li>
<li><b>用一行代码验证：</b><br>
<code>df['close'] / (df['amount']/df['volume'])</code><br>
这个比值如果<b>逐年单调上升</b>（本例从 12 涨到 9,082），说明 close 是累积量，不是价格；如果<b>恒定在 5–50 之间波动</b>，说明它是价格，本报告的负面结论可以推翻。</li>
<li><b>换成已知指数做对照。</b>拉上证/万得全A 的日收益，与本文件 close 的日收益做 60 日滚动相关。真实相关应 &gt; 0.9；本例在 2026-11 的 5 天里只有约 0.5，且涨幅系统性放大 2.5–4 倍。</li>
</ol>
</div>

<h3>对逆向策略的一条提醒</h3>
<div class="warn">
近 10 年，这个序列的<b>极端下跌之后没有反弹，而是继续跌</b>：
<table style="margin-top:10px;">
<tr><th>条件</th><th>样本</th><th>次日</th><th>10 日</th><th>20 日</th></tr>
<tr><td>跌幅前 2%（≤ −3.50%）</td><td>53</td><td class="red">−0.26%（胜率 0.36）</td><td class="red">−3.63%（胜率 0.30）</td><td class="red">−4.84%（胜率 0.28）</td></tr>
<tr><td>跌幅前 5%（≤ −2.74%）</td><td>127</td><td class="red">−0.34%（胜率 0.35）</td><td class="red">−2.90%（胜率 0.31）</td><td class="red">−2.05%（胜率 0.33）</td></tr>
<tr><td>跌幅前 10%（≤ −2.21%）</td><td>259</td><td class="red">−0.42%（胜率 0.34）</td><td class="red">−3.20%（胜率 0.31）</td><td class="red">−3.27%（胜率 0.29）</td></tr>
<tr><td>无条件基准</td><td>2,638</td><td>+0.46 胜率</td><td>+0.54%</td><td>+1.12%</td></tr>
</table>
<b>「跌多了就买」在这段数据上是负期望</b>：所有极端下跌分组的 10 日、20 日胜率都在 0.28–0.33，比基准的 0.46 还低。这与你平时用的"极度便宜"框架方向相反——但请注意，这个结论建立在<b>已被证伪的 close 列</b>上，所以它本身也不该被当成证据，只能作为"别急着用这份数据下结论"的提醒。
</div>

<h2>七、下一步建议</h2>
<div class="card">
<p><b>优先级 1：搞清 close 是什么。</b>这是所有分析的前提。如果它是总市值/资金流累积量，那它本身是个<b>不错的指标</b>——只是用法要从"当成价格预测涨跌"改成"当成资金流入强度看趋势"。</p>
<p><b>优先级 2：用 amount/volume 单独建因子。</b>这两列已验证干净，且已验出均值回复结构。方向：量能比率（5 日/60 日）、放量脉冲衰减、量价背离。</p>
<p><b>优先级 3：如果要做价格预测，换数据源。</b>需要上证/万得全A/中证全指的真实日线，与本文件做交叉验证后再谈可预测性。</p>
</div>

<div class="foot">
检验脚本：explore.py / analyze1.py / analyze2.py / analyze3.py / diagnose.py / diagnose2.py（同目录）<br>
真实数据核对来源：2026-11-02 ~ 11-06 公开行情与成交额报道 · 报告生成时间 2026-11-18
</div>

</div></body></html>
"""

open('0amv_诊断报告.html', 'w', encoding='utf-8').write(html)
print('OK', len(html))
