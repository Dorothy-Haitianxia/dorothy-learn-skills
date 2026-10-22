# dorothy-picture 交接文档

> **给谁**：接手「教材配图」方向、准备把它做成独立 skill 的人。
> **一句话结论**：现在**不要**分仓，先按「可拆结构」整理（第 8 节有判据）。分仓的成本不在搬代码，在于接口还在动。

---

## 1. 这个 skill 在做什么

给教材段落画**有教学任务**的矢量图。它不美化页面。

流程强制先写「读者会卡在哪」，再决定画什么；对不画的地方也要留理由。一条被反复验证的判断：**一张图要么替读者完成一次推理，要么就不该存在。**

产出形态是 `<figure class="fig">` 内联 SVG 片段。图内不写颜色字面量，只挂语义类（`f-line` / `f-box` / `f-band` …），色值由宿主页的 CSS 令牌给。因此同一张图在「孤星」（暖白纸 #F5F3EE + 加灰橙 #C0633F）和「NASA-punk」（设备白 #ECE5D6 + 军绿蓝灰）两套主题下自动换色，零额外代码。

## 2. 现在真能做到什么

八阶段：提取知识点 → 识别理解障碍 → 四维打分（任一维 = 2 或总分 ≥ 4 才制图）→ 七问闸门 → 11 字段决策卡与编排 → 规格检查 → 实现 → 三层验收。

已实现并经过实际渲染核对（不是「理论上支持」）的入口：

| 类别 | 入口函数 | 用途 |
|---|---|---|
| 结构关系 | `objmap` | 左对象 →（若干映射）→ 右对象，支持一对多 |
| 分层依赖 | `depgraph` | 按层排布的有向依赖图，边上可带关系名 |
| 区间事件 | `axis` | 数轴 + 区间带 + 标记点，用于「概率对应哪一段」 |
| 过程阶段 | `stages` | 编号步骤 + 箭头，用于「分几步」讲不清的地方 |
| 证明流程 | `proof` | 每步右侧带「依据」列（定义 8.3 / Fubini / X ≥ 0） |
| 对照反例 | `compare` | 左右两栏同构对比，差异行用强调框 |
| 几何直觉 | `gcircle` `garc` `gchord` `gpoly` `ghline` | 圆 / 弧 / 弦 / 正多边形 / 弦心距 |
| 复合几何 | `chord_models` | 同一事件在三种随机模型下的三格并置 |
| 数据分布 | `bertrand_area` `poisson_bars` `memoryless_line` | 密度曲线 / 柱状 / 指数尾 |
| 复合分布 | `marginal_joint_pair` `cdf_jumps` | 边缘相同联合不同 / 阶梯与原子 |
| 推前测度 | `pushforward_pair` | 原像（可多块）与目标集合的对应 |

底层原语：`el` `txt` `path` `line` `dot` `box` `head_arrow` `wrap` `esc` `fmt` `rnd`。写新图型基本都用它们，不要直接拼字符串（转义和 aria 会漏）。

## 3. 文件盘点

受控文件 15 个，按**改动频率**排序 —— 越靠前越是你日常要动的：

| 文件 | 行数 | 职责 | 改动频率 |
|---|---|---|---|
| `scripts/lib/figlib.py` | 1010 | 图型库：原语 + 布局 + 全部图型入口 | 每次加图 |
| `SKILL.md` | 261 | 八阶段流程、四维打分、七问闸门、硬约束、自检清单 | 流程变动时 |
| `reference/visual-grammar.md` | 195 | 视觉文法：线宽层级、字号、留白、注记规则 | 少改 |
| `scripts/check_plan.py` | 161 | 规划清单的机械校验（打分 / 11 字段 / 编排 / 替代文本 / 状态机 / 锚点） | 契约变动时 |
| `reference/plan-contract.md` | 158 | 规划清单的格式定义 | 与上一行同步 |
| `reference/assessment.md` | 154 | 六类障碍 → 图型对照、四维打分细则 | 少改 |
| `reference/selection-samples.md` | 149 | 选图范例（来自 VGT 教材的 6 张原图分析） | 少改 |
| `scripts/render_fig.js` | 191 | 渲 PNG：抽令牌 → 剥 `.fig` 前缀 → 解析 `var()` → 交 resvg | 少改 |
| `scripts/check_figure.py` | 127 | 单张片段校验（可访问性 / 图注 / 色字面量 / 字号 / 类名白名单） | 加新类时两处改 |
| `reference/interactive.md` | 89 | 交互图手法、四条硬约束、四层验收 | 少改 |
| `scripts/extract_js.py` | 16 | 抽出内联脚本交给 `node --check` | 几乎不改 |
| `assets/figure-plan-template.md` | — | 规划清单模板 | 少改 |
| `assets/figure-scaffold.html` | — | 图片段骨架 | 少改 |
| `package.json` / `pnpm-lock.yaml` | — | 只锁 `@resvg/resvg-js` | 几乎不改 |

## 4. 架构：figlib.py 是三段拼接，而且有整段重复

文件由三次追加拼成：part1（原 dorothy-html 的三张数据图 + 原语）→ part2（六类障碍图型）→ geo（几何图元 + 复合图型）。三段各自定义了同名的 `esc` / `wrap` / `box` / `head_arrow`。

**实测**：part1 的定义占 309–540 行，part2 从 544 行起把同一批函数（`esc` `wrap` `box` `head_arrow` `objmap` `axis` `stages` `proof` `compare` `depgraph`）**逐字重抄了一遍**，约 230 行冗余。Python 后定义覆盖前定义，所以运行正常 —— 这是个「看不出问题」的债，但它是接手后第一个该清的。

清理方法：删掉 309–540 那一段，只留 part2 的版本；或反过来，看哪一份更新。**清完必须重跑第 9 节的渲染命令逐图比对**，因为覆盖方向一改，行为可能变。

## 5. 与宿主页的接口（三条，都是双向的）

这三条决定了「独立」能做到什么程度。

**① 规划清单** `<产物>_figures-plan.md`

- 内容：逐知识点的四维打分、出图 / 不出图理由、11 字段决策卡（对应知识点 / 打分 / 理解障碍 / 教学任务 / 插入位置 / 编排 / 视觉顺序 / 图文对应 / 图后解释 / 理解检查 / 替代文本）、三层验收记录
- 状态机：未开始 → 已生成 → 已渲染核对 → 已内联 → 已弃用。**只有到「已渲染核对」才允许内联**
- 宿主侧消费：dorothy-html 的 `check_note.py --plan` 校验「正文里的图数 = 图后检查数」、锚点能定位、卡片 id 对账

**② 图片段** `figs/fig-*.html`

- 结构：`<figure class="fig" id="fig-5-chord">` + `<title>` + `role="img"` + 非空 `aria-label`（不许以「图片」「示意图」开头）+ `<figcaption>图 N · 描述（正文 §8.1.2）</figcaption>`
- 宿主侧消费：dorothy-html 的 `_build.py` 按锚点注入，图号由宿主改（所以片段里的图号是占位）

**③ 语义类名**

- 目前图内类名是**闭集**，白名单硬编码在 `check_figure.py` 的 `STROKE_CLASSES` / `FILL_CLASSES` / `TEXT_CLASSES`（20 余个）
- 新增类要改两处：宿主 `design-spec.md` 第十二节登记（基础 `:root` 一条 + NASA-punk 一条），再把类名加进白名单
- **这是独立性最大的障碍**：类名与样式现在归 dorothy-html 管

## 6. 已经踩过的坑（不写下来会重踩）

1. **`@resvg/resvg-js` 要另装平台包**。只装主包时 require 报 `Cannot find module '@resvg/resvg-js-win32-x64-msvc'`。用 `pnpm install --ignore-scripts` 装，平台包会自动带上。
2. **CSS 规则拼接多一个 `}` 会毁掉整张图**。`extractRules` 已经收过尾，后续 map 又加一次，形成 `}}` → usvg 的 CSS 解析器直接放弃其后的规则 → 所有 `f-*` 的 stroke 失效，图看着「少了一半东西」。浏览器完全正常，**只有渲成 PNG 亲眼看才能发现**。
3. **静态渲染必须排除 `.panel.is-in` 入场动画**，否则渲出来停在第 0 帧（`opacity:0`），整张图空白。
4. **字面反斜杠加 n 是致命坑**。拼片段时若写成 Python 的转义写法（得到反斜杠与 n 两个字符），页面会把这些字符原样显示，且 `<script>` 末尾的它 在 JS 里是非法 token → 整段脚本语法错误 → 滑块全失效。`render_fig.js` 只抽 `<svg>` 渲染，抓不到这类问题 —— 因此才补了 `extract_js.py` + `node --check`，以及 `check_figure` 里的转义残留正则拦截。
5. **SVG 的 y 轴向下**。画 `y = x` 对角线时第一版画成了「左上 → 右下」，数学上是反的。凡是数学坐标映射到屏幕坐标，先写一行注释确认方向。
6. **`compare()` 的 viewBox 高度不能写死**。写死 300 会裁掉第 4、5 行注记，改成按行数算：`top + len(rows)*(BH+gap) + (30 if note else 10)`。
7. **pencil（.pen）不能用作交付路径**。`export_nodes` 不支持 svg（只 png / jpeg / webp / pdf）、`get_screenshot` 把中文渲成豆腐块、沙箱里插件根本起不来（`spawn` 用 pipe stdio 被禁）。.pen 只能当人工微调通道。
8. **字形回退是渲染器差异，不是 bug**。`ℙ_X` 在 resvg 里被回退字体画成单线 `P_X`（同页 `(Ω, 𝒜, ℙ)` 的 ℙ 却正常），浏览器不受影响。验收时别把它当错误去修。

## 7. 已知缺口（按优先级）

**P0 — 阻碍「独立」**

- **没有宿主令牌兜底**：现在图必须挂在 dorothy-html 的样式表上才（以正确颜色）渲出来。要独立，得自带一份最小令牌集（可在 `render_fig.js` 里内置默认值），否则它只是「别人的插件」而不是 skill。

**P1 — 内部质量**

- `figlib.py` 230 行重复定义（第 4 节）
- 图型函数**没有任何单元测试**。目前的正确性保证是「渲成 PNG 肉眼看」，这不可扩展：改一个原语，要重看 8 张图
- 类名白名单与 `design-spec.md` 两处维护，容易漂

**P2 — 文档漂移**

- `SKILL.md` 第 85 行写「五类图型」（结构 / 几何 / 证明 / 对照 / 数据），但库里实际是六类（多一个「过程阶段」）+ 4 个复合图型
- `plan-contract.md` 的 11 字段与 `check_plan.py` 的 `FIELDS` 列表各写一遍（字段只是清单格式，不是校验逻辑；改字段要两处同时改）
- 宿主侧 `dorothy-html/SKILL.md` 仍有 3 处指向已删除的 `scripts/figures.py`（第 184、220 行）和 `design-spec.md` 第 111 行

**P3 — 无法自动化的**

- 第四层验收（交互图运行时行为）只能人工拖一遍。自动化测不了 DOM 事件之后的视觉状态
- 「教学有效性」这一层的判断本质主观，只能靠「图后检查题能答对」间接验证

## 8. 拆仓判断：现在别拆，但要按可拆结构整理

**为什么现在不拆**

1. **接口还在动**。上面三条接口（第 5 节）没有一条冻结。跨仓改接口 = 两个 PR + 版本对齐；同仓改接口 = 一次提交。
2. **令牌策略是为 dorothy-html 设计的**。图内只挂语义类、色值由宿主给 —— 这个决定让图「免费跟随主题」，但也让图离开宿主就不能看。真要独立，第一步不是搬代码，是**补宿主令牌兜底**（第 7 节 P0），而这件事需要两边同时在场才能判断兜底值取得对不对。
3. **现在拆会得到两个都要改的半成品**。dorothy-html 侧还有 3 处文档指向已删文件，dorothy-picture 侧还有 230 行重复 —— 这些债在同一个仓库里清最便宜。

**什么时候该拆（三条判据，满足其一）**

- 出现**第二个宿主**：Markdown 文档、幻灯片、Obsidian 笔记也需要它配图。这时它需要自己的版本号与渲染矩阵
- 需要**独立发布节奏**：外面有人只用 dorothy-picture 不用 dorothy-html
- 需要**独立 issue / CI**：图型库要跑视觉回归测试时

**拆分路线（三步，前两步在现仓就能做）**

1. **解耦**：内置宿主令牌兜底 + 建一个不依赖 dorothy-html 的 demo（`examples/` 里一份自包含 html）+ 清掉 figlib 重复段
2. **固化契约**：把第 5 节三条写成 `reference/host-contract.md`，两侧文档都引用它，而不是互相引用对方的文件
3. **搬迁**：`git filter-repo --path skills/dorothy-picture` 一条命令把目录连同历史带走；本仓库留一个 submodule 或在 README 里指回新仓库

## 9. 接手第一天

```bash
git clone git@github.com:Dorothy-Haitianxia/dorothy-learn-skills.git
cd dorothy-learn-skills/skills/dorothy-picture
pnpm install --ignore-scripts     # 装 @resvg/resvg-js 与平台包
node -e "console.log(typeof require('@resvg/resvg-js').Resvg)"   # 应输出 function

# 用现成的 8 个片段做一次渲染回归（片段在 repo 根的 beta/figs/）
node scripts/render_fig.js --figure ../../beta/figs/fig-5-chord.html --css ../../beta/_style.css --out out-chord.png

# 换主题再渲一次，确认令牌生效
node scripts/render_fig.js --figure ../../beta/figs/fig-5-chord.html --css ../../beta/_style.css --theme nasapunk --out out-chord-nasa.png

# 校验片段
python scripts/check_figure.py ../../beta/figs/*.html
```

看到 `out-chord*.png` 里两条密度曲线、竖线、色带都在（不是只剩圆点和文字），说明环境是对的 —— 只剩圆点与文字就是第 6 节第 2 条的 CSS 拼接 bug 复现。

---

**最后一句**：这个 skill 的真正资产不是 `figlib.py` 那一千行，是 `SKILL.md` 和 `reference/assessment.md` 里那套「先认障碍、再打分、再闸门」的决策流程。图型函数换成任何绘图库都能替，流程丢了就退回「配图美化」。
