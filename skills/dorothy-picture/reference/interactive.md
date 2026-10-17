# 交互图（HTML 相对 PDF 的优势）

平面静止图是默认；当内容本身是**随参数变化、随机、可迭代、可穷举**的时候，交互能提供 PDF 给不了的东西。参考范式：setosa.io/ev（可读源码，几何写在代码里）。

## 一、什么时候值得做交互

| 内容特征 | 静态图做不到的 | 手法 |
|---|---|---|
| 随机性、收敛、大数定律 | 随机与收敛过程无法呈现 | **抽样迭代**：按钮触发 + 累积绘制 + 实时统计 |
| 含参公式、曲线族 | 读者不能穷举参数 | **参数滑块**：`input[type=range]` + 重绘 |
| 证明步骤、构造过程 | 信息只能一次给全 | **分步揭示**：按钮推进，前步保留降权 |
| 自由变量、「自己找一个解」 | 读者是被动读者 | **拖拽对象**：`pointermove` |
| 表 ↔ 图 ↔ 式的对应 | 跨表征对照要来回翻页 | **联动高亮**：hover / click 同步 |
| 同一对象的多重读法 | 只能并列印两遍 | **状态切换**：tab / toggle |

**判断标准**：如果读者必须「试几次」「调一调」「自己走一步」才能真正理解，就值得做交互；否则静态图更诚实。

## 二、四条硬约束（实测，不是理论）

1. **图必须以内联 SVG 为主体** —— `check_figure.py` 要求 figure 里有 `<svg>`，所以 **canvas 不能用**；
2. **内联 `<script>` 允许**（checker 只拦带 `src` 的外链），但代码里**不能出现任何外链字面量**：`createElementNS` 要复用已有元素的 `SVG.namespaceURI`，不要写 `http://www.w3.org/2000/svg`；
3. **过渡只动 `opacity` / `transform`**，不许动 `height` / `width`；要改几何就直接改 SVG 属性（不走 CSS 过渡）；
4. **控件用 `class="fig__ctl"`**（已登记样式），按钮一律 `<button type="button">`；不要新增未登记的类名。

## 三、设计原则：静态可读、动态增强

**首帧必须带完整几何**，JS 只是加料。三条理由：

- `render_fig.js` 只能渲**静态首帧**，动态行为渲不出来；
- 打印、无脚本环境、读屏用户都要能读；
- `prefers-reduced-motion` 下不能只剩一个空框。

## 四、验收：三层之外加一层「运行时」

| 层 | 怎么验 | 谁做 |
|---|---|---|
| 数学正确性 | **离线复刻**：把片段里的抽样 / 迭代逻辑用 Python 重写，跑大样本核对数值（例：Bertrand 三种模型各抽 20 万次 → 0.3336 / 0.4998 / 0.2498，对上 1/3、1/2、1/4） | 我 |
| **语法**（可机械） | `extract_js.py` 抽出内联脚本 → `node --check` 验语法；再用 `check_figure.py` 拦字面转义残留（`\n` `\t` `\r`） | 我 |
| 视觉表达 | `render_fig.js` 渲首帧 + 亲眼看 | 我 |
| 教学有效性 | 只看首帧能不能独立读懂这张图 | 我 |
| **运行时** | 真的点一遍：弦是否累积、颜色是否正确、数字是否收敛、主题切换后是否跟随 | **只能人工** |

`check_note.py` 与 `check_figure.py` **管不到运行时**，所以交付动态图时必须在正文或清单里列出「请点这几下」的清单。

## 五、最小代码骨架

```html
<figure class="fig" id="fig-N-slug">
  <svg id="figNSvg" viewBox="0 0 660 320" role="img" aria-label="（首帧就该讲清楚这张图在讲什么）">
    <title>…</title>
    <!-- 首帧几何：所有关键元素都在 -->
  </svg>
  <div class="fig__legend">…</div>
  <div class="fig__ctl" data-ctl="slug">
    <button type="button" data-act="one">抽 1 条</button>
    <button type="button" data-act="fifty">抽 50 条</button>
    <button type="button" data-act="reset">重置</button>
    <span data-hint>（一句话说明这些按钮在演示什么）</span>
  </div>
  <figcaption>图 N · …（正文 §X.Y）</figcaption>
  <script>
(function () {
  var SVG = document.getElementById("figNSvg");
  if (!SVG) return;
  function el(name, attrs) {
    var e = document.createElementNS(SVG.namespaceURI, name);   // 注意：不写 http 字面量
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  // …只操作 SVG 属性与 textContent；过渡只动 opacity / transform
})();
</script>
</figure>
```

## 六、反面清单

- **不为装饰加交互**：元素背后没有真实对象（纯肌理）时，加 hover 是欺骗；
- **不把关键信息藏在交互后面**：首帧必须能独立读懂，交互只提供「更多次、更多参数、更多步」；
- **不用 canvas**（违反内联 SVG 要求）；
- **不引入任何库**（d3 / ECharts 一律不行）：单文件离线是硬约束，几何自己算；
- **不写无限循环动画**：迭代必须由用户触发，或遵循 `prefers-reduced-motion`。

## 七、已知的可用范例

- `fig-8-bertrand-live`（ch08）：三个圆并排，同一句「随机取弦」，随机分别加在端点 / 直径中点 / 圆内中点上；按钮抽样、累积绘制、实时给出比例。
  - 首帧：三条示例弦 + 临界圆；
  - 运行时验收：请点「抽 1 条」看单次、「抽 50 条」看比例收敛、「重置」清空；
  - 数学层已离线复刻验证（见第四节表格）。
