# -*- coding: utf-8 -*-
"""dorothy-picture · 图型库

只挂语义类，不写颜色：颜色与线宽由宿主页样式表按令牌给（见 SKILL.md 第五节）。
每个 fig_* 函数返回完整的 <figure class="fig"> 片段。

数据图型（改数据即可复用）：
  · B3 hairline area  → bertrand_area()     两条密度 + 尾面积
  · B1 rung bars      → poisson_bars()      1 档 = 1%，虚线 = 极限
  · B2 hairline line  → memoryless_line()   日历地板 + 发丝折线 + 关键点

结构图型（六类理解障碍 A–F）：
  · A 对象与结构 → objmap()    左右两列对象框 + 关系箭头
  · B 空间与几何 → axis()      数轴 + 区间带 + 标注点
  · C 过程与变化 → stages()    阶段框 + 阶段箭头 + 编号
  · D 推理与证明 → proof()     编号步骤 + 依据 + 依赖箭头
  · E 概念辨析   → compare()   左右同构两栏 + 差异标记
  · F 知识关联   → depgraph()  分层节点 + 有向边

新增语义类（f-box / f-box--acc / f-band / f-link）需在 dorothy-html 的
reference/design-spec.md 里登记对应样式。
"""
import math

# lieflat 的确定性伪随机（mono-tokens.js 的 rnd）
def rnd(i, k):
    return abs(((i * 73856093) ^ (k * 19349663)) % 1000) / 1000


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def el(tag, attrs, text=None):
    a = ' '.join('%s="%s"' % (k, v) for k, v in attrs.items() if v is not None)
    if text is None:
        return '<%s %s/>' % (tag, a)
    return '<%s %s>%s</%s>' % (tag, a, esc(text), tag)


def txt(x, y, s, cls='t-lab', anchor='middle', size=None, delay=None, extra=None):
    attrs = {'x': fmt(x), 'y': fmt(y), 'class': cls + ' f-fade', 'text-anchor': anchor}
    if size:
        attrs['font-size'] = size
    if delay is not None:
        attrs['style'] = 'animation-delay:%ss' % delay
    if extra:
        attrs.update(extra)
    return el('text', attrs, s)


def fmt(v):
    return ('%.2f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else str(v)


def path(d, cls='f-line', delay=None, path_len=True, extra=None):
    attrs = {'d': d, 'class': cls, 'fill': 'none'}
    if path_len:
        attrs['pathLength'] = '1'
    if delay is not None:
        attrs['style'] = 'animation-delay:%ss' % delay
    if extra:
        attrs.update(extra)
    return el('path', attrs)


def line(x1, y1, x2, y2, cls='f-rail', delay=None, extra=None):
    attrs = {'x1': fmt(x1), 'y1': fmt(y1), 'x2': fmt(x2), 'y2': fmt(y2),
             'class': cls + ' f-fade'}
    if delay is not None:
        attrs['style'] = 'animation-delay:%ss' % delay
    if extra:
        attrs.update(extra)
    return el('line', attrs)


def dot(cx, cy, r, cls='f-dot', delay=None, tip=None):
    attrs = {'cx': fmt(cx), 'cy': fmt(cy), 'r': fmt(r), 'class': cls}
    if delay is not None:
        attrs['style'] = 'animation-delay:%ss' % delay
    inner = el('title', {}, tip) if tip else ''
    return '<circle %s>%s</circle>' % (
        ' '.join('%s="%s"' % (k, v) for k, v in attrs.items()), inner)


def wrap(fig_id, view, body, caption, legend):
    return ('<figure class="fig" id="%s">\n'
            '            <svg viewBox="%s" role="img" aria-label="%s">%s</svg>\n'
            '            <div class="fig__legend">%s</div>\n'
            '            <figcaption>%s</figcaption>\n'
            '          </figure>' % (
                fig_id, view, esc(caption), body, legend, esc(caption)))


# ══════════════════════════════════════════════════════════════
# B3 · hairline area → Bertrand 悖论的两条密度
# ══════════════════════════════════════════════════════════════
def bertrand_area():
    X0, X1, BASE, TOP = 76.0, 604.0, 246.0, 44.0
    YMAX = 1.10
    XS = lambda xv: X0 + xv / 2.0 * (X1 - X0)
    YS = lambda p: BASE - p / YMAX * (BASE - TOP)

    p_of = lambda xv: (1.0 / math.pi) / math.sqrt(1 - xv * xv / 4.0) if xv < 2 else float('inf')
    q_of = lambda xv: 0.5 * xv
    XCUT = 1.915                       # p 在这一点出图（p ≈ 1.105）
    root3 = math.sqrt(3.0)

    g = []
    # 网格与坐标轴
    for pv in (0.5, 1.0):
        g.append(line(X0, YS(pv), X1, YS(pv), 'f-grid'))
        g.append(txt(X0 - 8, YS(pv) + 4, fmt(pv), 't-lab', 'end', 11))
    g.append(line(X0, BASE, X1, BASE, 'f-axis'))
    g.append(txt(X0 - 8, BASE + 4, '0', 't-lab', 'end', 11))
    g.append(txt(X1 + 6, BASE + 4, 'x', 't-lab', 'start', 11))
    g.append(txt(X0 - 8, TOP + 2, '密度', 't-lab', 'end', 11))

    # √3 阈值
    g.append(line(XS(root3), TOP, XS(root3), BASE, 'f-rule-dash'))
    g.append(txt(XS(root3), TOP - 6, 'x = √3 ≈ 1.732', 't-num', 'middle', 11.5))

    # q：弦心随机 —— 尾部的发丝（一片 = 一个 x 切片）
    xv = root3
    i = 0
    while xv <= 2.0001:
        g.append(line(XS(xv), BASE, XS(xv), YS(q_of(xv)), 'f-hair', min(i * 0.006, 0.3)))
        xv += 0.01
        i += 1
    # p：端点随机
    xv = root3
    i = 0
    while xv <= XCUT:
        g.append(line(XS(xv), BASE, XS(xv), YS(p_of(xv)), 'f-hair f-hair--acc', min(i * 0.006, 0.3)))
        xv += 0.01
        i += 1

    # 轮廓线（draw）
    pts_q = ['%.1f %.1f' % (XS(x / 200.0 * 2), YS(q_of(x / 200.0 * 2))) for x in range(0, 201)]
    g.append(path('M' + ' L '.join(pts_q), 'f-line f-line--acc-dash', 0.15, path_len=False))
    pts_p = []
    xv = 0.0
    while xv <= XCUT:
        pts_p.append('%.1f %.1f' % (XS(xv), YS(p_of(xv))))
        xv += 0.005
    g.append(path('M' + ' L '.join(pts_p), 'f-line f-line--acc', 0.1))

    # 出图标记（诚实标注截断）
    g.append(el('polygon', {'points': '%s,%s %s,%s %s,%s' % (
        XS(XCUT), YS(1.105), XS(XCUT) - 5, YS(1.105) + 9, XS(XCUT) + 5, YS(1.105) + 9),
        'class': 'f-arrow'}))
    g.append(txt(XS(XCUT), TOP - 22, 'p → ∞（x → 2⁻）', 't-note', 'middle'))

    # 关键读数
    g.append(dot(XS(XCUT), YS(1.105), 3.4, 'f-dot f-dot--acc', 0.5, 'p 在 x → 2⁻ 处发散，曲线在 x = 1.915 处出图'))
    g.append(txt(XS(1.35), YS(p_of(1.35)) - 10, 'p(x) 端点随机', 't-num t-halo', 'middle', 12.5, 0.7))
    g.append(txt(XS(1.55), YS(q_of(1.55)) + 20, 'q(x) 弦心随机', 't-num t-halo', 'middle', 12.5, 0.8))

    # x 刻度
    for xv, lab in ((0, '0'), (1.0, '1'), (2.0, '2')):
        g.append(line(XS(xv), BASE, XS(xv), BASE + 5, 'f-axis'))
        g.append(txt(XS(xv), BASE + 18, lab, 't-lab', 'middle', 11))

    g.append(txt(320, 288, 'ONE HAIRLINE = ONE X-SLICE · SHADED TAIL = P(X ≥ √3)',
                 't-note', 'middle', None, 0.9))
    legend = ('<span><i class="sw sw--acc"></i>p(x)：尾面积 1/3</span>'
              '<span><i class="sw sw--ink"></i>q(x)：尾面积 1/4</span>')
    caption = '图 1 · Bertrand 悖论：两种“随机投弦”给出的密度与尾概率（正文 §8.1.4）'
    return wrap('fig-bertrand', '0 0 640 300', ''.join(g), caption, legend)


# ══════════════════════════════════════════════════════════════
# B1 · rung bars → Poisson 的二项逼近（1 档 = 1%）
# ══════════════════════════════════════════════════════════════
def _binom(n, k, p):
    if k > n:
        return 0.0
    return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def _poisson(lam, k):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def poisson_bars():
    LAM = 2.0
    KS = list(range(8))
    panels = [(5, 0.4, 'n = 5'), (20, 0.1, 'n = 20'), (100, 0.02, 'n = 100')]
    limit = [_poisson(LAM, k) for k in KS]

    BASE, RUNG, HW = 246.0, 5.0, 7.0
    H = lambda v: v * 100 * RUNG          # 概率 → 用户坐标高度（1 档 = 1%）
    g = []
    for pi, (n, p, title) in enumerate(panels):
        left = 26.0 + pi * 205.0
        g.append(line(left, BASE, left + 182, BASE, 'f-axis'))
        g.append(txt(left, 40, title, 't-num', 'start', 12.5))
        g.append(txt(left, 56, 'p = %s' % fmt(p), 't-lab', 'start', 11))
        for j, k in enumerate(KS):
            bx = left + 16 + j * 21.0
            v = _binom(n, k, p)
            rungs = int(round(v * 100))
            for r in range(rungs):
                y = BASE - r * RUNG
                w = HW - 1.2 + rnd(r + 1, j + 2) * 2.4
                delay = min(pi * 0.08 + r * 0.012, 0.55)
                g.append(line(bx - w, y, bx + w, y, 'f-rung', delay))
                if r % 5 == 4:
                    g.append(dot(bx + HW + 3.5, y, 0.9, 'f-tick', delay))
            # 标签隔一根标一根，21 单位的间距下才不会并排撞在一起
            if j % 2 == 0:
                if rungs:
                    ly = BASE - (rungs - 1) * RUNG - 8
                    g.append(txt(bx, ly, '%.1f' % (v * 100),
                                 't-num t-halo', 'middle', 11, min(0.4 + pi * 0.08, 0.8)))
                else:
                    g.append(txt(bx, BASE - 8, '0', 't-lab', 'middle', 11,
                                 min(0.4 + pi * 0.08, 0.8)))
            # Poisson 极限：虚线横档 + 空心点
            lim = limit[k]
            if lim > 0.005:
                ly = BASE - H(lim)
                g.append(line(bx - HW - 3, ly, bx + HW + 3, ly, 'f-rule-dash-sm',
                              min(0.6 + pi * 0.08, 1.0)))
                g.append(dot(bx - HW - 6, ly, 2.0, 'f-dot-hollow', min(0.6 + pi * 0.08, 1.0)))
            if pi == 2 or j % 2 == 0:
                g.append(txt(bx, BASE + 17, str(k), 't-lab', 'middle', 11))

    g.append(txt(320, 288, 'ONE RUNG = 1% PROBABILITY · DASHED RULE + HOLLOW DOT = POISSON(λ = 2)',
                 't-note', 'middle', None, 1.0))
    legend = ('<span><i class="sw sw--ink"></i>二项分布 B(n, p) 的概率质量</span>'
              '<span><i class="sw sw--acc"></i>Poisson(λ = 2) 极限</span>')
    caption = '图 2 · Poisson 分布的二项逼近：n → ∞ 且 np → λ 时逐点收敛到 λ^k e^(−λ)/k!（正文 §8.1.5、例题 E4）'
    return wrap('fig-poisson', '0 0 640 300', ''.join(g), caption, legend)


# ══════════════════════════════════════════════════════════════
# B2 · hairline line → 指数分布的无记忆性
# ══════════════════════════════════════════════════════════════
def memoryless_line():
    X0, X1, BASE, TOP = 76.0, 604.0, 246.0, 60.0
    TMAX = 3.0
    XS = lambda t: X0 + t / TMAX * (X1 - X0)
    YS = lambda s: BASE - s * (BASE - TOP)

    S = lambda t: math.exp(-t)
    g = []
    # 日历地板：一片 = 一个时间切片
    t = 0.0
    i = 0
    while t <= TMAX + 1e-9:
        g.append(line(XS(t), BASE, XS(t), BASE - 7, 'f-hair-thin', min(i * 0.006, 0.3)))
        t += 0.1
        i += 1
    g.append(line(X0, BASE, X1, BASE, 'f-axis'))
    g.append(txt(X0 - 10, TOP + 4, 'S(t)', 't-lab', 'end', 11))
    g.append(txt(X0 - 10, BASE + 4, '0', 't-lab', 'end', 11))
    g.append(txt(X1 + 6, BASE + 4, 't', 't-lab', 'start', 11))

    for sv in (0.5, 1.0):
        g.append(line(X0, YS(sv), X1, YS(sv), 'f-grid'))
        g.append(txt(X0 - 10, YS(sv) + 4, fmt(sv), 't-lab', 'end', 11))

    pts = []
    t = 0.0
    while t <= TMAX + 1e-9:
        pts.append('%.1f %.1f' % (XS(t), YS(S(t))))
        t += 0.02
    g.append(path('M' + ' L '.join(pts), 'f-line', 0.1))

    A, B = 0.5, 1.0
    for tv, lab, sv in ((A, 'a = 0.5', S(A)), (A + B, 'a + b = 1.5', S(A + B))):
        g.append(line(XS(tv), YS(sv), XS(tv), BASE, 'f-rule-dash'))
        g.append(dot(XS(tv), YS(sv), 3.4, 'f-dot f-dot--acc', 0.5,
                     '%s → S = %.4f' % (lab, sv)))
    g.append(dot(XS(B), YS(S(B)), 3.0, 'f-dot', 0.6, 'b = 1.0 → S(b) = %.4f' % S(B)))

    g.append(txt(XS(A), YS(S(A)) - 12, 'S(a) = 0.6065', 't-num t-halo', 'middle', 12, 0.7))
    g.append(txt(XS(B) - 6, YS(S(B)) - 12, 'S(b) = 0.3679', 't-num t-halo', 'middle', 12, 0.8))
    g.append(txt(XS(A + B) + 8, YS(S(A + B)) + 16, 'S(a+b) = 0.2231', 't-num t-halo', 'start', 12, 0.9))

    # 区间括号
    for t0, t1, lab in ((0.0, A, 'a'), (A, A + B, 'b')):
        y = BASE + 20
        g.append(el('path', {'d': 'M%.1f %.1f L%.1f %.1f L%.1f %.1f' % (
            XS(t0), y - 4, XS(t0), y, XS(t1), y), 'class': 'f-bracket', 'fill': 'none'}))
        g.append(el('path', {'d': 'M%.1f %.1f L%.1f %.1f' % (
            XS(t1), y, XS(t1), y - 4), 'class': 'f-bracket', 'fill': 'none'}))
        g.append(txt((XS(t0) + XS(t1)) / 2, y + 15, lab, 't-num', 'middle', 11.5))

    g.append(txt(320, 296, 'S(a)·S(b) = 0.6065 × 0.3679 = 0.2231 = S(a + b)',
                 't-num t-halo', 'middle', 12.5, 1.0))
    g.append(txt(320, 316, 'ONE HAIRLINE = ONE TIME SLICE · S(t) = e^(−λt)，图中取 λ = 1 示意',
                 't-note', 'middle', None, 1.1))
    legend = ('<span><i class="sw sw--ink"></i>S(t) = P(X ≥ t)</span>'
              '<span><i class="sw sw--acc"></i>关键点 a、a + b</span>')
    caption = '图 3 · 指数分布的无记忆性：P(X ≥ a + b) = P(X ≥ a)·P(X ≥ b)，即 (8.1)（正文 §8.1.5）'
    return wrap('fig-memoryless', '0 0 640 330', ''.join(g), caption, legend)


# ══════════════════════════════════════════════════════════════
# dorothy-picture 新增：六类理解障碍的图型（A–F）
#   一律只挂语义类、不写颜色；渲染核对用 scripts/render_fig.js
#   下面重新定义 esc / wrap（Python 后定义覆盖前定义），升级点：
#     · esc 补 " → &quot;（aria-label / 文本属性安全）
#     · wrap 增加 <title> 与独立 aria；aria-label 不再硬塞整条图注
# ══════════════════════════════════════════════════════════════

def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def wrap(fig_id, view, body, caption, legend, aria=None, title=None):
    """figure 包装：aria-label 与 <title> 给读屏，figcaption 是可见图注。"""
    return ('<figure class="fig" id="%s">\n'
            '  <svg viewBox="%s" role="img" aria-label="%s">\n'
            '    <title>%s</title>\n'
            '    %s\n'
            '  </svg>\n'
            '  <div class="fig__legend">%s</div>\n'
            '  <figcaption>%s</figcaption>\n'
            '</figure>' % (fig_id, view, esc(aria or caption), esc(title or caption),
                           body, legend, esc(caption)))


def box(x, y, w, h, cls='f-box', label=None, sub=None, delay=0):
    """对象框：结构图 / 阶段图 / 对照图共用。label 居中，sub 在其下。"""
    g = [el('rect', {'x': fmt(x), 'y': fmt(y), 'width': fmt(w), 'height': fmt(h),
                     'class': cls, 'style': 'animation-delay:%ss' % delay})]
    cy = y + h / 2.0
    if label is not None:
        g.append(txt(x + w / 2.0, cy + 4 - (7 if sub is not None else 0), label, 't-num', 'middle', 12.5, delay))
    if sub is not None:
        g.append(txt(x + w / 2.0, cy + 16, sub, 't-lab', 'middle', 11, delay))
    return ''.join(g)


def head_arrow(x1, y1, x2, y2, cls='f-line'):
    """直线 + 实心箭头（箭头是填充三角，放终点）。"""
    ang = math.atan2(y2 - y1, x2 - x1)
    L, Wd = 8.0, 4.0
    bx, by = x2 - L * math.cos(ang), y2 - L * math.sin(ang)
    px, py = -math.sin(ang), math.cos(ang)
    pts = '%.1f,%.1f %.1f,%.1f %.1f,%.1f' % (
        x2, y2, bx + Wd * px, by + Wd * py, bx - Wd * px, by - Wd * py)
    return (path('M%.1f %.1f L%.1f %.1f' % (x1, y1, bx, by), cls, None, False)
            + el('polygon', {'points': pts, 'class': 'f-arrow'}))


def objmap(fid, caption, left, right, maps, ltitle='', rtitle='',
               note=None, aria=None, legend='', view='0 0 640 300'):
    """A 对象与结构障碍：左右两列对象框 + 带关系名的箭头。

    left / right: ['名字'] 或 [('名字', '副标签')]
    maps:        [(左索引, 右索引, '关系名')]
    """
    BW, BH = 150.0, 42.0
    lx, rx = 58.0, 432.0
    n = max(len(left), len(right), 1)
    top, bot = 74.0, 250.0
    ys = [top + i * ((bot - top) / max(n - 1, 1)) if n > 1 else (top + bot) / 2 for i in range(n)]
    g = []
    if ltitle:
        g.append(txt(lx + BW / 2, 44, ltitle, 't-lab', 'middle', 11.5))
    if rtitle:
        g.append(txt(rx + BW / 2, 44, rtitle, 't-lab', 'middle', 11.5))
    ys_of = {}
    for side, x0, nodes in (('l', lx, left), ('r', rx, right)):
        m = max(len(nodes), 1)
        yy = [top + i * ((bot - top) / max(m - 1, 1)) if m > 1 else (top + bot) / 2 for i in range(m)]
        ys_of[side] = yy
        for i, item in enumerate(nodes):
            lab = item[0] if isinstance(item, (tuple, list)) else item
            sub = item[1] if isinstance(item, (tuple, list)) and len(item) > 1 else None
            g.append(box(x0, yy[i] - BH / 2, BW, BH, 'f-box', lab, sub, 0.04 * i))
    for li, ri, rel in maps:
        y1 = ys_of['l'][li] if li < len(ys_of['l']) else (top + bot) / 2
        y2 = ys_of['r'][ri] if ri < len(ys_of['r']) else (top + bot) / 2
        x1, x2 = lx + BW, rx - 2
        mx = (x1 + x2) / 2.0
        g.append(path('M%.1f %.1f C%.1f %.1f %.1f %.1f %.1f %.1f' % (
            x1, y1, mx, y1, mx, y2, x2 - 7, y2), 'f-link', 0.25, False))
        g.append(el('polygon', {'points': '%.1f,%.1f %.1f,%.1f %.1f,%.1f' % (
            x2, y2, x2 - 9, y2 - 4.5, x2 - 9, y2 + 4.5), 'class': 'f-arrow'}))
        g.append(txt(mx, (y1 + y2) / 2.0 - 7, rel, 't-num', 'middle', 11.5, 0.35))
    if note:
        g.append(txt(320, 284, note, 't-note', 'middle', None, 0.6))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


def axis(fid, caption, xmin, xmax, marks=(), bands=(), xlabel='',
             note=None, aria=None, legend='', view='0 0 640 240'):
    """B 空间与几何障碍：数轴 + 区间带 + 标注点。

    marks: [(x, '标签', True/False)]   True = 用强调色
    bands: [(x0, x1, '标签')]
    """
    X0, X1, Y = 70.0, 596.0, 150.0
    S = lambda v: X0 + (v - xmin) / float(xmax - xmin) * (X1 - X0)
    g = [line(X0, Y, X1, Y, 'f-axis')]
    if xlabel:
        g.append(txt(X1 + 8, Y + 4, xlabel, 't-lab', 'start', 11))
    for b0, b1, blab in bands:
        g.append(el('rect', {'x': fmt(S(b0)), 'y': fmt(Y - 16), 'width': fmt(S(b1) - S(b0)),
                             'height': '16', 'class': 'f-band'}))
        g.append(txt((S(b0) + S(b1)) / 2, Y - 25, blab, 't-lab', 'middle', 11))
    for mv, mlab, strong in marks:
        cls = 'f-dot f-dot--acc' if strong else 'f-dot'
        g.append(line(S(mv), Y, S(mv), Y - 9, 'f-axis'))
        g.append(dot(S(mv), Y, 3.4, cls, 0.2))
        g.append(txt(S(mv), Y + 20, mlab, 't-num' if strong else 't-lab', 'middle', 11.5))
    for v, lab, _s in marks:
        pass
    if note:
        g.append(txt(320, 218, note, 't-note', 'middle', None, 0.5))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


def stages(fid, caption, stages, note=None, aria=None, legend='', view='0 0 640 220'):
    """C 过程与变化障碍：横向阶段框 + 阶段箭头 + 编号。

    stages: [('阶段标题', '说明')]
    """
    n = max(len(stages), 1)
    BW, BH, GAP = 132.0, 64.0, 22.0
    total = n * BW + (n - 1) * GAP
    x0 = (640 - total) / 2.0
    Y = 92.0
    g = []
    for i, st in enumerate(stages):
        title = st[0] if isinstance(st, (tuple, list)) else st
        sub = st[1] if isinstance(st, (tuple, list)) and len(st) > 1 else None
        bx = x0 + i * (BW + GAP)
        g.append(box(bx, Y, BW, BH, 'f-box', title, sub, 0.06 * i))
        g.append(txt(bx + 10, Y - 10, str(i + 1), 't-num', 'start', 11.5, 0.06 * i))
        if i < n - 1:
            g.append(head_arrow(bx + BW + 3, Y + BH / 2, bx + BW + GAP - 3, Y + BH / 2))
    if note:
        g.append(txt(320, 196, note, 't-note', 'middle', None, 0.5))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


def proof(fid, caption, steps, note=None, aria=None, legend='', view='0 0 640 300'):
    """D 推理与证明障碍：编号步骤 + 每步依据 + 依赖竖箭头。

    steps: [('这一步做了什么', '依据：命题 8.5')]
    """
    n = max(len(steps), 1)
    X, W, BH = 92.0, 430.0, 40.0
    top, gap = 56.0, 14.0
    g = []
    for i, st in enumerate(steps):
        text = st[0] if isinstance(st, (tuple, list)) else st
        why = st[1] if isinstance(st, (tuple, list)) and len(st) > 1 else None
        y = top + i * (BH + gap)
        g.append(box(X, y, W, BH, 'f-box', None, None, 0.05 * i))
        g.append(txt(X + 12, y + BH / 2 + 4, text, 't-num', 'start', 12, 0.05 * i))
        g.append(dot(X - 18, y + BH / 2, 10, 'f-dot-hollow', 0.05 * i))
        g.append(txt(X - 18, y + BH / 2 + 4, str(i + 1), 't-num', 'middle', 11))
        if why:
            g.append(txt(X + W - 10, y + BH / 2 + 4, why, 't-lab', 'end', 11, 0.05 * i))
        if i < n - 1:
            g.append(head_arrow(X + 20, y + BH + 1, X + 20, y + BH + gap - 1))
    if note:
        g.append(txt(320, top + n * (BH + gap) + 14, note, 't-note', 'middle', None, 0.5))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


def compare(fid, caption, rows, ltitle='', rtitle='',
                note=None, aria=None, legend='', view='0 0 640 300'):
    """E 概念辨析障碍：左右同构两栏，差异行右侧加强调标记。

    rows: [('左', '右', 是否差异)]   差异行两侧都画强调框
    """
    BW, BH, GAPX = 250.0, 44.0, 60.0
    lx = (640 - (BW * 2 + GAPX)) / 2.0
    rx = lx + BW + GAPX
    top, gap = 74.0, 12.0
    g = []
    if ltitle:
        g.append(txt(lx + BW / 2, 58, ltitle, 't-num', 'middle', 13))
    if rtitle:
        g.append(txt(rx + BW / 2, 58, rtitle, 't-num', 'middle', 13))
    for i, row in enumerate(rows):
        ltxt = row[0]
        rtxt = row[1] if len(row) > 1 else ''
        diff = row[2] if len(row) > 2 else False
        y = top + i * (BH + gap)
        g.append(box(lx, y, BW, BH, 'f-box--acc' if diff else 'f-box', None, None, 0.05 * i))
        g.append(box(rx, y, BW, BH, 'f-box--acc' if diff else 'f-box', None, None, 0.05 * i))
        g.append(txt(lx + BW / 2, y + BH / 2 + 4, ltxt, 't-num' if diff else 't-lab', 'middle', 11.5, 0.05 * i))
        g.append(txt(rx + BW / 2, y + BH / 2 + 4, rtxt, 't-num' if diff else 't-lab', 'middle', 11.5, 0.05 * i))
    if note:
        g.append(txt(320, top + len(rows) * (BH + gap) + 12, note, 't-note', 'middle', None, 0.5))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


def depgraph(fid, caption, layers, edges, note=None, aria=None, legend='', view='0 0 640 300'):
    """F 多知识点关联障碍：分层节点 + 有向边。

    layers: [['节点名', ...], ...]          从左到右一层
    edges:  [('起点名', '终点名', '关系名')]
    """
    BW, BH = 112.0, 34.0
    n = max(len(layers), 1)
    step = (640.0 - 2 * 30.0) / n if n else 0
    cx0 = 30.0
    pos = {}
    g = []
    for li, nodes in enumerate(layers):
        cx = cx0 + step * li + (step - BW) / 2.0 + BW / 2.0
        m = max(len(nodes), 1)
        for i, name in enumerate(nodes):
            cy = 300.0 / 2 + (i - (m - 1) / 2.0) * (BH + 16)
            pos[name] = (cx, cy)
            g.append(box(cx - BW / 2, cy - BH / 2, BW, BH, 'f-box', name, None, 0.04 * (li + i)))
    for a, b, lab in edges:
        if a not in pos or b not in pos:
            continue
        (x1, y1), (x2, y2) = pos[a], pos[b]
        sx = x1 + BW / 2 if x2 >= x1 else x1 - BW / 2
        tx = x2 - BW / 2 - 6 if x2 >= x1 else x2 + BW / 2 + 6
        g.append(path('M%.1f %.1f C%.1f %.1f %.1f %.1f %.1f %.1f' % (
            sx, y1, (sx + tx) / 2, y1, (sx + tx) / 2, y2, tx, y2), 'f-link', 0.2, False))
        g.append(el('polygon', {'points': '%.1f,%.1f %.1f,%.1f %.1f,%.1f' % (
            tx + 7 if x2 >= x1 else tx - 7, y2, tx if x2 >= x1 else tx, y2 - 4.5,
            tx if x2 >= x1 else tx, y2 + 4.5), 'class': 'f-arrow'}))
        if lab:
            g.append(txt((sx + tx) / 2, (y1 + y2) / 2 - 12, lab, 't-num t-halo', 'middle', 11))
    if note:
        g.append(txt(320, 288, note, 't-note', 'middle', None, 0.4))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


# ══════════════════════════════════════════════════════════════
# dorothy-picture 新增：六类理解障碍的图型（A–F）
#   一律只挂语义类、不写颜色；渲染核对用 scripts/render_fig.js
#   下面重新定义 esc / wrap（Python 后定义覆盖前定义），升级点：
#     · esc 补 " → &quot;（aria-label / 文本属性安全）
#     · wrap 增加 <title> 与独立 aria；aria-label 不再硬塞整条图注
# ══════════════════════════════════════════════════════════════

def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def wrap(fig_id, view, body, caption, legend, aria=None, title=None):
    """figure 包装：aria-label 与 <title> 给读屏，figcaption 是可见图注。"""
    return ('<figure class="fig" id="%s">\n'
            '  <svg viewBox="%s" role="img" aria-label="%s">\n'
            '    <title>%s</title>\n'
            '    %s\n'
            '  </svg>\n'
            '  <div class="fig__legend">%s</div>\n'
            '  <figcaption>%s</figcaption>\n'
            '</figure>' % (fig_id, view, esc(aria or caption), esc(title or caption),
                           body, legend, esc(caption)))


def box(x, y, w, h, cls='f-box', label=None, sub=None, delay=0):
    """对象框：结构图 / 阶段图 / 对照图共用。label 居中，sub 在其下。"""
    g = [el('rect', {'x': fmt(x), 'y': fmt(y), 'width': fmt(w), 'height': fmt(h),
                     'class': cls, 'style': 'animation-delay:%ss' % delay})]
    cy = y + h / 2.0
    if label is not None:
        g.append(txt(x + w / 2.0, cy + 4 - (7 if sub is not None else 0), label, 't-num', 'middle', 12.5, delay))
    if sub is not None:
        g.append(txt(x + w / 2.0, cy + 16, sub, 't-lab', 'middle', 11, delay))
    return ''.join(g)


def head_arrow(x1, y1, x2, y2, cls='f-line'):
    """直线 + 实心箭头（箭头是填充三角，放终点）。"""
    ang = math.atan2(y2 - y1, x2 - x1)
    L, Wd = 8.0, 4.0
    bx, by = x2 - L * math.cos(ang), y2 - L * math.sin(ang)
    px, py = -math.sin(ang), math.cos(ang)
    pts = '%.1f,%.1f %.1f,%.1f %.1f,%.1f' % (
        x2, y2, bx + Wd * px, by + Wd * py, bx - Wd * px, by - Wd * py)
    return (path('M%.1f %.1f L%.1f %.1f' % (x1, y1, bx, by), cls, None, False)
            + el('polygon', {'points': pts, 'class': 'f-arrow'}))


def objmap(fid, caption, left, right, maps, ltitle='', rtitle='',
               note=None, aria=None, legend='', view='0 0 640 300'):
    """A 对象与结构障碍：左右两列对象框 + 带关系名的箭头。

    left / right: ['名字'] 或 [('名字', '副标签')]
    maps:        [(左索引, 右索引, '关系名')]
    """
    BW, BH = 150.0, 42.0
    lx, rx = 58.0, 432.0
    n = max(len(left), len(right), 1)
    top, bot = 74.0, 250.0
    ys = [top + i * ((bot - top) / max(n - 1, 1)) if n > 1 else (top + bot) / 2 for i in range(n)]
    g = []
    if ltitle:
        g.append(txt(lx + BW / 2, 44, ltitle, 't-lab', 'middle', 11.5))
    if rtitle:
        g.append(txt(rx + BW / 2, 44, rtitle, 't-lab', 'middle', 11.5))
    ys_of = {}
    for side, x0, nodes in (('l', lx, left), ('r', rx, right)):
        m = max(len(nodes), 1)
        yy = [top + i * ((bot - top) / max(m - 1, 1)) if m > 1 else (top + bot) / 2 for i in range(m)]
        ys_of[side] = yy
        for i, item in enumerate(nodes):
            lab = item[0] if isinstance(item, (tuple, list)) else item
            sub = item[1] if isinstance(item, (tuple, list)) and len(item) > 1 else None
            g.append(box(x0, yy[i] - BH / 2, BW, BH, 'f-box', lab, sub, 0.04 * i))
    for li, ri, rel in maps:
        y1 = ys_of['l'][li] if li < len(ys_of['l']) else (top + bot) / 2
        y2 = ys_of['r'][ri] if ri < len(ys_of['r']) else (top + bot) / 2
        x1, x2 = lx + BW, rx - 2
        mx = (x1 + x2) / 2.0
        g.append(path('M%.1f %.1f C%.1f %.1f %.1f %.1f %.1f %.1f' % (
            x1, y1, mx, y1, mx, y2, x2 - 7, y2), 'f-link', 0.25, False))
        g.append(el('polygon', {'points': '%.1f,%.1f %.1f,%.1f %.1f,%.1f' % (
            x2, y2, x2 - 9, y2 - 4.5, x2 - 9, y2 + 4.5), 'class': 'f-arrow'}))
        g.append(txt(mx, (y1 + y2) / 2.0 - 7, rel, 't-num', 'middle', 11.5, 0.35))
    if note:
        g.append(txt(320, 284, note, 't-note', 'middle', None, 0.6))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


def axis(fid, caption, xmin, xmax, marks=(), bands=(), xlabel='',
             note=None, aria=None, legend='', view='0 0 640 240'):
    """B 空间与几何障碍：数轴 + 区间带 + 标注点。

    marks: [(x, '标签', True/False)]   True = 用强调色
    bands: [(x0, x1, '标签')]
    """
    X0, X1, Y = 70.0, 596.0, 150.0
    S = lambda v: X0 + (v - xmin) / float(xmax - xmin) * (X1 - X0)
    g = [line(X0, Y, X1, Y, 'f-axis')]
    if xlabel:
        g.append(txt(X1 + 8, Y + 4, xlabel, 't-lab', 'start', 11))
    for b0, b1, blab in bands:
        g.append(el('rect', {'x': fmt(S(b0)), 'y': fmt(Y - 16), 'width': fmt(S(b1) - S(b0)),
                             'height': '16', 'class': 'f-band'}))
        g.append(txt((S(b0) + S(b1)) / 2, Y - 25, blab, 't-lab', 'middle', 11))
    for mv, mlab, strong in marks:
        cls = 'f-dot f-dot--acc' if strong else 'f-dot'
        g.append(line(S(mv), Y, S(mv), Y - 9, 'f-axis'))
        g.append(dot(S(mv), Y, 3.4, cls, 0.2))
        g.append(txt(S(mv), Y + 20, mlab, 't-num' if strong else 't-lab', 'middle', 11.5))
    for v, lab, _s in marks:
        pass
    if note:
        g.append(txt(320, 218, note, 't-note', 'middle', None, 0.5))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


def stages(fid, caption, stages, note=None, aria=None, legend='', view='0 0 640 220'):
    """C 过程与变化障碍：横向阶段框 + 阶段箭头 + 编号。

    stages: [('阶段标题', '说明')]
    """
    n = max(len(stages), 1)
    BW, BH, GAP = 132.0, 64.0, 22.0
    total = n * BW + (n - 1) * GAP
    x0 = (640 - total) / 2.0
    Y = 92.0
    g = []
    for i, st in enumerate(stages):
        title = st[0] if isinstance(st, (tuple, list)) else st
        sub = st[1] if isinstance(st, (tuple, list)) and len(st) > 1 else None
        bx = x0 + i * (BW + GAP)
        g.append(box(bx, Y, BW, BH, 'f-box', title, sub, 0.06 * i))
        g.append(txt(bx + 10, Y - 10, str(i + 1), 't-num', 'start', 11.5, 0.06 * i))
        if i < n - 1:
            g.append(head_arrow(bx + BW + 3, Y + BH / 2, bx + BW + GAP - 3, Y + BH / 2))
    if note:
        g.append(txt(320, 196, note, 't-note', 'middle', None, 0.5))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


def proof(fid, caption, steps, note=None, aria=None, legend='', view='0 0 640 300'):
    """D 推理与证明障碍：编号步骤 + 每步依据 + 依赖竖箭头。

    steps: [('这一步做了什么', '依据：命题 8.5')]
    """
    n = max(len(steps), 1)
    X, W, BH = 92.0, 430.0, 40.0
    top, gap = 56.0, 14.0
    g = []
    for i, st in enumerate(steps):
        text = st[0] if isinstance(st, (tuple, list)) else st
        why = st[1] if isinstance(st, (tuple, list)) and len(st) > 1 else None
        y = top + i * (BH + gap)
        g.append(box(X, y, W, BH, 'f-box', None, None, 0.05 * i))
        g.append(txt(X + 12, y + BH / 2 + 4, text, 't-num', 'start', 12, 0.05 * i))
        g.append(dot(X - 18, y + BH / 2, 10, 'f-dot-hollow', 0.05 * i))
        g.append(txt(X - 18, y + BH / 2 + 4, str(i + 1), 't-num', 'middle', 11))
        if why:
            g.append(txt(X + W - 10, y + BH / 2 + 4, why, 't-lab', 'end', 10.5, 0.05 * i))
        if i < n - 1:
            g.append(head_arrow(X + 20, y + BH + 1, X + 20, y + BH + gap - 1))
    if note:
        g.append(txt(320, top + n * (BH + gap) + 14, note, 't-note', 'middle', None, 0.5))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


def compare(fid, caption, rows, ltitle='', rtitle='',
                note=None, aria=None, legend='', view=None):
    """E 概念辨析障碍：左右同构两栏，差异行右侧加强调标记。

    rows: [('左', '右', 是否差异)]   差异行两侧都画强调框
    """
    BW, BH, GAPX = 250.0, 44.0, 60.0
    lx = (640 - (BW * 2 + GAPX)) / 2.0
    rx = lx + BW + GAPX
    top, gap = 74.0, 12.0
    # 高度按行数算：写死 300 时 4 行以上的注记行会被裁掉
    if view is None:
        view = '0 0 640 %d' % int(top + len(rows) * (BH + gap) + (30 if note else 10))
    g = []
    if ltitle:
        g.append(txt(lx + BW / 2, 58, ltitle, 't-num', 'middle', 13))
    if rtitle:
        g.append(txt(rx + BW / 2, 58, rtitle, 't-num', 'middle', 13))
    for i, row in enumerate(rows):
        ltxt = row[0]
        rtxt = row[1] if len(row) > 1 else ''
        diff = row[2] if len(row) > 2 else False
        y = top + i * (BH + gap)
        g.append(box(lx, y, BW, BH, 'f-box--acc' if diff else 'f-box', None, None, 0.05 * i))
        g.append(box(rx, y, BW, BH, 'f-box--acc' if diff else 'f-box', None, None, 0.05 * i))
        g.append(txt(lx + BW / 2, y + BH / 2 + 4, ltxt, 't-num' if diff else 't-lab', 'middle', 11.5, 0.05 * i))
        g.append(txt(rx + BW / 2, y + BH / 2 + 4, rtxt, 't-num' if diff else 't-lab', 'middle', 11.5, 0.05 * i))
    if note:
        g.append(txt(320, top + len(rows) * (BH + gap) + 12, note, 't-note', 'middle', None, 0.5))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


def depgraph(fid, caption, layers, edges, note=None, aria=None, legend='', view='0 0 640 300'):
    """F 多知识点关联障碍：分层节点 + 有向边。

    layers: [['节点名', ...], ...]          从左到右一层
    edges:  [('起点名', '终点名', '关系名')]
    """
    BW, BH = 112.0, 34.0
    n = max(len(layers), 1)
    step = (640.0 - 2 * 30.0) / n if n else 0
    cx0 = 30.0
    pos = {}
    g = []
    for li, nodes in enumerate(layers):
        cx = cx0 + step * li + (step - BW) / 2.0 + BW / 2.0
        m = max(len(nodes), 1)
        for i, name in enumerate(nodes):
            cy = 300.0 / 2 + (i - (m - 1) / 2.0) * (BH + 16)
            pos[name] = (cx, cy)
            g.append(box(cx - BW / 2, cy - BH / 2, BW, BH, 'f-box', name, None, 0.04 * (li + i)))
    for a, b, lab in edges:
        if a not in pos or b not in pos:
            continue
        (x1, y1), (x2, y2) = pos[a], pos[b]
        sx = x1 + BW / 2 if x2 >= x1 else x1 - BW / 2
        tx = x2 - BW / 2 - 6 if x2 >= x1 else x2 + BW / 2 + 6
        g.append(path('M%.1f %.1f C%.1f %.1f %.1f %.1f %.1f %.1f' % (
            sx, y1, (sx + tx) / 2, y1, (sx + tx) / 2, y2, tx, y2), 'f-link', 0.2, False))
        g.append(el('polygon', {'points': '%.1f,%.1f %.1f,%.1f %.1f,%.1f' % (
            tx + 7 if x2 >= x1 else tx - 7, y2, tx if x2 >= x1 else tx, y2 - 4.5,
            tx if x2 >= x1 else tx, y2 + 4.5), 'class': 'f-arrow'}))
        if lab:
            g.append(txt((sx + tx) / 2, (y1 + y2) / 2 - 12, lab, 't-num t-halo', 'middle', 11))
    if note:
        g.append(txt(320, 288, note, 't-note', 'middle', None, 0.4))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


# ══════════════════════════════════════════════════════════════
# 几何直觉图（B 类）· 模块化图元 + Bertrand 三种「随机」
#   坐标一律用「圆心 + 半径 + 角度」，角度按数学惯例（0° 向右、
#   逆时针为正），内部换算成屏幕坐标（y 向下）。
#   验收要点：图必须展示「随机对象 → 弦长」的因果，不能只画区域。
# ══════════════════════════════════════════════════════════════

def gpt(cx, cy, r, deg):
    """圆上一点（数学角度 → 屏幕坐标）。"""
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy - r * math.sin(a))


def gcircle(cx, cy, r, cls='f-axis', delay=None):
    attrs = {'cx': fmt(cx), 'cy': fmt(cy), 'r': fmt(r), 'class': cls, 'fill': 'none'}
    if delay is not None:
        attrs['style'] = 'animation-delay:%ss' % delay
    return el('circle', attrs)


def garc(cx, cy, r, deg0, deg1, cls='f-line--acc', delay=None):
    """从 deg0 沿数学逆时针到 deg1 的弧（屏幕 sweep=0）。"""
    x0, y0 = gpt(cx, cy, r, deg0)
    x1, y1 = gpt(cx, cy, r, deg1)
    span = (deg1 - deg0) % 360
    large = 1 if span > 180 else 0
    d = 'M%.1f %.1f A%.1f %.1f 0 %d 0 %.1f %.1f' % (x0, y0, r, r, large, x1, y1)
    attrs = {'d': d, 'class': cls, 'fill': 'none'}
    if delay is not None:
        attrs['style'] = 'animation-delay:%ss' % delay
    return el('path', attrs)


def gchord(cx, cy, r, deg0, deg1, cls='f-line', delay=None):
    x0, y0 = gpt(cx, cy, r, deg0)
    x1, y1 = gpt(cx, cy, r, deg1)
    attrs = {'x1': fmt(x0), 'y1': fmt(y0), 'x2': fmt(x1), 'y2': fmt(y1), 'class': cls}
    if delay is not None:
        attrs['style'] = 'animation-delay:%ss' % delay
    return el('line', attrs)


def gpoly(cx, cy, r, n, rot=90.0, cls='f-hair-thin', delay=None):
    pts = [gpt(cx, cy, r, rot + 360.0 * k / n) for k in range(n)]
    d = 'M' + ' L '.join('%.1f %.1f' % p for p in pts) + ' Z'
    attrs = {'d': d, 'class': cls, 'fill': 'none'}
    if delay is not None:
        attrs['style'] = 'animation-delay:%ss' % delay
    return el('path', attrs)


def ghline(cx, cy, r, d, cls='f-line', delay=None):
    """距圆心 d 的水平弦（长度 2√(R²−d²)）—— 弦心距越小，弦越长。"""
    half = math.sqrt(max(r * r - d * d, 0.0))
    y = cy + d
    return line(cx - half, y, cx + half, y, cls, delay)


def chord_models(fid, caption, note=None, aria=None, legend='', view='0 0 660 300'):
    """几何直觉图 · 同一条弦、三种「随机」→ 三个不同的几何量之比。

    教学任务：让读者看见「随机加在哪个几何对象上」如何决定「弦长 > √3R」
    对应哪一块区域，从而决定概率 —— 而不是只看到三个不同的数。
    """
    R, CY = 74.0, 158.0
    centers = [112.0, 330.0, 548.0]
    titles = ['① 随机在圆周上', '② 随机在半径上', '③ 随机在圆面内']
    subs = ['B 在圆周上均匀', 'd 在 (0, R) 上均匀', 'M 在圆面内均匀']
    results = ['弧长比 120°/360° = 1/3', '长度比 (R/2)/R = 1/2', '面积比 (R/2)²/R² = 1/4']
    half = R * math.sqrt(3) / 2.0
    y_crit = CY + R / 2.0
    d_long = 0.30 * R
    g = []
    for i, cx in enumerate(centers):
        if i == 2:
            # 允许的中点区域先铺底，三角形压在上面
            g.append(el('circle', {'cx': fmt(cx), 'cy': fmt(CY), 'r': fmt(R / 2.0), 'class': 'f-band'}))
        g.append(gcircle(cx, CY, R, 'f-axis'))
        g.append(gpoly(cx, CY, R, 3, 90.0, 'f-hair-thin'))
        g.append(ghline(cx, CY, R, R / 2.0, 'f-rule-dash-sm'))
        if i == 0:
            # 长弦（B 在下半弧）+ 短弦（B' 在上半弧）
            g.append(gchord(cx, CY, R, 90, 250, 'f-line--acc'))
            g.append(dot(*gpt(cx, CY, R, 250), 3.4, 'f-dot--acc', 0.2))
            g.append(gchord(cx, CY, R, 90, 38, 'f-line--acc-dash'))
            g.append(dot(*gpt(cx, CY, R, 38), 3.0, 'f-dot', 0.3))
            g.append(garc(cx, CY, R, 210, 330, 'f-line--acc'))
            g.append(dot(cx, CY - R, 3.6, 'f-dot', 0.1))
            g.append(txt(cx, CY - R - 10, 'A（固定）', 't-lab', 'middle', 11, 0.12))
            bx, by = gpt(cx, CY, R, 250)
            g.append(txt(bx - 24, by + 4, 'B', 't-num', 'middle', 11.5, 0.24))
        elif i == 1:
            g.append(ghline(cx, CY, R, d_long, 'f-line--acc'))
            g.append(line(cx, CY, cx, CY + d_long, 'f-line--acc', 0.16))
            g.append(dot(cx, CY, 3.0, 'f-dot', 0.1))
            g.append(txt(cx + 8, CY + d_long + 12, 'd 小 → 弦长', 't-num', 'start', 11, 0.22))
        else:
            g.append(ghline(cx, CY, R, d_long, 'f-line--acc'))
            g.append(gcircle(cx, CY, R / 2.0, 'f-line--acc-dash', 0.16))
            g.append(dot(cx, CY + d_long, 3.4, 'f-dot--acc', 0.24))
            g.append(txt(cx + 8, CY + d_long - 8, '中点 M', 't-num', 'start', 11, 0.26))
        g.append(txt(cx, 30, titles[i], 't-num', 'middle', 12.5, 0.05 * i))
        g.append(txt(cx, 48, subs[i], 't-lab', 'middle', 11, 0.08 * i))
        g.append(txt(cx, 268, results[i], 't-num', 'middle', 12, 0.14 + 0.05 * i))
    if note:
        g.append(txt(330, 290, note, 't-note', 'middle', None, 0.4))
    return wrap(fid, view, ''.join(g), caption, legend, aria)

# ══════════════════════════════════════════════════════════════
# 对照反例图 · 同尺度并置 + 灰阶强调
#   各格坐标与尺寸完全相同，只变高亮或数据；强调走灰阶通道，不占色相
# ══════════════════════════════════════════════════════════════

def _hashseq(n, seed):
    """确定性伪随机序列（sin hash）—— 示意点阵刷新必须长一样。"""
    return [abs(math.sin(seed + i * 12.9898) * 43758.5453) % 1.0 for i in range(n)]


def _bellseq(n, seed):
    """两个均匀序列取平均 → 中间密的确定性序列（点云要反映密度形态，不能是网格状均匀）。"""
    u = _hashseq(n, seed)
    v = _hashseq(n, seed + 41.7)
    return [(u[i] + v[i]) / 2.0 for i in range(n)]


def marginal_joint_pair(fid, caption, note=None, aria=None, legend='', view='0 0 660 300'):
    """边缘分布相同、联合分布不同 —— 两格同尺度并置，边缘区用灰阶高亮。

    教学任务：让「边缘分布决定不了联合分布」变成可见的差异。
    两格用同一批边缘数据，只有联合结构不同（点阵是示意）。
    """
    n = 52
    xs = _bellseq(n, 1.7)
    ys = _bellseq(n, 9.3)
    S, Y0 = 118.0, 34.0
    LX, RX = 118.0, 420.0
    g = []
    for k, x0 in enumerate((LX, RX)):
        g.append(el('rect', {'x': fmt(x0), 'y': fmt(Y0), 'width': fmt(S), 'height': fmt(S), 'class': 'f-box'}))
        if k == 1:
            g.append(el('path', {'d': 'M%.1f %.1f L%.1f %.1f' % (x0 + 6, Y0 + S - 6, x0 + S - 6, Y0 + 6),
                                 'class': 'f-rule-dash-sm', 'fill': 'none'}))
        g.append(txt(x0 + S + 5, Y0 + S - 1, 'x₁', 't-lab', 'start', 11, 0.05))
        g.append(txt(x0 - 5, Y0 + 7, 'x₂', 't-lab', 'end', 11, 0.05))
        for i in range(n):
            px = x0 + 6 + xs[i] * (S - 12)
            ty = ys[i] if k == 0 else xs[i]
            py = Y0 + 6 + (1.0 - ty) * (S - 12)      # y 轴向上：对角线要左下 → 右上
            g.append(el('circle', {'cx': '%.1f' % px, 'cy': '%.1f' % py, 'r': '1.9',
                                   'class': 'f-dot', 'opacity': '.45'}))
    for x0 in (LX, RX):
        g.append(el('rect', {'x': fmt(x0 - 8), 'y': '184', 'width': fmt(S + 16), 'height': '40', 'class': 'f-hl'}))
        pts = []
        for i in range(0, 41):
            t = i / 40.0
            d = (t - 0.5) * 2.0
            pts.append('%.1f %.1f' % (x0 + 6 + t * (S - 12), 216.0 - math.exp(-d * d * 3.2) * 24.0))
        g.append(el('path', {'d': 'M' + ' L '.join(pts), 'class': 'f-line', 'fill': 'none'}))
        g.append(el('line', {'x1': fmt(x0), 'y1': '218', 'x2': fmt(x0 + S), 'y2': '218', 'class': 'f-axis'}))
        g.append(txt(x0 + S / 2, 232, '边缘 ℙ_X₁ = ℙ_X₂ = q', 't-lab', 'middle', 11))
    g.append(txt(336, 208, '完全相同', 't-num', 'middle', 12))
    g.append(txt(LX + S / 2, 24, '(X₁, X₂) 独立', 't-num', 'middle', 12.5))
    g.append(txt(RX + S / 2, 24, '(X₁, X₁) 完全相关', 't-num', 'middle', 12.5))
    g.append(txt(LX + S / 2, 256, '联合 = q(x₁)·q(x₂)', 't-num', 'middle', 11.5))
    g.append(txt(RX + S / 2, 256, '联合集中在 x₁ = x₂', 't-num', 'middle', 11.5))
    if note:
        g.append(txt(330, 286, note, 't-note', 'middle', None, 0.4))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


# ══════════════════════════════════════════════════════════════
# 原子与 CDF 跳跃的对应（补：分布函数为什么能直接读出原子）
# ══════════════════════════════════════════════════════════════

def cdf_jumps(fid, caption, atoms, note=None, aria=None, legend='', view='0 0 660 300'):
    """阶梯分布函数：跳跃位置 = 原子位置，跳跃高度 = 原子质量。

    atoms: [(t, 质量)]，质量之和应为 1。
    """
    X0, X1, BASE, TOP = 88.0, 596.0, 250.0, 58.0
    T0, T1 = -2.2, 3.2
    TS = lambda t: X0 + (t - T0) / (T1 - T0) * (X1 - X0)
    FS = lambda v: BASE - v * (BASE - TOP)
    g = []
    g.append(line(X0, BASE, X1, BASE, 'f-axis'))
    g.append(line(X0, BASE, X0, TOP - 10, 'f-axis'))
    for v, lab in ((0.0, '0'), (0.5, '0.5'), (1.0, '1')):
        g.append(line(X0 - 5, FS(v), X0, FS(v), 'f-axis'))
        g.append(txt(X0 - 9, FS(v) + 4, lab, 't-lab', 'end', 11))
    g.append(txt(X0 - 9, TOP - 14, 'F(t)', 't-lab', 'end', 11.5))
    cum = 0.0
    g.append(line(TS(T0), FS(0.0), TS(atoms[0][0]), FS(0.0), 'f-line'))
    for i, (t, p) in enumerate(atoms):
        g.append(line(TS(t), FS(cum), TS(t), FS(cum + p), 'f-line--acc', 0.08 * i))
        g.append(el('circle', {'cx': '%.1f' % TS(t), 'cy': '%.1f' % FS(cum), 'r': '3.0',
                               'class': 'f-dot-hollow', 'fill': 'none'}))
        g.append(dot(TS(t), FS(cum + p), 3.2, 'f-dot--acc', 0.08 * i))
        g.append(txt(TS(t) + 8, FS(cum + p / 2.0) + 4, '%.1f' % p, 't-num', 'start', 11.5, 0.14 + 0.08 * i))
        cum += p
        nxt = atoms[i + 1][0] if i + 1 < len(atoms) else T1
        g.append(line(TS(t), FS(cum), TS(nxt), FS(cum), 'f-line', 0.08 * i))
    for t, _p in atoms:
        g.append(txt(TS(t), BASE + 18, '%g' % t, 't-lab', 'middle', 11))
    g.append(txt(X1, BASE + 18, 't', 't-lab', 'end', 11))
    if note:
        g.append(txt(330, BASE + 44, note, 't-note', 'middle', None, 0.4))
    return wrap(fid, view, ''.join(g), caption, legend, aria)


# ══════════════════════════════════════════════════════════════
# 前推的完整链条：B → X⁻¹(B) → 概率相等（图 4 的核心关系）
# ══════════════════════════════════════════════════════════════

def pushforward_pair(fid, caption, note=None, aria=None, legend='', view='0 0 660 300'):
    """把「先取原像、再取概率」画出来：左侧两块原像都映进右侧同一个 B。"""
    LCX, RCX, CY, R = 168.0, 492.0, 130.0, 76.0
    g = []
    g.append(gcircle(LCX, CY, R, 'f-axis'))
    g.append(gcircle(RCX, CY, R, 'f-axis'))
    g.append(txt(LCX, CY - R - 14, 'Ω', 't-num', 'middle', 12.5, 0.05))
    g.append(txt(RCX, CY - R - 14, 'E', 't-num', 'middle', 12.5, 0.05))
    g.append(el('ellipse', {'cx': '126', 'cy': '102', 'rx': '27', 'ry': '17', 'class': 'f-band'}))
    g.append(el('ellipse', {'cx': '198', 'cy': '162', 'rx': '23', 'ry': '15', 'class': 'f-band'}))
    g.append(txt(206, 190, 'X⁻¹(B)', 't-num', 'middle', 11.5, 0.15))
    g.append(el('ellipse', {'cx': '516', 'cy': '128', 'rx': '46', 'ry': '30', 'class': 'f-band'}))
    g.append(txt(516, 133, 'B', 't-num', 'middle', 13, 0.15))
    g.append(head_arrow(LCX + R + 4, CY - 8, RCX - R - 10, CY - 8, 'f-line'))
    g.append(txt((LCX + RCX) / 2.0, CY - 18, 'X', 't-num', 'middle', 12.5, 0.25))
    g.append(txt(LCX, 246, 'ℙ(X⁻¹(B))', 't-num', 'middle', 12.5, 0.3))
    g.append(txt((LCX + RCX) / 2.0, 246, '=', 't-num', 'middle', 15, 0.32))
    g.append(txt(RCX, 246, 'ℙ_X(B)', 't-num', 'middle', 12.5, 0.34))
    if note:
        g.append(txt(330, 280, note, 't-note', 'middle', None, 0.4))
    return wrap(fid, view, ''.join(g), caption, legend, aria)



