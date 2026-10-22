# 视觉与交互规格（宽屏翻页版）

孤星参考页（`rhine-lab-lone-trail.html`）的科研档案终端语言，砍掉品牌展示部分，收窄为**单强调色 + 暖白纸面**的阅读版；宽屏翻页、真地图、互引浮层、lieflat 结构插图都在 `assets/note-template.html` 里有可运行实现。本文件是颜色、字面量、动效的**唯一**依据。

## 一、颜色令牌

| 令牌 | 值 | 允许用在哪里 |
|---|---|---|
| `--paper` | `#F5F3EE` | 画布底色 |
| `--paper-2` | `#ECE8E0` | 次级纸面：表头、行内代码底 |
| `--paper-3` | `#FCFBF8` | 卡片纸面、浮层纸面 |
| `--ink` | `#242322` | 正文、标题 |
| `--ink-2` | `#4A4844` | 次级正文（摘要、展开内容） |
| `--muted` | `#86817A` | 弱信息、未选中导航 |
| `--faint` | `#B0AAA0` | 编号、统计标签、出处行、图注 |
| `--line` / `--line-2` | `#D9D1BA` / `#E5E0D6` | 细线框 / 卡内分隔 |
| `--dark` / `--on-dark` | `#2A2723` / `#F3F1EA` | 深色块底 / 深底上的字 |
| `--accent` | `#C0633F` | 标记块、边框、进度填充、关键点 |
| `--accent-ink` | `#9E4E30` | 纸面上的橙色文字（对比度更高） |
| `--accent-soft` | `#D8A48D` | 连线、下划线、次要标记 |
| `--accent-wash` | `#F3E5DE` | 交互高亮底（小面积） |

规则：颜色字面量**只能**出现在 `:root`；其余位置一律 `var(--…)`。换配色就改 `:root`，不要新增颜色。橙色在原 `#F06030` 基础上降饱和压亮度得到（HSL 14°, 50%, 52%），这是“橙色太亮”的修正值。

## 二、主题：孤星 ⇄ NASA-punk（运行时切换）

同一份 HTML 里装两套令牌，由 `html[data-theme]` 决定用哪套，切换**不重出文件**。

| 主题 | `data-theme` | 令牌块 | 身份 |
|---|---|---|---|
| 孤星（默认） | `lonetrail` | 基础 `:root{}` | 暖白纸面 + 加灰的橙 `#C0633F` |
| NASA-punk | `nasapunk` | `:root[data-theme="nasapunk"]{}` | 设备白 `#ECE5D6` + 身份四色 `#4C5A68 #7A7F4E #D2A85E #A8432F` + 唯一鲜色 `#D63A2C` |

**三条硬规则**：

1. **令牌键名两套齐全**：主题块只许覆盖、不许新增键。NASA-punk 专用令牌（`--red` / `--red-ink` / `--s1..--s4` / `--rivet` / `--wear-dark` / `--wear-light`）在孤星主题的基础 `:root` 里也保留占位值 —— 否则切回默认主题会缺声明。`check_note.py` 据此断言：主题块新增键报错、任何 `var()` 解析不到也报错（`--i/--n/--p/--x/--y` 是 JS 写进内联 style 的运行时变量，豁免）。
2. **主题块只覆盖颜色与面板线条**：不许覆盖 `font-family / font-size / letter-spacing / text-transform / font-style / line-height` —— 两套主题的字体、字号、字距完全一致，NASA-punk 也不换字体。
3. **装饰件常驻 DOM**：`.np-chrome` 包住四色身份条 / 黑白警示斜纹 / 接缝铆钉 / 角螺丝 / 使用痕迹，全部 `aria-hidden="true"`。孤星主题下 `.np-chrome{display:none}`（不占排布，孤星的观感与单主题版逐字一致）；NASA-punk 下 `display:contents`（子元素直接成为 `.deck` 的 flex item，绝对定位项仍相对 `.deck`），并按 34ms 级联淡入（`--i`，与地图节点同一套 `cascadeIn` 节奏）。

**NASA-punk 的鲜色 `#D63A2C` 只给三处**：关键结论（`.key-mark` / `.key`）、易错点（`#p-pitfalls` 的左边线与标签）、浮层返回键（全页唯一实心按钮）。其余结构色一律走 `--accent*`，在 NASA-punk 下换成身份四色里的蓝灰。

**记忆**：`localStorage['dorothy:theme']`，知识库里各章共用同一份偏好。首屏由一个 `<head>` 小脚本在绘制前落定 `data-theme`，避免先闪一下默认主题；`try/catch` 兜住 `file://` 受限与隐私模式，失败即用默认孤星。

**完成态**：`html[data-theme]` 已是新值；选中态与 `aria-pressed` 同步；进度条驻留后淡出并归零；`html` 上不残留 `is-theming`。

## 三、橙色使用范围

| 允许 | 具体位置 |
|---|---|
| 语义标签 | `.tag` 的文字与 code、`.bar__sq` 方块 |
| 关键结论标记 | `.key-mark`、`.key` 的左侧竖标 |
| 当前展开状态 | `.card.is-open` / `.quiz.is-open` 边框、`.toggle[aria-expanded="true"]` 文字 |
| 交互高亮 | hover / `:focus-visible`、互引术语 `.ref`、顶栏当前锚点（全页只一处）、地图当前节点与热边、浮层返回键 |

禁止：走马灯/横幅背景、按钮大面积填充、纯装饰线、任何区块的大面积底色。

## 四、深色块

- 只允许 `.bar`（区块语义标签条）。页脚已改为浅色翻页器 `.pager`，不再是深色块。
- 单屏深色面积 ≤ 5%。参考量级：`.bar` 高 30px、宽 ≈ `--shell`（1560px）→ 约 47,000 px²；在 1200×800 视口里两条同屏约 9.7%……所以**一屏内不要出现两个 `.bar`**：五页翻页结构天然保证每屏只有页内一个标签条，只有 `#p-core` 因为分三组会有 1 个标签条 + 3 个小标签；若深色面积吃紧，把 `.bar` 高降到 26px。
- 深色块里只放区块名，不承担阅读任务。

## 五、字体与数学兜底

| 令牌 | 栈 | 用途 |
|---|---|---|
| `--font-text` | Times New Roman → LXGW WenKai（霞鹜文楷）→ KaiTi（楷体）→ `NoteMath` → serif | 正文、标题、卡片名、公式 |
| `--font-mono` | Consolas → Courier New → ui-monospace | 数字注记、编号、出处行、图注、公式编号 |

英文与数字走 Times（课本衬线），中文走霞鹜文楷（缺字体回退楷体）——两者在同一栈里，浏览器按字符各自取，是**刻意的一层混排**。

数学字符 `𝔼 𝒜 𝒩 𝒫 ⟹ ⟺ ↦ ∀ ∅ ⊂ ⋃ ⋯ ∗ ∘ ⟨ ⟩`（16 类）在本机没有任何正文字体覆盖，必须显式兜底：

```css
@font-face{
  font-family:"NoteMath";
  src:local("Cambria Math"),local("Cambria Math Regular"),local("Segoe UI Symbol");
  size-adjust:94%;                 /* 对齐 Times 的视觉大小，92%–98% 之间调 */
  unicode-range:U+1D400-1D7FF,U+21A6,U+2200,U+2205,U+2217-2218,U+2282,U+22C3,U+22EF,U+27E8-27E9,U+27F9-27FA;
}
```

三条硬规则：**只用 `local()`**（不引外链字体）；`unicode-range` 只圈这些数学区段（`ℙ ℝ ℤ ℕ ℬ ℰ` 仍由 Times 渲染，不抢）；`size-adjust` 用来消除不同字体 x-height 不一致造成的“鼓包”。

判断要不要兜底的方法：统计正文里所有非 ASCII 字符，逐个查 Times / 霞鹜文楷 / 楷体是否含该字形，不含的即为回落字符。别凭感觉猜。

## 六、排版尺度

| 项 | 值 |
|---|---|
| 正文字号 / 行高 | 18px / 1.78 |
| 正文测量宽 `--measure` | 36em（≈ 每行 36 字） |
| 页宽 `--shell` | 1560px（宽屏两栏卡片：`minmax(620px,1fr)`） |
| 卡片标题 / 章节名 | 23px / 30px（≤900px 降为 20px / 24px） |
| 语义标签 | 12px code + 13px 中文 |
| 公式 | 正文字族、17.5px、居中、上下 ≥ 1.5em |
| 插图内字号 | 数值 11–12.5px、注记 11px（等宽） |
| 出处行 | 12px、`--faint` |

`sub/sup` 统一为 `line-height:0; font-size:.72em; position:relative; vertical-align:baseline;`，`sup{top:-.44em}` / `sub{top:.24em}`——避免上下标把行距顶跳。

## 七、动效

| 项 | 值 |
|---|---|
| 属性 | 只动 `opacity` + `transform`（位移/缩放） |
| 曲线与时长 | `--e-out cubic-bezier(.16,1,.3,1)`、`--e-inout`、`--e-spring`；`--t-press .12s` / `--t-fast .22s` / `--t-swift .34s` / `--t-med .5s`（词表沿用 cassette）；`--t-theme .34s` 专给主题切换，**必须与 JS 里的 `THEME_MS` 相等** |
| 翻页 | 退场立刻、入场等 60ms（两拍）；位移 ±16px |
| 展开面板 | `opacity` + `translateY(-7px→0)`，`.22s` |
| 地图节点入场 | `translateY(+16px→0)` + `opacity`，`34ms × 序号`（封顶 400ms）；连线用 `pathLength="1"` + `stroke-dashoffset` 生长 |
| 图表入场 | 挂在 `.panel.is-in .fig …`，卡片展开时才播；按挂类分四拍（`.f-fade` 淡入 / `.f-line` 画线 / `.f-dot`·`.f-arrow` 落点 / `.f-line--acc-dash` 换虚线），规则在 `assets/note-template.html` 的 8.5 节，**不按序号 stagger** |
| 禁止 | `height` / `width` / `max-height` 过渡；缩放回弹以外的弹簧；模糊转场 |
| 板块切换 | `.board.is-in` 的 `boardIn`：`opacity` + `translateY(12px→0)`，`.22s`（`--t-fast` / `--e-out`）；指示条 `.tabs__ind` 只动 `transform:translateX(...)`，同一条曲线 |
| 降级 | `prefers-reduced-motion` 用通配长属性规则一次清干净（`.board.is-in` 另有 `animation:none`）；JS 的定时收尾留 `SETTLE` 兜底 |

**具名例外：主题切换的颜色过渡。** 颜色状态互换做不到只靠 opacity/transform，所以 `html.is-theming` 存活期内（`--t-theme = .34s`）放开 6 个颜色类属性：`background-color / color / border-color / outline-color / fill / stroke`，曲线 `--e-inout`。三条约束缺一不可：① 只在 `.is-theming` 存活期内（JS 加类 → 强制重排 → 换 `data-theme` → `THEME_MS + 20ms` 后移除）；② 必须显式写 `transition-delay:0s`，否则 `.page.is-active` 那类多值 delay 会让 6 个属性错拍；③ 放开列表不得出现这 6 个以外的属性，`check_note.py` 会断言。除这一块之外，仍然**只动 opacity / transform**。

**主题切换进度条与读数**：`.theme` 容器加 `.is-running` 才显形（`opacity` 过渡）。`.theme__fill` 只动 `transform:scaleX(var(--p))`（`transform-origin:0 50%`，**不是 width**），rAF 线性 0→1，读数写等宽百分比；`p = 1` 后条**驻留 240ms**，再以 `opacity`（`--t-fast`）淡出并归零，读数写回主题代号。`prefers-reduced-motion` 下时长 0、进度条不出现。

**装饰件入场**：切到 NASA-punk（含首屏记忆即 NASA-punk）时 `.np-chrome > *` 按 `min(calc(--i * 34ms), 400ms)` 级联淡入（`npIn`），与地图节点同节奏。退出时不淡出（整块 `display:none`），由纸面颜色的交叉过渡带走视觉。

## 八、断点

| 断点 | 变化 |
|---|---|
| > 1180px | 卡片两栏（`minmax(620px,1fr)`），翻页器显示来源行 |
| ≤ 1180px | 卡片单栏，隐藏翻页器来源行 |
| ≤ 900px | 顶栏换行（导航移到第二行）、章节名与卡片标题降级、`.facts` 改单列、隐藏页码点、主题控件隐藏 `THEME` 标签、分段控件改整行（`margin-left:0; width:100%`） |

主栏宽度用 `--shell` 与 `--measure` 两个变量控制：改宽只改这两处。

## 九、可访问性

- 展开控件 `<button aria-expanded aria-controls>`；面板用 `hidden` 切换；浮层 `role="dialog" aria-modal="true"` + 焦点锁。
- 互引术语用 `<a href="#id" class="ref">`，无 JS 时退化为锚点跳转。
- 地图节点 `tabindex="0" role="link"` + `aria-label`，Enter/空格可激活。
- 不靠颜色单独传达信息：语义标签同时有 code（`DEF`/`THM`…）与中文名；互引术语除颜色外还有下划线。
## 十、分板块与分段控件（核心概念三块 / 末页两块）

定义 / 定理 / 例子**分屏**，不要挤在同一屏上；末页的自测 / 课本章末习题同样分屏。切换控件放在子标题（`.section__head`）里，**一组一个**：`data-tabs="core"`（三块）与 `data-tabs="quiz"`（两块，加 `.tabs--two`）。

`data-board` 全局唯一：`def` / `thm` / `ex` / `self` / `exercise`（末页不能用 `ex`，那是例题块）。

| 元素 | 要求 |
|---|---|
| `.tabs` | `role="tablist"`，三段等宽（`grid-template-columns:repeat(3,minmax(0,1fr))`），`width:min(520px,100%)`，细线框 + `--paper-3` 底；卡数写进 `.tabs__n`（等宽小字）。两块式加 `.tabs--two`：`repeat(2,...)`、`width:min(360px,100%)`、指示条 `width:calc(100% / 2)` |
| `.tabs__ind` | 指示条：`position:absolute`，`width:calc(100% / 3)`，`transform:translateX(calc(var(--tab,0) * 100%))`，`--accent-wash` 底 + 2px `--accent` 下边；**只动 transform** |
| `.tabs__tab` | `role="tab"`，`aria-selected` + roving `tabindex`（选中 0、其余 −1）；选中态同时改文字色（`--ink`）与指示条位置，不靠颜色单独传达 |
| `.board` | `role="tabpanel"` + `aria-labelledby` + `data-board`；非默认块加 `hidden`；**默认显示「定义」** |

**硬规则**：

1. **指示条的 `--tab` 只能由 JS 写在 `.tabs` 上**（`boardBox.style.setProperty('--tab', String(index))`）。**绝不要给 `.tabs__ind` 写内联 `--tab`** —— 内联声明优先于继承，指示条会永远停在 0。
2. **翻页快捷键必须让路**：`←/→/Home/End` 在 `[role="tablist"]` 里是切板块，`document` 的翻页键处理要先 `closest('[role="tablist"]')` 返回。
3. **每组、每块各自记 `scrollTop`**：切走时存、切回时恢复（首次为 0）；两组互不干扰。`openCard()` 用 `keepScroll` 跳过恢复，自己精确滚到卡片。
3.1 **板块的滚动容器是它所在页的 `.page__inner`**（用 `board.closest('.page').querySelector('.page__inner')` 取），不要写死 `#p-core`。
4. **跳转要带板块**：地图节点、搜索命中、`#c3` 这类卡片深链，都必须先切到卡片所在板块再展开+滚动，否则会滚到隐藏元素上（`getBoundingClientRect` 全 0）。
## 十一、顶栏工具区（搜索 + 主题开关）

`.chrome` 从左到右：章节号 → 页面导航（`flex:1`）→ `.chrome__tools`（**右上角**）：搜索框 → 主题开关 → 页码。

| 元素 | 要求 |
|---|---|
| `.search` | `role="search"`；细线框 + `--paper-3` 底；`FIND` 小标签（`aria-hidden="true"`，不当作输入框的可见名） |
| `#searchIn` | `input[type="search"]` + `role="combobox"` + `aria-expanded` + `aria-controls="searchHits"` + `aria-autocomplete="list"` + `aria-activedescendant="hit-N"`；`width:clamp(118px,16vw,238px)`（≤900px 收窄到 `clamp(92px,30vw,180px)` 并隐藏 `FIND`） |
| `.hits` | `position:absolute`，`top:calc(100% + 5px)`、`right:-1px`、`z-index:20`，`width:min(440px,88vw)`、`max-height:min(54vh,430px)`；开合只动 `opacity` + `translateY(-6px→0)` + `visibility`（照 `.page` 的写法），关闭时 `pointer-events:none` |
| 结果项 | 语义标签（等宽、`--accent-ink`）+ 概念标题 + 匹配片段；`mark` 用透明底 + `--accent` 下划线（**不要浏览器默认黄底**）；列表尾部一行等宽提示（条数 + 操作说明） |

**硬规则**：

1. **索引范围只有 `#p-core .card`**：易错点 / 自测题 / 章末习题都不进索引；`.card__src` 出处行要剔除（否则「正文」「§」会命中一切）。
2. **多词 AND，权重 标题 3 > 摘要 2 > 正文 1**，同分按文档顺序，最多 20 条。
3. **折叠（case folding）两侧都要做**：查询词与正文都过 `fold()`（`\u3000`→空格、`toLowerCase`，**保长度**，所以下标能直接映射回原文做切片）。只折叠一侧会让 `Fourier` 这类大写词永远搜不到。
4. **片段与高亮只用 `createTextNode`**，用户输入不拼 `innerHTML`。
5. **翻页快捷键让路**：`document` 的翻页键处理遇 `closest('[data-search]')` 直接返回（输入框里 `←/→` 是光标、`Home/End` 是行首行尾）。
6. **中文输入法**：`compositionstart` 期间不搜、`compositionend` 再搜。
7. **顶栏裁剪放在 `.deck`**：`.chrome` 不能有 `overflow:hidden`，否则下拉结果被裁掉。
8. **跳转复用 `openCard(id)`**（先切板块、再展开、滚动、闪一下），完成后把焦点交给卡片的展开按钮。
## 十二、插图（由 `dorothy-picture` 产出）

本页不自己做图；插图是 dorothy-picture 交付的 `<figure class="fig">` 片段。本页只规定**落地要求**。

### 尺寸与比例

| 项 | 值 |
|---|---|
| 图宽 | `.fig{width:min(calc(100% + 8em), 52em); margin-inline:auto}`——宽图**出栏**（正文测量宽 36em，图可以更宽） |
| 高度上限 | `max-height:min(52vh, 460px)`；栅格图加 `object-fit:contain` |
| 比例 | SVG 由 `viewBox` 决定；栅格图按原图比例写 `aspect-ratio` |
| `≤1180px` | 回到 `width:100%`（单栏不出栏） |

### alt 与读屏

- 内联 SVG：`role="img"` + **非空** `aria-label` + `<title>`；栅格图：`<img alt="…">`；
- 写「图的类型 + 主体 + 变量范围」，**不许以「图片 / 示意图」开头**；
- 图内 `<text>` 不参与读屏，关键信息必须同时出现在 `aria-label` 或图注里。

### 图注

- 逐字格式：`图 N · 一句话说明（正文 §X.Y）`；
- 数据来源、示意参数、发散 / 截断写进图注（例：「图中取 λ = 1 示意」「p 在 x → 2⁻ 处发散，曲线在 x = 1.915 处出图」）；
- 图注走等宽字体（`.fig figcaption`），12px。

### 来源优先级与内联

| 序 | 来源 | 落地方式 |
|---|---|---|
| 1 | 本地已有图库 | 等比缩到长边 ≤1400px → base64 内联（保单文件）→ `mix-blend-mode:multiply` 让白底并入纸色 → 1px `--line` 边框；图注写原始文件名 |
| 2 | 生成图 | 内联 SVG（默认形态）；**图内不写颜色字面量**，颜色由 `.fig .f-*` / `.fig .t-*` 按令牌给，因此**跟随主题切换** |
| 3 | 占位图 | 主题化空框 + `[图示待补充]`；**绝不画假数据** |

### 允许的图内语义类

- 线：`f-grid` `f-axis` `f-rail` `f-hair` `f-hair--acc` `f-hair-thin` `f-rung` `f-line` `f-line--acc` `f-line--acc-dash` `f-rule-dash` `f-rule-dash-sm` `f-bracket`
- 结构：`f-box` `f-box--acc` `f-band` `f-link`
- 灰阶通道（不占色相）：`f-hl`（强调区域填充 / 数据柱填充）`f-hl-edge`（强调边框）
- 交互图控件：`fig__ctl`（容器）+ 其内的 `button`（走元素选择器，不新增类）+ `[data-hint]`

**交互图**（图内含内联 `<script>`）的额外要求见 `dorothy-picture/reference/interactive.md`：静态首帧必须自立、只动 `opacity/transform`、不许出现任何外链字面量。
- 点：`f-dot` `f-dot--acc` `f-dot-hollow` `f-tick` `f-arrow`
- 文字：`t-num` `t-lab` `t-note` `t-halo`；入场：`f-fade`

**需要新语义时先在这里登记样式**（基础 `:root` 一条 + NASA-punk 一条），再由 dorothy-picture 使用；图内字号 ≥ 11px。


