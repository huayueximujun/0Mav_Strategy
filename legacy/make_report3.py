# -*- coding: utf-8 -*-
import base64
IMG = base64.b64encode(open('rule_result.png','rb').read()).decode()

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>大哥规则验证：AMV +4% 入场 / -2.3% 出场</title>
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
.kpi .val{{font-size:21px;font-weight:700;margin:5px 0 2px;letter-spacing:-.5px}}
.kpi .note{{font-size:11.5px;color:#8b95a3}}
.red{{color:#c0392b}}.green{{color:#1e8449}}.blue{{color:#2471a3}}.amber{{color:#b9770e}}
.card{{background:#fff;border:1px solid #e3e7ee;border-radius:12px;padding:20px 22px;margin:16px 0}}
.verdict{{background:linear-gradient(135deg,#fdf3f2,#fbe9e7);border:1px solid #f0c4bd;border-radius:12px;padding:20px 24px;margin:20px 0}}
.verdict ol{{margin:8px 0 0;padding-left:22px}}.verdict li{{margin:9px 0}}
table{{width:100%;border-collapse:collapse;margin:14px 0;font-size:13px;background:#fff}}
th{{background:#eef1f6;text-align:left;padding:9px 11px;font-weight:600;border-bottom:2px solid #dde3ec;font-size:12.5px;white-space:nowrap}}
td{{padding:8px 11px;border-bottom:1px solid #eef1f5}}
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
  <h1>大哥规则验证：AMV 单日 +4% 入场 / 单日 −2.3% 出场</h1>
  <div class="sub">上证 1993-2026（8,244 日）· 创业板 2010-2026（3,995 日）· T 日收盘出信号、T+1 收盘执行、含 2bp 双边成本</div>
</header>

<div class="verdict">
  <strong style="font-size:16px;">一句话结论</strong>
  <ol>
    <li><b>入场那半句是对的，而且相当好。</b>AMV 单日 ≥+4% 之后，上证未来 20 日平均 <b class="green">+2.13%</b>、上涨概率 <b class="green">65%</b>（同期基准只有 +0.26%）。这个信号确实能抓到"资金异动启动"。</li>
    <li><b>出场那半句是错的，而且错得很稳定。</b>AMV 单日 ≤−2.3% 之后，上证未来 20 日平均 <b class="red">+0.69%</b>、创业板 <b class="red">+1.15%</b>——都比基准好。<b>你是在最该买的时候卖。</b></li>
    <li><b>把出场改成"持有 15–20 天 + 价格止损 −3~5%"，收益翻 3–8 倍，回撤还更低。</b>上证近 10 年：年化 <b class="green">2.25% → 8.0%</b>（Sharpe 0.27 → 0.86，回撤 −16.1% → −11%）；创业板：<b class="green">2.27% → 18.9%</b>（Sharpe 0.21 → 1.18）。</li>
  </ol>
</div>

<div class="kpis">
  <div class="kpi"><div class="lab">大哥规则 · 上证全样本</div><div class="val blue">8.61%</div><div class="note">年化 · Sharpe 0.53 · 回撤 −37.6%</div></div>
  <div class="kpi"><div class="lab">买入持有 · 同区间</div><div class="val red">4.68%</div><div class="note">年化 · Sharpe 0.30 · 回撤 −78.3%</div></div>
  <div class="kpi"><div class="lab">改进版 · 上证近10年</div><div class="val green">8.0%</div><div class="note">Sharpe 0.86 · 回撤 −11%</div></div>
  <div class="kpi"><div class="lab">改进版 · 创业板近10年</div><div class="val green">18.9%</div><div class="note">Sharpe 1.18 · 回撤 −21%</div></div>
</div>

<h2>一、规则原样跑：能赚钱，但主要赚的是"控回撤"</h2>
<table>
<tr><th>区间</th><th>笔数</th><th>胜率</th><th>平均单笔</th><th>平均持仓</th><th>年化</th><th>Sharpe</th><th>最大回撤</th></tr>
<tr><td colspan="8" style="background:#f7f9fc;font-weight:600;">上证指数</td></tr>
<tr><td>1993–2026 全样本</td><td>259</td><td>44.8%</td><td>+1.50%</td><td>12.1 天</td><td>8.61%</td><td>0.53</td><td>−37.6%</td></tr>
<tr><td>1993–2005</td><td>132</td><td>44.7%</td><td>+1.62%</td><td>9.0 天</td><td>13.14%</td><td>—</td><td>—</td></tr>
<tr><td>2006–2015</td><td>74</td><td>43.2%</td><td>+1.83%</td><td>13.2 天</td><td>12.50%</td><td>—</td><td>—</td></tr>
<tr><td><b>2016–2026</b></td><td>51</td><td>51.0%</td><td><b class="red">+0.59%</b></td><td>18.5 天</td><td><b class="red">2.25%</b></td><td>0.27</td><td>−16.1%</td></tr>
<tr><td colspan="8" style="background:#f7f9fc;font-weight:600;">创业板指</td></tr>
<tr><td>2011–2026</td><td>83</td><td>42.2%</td><td>+1.47%</td><td>16.7 天</td><td>3.36%</td><td>0.27</td><td>−43.9%</td></tr>
<tr><td><b>2016–2026</b></td><td>51</td><td>43.1%</td><td>+1.28%</td><td>18.5 天</td><td><b class="red">2.27%</b></td><td>0.21</td><td>−43.9%</td></tr>
</table>

<p>把大哥的原话直接跑，两个事实跳出来：</p>
<ul>
<li><b>中位数是负的。</b>上证全样本单笔收益中位数 <b>−0.41%</b>、创业板 <b>−0.67%</b>。<b>超过一半的交易是亏钱的</b>，全靠少数大赚的单子把平均值拉正。这种"低胜率高赔率"的结构很考验心态。</li>
<li><b>全样本年化 8.61% vs 买入持有 4.68%，但回撤从 −78% 压到 −38%。</b>这才是它的真实价值——<b>它是一套风控系统，不是一套进攻系统</b>。而且这套风控在 2015 年股灾、2008 年熊市里确实救了命。</li>
</ul>

<div class="warn">
<b>但近 10 年退化了：</b>年化只剩 2.25%，平均单笔 +0.59%。1993–2015 能做到 12–13%，2016 年后掉到 2%。原因见第四节——<b>不是大哥记错了，是这个阈值在今天的波动环境里已经"太严"了</b>。
</div>

<h2>二、拆开看：入场是对的，出场是反的</h2>

<h3>入场信号（AMV ≥ +4%）之后发生了什么</h3>
<table>
<tr><th>区间</th><th>信号数</th><th>1 日</th><th>5 日</th><th>10 日</th><th>20 日</th><th>60 日</th><th>基准（20日）</th></tr>
<tr><td>上证 1993–2026</td><td>760</td><td>+0.33%</td><td>+1.30%</td><td>+1.74%</td><td>+2.47%</td><td>+2.32%</td><td>+0.71%</td></tr>
<tr><td><b>上证 2016–2026</b></td><td>121</td><td>+0.43%<br><span style="font-size:11px;color:#7b8695">胜 62%</span></td><td>+1.01%<br><span style="font-size:11px;color:#7b8695">胜 62%</span></td><td>+1.23%<br><span style="font-size:11px;color:#7b8695">胜 66%</span></td><td><b class="green">+2.13%</b><br><span style="font-size:11px;color:#7b8695">胜 65%</span></td><td>+1.10%</td><td>+0.26%</td></tr>
<tr><td><b>创业板 2016–2026</b></td><td>121</td><td>+0.63%</td><td>+2.00%</td><td>+2.26%</td><td><b class="green">+4.20%</b><br><span style="font-size:11px;color:#7b8695">胜 63%</span></td><td>+2.10%</td><td>+0.47%</td></tr>
</table>
<p><b>入场信号的质量很高。</b>近 10 年上证 20 日 +2.13% 对基准 +0.26%，超额接近 2 个点，胜率 65%。创业板更猛，20 日 +4.20%。<b>而且这个 alpha 在 10–20 日维度最强，60 日就衰减掉了</b>——这直接决定了正确的持有期应该是 2–4 周，不是"一直拿到出场信号"。</p>

<h3>出场信号（AMV ≤ −2.3%）之后发生了什么</h3>
<table>
<tr><th>指数 / 区间</th><th>信号数</th><th>1 日</th><th>5 日</th><th>10 日</th><th>20 日</th></tr>
<tr><td>上证 1993–2026</td><td>1,624</td><td>−0.04%</td><td>+0.01%</td><td>+0.15%</td><td>+0.24%</td></tr>
<tr><td><b>上证 2016–2026</b></td><td>242</td><td class="red">+0.24%</td><td class="red">+0.64%</td><td class="red">+0.52%</td><td class="red">+0.69%</td></tr>
<tr><td>创业板 1993–2026</td><td>463</td><td>+0.17%</td><td>+0.82%</td><td>+0.89%</td><td>+1.17%</td></tr>
<tr><td><b>创业板 2016–2026</b></td><td>242</td><td class="red">+0.52%</td><td class="red">+1.09%</td><td class="red">+0.95%</td><td class="red">+1.15%</td></tr>
</table>

<div class="good">
<b>这是整份报告最关键的一张表。</b>AMV 单日暴跌 2.3% 之后，指数不但没继续跌，<b>未来 20 日平均还涨 0.69%（上证）/ 1.15%（创业板）</b>，全部高于同期基准。<br>
换句话说：<b>"AMV 跌 2.3% 就跑"这个动作，系统性地卖在了洗盘的低点上。</b>它把本来 20 日 +2.13% 的仓位，硬生生截成 +0.59%。
</div>

<h2>三、改进版：只改出场，收益翻 3–8 倍</h2>
<img src="data:image/png;base64,{IMG}" alt="大哥规则 vs 改进版">
<div class="cap">① 上证近10年净值；② 创业板近10年净值；③ 参数网格（越绿越好，成片分布说明不是过拟合）；④ 同一个 4% 在不同年代的"标准差倍数"。</div>

<table>
<tr><th>方案（近 10 年 2016–2026）</th><th>上证 年化/Sharpe/回撤</th><th>创业板 年化/Sharpe/回撤</th></tr>
<tr><td>买入持有</td><td>0.94% / 0.14 / −30.8%</td><td>−0.25% / 0.14 / −57.1%</td></tr>
<tr><td><b>大哥规则</b> 4% 进 / −2.3% 出</td><td>2.25% / 0.27 / −16.1%</td><td>2.27% / 0.21 / −43.9%</td></tr>
<tr><td>4% 进 / 持 10 天 / 无止损</td><td>5.99% / 0.67 / −11.5%</td><td>13.6% / 0.98 / −23%</td></tr>
<tr><td>4% 进 / 持 20 天 / 无止损</td><td>8.24% / 0.82 / −13.5%</td><td>11.61% / 0.68 / −36.1%</td></tr>
<tr><td><b>4% 进 / 持 20 天 / 止损 −3%</b></td><td><b class="green">8.0% / 0.86 / −11%</b></td><td><b class="green">18.9% / 1.18 / −21%</b></td></tr>
<tr><td>4% 进 / 持 20 天 / 止损 −5%</td><td>7.75% / 0.80 / −14.0%</td><td>15.2% / 0.92 / −31%</td></tr>
<tr><td>4% 进 / 持 30 天 / 止损 −3%</td><td>10.2% / 1.00 / −10%</td><td>14.0% / 0.84 / −21%</td></tr>
</table>

<p>全样本（1993–2026）上证：<b>4% 进 / 持 20 天 / 止损 −5% → 年化 18.43%、Sharpe 0.91、回撤 −33.9%</b>（买入持有 4.68%/0.30/−78.3%）。</p>

<h3>为什么这个改动有效</h3>
<p>因为它把"出场"从<b>指标信号</b>换成了<b>两件不相关的事</b>：</p>
<ul>
<li><b>时间窗口（15–20 天）</b>：入场 alpha 的衰减曲线显示，超额在 10–20 日最强、60 日归零。那就拿 20 天，别贪。</li>
<li><b>价格止损（−3~5%）</b>：真正的风险是"看错了还硬扛"，用持仓浮亏兜底，而不是用 AMV 的日内波动兜底。</li>
</ul>
<p><b>关键洞察：AMV 单日跌 2.3%，跟你手上这笔仓位亏没亏，是两件不同步的事。</b>指数可能已经涨了 5% 才回吐，AMV 才刚跌破 −2.3%；也可能指数横盘、AMV 因为结构切换而大跌。用前者当出场条件，等于用别人的体温计决定自己要不要吃药。</p>

<h2>四、4% 这个数字正在过期</h2>
<table>
<tr><th>年代</th><th>AMV 日波动（σ）</th><th>4% 相当于</th><th>触发频率</th></tr>
<tr><td>1995–1999</td><td>7.39%</td><td>0.5 σ</td><td>14.7%</td></tr>
<tr><td>2000–2004</td><td>4.19%</td><td>1.0 σ</td><td>9.3%</td></tr>
<tr><td>2005–2009</td><td>3.43%</td><td>1.2 σ</td><td>10.7%</td></tr>
<tr><td>2010–2014</td><td>2.49%</td><td>1.6 σ</td><td>6.5%</td></tr>
<tr><td>2015–2019</td><td>2.39%</td><td>1.7 σ</td><td>5.6%</td></tr>
<tr><td>2020–2024</td><td>2.28%</td><td>1.8 σ</td><td>4.6%</td></tr>
<tr><td><b>2025–2029</b></td><td><b>2.10%</b></td><td><b>1.9 σ</b></td><td><b>4.4%</b></td></tr>
</table>
<p>大哥当年说 4% 的时候，那是"每天都能见到的普通放量"；今天 4% 已经是"一年只有 11 次的极端事件"。<b>同一个数字，含义完全变了。</b>所以他这条规则在 1993–2015 能做出 12–13% 的年化，2016 年后只剩 2%。</p>
<p>要修的话，把固定 4% 换成 <b>"1.5–1.8 倍 60 日滚动标准差"</b>——但实测下来，改阈值带来的提升远不如改出场。所以如果只改一处，<b>先改出场</b>。</p>

<h2>五、给你的落地版本</h2>
<div class="card">
<p><b>入场（保留大哥的逻辑，改成自适应）：</b></p>
<ul>
<li>AMV 单日涨幅 <b>≥ +4%</b>，或 ≥ <b>1.5 倍 60 日滚动 σ</b>（两者取其一，历史上等价，看哪个方便）</li>
<li>T 日收盘确认，<b>T+1 收盘买入</b>（不要当天追）</li>
</ul>
<p><b>持仓（关键改动）：</b></p>
<ul>
<li><b>持满 20 个交易日</b>，到期无条件卖出；<b>不要</b>用 AMV 单日 −2.3% 出场</li>
<li>中途触发 <b>−3% ~ −5% 的持仓浮亏</b>就止损（这是唯一该用的提前出场条件）</li>
</ul>
<p><b>标的选择：</b></p>
<ul>
<li>上证/沪深300：改进版年化 8%、Sharpe 0.86、回撤 −11%，适合做底仓择时</li>
<li>创业板/科创：改进版年化 18.9%、Sharpe 1.18，但回撤 −21%，适合小仓位</li>
<li><b>创业板对这套规则的弹性明显更大</b>——AMV 异动时创业板的爆发力强，20 天能吃到 4% 以上的均值</li>
</ul>
</div>

<div class="warn">
<b>必须打折听的四件事：</b>
<ol>
<li><b>参数是我从网格里挑的，有过拟合风险。</b>不过图③的网格是<b>成片</b>的（持有 5–30 天 × 止损 3%–无，近 10 年上证每一格 Sharpe 都在 0.44–1.04，全部好于买入持有 0.14），不是孤立尖峰，所以框架本身应该站得住，但别迷信"20 天 + 止损 3%"这组精确数字。</li>
<li><b>样本短。</b>近 10 年只有 46–59 笔交易，统计上不够。全样本 259 笔更可靠，但早期市场结构完全不同。</li>
<li><b>成本算得乐观。</b>我按 2bp 双边算，实际 ETF 申赎+冲击成本约 3–8bp。若按 8bp，年化会掉 1–2 个点，排名不变。</li>
<li><b>AMV 是收盘后计算的全市场指标。</b>实盘只能 T 日尾盘估算，或 T+1 才知道准确值。我全程用 T+1 收盘执行，已经比较保守，但如果你的券商行情里 AMV 有延迟，还要再打折。</li>
</ol>
</div>

<h2>六、怎么回大哥</h2>
<div class="card" style="border-left:4px solid #2471a3;">
<p><b>可以这么说：</b>"你这个入场点抓得准，AMV 单日涨 4% 之后 20 天平均能涨 2 个多点、胜率 65%，确实有东西。但出场那半句可以再优化——AMV 单日跌 2.3% 之后，大盘 20 天平均还涨 0.7%，等于卖早了。要不要试试进场后固定拿 20 天、跌 3% 止损？回测下来年化从 2.3% 提到 8%，回撤还小一点。"</p>
</div>

<div class="foot">
脚本：rule_test.py / rule_decompose.py / rule_full.py / plot_rule.py（同目录）<br>
数据：AMV 日线（用户提供）· 上证 / 创业板日线（新浪财经）· 生成 2026-11-18
</div>

</div></body></html>"""

open('大哥规则验证.html','w',encoding='utf-8').write(html)
print('OK', len(html))
