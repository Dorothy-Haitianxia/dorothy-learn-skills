# -*- coding: utf-8 -*-
"""把 assets/src 的设计与交互层合成 skill 模板（内容换成占位骨架）。

样式与交互层的唯一源是 assets/src/style.css 与 assets/src/app.js —— 它们住在 skill 里，
所以本脚本不依赖仓库外的任何目录（clone 到任何地方都能跑）。
"""
import pathlib

SKILL = pathlib.Path(__file__).resolve().parents[1]   # skills/dorothy-html
SRC = SKILL / "assets" / "src"

CSS = (SRC / "style.css").read_text(encoding="utf-8")
JS = (SRC / "app.js").read_text(encoding="utf-8")

MAP_SVG = '''<svg id="mapSvg" viewBox="0 0 1200 620" preserveAspectRatio="xMidYMid meet" role="img" aria-label="本章知识点关系图">
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9" fill="none" class="f-arrowline"/></marker></defs>
<g id="mapView">
<g class="edge" data-from="c1" data-to="t1" data-span="1"><path class="edge__line" d="M420,140 C520,140 520,140 620,140" pathLength="1" marker-end="url(#arrow)" style="--i:0"/><text class="edge__label" x="0" y="0"><textPath href="#tp0" startOffset="50%" text-anchor="middle">前提</textPath></text><path id="tp0" d="M420,140 C520,140 520,140 620,140" fill="none" stroke="none"/></g>
<g class="edge edge--far" data-from="c1" data-to="e1" data-span="2"><path class="edge__line" d="M420,140 C620,140 620,300 820,300" pathLength="1" marker-end="url(#arrow)" style="--i:1"/><text class="edge__label" x="0" y="0"><textPath href="#tp1" startOffset="50%" text-anchor="middle">应用</textPath></text><path id="tp1" d="M420,140 C620,140 620,300 820,300" fill="none" stroke="none"/></g>
<text class="map__col" x="90" y="86">概念 / DEFINITIONS</text><line class="map__rule" x1="90" y1="104" x2="420" y2="104"/>
<text class="map__col" x="620" y="86">定理与命题 / THEOREMS</text><line class="map__rule" x1="620" y1="104" x2="950" y2="104"/>
<text class="map__col" x="90" y="246">例题 / EXAMPLES</text><line class="map__rule" x1="90" y1="264" x2="420" y2="264"/>
<g class="node node--concept" data-id="c1" transform="translate(90,120)" style="--x:90px;--y:120px" tabindex="0" role="link" aria-label="概念名（点击查看知识卡）"><title>概念名（点击查看知识卡）</title><rect class="node__box" width="330" height="78"/><rect class="node__bar" width="6" height="78"/><text class="node__code" x="22" y="34">DEF</text><text class="node__title" x="22" y="60">概念名</text></g>
<g class="node node--theorem" data-id="t1" transform="translate(620,120)" style="--x:620px;--y:120px" tabindex="0" role="link" aria-label="定理名（点击查看知识卡）"><title>定理名（点击查看知识卡）</title><rect class="node__box" width="330" height="78"/><rect class="node__bar" width="6" height="78"/><text class="node__code" x="22" y="34">THM</text><text class="node__title" x="22" y="60">定理名</text></g>
<g class="node node--example" data-id="e1" transform="translate(90,280)" style="--x:90px;--y:280px" tabindex="0" role="link" aria-label="例题名（点击查看知识卡）"><title>例题名（点击查看知识卡）</title><rect class="node__box" width="330" height="78"/><rect class="node__bar" width="6" height="78"/><text class="node__code" x="22" y="34">EX</text><text class="node__title" x="22" y="60">例题名</text></g>
</g></svg>'''

MINI_SVG = '''<svg id="miniSvg" viewBox="0 0 1200 620" preserveAspectRatio="xMidYMid meet">
<path class="mini__edge" d="M420,140 C520,140 520,140 620,140"/><path class="mini__edge" d="M420,140 C620,140 620,300 820,300"/>
<rect class="mini__node" x="90" y="120" width="330" height="78"/><rect class="mini__node" x="620" y="120" width="330" height="78"/><rect class="mini__node" x="90" y="280" width="330" height="78"/>
<rect id="miniView" x="0" y="0" width="1200" height="620"/></svg>'''

CARD = '''          <article class="card" id="{cid}">
            <div class="card__head">
              <p class="tag"><span>{code}</span><span class="tag__cn">{cn}</span></p>
              <h3 class="card__title">{title}</h3>
            </div>
            <p class="card__summary">{summary}</p>
            <!-- 学习问题：必须上到卡头，读者在收起状态就要知道"这张卡为什么存在" -->
            <p class="tk-q"><b>学习问题</b>为什么这个概念非要单独定义一次？（教学稿「学习问题」原句）</p>
            <button class="toggle" type="button" aria-expanded="false" aria-controls="{cid}-body"
                    data-open-label="收起{open_tx}" data-close-label="展开{open_tx}">
              <span class="toggle__tx">展开{open_tx}</span><span class="toggle__ico" aria-hidden="true">+</span>
            </button>
            <div class="panel" id="{cid}-body" hidden>
              <div class="panel__inner prose">
                <!-- 教学层四块，顺序固定：直觉 → 前置回放 → 教材原文 → 理解检查。
                     内容全部来自教学稿，缺哪块就删哪块，不要在这里临时编。 -->
                <div class="tk-note"><span class="tk-label">直觉</span><p>把这个概念"想成什么"的一句话（教学稿「直觉」原句）。</p></div>
                <details class="is-recall">
                  <summary>回放 · 1 处：前置概念名</summary>
                  <div class="tk-recall"><b>前置概念名</b><p>一句话把它拉回来（教学稿「前置回放」原句）。</p></div>
                </details>
                <div class="tk-src"><p class="tk-src-label">教材原文</p>
                  <div class="tk-src-body"><p>{body}</p></div>
                </div>
                <p class="is-added">导师增补的一句：只用这条极浅左线区分，正文里不写「补」字样，文末也不做清单。</p>
                <div class="fig__check tk-check"><b>理解检查</b>检验是否真懂的一个小问题？
                  <details class="tk-ans"><summary>看答案</summary><p>答案（教学稿「检查」的答案原句）。</p></details>
                </div>
                <p class="card__src">出处：正文 §X.Y</p>
              </div>
            </div>
          </article>'''


# ---------------------------------------------------------------- 双主题（运行时切换）
DECOR = """  <!-- ========================================================================
       双主题装饰件（主题 = NASA-punk 时才渲染；孤星下 .np-chrome{display:none} 不占排布）
       四色身份条 / 黑白警示斜纹 / 接缝铆钉 / 角螺丝 / 使用痕迹：全部 aria-hidden、无文本
       --i 是 34ms 级联入场的序号
       ======================================================================== -->
  <div class="np-chrome" aria-hidden="true">
    <div class="np-stripe" style="--i:0"><i></i><i></i><i></i><i></i></div>
    <div class="np-hazard" style="--i:1"></div>
    <div class="np-rivet" style="--i:2"></div>
    <span class="np-rivet np-rivet--vert np-rivet--left" style="--i:3"></span>
    <span class="np-rivet np-rivet--vert np-rivet--right" style="--i:4"></span>
    <svg class="np-screw np-screw--tl" viewBox="0 0 14 14" aria-hidden="true" style="--i:5"><circle class="np-screw__body" cx="7" cy="7" r="6.2" stroke-width="1"/><line class="np-screw__slot" x1="3.2" y1="7" x2="10.8" y2="7"/></svg>
    <svg class="np-screw np-screw--tr" viewBox="0 0 14 14" aria-hidden="true" style="--i:6"><circle class="np-screw__body" cx="7" cy="7" r="6.2" stroke-width="1"/><line class="np-screw__slot" x1="3.2" y1="7" x2="10.8" y2="7"/></svg>
    <svg class="np-screw np-screw--bl" viewBox="0 0 14 14" aria-hidden="true" style="--i:7"><circle class="np-screw__body" cx="7" cy="7" r="6.2" stroke-width="1"/><line class="np-screw__slot" x1="3.2" y1="7" x2="10.8" y2="7"/></svg>
    <svg class="np-screw np-screw--br" viewBox="0 0 14 14" aria-hidden="true" style="--i:8"><circle class="np-screw__body" cx="7" cy="7" r="6.2" stroke-width="1"/><line class="np-screw__slot" x1="3.2" y1="7" x2="10.8" y2="7"/></svg>
    <div class="np-wear" style="--i:9">
      <span class="np-scratch np-scratch--dark" style="left:8%;top:19%;width:96px;transform:rotate(-1.4deg)"></span>
      <span class="np-scratch np-scratch--light" style="left:9%;top:21%;width:70px;transform:rotate(-1.4deg)"></span>
      <span class="np-scratch np-scratch--dark" style="left:72%;top:44%;width:130px;transform:rotate(.9deg)"></span>
      <span class="np-scratch np-scratch--light" style="left:31%;top:78%;width:110px;transform:rotate(-.6deg)"></span>
      <span class="np-scratch np-scratch--dark" style="left:46%;top:62%;width:64px;transform:rotate(2.1deg)"></span>
      <span class="np-scuff" style="left:62%;top:12%;width:170px;height:26px;transform:rotate(-8deg)"></span>
      <span class="np-scuff" style="left:14%;top:66%;width:120px;height:20px;transform:rotate(5deg)"></span>
    </div>
  </div>"""

TOOLS = """    <div class="chrome__tools">
      <div class="search" data-search role="search">
        <span class="search__lab mono" aria-hidden="true">FIND</span>
        <input class="search__in" id="searchIn" type="search" role="combobox" placeholder="搜索核心概念"
               aria-label="搜索核心概念" aria-expanded="false" aria-controls="searchHits" aria-autocomplete="list"
               autocomplete="off" spellcheck="false">
        <ul class="hits" id="searchHits" role="listbox" aria-label="搜索结果"></ul>
      </div>
      <div class="theme" role="group" aria-label="视觉主题">
        <span class="theme__lab mono" aria-hidden="true">THEME</span>
        <button class="theme__opt" type="button" data-theme-set="lonetrail" aria-pressed="true">孤星</button>
        <button class="theme__opt" type="button" data-theme-set="nasapunk" aria-pressed="false">NASA</button>
        <span class="theme__read mono" id="themeRead" aria-hidden="true">LONE</span>
        <span class="theme__bar" aria-hidden="true"><span class="theme__fill" id="themeFill"></span></span>
      </div>
      <p class="chrome__count mono"><span id="pageNow">01</span> / <span id="pageAll">05</span></p>
    </div>
"""

THEME_BOOT = """<script>
/* 主题记忆：在任何绘制之前落定，避免首屏先闪一下默认主题；
   localStorage 不可用（file:// 受限、隐私模式）时保持默认孤星。 */
(function(){try{var t=window.localStorage.getItem('dorothy:theme');
if(t==='nasapunk'||t==='lonetrail'){document.documentElement.setAttribute('data-theme',t);}}catch(e){}})();
</script>"""

BODY = f'''<body>
<div class="deck" id="deck">
{DECOR}

  <header class="chrome">
    <p class="chrome__id mono">CHXX / <b>章节名</b></p>
    <nav class="chrome__nav" aria-label="页面导航">
      <button class="navlink" type="button" data-goto="p-overview"><span class="navlink__tx">章节概览</span></button>
      <button class="navlink" type="button" data-goto="p-map"><span class="navlink__tx">知识地图</span></button>
      <button class="navlink" type="button" data-goto="p-core"><span class="navlink__tx">核心概念</span></button>
      <button class="navlink" type="button" data-goto="p-pitfalls"><span class="navlink__tx">易错点</span></button>
      <button class="navlink" type="button" data-goto="p-quiz"><span class="navlink__tx">自测与习题</span></button>
    </nav>
{TOOLS}
  </header>

  <main class="pages" id="pages">

    <!-- ============ 1. 章节概览 ============ -->
    <section class="page" id="p-overview" data-title="章节概览" data-en="OVERVIEW">
      <div class="page__inner">
        <section class="meta" aria-label="章节元信息">
          <div class="meta__row">
            <h1 class="meta__chapter"><span class="mono">CHXX</span>章节名</h1>
            <dl class="meta__stats">
              <div><dt>知识点</dt><dd>00</dd></div>
              <div><dt>定义 · 定理</dt><dd>00 / 00</dd></div>
              <div><dt>预计复习</dt><dd>00 min</dd></div>
            </dl>
          </div>
          <div class="meta__key">
            <span class="key-mark">关键结论</span>
            <p>用一句话写出本章最重要的结论（取自正文，不自行概括出材料里没有的判断）。</p>
          </div>
        </section>

        <section class="section" aria-labelledby="path-title">
          <div class="section__head">
            <h2 class="bar" id="path-title"><span class="bar__sq" aria-hidden="true"></span><span class="bar__tx">阅读路径</span></h2>
            <span class="bar__en">READING PATH</span>
            <span class="section__note">按 ← → 或点下方按钮翻页</span>
          </div>
          <ul class="path">
            <li><button class="jump" type="button" data-goto="p-map"><span class="jump__no">01</span><span class="jump__tx">知识地图</span><span class="jump__en">MAP</span></button></li>
            <li><button class="jump" type="button" data-goto="p-core"><span class="jump__no">02</span><span class="jump__tx">核心概念</span><span class="jump__en">CORE</span></button></li>
            <li><button class="jump" type="button" data-goto="p-pitfalls"><span class="jump__no">03</span><span class="jump__tx">易错点</span><span class="jump__en">PITFALLS</span></button></li>
            <li><button class="jump" type="button" data-goto="p-quiz"><span class="jump__no">04</span><span class="jump__tx">自测与习题</span><span class="jump__en">SELF CHECK</span></button></li>
          </ul>
        </section>
      </div>
    </section>

    <!-- ============ 2. 知识地图（可平移缩放，节点与卡片 id 对应） ============ -->
    <section class="page page--map" id="p-map" data-title="知识地图" data-en="KNOWLEDGE MAP">
      <div class="page__inner">
        <div class="mapwrap">
          <div class="map__hint mono">拖拽平移 · 滚轮 / 双击缩放 · 点击节点跳到对应知识卡</div>
          <div class="map__stage">{MAP_SVG}</div>
          <div class="map__mini" style="aspect-ratio:1200 / 620">{MINI_SVG}</div>
          <div class="map__tools">
            <button class="tool" type="button" data-zoom="in" aria-label="放大">+</button>
            <button class="tool" type="button" data-zoom="out" aria-label="缩小">−</button>
            <button class="tool tool--wide" type="button" data-zoom="fit">适配</button>
          </div>
          <div class="map__legend mono">C 概念 · T 定理/命题 · E 例题 · ERR 易错点</div>
        </div>
      </div>
    </section>

    <!-- ============ 3. 核心概念（三板块：定义 / 定理 / 例子；组内互斥展开，橙色术语可点开前置概念） ============ -->
    <section class="page" id="p-core" data-title="核心概念" data-en="CORE CONCEPTS">
      <div class="page__inner">
        <section class="section" id="core" aria-labelledby="core-title">
          <div class="section__head">
            <h2 class="bar" id="core-title"><span class="bar__sq" aria-hidden="true"></span><span class="bar__tx">核心概念</span></h2>
            <span class="bar__en">CORE CONCEPTS</span>
            <span class="section__note">同组内同时只展开一张</span>
            <div class="tabs" role="tablist" aria-label="核心概念分组" data-tabs="core">
              <span class="tabs__ind" aria-hidden="true"></span>
              <button class="tabs__tab" type="button" role="tab" id="tab-def" aria-controls="board-def" aria-selected="true" tabindex="0" data-board="def"><span class="tabs__name">定义</span><span class="tabs__n">00</span></button>
              <button class="tabs__tab" type="button" role="tab" id="tab-thm" aria-controls="board-thm" aria-selected="false" tabindex="-1" data-board="thm"><span class="tabs__name">定理</span><span class="tabs__n">00</span></button>
              <button class="tabs__tab" type="button" role="tab" id="tab-ex" aria-controls="board-ex" aria-selected="false" tabindex="-1" data-board="ex"><span class="tabs__name">例子</span><span class="tabs__n">00</span></button>
            </div>
          </div>

          <div class="board" id="board-def" role="tabpanel" aria-labelledby="tab-def" data-board="def" tabindex="0">
            <div class="stack" data-accordion="core-def">
{CARD.format(cid='c1', code='DEF', cn='定义', title='概念名', summary='一句话摘要：扫读用，写清这个概念解决什么问题。', open_tx='完整定义', body='完整定义（照抄正文表述）。提到前面某个概念时写成 <a href="#c2" class="ref" data-ref="c2">该概念</a>，点击会浮出前置概念速览。')}
{CARD.format(cid='c2', code='DEF', cn='定义', title='后面的概念名', summary='一句话摘要。', open_tx='完整定义', body='完整定义。')}
          </div>
          </div>

          <div class="board" id="board-thm" role="tabpanel" aria-labelledby="tab-thm" data-board="thm" tabindex="0" hidden>
            <div class="stack" data-accordion="core-thm">
          <article class="card" id="t1">
            <div class="card__head">
              <p class="tag"><span>THM</span><span class="tag__cn">定理</span></p>
              <h3 class="card__title">定理名</h3>
            </div>
            <dl class="facts">
              <dt>条件</dt><dd>材料给出的前提条件。</dd>
              <dt>结论</dt><dd>材料给出的结论。</dd>
            </dl>
            <button class="toggle" type="button" aria-expanded="false" aria-controls="t1-body"
                    data-open-label="收起证明思路" data-close-label="展开证明思路">
              <span class="toggle__tx">展开证明思路</span><span class="toggle__ico" aria-hidden="true">+</span>
            </button>
            <div class="panel" id="t1-body" hidden>
              <div class="panel__inner prose">
                <p>证明思路：按材料的步骤写，跳步就标 [待补充]。</p>
                <p class="formula">f(x) = …<span class="formula__no">式 (1)</span></p>
                <p class="key">关键结论：这一步用到的核心判断。</p>
                <p class="card__src">出处：正文 §X.Y 定理 X.Y</p>
              </div>
            </div>
          </article>
          </div>
          </div>

          <div class="board" id="board-ex" role="tabpanel" aria-labelledby="tab-ex" data-board="ex" tabindex="0" hidden>
            <div class="stack" data-accordion="core-ex">
          <article class="card" id="e1">
            <div class="card__head">
              <p class="tag"><span>EX</span><span class="tag__cn">例题</span></p>
              <h3 class="card__title">题目名</h3>
            </div>
            <p class="card__summary">题目：写清已知与所求。</p>
            <button class="toggle" type="button" aria-expanded="false" aria-controls="e1-body"
                    data-open-label="收起解答" data-close-label="展开解答">
              <span class="toggle__tx">展开解答</span><span class="toggle__ico" aria-hidden="true">+</span>
            </button>
            <div class="panel" id="e1-body" hidden>
              <div class="panel__inner prose">
                <ol><li>第一步</li><li>第二步</li></ol>

                <!-- 插图：片段由 dorothy-picture 生成，只挂语义类，配色字体走本页令牌 -->
                <figure class="fig" id="fig-demo">
                  <svg viewBox="0 0 640 200" role="img" aria-label="（图的类型 + 主体 + 变量范围，供读屏；不许以「图片 / 示意图」开头）">
                    <title>（同 aria-label）</title>
                    <line class="f-axis f-fade" x1="60" y1="160" x2="600" y2="160"/>
                    <line class="f-grid f-fade" x1="60" y1="90" x2="600" y2="90"/>
                    <line class="f-hair f-fade" x1="140" y1="160" x2="140" y2="70"/>
                    <line class="f-hair f-hair--acc f-fade" x1="240" y1="160" x2="240" y2="46"/>
                    <line class="f-hair f-fade" x1="340" y1="160" x2="340" y2="96"/>
                    <path class="f-line" d="M140 70 L 240 46 L 340 96 L 440 120 L 540 140" fill="none" pathLength="1" style="animation-delay:.1s"/>
                    <circle class="f-dot f-dot--acc" cx="240" cy="46" r="3.4" style="animation-delay:.5s"/>
                    <text class="t-num t-halo f-fade" x="240" y="34" text-anchor="middle" font-size="12.5">峰值</text>
                    <text class="t-note f-fade" x="320" y="188" text-anchor="middle">ONE HAIRLINE = ONE SLICE · 数据来源写在图注里</text>
                  </svg>
                  <div class="fig__legend"><span><i class="sw sw--ink"></i>主序列</span><span><i class="sw sw--acc"></i>关键点</span></div>
                  <figcaption>图 1 · 一句话说明这张图在讲什么，并给正文出处（正文 §X.Y）</figcaption>
                </figure>

                <p>图 1 中折线是主序列、圆点是关键点；正文在这里逐一点名图中元素，并说明它对应哪条定义或公式（不要只写「如图所示」）。</p>
                <p class="fig__check"><b>检查</b>（一个可判定对错的问题）？（答案：把答案写出来 —— 只提问不给答案不算检查。）</p>
                <p class="card__src">出处：正文 §X.Y 例 X.Y</p>
              </div>
            </div>
          </article>
          </div>
          </div>
        </section>
      </div>
    </section>

    <!-- ============ 4. 易错点 ============ -->
    <section class="page" id="p-pitfalls" data-title="易错点" data-en="COMMON PITFALLS">
      <div class="page__inner">
        <section class="section" id="pitfalls" aria-labelledby="pitfalls-title">
          <div class="section__head">
            <h2 class="bar" id="pitfalls-title"><span class="bar__sq" aria-hidden="true"></span><span class="bar__tx">易错点</span></h2>
            <span class="bar__en">COMMON PITFALLS</span>
            <span class="section__note">错误说法 + 触发场景 → 展开限制条件</span>
          </div>
          <div class="stack" data-accordion="pitfalls">
            <article class="card" id="p1">
              <div class="card__head">
                <p class="tag"><span>ERR</span><span class="tag__cn">易错点</span></p>
                <h3 class="card__title">错误说法（照抄材料里出现过的说法）</h3>
              </div>
              <p class="card__summary">触发场景：什么情况下容易这么想。</p>
              <p class="tk-q"><b>学习问题</b>这个说法错在哪一步？（教学稿「学习问题」原句）</p>
              <button class="toggle" type="button" aria-expanded="false" aria-controls="p1-body"
                      data-open-label="收起限制条件" data-close-label="展开限制条件与正确做法">
                <span class="toggle__tx">展开限制条件与正确做法</span><span class="toggle__ico" aria-hidden="true">+</span>
              </button>
              <div class="panel" id="p1-body" hidden>
                <div class="panel__inner prose">
                  <p><strong>限制条件</strong>：定理或定义成立的前提。</p>
                  <p><strong>正确做法</strong>：材料给出的纠正。</p>
                  <p class="card__src">出处：正文 §X.Y（注 / 特殊情形 / 反例）</p>
                </div>
              </div>
            </article>
          </div>
        </section>
      </div>
    </section>

    <!-- ============ 5. 自测与习题（自测各自独立展开；课本章末习题照抄题目） ============ -->
    <section class="page" id="p-quiz" data-title="自测与习题" data-en="SELF CHECK · EXERCISES">
      <div class="page__inner">
        <section class="section" id="quiz" aria-labelledby="quiz-title">
          <div class="section__head">
            <h2 class="bar" id="quiz-title"><span class="bar__sq" aria-hidden="true"></span><span class="bar__tx">复习自测与习题</span></h2>
            <span class="bar__en">SELF CHECK · EXERCISES</span>
            <span class="section__note">自测答案默认隐藏；课本章末习题只给题目，课本未给解答</span>
            <div class="tabs tabs--two" role="tablist" aria-label="自测与习题分组" data-tabs="quiz">
              <span class="tabs__ind" aria-hidden="true"></span>
              <button class="tabs__tab" type="button" role="tab" id="tab-self" aria-controls="board-self" aria-selected="true" tabindex="0" data-board="self"><span class="tabs__name">自测</span><span class="tabs__n">00</span></button>
              <button class="tabs__tab" type="button" role="tab" id="tab-exercise" aria-controls="board-exercise" aria-selected="false" tabindex="-1" data-board="exercise"><span class="tabs__name">章末习题</span><span class="tabs__n">00</span></button>
            </div>
          </div>
          <div class="board" id="board-self" role="tabpanel" aria-labelledby="tab-self" data-board="self" tabindex="0">
            <div class="stack">
            <article class="quiz" id="q1">
              <p class="quiz__q"><span class="quiz__no">Q1</span>问题（正文关键陈述改写成问句）。</p>
              <button class="toggle" type="button" aria-expanded="false" aria-controls="q1-a"
                      data-open-label="隐藏答案" data-close-label="显示答案">
                <span class="toggle__tx">显示答案</span><span class="toggle__ico" aria-hidden="true">+</span>
              </button>
              <div class="panel" id="q1-a" hidden>
                <div class="panel__inner">
                  <p class="quiz__a">答案要点。</p>
                  <p class="card__src">出处：正文 §X.Y</p>
                </div>
              </div>
            </article>
          </div>
          </div>

          <!-- 课本章末习题：题目照抄课本；多小问用 .quiz__part 分行。
               课本给了答案 -> .toggle + .panel；课本没给 -> 静态 .quiz__ans，不出展开按钮 -->
          <div class="board" id="board-exercise" role="tabpanel" aria-labelledby="tab-exercise" data-board="exercise" tabindex="0" hidden>
            <div class="stack">
            <article class="quiz quiz--ex" id="x1-1">
              <div class="quiz__q"><span class="quiz__no">习题 1.1</span>题目照抄课本正文。
                <span class="quiz__part">(1) 第一小问。</span>
                <span class="quiz__part">(2) 第二小问。</span>
              </div>
              <p class="quiz__ans"><span class="mono">答案</span><span class="wait">[待补充]</span> 课本只给题目、未给解答，此处不作推断。</p>
              <p class="card__src">出处：正文 §X.Y 习题 1.1</p>
            </article>
            <article class="quiz quiz--ex" id="x1-2">
              <div class="quiz__q"><span class="quiz__no">习题 1.2</span>课本给了答案的题目（这一张演示可展开答案的写法）。</div>
              <button class="toggle" type="button" aria-expanded="false" aria-controls="x1-2-a"
                      data-open-label="隐藏答案" data-close-label="显示答案">
                <span class="toggle__tx">显示答案</span><span class="toggle__ico" aria-hidden="true">+</span>
              </button>
              <div class="panel" id="x1-2-a" hidden>
                <div class="panel__inner">
                  <p class="quiz__a">答案照材料写，不作推断。</p>
                  <p class="card__src">出处：正文 §X.Y 习题 1.2</p>
                </div>
              </div>
            </article>
          </div>
          </div>
        </section>
      </div>
    </section>
  </main>

  <footer class="pager">
    <button class="pager__btn" type="button" id="prevPage">← 上一页</button>
    <div class="pager__bar"><span class="pager__fill" id="pageFill"></span></div>
    <div class="pager__dots" id="pageDots"></div>
    <span class="pager__src mono">来源：正文 §X.Y（含课本章末习题）</span>
    <button class="pager__btn" type="button" id="nextPage">下一页 →</button>
  </footer>

  <!-- 概念互引浮层：点开橙色术语后在这里展示前置概念 -->
  <div class="refbox" id="refBox" hidden>
    <div class="refbox__scrim" data-ref-close="1"></div>
    <div class="refbox__card" role="dialog" aria-modal="true" aria-labelledby="refBoxTitle">
      <div class="refbox__head">
        <span class="refbox__label mono" id="refStackLabel">概念速览</span>
        <button class="refbox__back" type="button" id="refBack"><span class="refbox__tx">返回原处</span> ←</button>
      </div>
      <div class="refbox__body" id="refBoxBody"></div>
    </div>
  </div>
</div>
'''

HEAD = '''<!DOCTYPE html>
<!--
  ============================================================================
  知识笔记 HTML · 单文件模板（dorothy-html skill · 宽屏翻页版）
  ---------------------------------------------------------------------------
  用法：整份复制，只改 <body> 里的内容；<style> 的令牌区与 <script> 的交互层照用。
        改颜色只改变量值，不要在别处写颜色字面量。
  页面：01 章节概览 → 02 知识地图 → 03 核心概念 → 04 易错点 → 05 自测与习题
  视觉：暖白纸底 #F5F3EE · 加灰的橙 #C0633F · 细线框 #D9D1BA · 黑底白字标签条
  字体：中文 霞鹜文楷（缺失回退楷体）· 英文数字 Times New Roman
        数学符号由 @font-face "NoteMath" 兜底（只接管 Times/楷体都没有的字符）
  互引：正文里的前置概念写成 <a href="#c2" class="ref" data-ref="c2">…</a>
  插图：结构沿用 lieflat-charts 的 B1 rung bars / B2 hairline line / B3 hairline area
  输入：该章课本正文（Markdown），课本章末习题随正文一起给。本 skill 不接收笔记类材料。
  必须替换：<title>、chrome__id、meta、地图节点与连线、五页内容
  待补充：材料里没有的信息写 [待补充]，不要编造
  自检：python scripts/check_note.py <本文件>
  ============================================================================
-->
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CHXX · 章节名 — 知识笔记</title>
<style>
'''

out = HEAD + CSS + "</style>\n" + THEME_BOOT + "\n</head>\n\n" + BODY + "\n<script>\n" + JS + "</script>\n</body>\n</html>\n"
target = SKILL / "assets" / "note-template.html"
target.write_text(out, encoding="utf-8")
print("wrote", target, len(out), "chars")
