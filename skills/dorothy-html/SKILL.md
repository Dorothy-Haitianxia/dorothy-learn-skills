---
name: dorothy-html
description: "全局 skill：把任意科目的某章课本正文（含课本章末习题）生成一份可直接在浏览器打开的单文件知识笔记 HTML（宽屏翻页式：章节概览 → 知识地图 → 核心概念 → 易错点 → 自测与习题）。视觉沿用「孤星」科研档案终端语言：暖白纸底 #F5F3EE、加灰的橙 #C0633F、细线框 #D9D1BA、黑底白字标签条；中文霞鹜文楷、英文数字 Times New Roman、数学符号由本机 @font-face 兜底。硬约束：颜色全走 CSS 变量、无圆角无阴影、accordion 互斥展开、只动 opacity/transform、正文每行 30–40 字、内容只来自输入材料（缺料写 [待补充]）。含可平移缩放的知识地图、前置概念互引浮层（橙色下划线术语 + 逐层返回）、按 lieflat-charts 结构的辅助插图；内置孤星 ⇄ NASA-punk 双主题（运行时切换、localStorage 记忆）；顶栏全局搜索只索引核心概念，结果给标题 + 匹配片段并自动切板块跳转。"
---

# 知识笔记 HTML 生成

给一章课本内容做一份**可反复回看的单文件知识页**：五页翻页式（章节概览 → 知识地图 → 核心概念 → 易错点 → 自测与习题），概念可逐张展开，后出现的概念能点开前面定义的概念速览，关键处配一张从材料数据画出来的图。

**只管产出这份 HTML**。内容怎么挑、题目由谁出，按上游材料与科目约定；本文件管页面结构、卡片字段、互引与插图规则、视觉与交互的硬约束。

## 一、输入

| 输入 | 用途 | 缺失时 |
|---|---|---|
| 课本正文（Markdown） | 全部定义、定理、证明、例题、经典对象 | 没有正文就不生成，先要材料 |
| 课本章末习题（通常随正文一起给） | 末页「课本章末习题」段的题目，题目照抄 | 末页不出现该段，只留自测 |
| 额外题目（可选，用户另行给出） | 追加到末页习题段，出处写清来源 | 只收课本章末的 |

**只处理课本材料**：不接收笔记类输入（课堂笔记、`#idea`、他人整理的笔记都不收）。

公式就地取自材料；材料用 LaTeX 时**转写成可读的 Unicode/HTML 公式**（`𝔼[X]`、`∫`、`Σ`、`√`、`<sub>`/`<sup>`），交付物不依赖 KaTeX/MathJax。

## 二、输出

- 文件名 `chXX-章节名.html`，放在科目工作区。
- **单文件**：CSS/JS 内联，不引外部图片、字体、脚本；字体只用系统字体栈 + 本机 `local()` 兜底。
- 模板：`assets/note-template.html`。复制它，只改 `<body>` 内容；`<style>` 的令牌区与 `<script>` 的交互层照用。模板由 `scripts/build_template.py` 从 `assets/src/style.css` 与 `assets/src/app.js` 生成（样式与交互层的**唯一源就在 skill 里**，clone 到任何地方都能重建；教学层样式在 `style.css` 内，所以模板默认就带 `.tk-*` 全套）。

## 三、页面结构（五页 + 一个浮层）

| 页 | 必须有 | 不许出现 |
|---|---|---|
| `#p-overview` 章节概览 | 章节名、知识点数、定义/定理数、预计复习时长；**关键结论**一行；阅读路径 | 状态条式假读数（AES-256、节点号一类） |
| `#p-map` 知识地图 | 分层节点（可点击跳卡）+ 连线与关系词 + 缩略图 + 缩放控件；画布比屏幕大，可拖拽缩放 | 装饰性插图、材料里没有的关系 |
| `#p-core` 核心概念 | **三板块**（定义 / 定理 / 例子）分屏，只显示一块；子标题处 `role="tablist"` 分段控件带卡数；默认「定义」；每块各自记 scrollTop；组内 accordion 互斥 | 三组挤在同一屏、编号、卡片代码、进度条、完成度百分比 |
| `#p-pitfalls` 易错点 | 错误说法 + 触发场景 → 限制条件 + 正确做法 | 编造的“常见错误” |
| `#p-quiz` 自测与习题 | **两块**分屏（自测 / 课本章末习题）＋子标题分段控件；自测＝问题 + 默认隐藏的答案（各题独立展开）；课本章末习题＝题目照抄，课本给了答案才出展开按钮 | 两段挤在同一屏、直接把答案摊开、给课本习题编造答案 |
| `#refBox` 概念速览浮层 | 点橙色术语后弹出前置概念；背景模糊；返回键 | — |

**顶栏 `.chrome`**（从左到右）：章节号 → 页面导航（`flex:1`）→ `.chrome__tools`（右上角：**搜索框 → 主题开关 → 页码**）。搜索框全局可用，但**只索引 `#p-core` 的卡片**；结果面板从顶栏下沿伸出，不遮挡主题开关与内容。

**删除**：巨幅 Hero、走马灯、页脚导航组、品牌展示元素。页脚只留一条翻页器（上一页 / 进度 / 页码点 / 下一页）。

## 四、卡片字段

| 卡型 | 标签 | 常显 | 展开 |
|---|---|---|---|
| 概念卡 | `DEF` 定义 | 概念名 + 一句话摘要 | 完整定义（材料原文表述）、要点、必要公式 |
| 定理卡 | `THM` 定理/命题 | 定理名 + `条件` + `结论`（`<dl class="facts">`） | 证明思路或证明要点 |
| 例题卡 | `EX` 例题 | 题目名 + 题目 | 解答步骤 |
| 易错点卡 | `ERR` 易错点 | 错误说法 + 触发场景 | 限制条件 + 正确做法 |
| 自测题 `.quiz` | `Q1`… | 问题 | 答案（独立展开，不进 accordion 组） |
| 课本章末习题 `.quiz--ex` | `习题 X.Y` | 题目（多小问用 `.quiz__part` 分行） | 答案：课本给了才出 `.toggle` + `.panel`；没给就写静态 `.quiz__ans` + `[待补充]` |

每张卡结尾必须有 `<p class="card__src">出处：正文 §x.y</p>`。摘要与展开内容是两层，不许互为同义改写，也不许出现材料里没有的判断、例子或数字。

## 五、互引标记（后出现的概念指向前面的定义）

**规则**（四条，缺一不可）：

1. **范围**：只在 `#p-core` 里 `.panel__inner`（展开内容）中标记；**出处行与插图 SVG 内不标**。
2. **方向与数量**：目标只能是**文档顺序更早的卡**（概念 / 定理 / 例题都可作目标）；同一张卡里，同一个目标只标**文中最早那一处**。
3. **降噪**：`随机变量 / 随机向量 / 期望 / 分布 / 方差` 这类每张卡都出现的基础词**不标**；只留编号引用（`定义 8.2`、`命题 8.5`）、记号（`𝔼[X]`、`var(X)`、`cov(X,Y)`、`F_X`、`Φ_X`、`L_X`）与专有概念名（`分布（律）`、`特征函数`、`Laplace 变换`、`Poisson 分布`…）。经验值：一章 25–35 张卡，标出 15–25 处最舒服。
4. **边界守卫**（否则必然错标）：
   - 编号后不能紧跟数字或 `.数字`：`定义 8.1` 不能吞 `定义 8.12`；
   - 左侧排除词：`二项 / 几何 / 均匀 / 指数 / Gamma / Cauchy / 高斯 / 正态 / 边缘 / 条件 / 离散 / 连续 …` + `分布` 不连到「分布（律）」；`协` + `方差` 不连到「矩与方差」；
   - 右侧后缀守卫：`分布` + `函数` 不连到「分布（律）」（那是「分布函数」）。

**实现**：标记写成 `<a href="#c2" class="ref" data-ref="c2">随机变量</a>`——用 `<a>` 不用 `<button>`，没有 JS 时退化为原生锚点跳转。**不要**把它放进任何 `display:flex/grid` 容器的直接子级（行内元素会被拆成独立 flex item，把词拆散）。标记区间要**扩展到行内标签的完整边界**：`L<sub>X</sub>` 必须整段包进去，否则得到 `L<sub>X</a></sub>` 这种坏嵌套。

**别名表不由模型即兴判断，走工具**：

```powershell
# 1) 审：打印并写出 <产物>_refs-review.md（别名表、守卫表、每处上下文、被拦下的）
& '<python>' -X utf8 'scripts/refs.py' --file '<产物.html>'
# 2) 逐条核对后应用（产出新文件，不改原件）
& '<python>' -X utf8 'scripts/refs.py' --file '<产物.html>' --apply --out '<产物-marked.html>'
```

`scripts/refs.py` 里要改的只有两处：`ALIASES`（术语 → 目标卡）与 `EXCLUDE` / `SUFFIX_BLOCK`（守卫词）。

**浮层行为**：内容从目标卡**原件克隆**（标签 + 标题 + 摘要/条件结论 + 完整展开内容 + 出处），克隆进 `.panel.is-in` 以便插图的入场动画重放；`role="dialog" aria-modal="true"`；背景 `backdrop-filter: blur(7px)`；Esc / 点背景 / 返回键三种关法；**逐层返回栈**（浮层内继续点橙色术语会压栈，返回先退一层，到栈底才关）；关闭时恢复 `#p-core` 的 `scrollTop`、把焦点还给被点的术语并闪一下。

## 六、插图：委托 `dorothy-picture`

**本 skill 不自己做图。** 插图统一交给全局 skill `dorothy-picture`：它先对六类内容源逐条做制图评估（结论落盘，不出图也要写理由），再用 11 字段决策卡定下教学任务、视觉顺序与替代文本，用令牌化内联 SVG 生成、渲染成 PNG 亲眼核对后交付。本 skill 只负责三件事：给它输入、把产出插到锚点、把图文闭环写进正文。

它的图型库结构语法从 `lieflat-charts` 的三张基础型出发，配色字体换成本页令牌：

| 结构正本 | 适用数据 | 本页实现 |
|---|---|---|
| **B1 rung bars** | 少类目概率/计数，可数单位（1 档 = 1%） | 图 2 Poisson 的二项逼近 |
| **B2 hairline line** | 一条曲线的形态与关键点 | 图 3 指数分布无记忆性 |
| **B3 hairline area** | 两条曲线对比、面积即概率 | 图 1 Bertrand 两条密度 |

**硬要求**：

- 数据必须来自材料的公式；**示意参数要写在图注里**（例：“图中取 λ = 1 示意”）。发散、截断、近似都要标出来（例：“p 在 x → 2⁻ 处发散，曲线在 x = 1.915 处出图”）。
- 命名沿用 lieflat 的语法：全大写注记行写清可数单位（`ONE RUNG = 1% PROBABILITY · DASHED RULE = POISSON(λ = 2)`）、数值加粗 + `paint-order` 光晕、峰值/关键点加圆点。
- 插图必须是**内联 SVG**（不引 CDN）；文字类用 `--font-text`，注记用 `--font-mono`，颜色只走令牌；图表内字号 ≥ 11px。
- 图注格式：`图 N · 一句话说明（正文 §X.Y）`；放在对应卡的展开内容里、出处行之前。
- 入场动画挂在 `.panel.is-in .fig …` 上——卡片展开时才播，`prefers-reduced-motion` 下由通配规则落终态。
- 图的数量由 dorothy-picture 的评估结果决定，**不再固定 1–3 张**；`scripts/figures.py` 已迁出为 dorothy-picture 的 `scripts/lib/figlib.py`。

### 与 dorothy-picture 的接口

| 方向 | 内容 |
|---|---|
| **给它** | ① 知识点清单（卡片 id + 类型 + 标题）；② **本地可用图清单** `<产物>_figure-assets.md`（路径 / 尺寸 / 能讲什么；没有就写「无」）；③ 宿主页令牌与插图标定（第七、九节 + `reference/design-spec.md`） |
| **收回来** | ① `<产物>_figures-plan.md`（制图评估与规划清单，**来源决策只在那一侧发生**）；② `figs/fig-<N>-<slug>.html`（完整 `<figure class="fig">` 片段）；③ `<产物>_figures-cost.md`（成本账） |

```powershell
$dp = "$HOME\.agents\skills\dorothy-picture"   # 或工作区源码 skills\dorothy-picture
# 规范通道：先读 $dp\SKILL.md，按它的五步流程（评估 → 规划 → 制图 → 渲染核对 → 交付）
& '<python>' -X utf8 "$dp\scripts\check_plan.py" '<产物>_figures-plan.md' --html '<产物>.html'
& '<python>' -X utf8 "$dp\scripts\check_figure.py" 'figs\*.html'
node "$dp\scripts\render_fig.js" --figure 'figs\fig-1-xxx.html' --css '<样式源>' --out '.work\fig-1.png'
```

### 本 skill 侧还要做到

- **图必须落在锚点处**：图前引导 + 图后解释写在卡片面板里，**不许只写「如图所示」**；
- **每张图要能在 `<产物>_figures-plan.md` 找到对应条目**（`check_note.py` 校验 figure id 与清单对得上）；
- **来源优先级**：本地已有图库 > 生成图 > 占位图；比较在 dorothy-picture 侧做，本 skill 只执行落到 HTML 的那一步；
- **图宽出栏**：`.fig{width:min(calc(100% + 8em), 52em)}`，高度上限 `min(52vh, 460px)`；`≤1180px` 回到 `100%`；
- 本地栅格图内联时：等比缩到长边 ≤1400px 后 base64 内联、`mix-blend-mode:multiply` 融进纸色、1px `--line` 边框；
- alt 与 aria-label：内联 SVG 用 `role="img"` + `aria-label` + `<title>`；栅格图用 `<img alt="…">`；都不许以「图片 / 示意图」开头。

## 七、视觉硬约束

颜色**只允许**出现在两个令牌块里：基础 `:root`（孤星，默认）与 `:root[data-theme="nasapunk"]`（NASA-punk），其余一律 `var(--…)`。

| 令牌 | 值 | 用途 |
|---|---|---|
| `--paper` / `--paper-2` / `--paper-3` | `#F5F3EE` / `#ECE8E0` / `#FCFBF8` | 画布 / 次级纸面 / 卡片纸面 |
| `--ink` / `--ink-2` / `--muted` / `--faint` | `#242322` / `#4A4844` / `#86817A` / `#B0AAA0` | 正文 / 次级正文 / 弱信息 / 编号刻度 |
| `--line` / `--line-2` | `#D9D1BA` / `#E5E0D6` | 细线框 / 卡内分隔 |
| `--dark` / `--on-dark` | `#2A2723` / `#F3F1EA` | 深色块底 / 深底上的字 |
| `--accent` / `--accent-ink` / `--accent-soft` | `#C0633F` / `#9E4E30` / `#D8A48D` | 标记块·边框 / 纸面上的橙字 / 连线 |
| `--shell` / `--measure` | `1560px` / `36em` | 页宽 / 正文测量宽（每行 30–40 字） |

- **橙色只用在四处**：语义标签、关键结论标记（`.key` / `.key-mark`）、当前展开状态（`.card.is-open`、`[aria-expanded="true"]`）、交互高亮（hover/focus、互引术语 `.ref`、顶栏当前锚点一处）。
- **深色块只剩一处**：区块语义标签条 `.bar`。禁止走马灯背景、按钮大面积填充、装饰线。
- **禁止**：圆角（`border-radius` 只能是 0）、阴影（`box-shadow` 只能是 none）、装饰插图、emoji 图标、超过三套字族、`url()` 外链字体。
- **字体三套**：`--font-text`（英文 Times New Roman + 中文 霞鹜文楷/楷体）、`--font-mono`（Consolas，用于数字注记与出处行）。数学字符（`𝔼 𝒜 𝒩 𝒫 ⟹ ⟺ ↦ ∀ ∅ ⊂ ⋃ ⋯ ∗ ∘ ⟨ ⟩`）由 `@font-face "NoteMath"` 兜底：`src: local("Cambria Math"), local("Segoe UI Symbol")` + `size-adjust:94%` + 限定 `unicode-range`，**只用 local()**。
- **双主题（运行时切换）**：`html[data-theme]` 取 `lonetrail`（默认）或 `nasapunk`。两套令牌**键名必须齐全**——主题块只许覆盖、不许新增键，NASA-punk 专用令牌（`--red` / `--s1..--s4` / `--rivet` / `--wear-*`）在基础 `:root` 里也留占位值；主题块不许覆盖字体 / 字号 / 字距 / `text-transform`。装饰件（四色身份条、黑白警示斜纹、接缝铆钉、角螺丝、使用痕迹）包在 `.np-chrome` 里常驻 DOM、全部 `aria-hidden="true"`：孤星下 `display:none`（不占排布），NASA-punk 下 `display:contents` 并按 34ms 级联淡入。首屏由 `<head>` 小脚本读 `localStorage['dorothy:theme']` 在绘制前落定，避免先闪默认主题。
- **主题切换的动效（唯一的具名例外）**：只在 `html.is-theming` 存活期内（`--t-theme = .34s`、`--e-inout`）放开 6 个颜色类属性（`background-color / color / border-color / outline-color / fill / stroke`），且必须显式写 `transition-delay:0s`；同时 `.theme__fill` 用 `transform:scaleX(var(--p))` 走百分比进度条，`p = 1` 后驻留 240ms 再淡出、归零、写回主题代号。除这一块之外仍**只动 opacity / transform**。数值与判定见 `reference/design-spec.md` 第二节与第七节。

## 八、交互硬约束

- **翻页**：`← →` / `PageUp·Down` / `Home·End`；顶栏锚点、阅读路径、页码点、上一页/下一页四路可达；两拍节奏（退场立刻、入场等 60ms）；进度条用 `transform: scaleX(var(--p))`，**不用 width 过渡**；页码用 WAAPI 滚动（落地交给定时器，不依赖 `animation.finish`）。
- **展开**：概念/定理/例题/易错点用 `.stack[data-accordion]` 分组互斥；自测题**不进组**（要能同时看多题）；`<button aria-expanded aria-controls>` 控制 `<div class="panel" hidden>`；展开/收起切换按钮文字与 `+ / −`；同组内 ↑/↓/Home/End 移动焦点。
- **分板块切换（两组）**：每组的 `role="tablist"` + N 个 `role="tab"`（`aria-selected` + roving `tabindex`）+ N 个 `role="tabpanel"` 的 `.board`，任一时刻每组只显示一块；**核心概念三块**（定义 / 定理 / 例子，默认定义，`data-board` = `def`/`thm`/`ex`）、**末页两块**（自测 / 课本章末习题，默认自测，`data-board` = `self`/`exercise`）。←/→/Home/End 在控件内切换（**自动激活**：焦点到哪块切到哪块），所以翻页快捷键必须先加 `closest('[role="tablist"]')` 守卫，否则按 ←/→ 会翻页而不是切板块。两块式用 `.tabs--two`（两格 + 指示条 `width:calc(100% / 2)`）。
  `data-board` 要**全局唯一**（两组共用一张查找表），所以末页用 `self` / `exercise` 而不是 `ex`（那是核心概念的例题块）。
- **顶栏搜索**：`input#searchIn`（`role="combobox"` + `aria-expanded` + `aria-controls="searchHits"` + `aria-activedescendant`）配 `<ul class="hits" role="listbox">`。**索引范围只有 `#p-core .card`**（易错点 / 自测题 / 章末习题不进），并剔除 `.card__src` 出处行。多词 **AND**，权重 标题 3 > 摘要 2 > 正文 1，同分按文档顺序，最多 20 条；片段取命中处窗口，命中词用 `mark`（透明底 + 橙色下划线，不要浏览器默认黄底）。
  **查询词与正文都要 `fold()`**（`\u3000`→空格 + `toLowerCase`，**保长度** 所以下标能映射回原文）——只折叠一侧会让 `Fourier` 这类大写词永远搜不到（这个 bug 实际出现过，由桩化 DOM 测试抓到）。片段与高亮**只用 `createTextNode`**，不拼 `innerHTML`。中文输入法：`compositionstart` 期间不搜、`compositionend` 再搜。翻页键处理遇 `closest('[data-search]')` 直接返回（输入框里 `←/→` 是光标、`Home/End` 是行首行尾）。跳转复用 `openCard(id)`，完成后焦点交给卡片展开按钮。
  顶栏的裁剪要放在 `.deck`（`.chrome` 不能有 `overflow:hidden`），否则下拉结果会被裁掉。
  指示条 `.tabs__ind` 只动 `transform:translateX(calc(var(--tab,0) * 100%))`（等宽三段，`width:calc(100% / 3)`）；**不要给指示条写内联 `--tab`**——内联声明会压过从 `.tabs` 继承下来的值，指示条就不动了（这个坑实际踩过一次，由桩化 DOM 行为测试抓到）。切换入场只做 `opacity + translateY(12px→0)`（`.board.is-in` 的 `boardIn`，`.22s`）；**每块各自记 scrollTop**，切回来恢复上次读到的位置（首次为 0）。`openCard()`（地图节点 / 搜索跳转 / `#c3` 深链）要先切到卡片所在板块再展开+滚动。
- **动画只动 `opacity` 与 `transform: translateY`**，时长走 `--t-fast`(.22s) / `--t-swift`(.34s)，曲线 `--e-out cubic-bezier(.16,1,.3,1)`；**禁止 height/width 过渡**。
- **知识地图**：拖拽 1:1 跟手；松手短滑行（速度 px/s、衰减 `exp(-5dt)`、低于 45px/s 收手、上限 1400px/s、最后一个 move 超过 80ms 则不再甩）；`clampPan()` 保证内容拖不出视野（缩小时居中）；滚轮/双击缩放锚定光标；缩略图框出当前视野并可点击定位；hover 高亮邻居（其余压到 .32）；点击节点跳到对应卡并展开+闪烁。**指针捕获只在移动超过阈值后调用**（否则 `click` 落到容器，节点点不动）。
- **概念速览浮层**：逐层返回栈 + 焦点锁在浮层内 + 关闭恢复滚动位置与焦点。
- **`prefers-reduced-motion`**：用通配长属性规则（`*,*::before,*::after{transition-duration:.01s!important; animation-duration:.01s!important; …}`）一次清干净；JS 侧的定时收尾要留 `SETTLE` 兜底，不能只靠 `transitionend`。
- **主题开关**：顶栏右上角两个 `[data-theme-set]` 按钮（`aria-pressed`）；选中态由 `html[data-theme]` 驱动而**不是** `aria-pressed`，这样首屏记忆生效时不会先闪一下错的那个选中态（JS 只负责把 `aria-pressed` 同步过来）。

## 九、排版硬约束

- 正文 18px / 行高 1.78；`.prose` 等文本块 `max-width: var(--measure)`（36em ≈ 每行 36 字）。
- 公式独立居中（`.formula`），用**正文字族**（不再用等宽），字号 17.5px、上下留白 ≥ 1.5em，编号写 `.formula__no`（等宽 12px）。
- `<sub>/<sup>` 统一为不撑行高的写法：`line-height:0; font-size:.72em; position:relative; vertical-align:baseline;` + `top` 偏移，避免行距跳动。
- 标题与卡片名用 `--font-text`；数字、编号、出处行、图注用 `--font-mono`。

## 十、生成流程

1. 读三份输入，通读正文，列出定义、定理、命题、引理、例题、经典对象；**先按 `reference/teaching-contract.md` 写出 `<产物>_teaching.md`**（读者档位 + 分簇 + 每单元六必需字段），拆卡与写卡的文字都从它取——不要边写 HTML 边想怎么讲。
2. 拆卡：一个概念一张卡；证明跟定理卡走；结论性命题独立成定理卡。
3. 每张卡写“一句话摘要”+ 展开内容 + 出处；两层不许同义重复。
4. 画知识地图：按“基本对象 → 分析工具 → 结论”分层，节点 code（`C1`/`T1`/`E1`）与卡片 `id` 一一对应；关系只写材料里出现过的依赖。
5. 挑易错点（限制条件、反例、参数化差异、存在性前提），每条都要有材料依据。
6. 末页两段：**自测**＝正文关键陈述改写成问句，答案照材料写；**课本章末习题**＝题目照抄课本、一题一张卡，教材给了答案才做展开面板，没给就在静态答案行写 `[待补充]`（不推断）。
7. 统计元信息：知识点 = 概念 + 定理 + 例题卡数；定义/定理 = `DEF` / `THM` 卡数；预计复习 = 知识点 × 1.5 min + 自测题 × 1 min，向上取整到 5 min（估价，不是材料里的事实）。
8. 复制模板填内容，替换 `<title>`、chrome、元信息条、地图节点；核心概念的三个板块卡数写进 `.tabs__n`（板内卡片按 `DEF` / `THM` / `EX` 归到定义 / 定理 / 例子）。
   **有教学稿就别手抄教学层**：卡片里只写教材内容，再跑 `python -X utf8 scripts/inject_teaching.py '<产出.html>' --teaching '<产物>_teaching.md'` 机械填入（幂等：重复跑会先剥离旧教学层再重建；单元管多张卡时只落首卡）。手写与脚本二选一，手写的会被脚本覆盖。模板的卡片骨架**已内建教学层**（卡头 `.tk-q` 学习问题 → panel 内 直觉 `.tk-note` / 前置回放 `.is-recall` / 教材原文 `.tk-src` / 增补段 `.is-added` / 理解检查 `.tk-check` + 折叠答案 `.tk-ans`），照教学稿填空即可；教学稿缺哪块就整块删掉，不要留空壳。
9. **互引**：先按第五节拟别名表与守卫词，跑 `scripts/refs.py --file …` 审报告，逐条核对后再 `--apply`。
10. **插图**：按第六节委托 `dorothy-picture` 做全量可视化评估，拿回 `figs/fig-*.html` 片段后内联。
11. 跑自检（下节），改到 OK；浏览器里过一遍翻页、展开、地图拖拽、互引浮层。

## 十一、交付前自检

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'
& '<python>' -X utf8 'scripts/check_teaching.py' '<产物>_teaching.md' --html '<产出.html>' --plan '<产物>_figures-plan.md'
& '<python>' -X utf8 'scripts/check_note.py' '<产出.html>'
& '<python>' -X utf8 'scripts/refs.py' --file '<产出.html>'
```

`check_teaching.py` 检查教学稿是否满足契约：档位声明、分簇、每个单元的六必需字段（学习问题 / 正式 / 检查 / 图示任务 / 前置回放 / 来源；其中**前置回放是条件必需**——只写本章没有卡片的前提，本章已有卡可跳的写"无新增"）、“检查”必须带答案、“图示任务”二选一且不出图要带四维分数与理由、增补标记数与附表的 `我补了什么` 行数一致、无「更清晰/更美观/更直观/更易懂」、单元标题里的卡 id 与页面卡片双向对账、标“出图”的单元必须落在清单的出图名单里。教学层落进 HTML 的位置（哪个字段进卡头、哪个进 panel、增补段怎么标）见 `reference/teaching-contract.md` 第十节。

`check_note.py` 检查：颜色是否全部令牌化、令牌是否齐全、`@font-face` 是否只用 `local()`、圆角/阴影/emoji/外链、字族数量、五页结构与翻页器、`#core/#pitfalls/#quiz` 与地图、互引链接是否指向存在的 id 且不在 SVG 里、浮层是否具备 `role="dialog"` 与返回键、插图 `figure/figcaption/svg` 是否成对、过渡属性里有没有 height/width、字号行高与公式间距、深色块数量、每张卡是否带出处、习题卡（`.quiz--ex`）是否带题号且"没有展开按钮时必有静态答案行"、双主题（主题块只许覆盖不得新增令牌、所有 `var()` 可解析、装饰件 `aria-hidden`、主题过渡只放开那 6 个颜色属性）、分板块（**逐组**校验：tab 与 board 数量一致、每组 `aria-selected="true"` 只有一个、每组初始只有一块可见、`aria-controls`/`aria-labelledby` 都能解析、核心概念与末页都要有分段控件、`.stack` 不得嵌套 `.stack`、翻页快捷键有 tablist 守卫）、顶栏搜索（索引限定 `#p-core .card`、有结果面板与空结果的"未找到"提示、翻页快捷键有 `[data-search]` 守卫、片段走 `createTextNode`）；并统计卡片数、自测题数、课本章末习题数、互引数、`[待补充]` 处数。页面带教学层（`.tk-q`）时再核对：学习问题 / 理解检查 / 答案折叠三者数目一致、有教学层必有 `.tk-src` 原文分隔、增补段只用 `.is-added` 段落左线（正文不该出现「补」字标，出现即警告；附录页若存在则正文必须有对应增补段）。

再人工确认：

- [ ] 打开 3 秒内能看出本章最重要的内容
- [ ] 翻页顺滑，键盘与四路入口都能走；1200px 与 900px 下布局正常
- [ ] 同组内展开一个时其他自动收起；自测题可同时看多题答案
- [ ] 地图拖拽跟手、松手不飘、内容拖不出视野；点节点能跳到卡并展开
- [ ] 互引术语是橙色带下划线，点开后背景模糊、浮层内容完整、返回回到原位置
- [ ] 教学稿里所有「我补的」内容都标了来源、都能单独删掉（删掉后原文论述仍成立），且没有把补的直觉写成教材的结论
- [ ] 带教学层的页面：卡片收起时就看得到「学习问题」（否则读者没有展开的理由）；展开后直觉块与「教材原文」有明确分隔；增补段靠段落左线就能一眼分出、正文里没有「补」字样
- [ ] 插图数据与材料一致，示意参数与截断都写在图注里
- [ ] 材料缺的部分都写成 `[待补充]`，没有编造
- [ ] 顶栏主题开关能在孤星 ⇄ NASA-punk 间切换：颜色平滑过渡、进度条走满后淡出、切完不闪；刷新（或另开一章）后记得上次的选择，`file://` 下记忆不可用也不报错
- [ ] 核心概念默认停在「定义」板块；点/键盘切板块顺滑，切回来停在原来的阅读位置；地图点节点、`#c3` 深链都能自动切到正确板块并展开
- [ ] 末页默认停在「自测」；切到「章末习题」能看到 16 道题且只有题目与静态 `[待补充]`；两块各自的滚动位置互不干扰
- [ ] 顶栏搜索：中文与英文（含大写 `Fourier`）都能搜到；结果给标题 + 带 `<mark>` 的片段；点击跳到对应卡片并自动切板块；搜不到时有明确的空结果提示；输入框里 `←/→` 不翻页、中文输入法拼字不抖

## 十二、安装与位置

这是一个**全局 skill**，装在本机全局 skill 目录下（与 `lieflat-charts`、`archify` 同级）：

```
$HOME\.agents\skills\dorothy-html\
├── SKILL.md                     本文件
├── assets\note-template.html    单文件模板
├── reference\                   design-spec.md · content-mapping.md · teaching-contract.md
└── scripts\                     check_note.py · check_teaching.py · refs.py · build_template.py · inject_teaching.py · lib\teachlib.py
```

同步（工作区源码 → 全局安装）：

```powershell
Copy-Item -LiteralPath '<repo>\skills\dorothy-html' `
          -Destination "$HOME\.agents\skills\dorothy-html" -Recurse -Force
```

装好后在 `$HOME\.agents\skills-registry.md` 的 Skill 清单登记一行（名称 / 用途 / 安装位置 / 安装日期）。**新装的 skill 要重启会话才会进技能目录。** frontmatter 校验（`name` 必须与目录名一致；`description` 里若出现 ` #`，YAML 会当成注释把描述截断，必须加双引号）：

```powershell
& '<python>' -c "import re,yaml,pathlib; t=pathlib.Path(r'<skills>\dorothy-html\SKILL.md').read_text(encoding='utf-8'); m=yaml.safe_load(re.match(r'^---\r?\n(.*?)\r?\n---\r?\n',t,re.S).group(1)); print(m['name'], len(m['description']), '字符')"
```

