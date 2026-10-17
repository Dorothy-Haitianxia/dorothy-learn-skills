# Dorothy Skills

把课本的一章变成可读产物的两个 agent skill：**dorothy-html**（课本 → 单文件知识笔记 HTML）与 **dorothy-picture**（为这类页面画有教学任务的矢量插图）。

**English.** Two agent skills that turn a textbook chapter into something you can actually read. `dorothy-html` takes a chapter's Markdown (end-of-chapter exercises included) and emits a single self-contained HTML page — overview, a pan-and-zoom knowledge map, concept cards split into definitions / theorems / examples, common mistakes, and a quiz — with two runtime themes and a search over concept cards. `dorothy-picture` designs the figures that go inside such a page: an eight-stage pipeline running from "name the comprehension barrier" to a three-layer acceptance, emitting inline SVG whose colors come from the host page's CSS tokens, so every figure follows the theme for free. No frameworks, no build step, no network at runtime — the deliverable is a file, not a service.

**中文.** 两个 agent skill，把课本的一章变成真正能读的东西。`dorothy-html` 接收一章课本 Markdown（含章末习题），产出单文件、可直接双击打开的 HTML 知识笔记页——概览、可平移缩放的知识地图、按定义 / 定理 / 例子三分屏的概念卡、易错点、自测与习题，带双主题运行时切换与概念卡全局搜索。`dorothy-picture` 负责画这类页面里的插图：从「识别理解障碍」到「三层验收」的八阶段流程，输出内联 SVG，颜色只挂宿主页的 CSS 令牌，因此自动跟随主题；每张图先在离线复刻上核对数学，再渲染成 PNG 逐张过目。没有框架、没有构建步骤、运行时零网络请求——交付物是文件，不是服务。

## 仓库结构

| 路径 | 内容 |
|---|---|
| `skills/dorothy-html/` | 课本 → 单文件知识笔记 HTML。`SKILL.md`、模板 `assets/note-template.html`、`reference/`（设计规格、内容映射）、`scripts/`（自检 `check_note.py`、互引 `refs.py`、模板构建 `build_template.py`） |
| `skills/dorothy-picture/` | 教学制图，被 dorothy-html 内联。`SKILL.md`、`reference/`（评估、选图范例、视觉文法、交互图、规划契约）、`assets/`、`scripts/`（图型库 `lib/figlib.py`、渲染核对 `render_fig.js`、机械校验 `check_figure.py` / `check_plan.py`、JS 抽取 `extract_js.py`） |
| `beta/` | 第 8 章「概率论基础」试点：样式源 `_style.css` / `_app.js`、构建脚本 `_build.py`、插图片段 `figs/`、制图规划与成本清单。成品 HTML 与教材原文片段**不入库**（含第三方教材的逐句翻译正文，见 `.gitignore`），在本地用你自己的材料生成 |
| `参考教材 报告/` | 参考教材的图文设计分析，用来提炼选图与排版规则。**仅本地留存、不入库**（含第三方教材截图，见 `.gitignore`） |

## 安装

两个 skill 都是纯文件形式（`SKILL.md` + 参考文档 + 脚本），复制到 agent 的技能目录即可，没有编译与打包步骤。

### 1. 取到本地

```bash
git clone git@github.com:Dorothy-Haitianxia/dorothy-learn-skills.git
cd dorothy-learn-skills
```

### 2. 复制到技能目录

```bash
# macOS / Linux
mkdir -p ~/.agents/skills
cp -r skills/dorothy-html skills/dorothy-picture ~/.agents/skills/
```

```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force "$HOME\.agents\skills" | Out-Null
Copy-Item -Recurse -Force .\skills\dorothy-html, .\skills\dorothy-picture "$HOME\.agents\skills\"
```

目录名必须与 `SKILL.md` 里 frontmatter 的 `name` 一致（`dorothy-html` / `dorothy-picture`）。

### 3. 装渲染依赖（只有 dorothy-picture 需要）

`dorothy-picture` 的「渲染成 PNG 亲眼核对」这一步靠 `@resvg/resvg-js`——纯本地预编译包，不需要系统级图形库：

```bash
cd ~/.agents/skills/dorothy-picture
pnpm install --ignore-scripts
```

不做渲染核对也能用，`check_figure.py` 等校验脚本不依赖它。

### 4. 验证

```bash
# 模板回归（应输出 OK）
python skills/dorothy-html/scripts/check_note.py skills/dorothy-html/assets/note-template.html

# 脚本语法
python -c "import py_compile; py_compile.compile('skills/dorothy-picture/scripts/lib/figlib.py', doraise=True)"
node --check skills/dorothy-picture/scripts/render_fig.js
```

### 依赖一览

| 依赖 | 用在哪 | 是否必需 |
|---|---|---|
| Python 3.9+（只用标准库） | 全部校验与生成脚本 | 是 |
| Node.js + pnpm | `render_fig.js` 渲染 PNG 核对 | 仅在渲染核对时需要 |
| `@resvg/resvg-js` | 同上 | 随 `pnpm install` 安装 |

装好后**重启 agent 会话**，skill 才会出现在技能目录里。

---

# 知识笔记 HTML 生成 Skill（dorothy-html）

把一章课本正文（含课本章末习题）生成一份**单文件、可直接在浏览器打开**的知识笔记页：宽屏翻页式（章节概览 → 知识地图 → 核心概念 → 易错点 → 自测与习题），带可平移缩放的知识地图、前置概念互引浮层、按 lieflat 结构的辅助插图。

## 交付物

| 路径 | 说明 |
|---|---|
| `skills/dorothy-html/SKILL.md` | skill 本体：输入输出、五页结构、卡片字段、互引规则、插图规则、视觉与交互硬约束、生成流程、自检清单 |
| `skills/dorothy-html/assets/note-template.html` | 可运行模板（宽屏翻页版）：令牌化 CSS + 五页骨架 + 地图/浮层/插图示例 + 交互层 |
| `skills/dorothy-html/reference/design-spec.md` | 颜色令牌、**双主题（令牌键名契约、装饰件层、主题切换的唯一具名例外）**、橙色范围、深色块、字体与**数学兜底 `@font-face`**、排版尺度、动效词表、断点、可访问性 |
| `skills/dorothy-html/reference/content-mapping.md` | 输入 → 五页/卡片映射、**互引取词与守卫规则**、插图数据来源、统计口径、缺料写法 |
| `skills/dorothy-html/scripts/check_note.py` | 产物自检：令牌化、无圆角阴影 emoji 外链、五页与翻页器、互引链接、浮层结构、插图配对、动画属性、出处行 |
| `skills/dorothy-html/scripts/refs.py` | 互引引擎：别名表 + 左右守卫 + 偏移映射 + 行内标签边界扩展；`--file` 出审报告，`--apply` 写标记 |
| `skills/dorothy-html/scripts/figures.py` | 三张插图的生成器（B1 rung bars / B2 hairline line / B3 hairline area），改数据即可复用 |
| `skills/dorothy-html/scripts/build_template.py` | 模板构建脚本：把 beta 的样式与交互层搬进模板骨架 |
| `beta/ch08-概率论基础.html` | 第 8 章试点成品（**不入库**，本地生成）。含 §8.3 课本章末习题 8.1–8.16；课本未给解答 → 标 `[待补充]`） |
| `beta/_style.css` · `beta/_app.js` | 模板的唯一样式/交互源：`build_template.py` 把这两个文件原样写进模板（改样式改这里，不要直接改模板） |
| `beta/_exercises.html` | 课本章末 16 道习题的卡片片段（题目照抄正文，由 `_build.py` 拼进末页）；**含教材内容，不入库** |
| `beta/ch08-概率论基础_refs-review.md` | 该成品的 23 处互引清单（别名表、守卫表、每处上下文） |

## 页面内部结构（运行时）

| 控件 | 位置 | 行为 |
|---|---|---|
| 主题开关 | 顶栏右上角 `.chrome__tools` | 孤星 ⇄ NASA-punk；颜色 0.34s 交叉过渡（唯一的具名例外）+ 百分比进度条，`localStorage['dorothy:theme']` 记忆 |
| 核心概念分段控件 | `#p-core` 子标题 `.section__head` | 定义 / 定理 / 例子**三板块分屏**（默认定义，其余 `hidden`）；三段等宽、指示条只动 `transform:translateX(calc(var(--tab) * 100%))`；**每块各自记 scrollTop**；地图节点、`#c3` 卡片深链都会先切到卡片所在板块再展开+滚动 |
| 末页分段控件 | `#p-quiz` 子标题 | **两块**（自测 / 课本章末习题，`.tabs--two` 两格；默认自测）；与核心概念共用同一套 `showBoard()`，`data-board` 全局唯一（`self` / `exercise`） |
| 概念速览浮层 | `#refBox` | 橙色下划线术语点开前置概念；逐层返回栈；关闭回到原处并闪一下 |
| 全局搜索 | 顶栏右上角 | 只索引 `#p-core` 的卡片（剔除出处行）；多词 AND，权重 标题 3 > 摘要 2 > 正文 1；结果给语义标签 + 标题 + 带 `<mark>` 的匹配片段，点击跳转并自动切板块；中文输入法与 `←/→` 都做了处理 |

三段卡数写进 `.tabs__n`；`openCard(id)` 是地图 / 搜索 / 深链的共同入口，改跳转逻辑只改它。

## 全局安装（与本工作区源码同步）

这是一个**全局 skill**，装在 `$HOME\.agents\skills\dorothy-html\`（与 `lieflat-charts`、`archify` 同级），已在 `$HOME\.agents\skills-registry.md` 登记。

```powershell
# 工作区源码 → 全局安装
Copy-Item -LiteralPath '<repo>\skills\dorothy-html' `
          -Destination "$HOME\.agents\skills\dorothy-html" -Recurse -Force

# frontmatter 校验（name 必须与目录名一致）
& 'python' -c "import re,yaml,pathlib; t=pathlib.Path(r'<skills>\dorothy-html\SKILL.md').read_text(encoding='utf-8'); m=yaml.safe_load(re.match(r'^---\r?\n(.*?)\r?\n---\r?\n',t,re.S).group(1)); print(m['name'], len(m['description']), '字符')"
```

**注意**：`description` 里若出现 ` #`（空格 + 井号），YAML 会当成注释把描述截断——写 frontmatter 时给它加双引号。这个坑实际踩过一次（描述只剩 29 个字符）。

## 用法

1. 给出：该章课本正文 Markdown（课本章末习题通常就在正文末尾，随正文一起给）。本 skill 只处理课本材料，不接收笔记类输入。
2. 产出 `chXX-章节名.html`。
3. 自检与互引审核：

```powershell
$env:PYTHONUTF8='1'; $env:PYTHONIOENCODING='utf-8'
$py = 'python'
$sk = "$HOME\.agents\skills\dorothy-html"      # 或工作区源码 skills\dorothy-html
& $py -X utf8 "$sk\scripts\check_note.py" '<产出.html>'
& $py -X utf8 "$sk\scripts\refs.py" --file '<产出.html>'          # 先审
& $py -X utf8 "$sk\scripts\refs.py" --file '<产出.html>' --apply --out '<产出-marked.html>'
```

## 成品自检结果（ch08）

```
check_note.py   → OK   知识卡 33 张 / 自测题 10 道 / 课本章末习题 16 道 / 出处行 59 / 板块 5 个（2 组分段控件）/ 语义标签 DEF×11 ERR×7 EX×5 THM×10
refs.py         → 会标出 23 处；同卡重复不标 23 处；被守卫拦下 0 处
frontmatter     → name=dorothy-html，description 完整（PyYAML 一行校验，见下）
```

## 双主题：孤星 ⇄ NASA-punk（运行时切换）

NASA-punk 已经**收进基础样式**、变成第二套令牌，不再是单独的构建变体：同一份 HTML 里两套主题，顶栏右上角切换，不重出文件。

| 位置 | 内容 |
|---|---|
| `beta/_style.css` 的 `:root[data-theme="nasapunk"]{}` | NASA-punk 的令牌块（设备白 `#ECE5D6`、身份四色 `#4C5A68 #7A7F4E #D2A85E #A8432F`、唯一鲜色 `#D63A2C`）+ 机身线条：彩条、警示斜纹、接缝铆钉、角螺丝、卡片双细线、痕迹覆盖层 |
| `beta/_style.css` 的 `.np-chrome` | 装饰件常驻 DOM：孤星下 `display:none`（不占排布），NASA-punk 下 `display:contents` 并按 34ms 级联淡入 |
| `beta/_app.js` 的主题模块 | `setTheme()`：加 `.is-theming` → 强制重排 → 换 `data-theme` → rAF 驱动百分比进度条 → 驻留 240ms 后淡出；`localStorage['dorothy:theme']` 记忆，`try/catch` 兜底 |

**只改线条与配色**：主题块里没有任何 `font-family / font-size / letter-spacing / text-transform / font-style / line-height` 覆盖，字体沿用基础样式（Times New Roman + 霞鹜文楷 + NoteMath + Consolas）。回归验证：切换前的 NASA-punk 单主题产物与当前双主题产物的「核心概念 + 易错点」区段**逐字相同**（113506 字符），3 张插图与知识地图 SVG 也逐字相同。

**令牌键名两套齐全**：主题块只许覆盖、不许新增键 —— NASA-punk 专用令牌（`--red` / `--s1..--s4` / `--rivet` / `--wear-*`）在基础 `:root` 里也留占位值，否则切回孤星会缺声明。`check_note.py` 会断言这一点。

> 历史留档（已从仓库移除）：`beta/_skin-nasapunk.*` 与 `beta/ch08-概率论基础-nasapunk.html` 是**运行时切换之前**的单主题产物，已被上面这套取代。


