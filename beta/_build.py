# -*- coding: utf-8 -*-
"""把 beta/ch08-概率论基础.html 重构成宽屏翻页式 + 真地图版本。

只做结构与样式替换：卡片正文原样保留（正则截取原文件的五段内容块）。
"""
import re
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]   # 仓库根（可移植）
# classic     → ch08-概率论基础.html（静态图）
# interactive → ch08-概率论基础-交互版.html（图 5 / 图 2 换成动态图，另有新增交互图）
MODE = sys.argv[1] if len(sys.argv) > 1 else "classic"
CLASSIC = ROOT / "beta" / "ch08-概率论基础.html"
OUT = CLASSIC if MODE == "classic" else ROOT / "beta" / "ch08-概率论基础-交互版.html"
PRISTINE = ROOT / "beta" / "_source.html"          # 首次运行留存原始版，保证脚本可反复跑
if not PRISTINE.exists():
    PRISTINE.write_text(CLASSIC.read_text(encoding="utf-8"), encoding="utf-8")

raw = PRISTINE.read_text(encoding="utf-8")

META = "  <!-- ================= 1. 章节元信息条 ================= -->"
MAP = "  <!-- ================= 2. 知识地图 ================= -->"
CORE = "  <!-- ================= 3. 核心概念区 ================= -->"
PIT = "  <!-- ================= 4. 易错点区 ================= -->"
QUIZ = "  <!-- ================= 5. 复习自测区 ================= -->"

i_meta, i_map, i_core, i_pit, i_quiz = (raw.index(m) for m in (META, MAP, CORE, PIT, QUIZ))
i_end = raw.index("\n</div>\n\n<footer")

block_meta = raw[i_meta:i_map].rstrip()
block_core = raw[i_core:i_pit].rstrip()
block_pit = raw[i_pit:i_quiz].rstrip()
block_quiz = raw[i_quiz:i_end].rstrip()

# ---------------------------------------------------------------- 末页：自测 + 课本章末习题
# 课本正文 §8.3 自带 16 道习题；原先笼统的 Q11 占位删掉，改为逐题列出：
# 题目照抄正文，课本没给答案 -> 静态 .quiz__ans 行，不生成展开按钮。
EXERCISES = (ROOT / 'beta' / '_exercises.html').read_text(encoding='utf-8').strip('\n')
print('课本习题 %d 道' % EXERCISES.count('<article class="quiz quiz--ex"'))
old_q11 = re.search(r'\s*<article class="quiz" id="q11">.*?</article>', block_quiz, re.S)
if old_q11:
    block_quiz = block_quiz[:old_q11.start()] + block_quiz[old_q11.end():]
    print('已移除 Q11 习题解答占位')
# 结构上的分段（自测 / 课本章末习题）交给后面的「末页拆板」一次做完，
# 这里不要先把习题段塞进自测栈里（那样会变成 .stack 嵌套 .stack，分组会串位）。
block_quiz = block_quiz.replace('<span class="bar__tx">复习自测</span>',
                                '<span class="bar__tx">复习自测与习题</span>')
block_quiz = block_quiz.replace('<span class="bar__en">SELF CHECK</span>',
                                '<span class="bar__en">SELF CHECK · EXERCISES</span>')
block_quiz = block_quiz.replace(
    '<span class="section__note">答案默认隐藏，点击显示；各题独立展开</span>',
    '<span class="section__note">自测答案默认隐藏；课本章末习题只给题目，课本未给解答</span>')

# ---------------------------------------------------------------- 插图（lieflat B1/B2/B3 结构）
# 图型库已迁到 dorothy-picture（scripts/lib/figlib.py）；别名回 figures，调用点不用改
# 注意：两个 path 都要留 —— refs.py 仍在 dorothy-html/scripts
sys.path.insert(0, str(ROOT / "skills" / "dorothy-picture" / "scripts" / "lib"))
sys.path.insert(0, str(ROOT / "skills" / "dorothy-html" / "scripts"))
import figlib as figures  # noqa: E402


def insert_figure_prose(block, card_id, figure_html, lead='', follow='', check=''):
    """插图 + 图前引导（lead）+ 图后解释（follow），都插在出处行之前。

    图文闭环的另两段（图中引导在图里、理解检查写在 follow 末尾或自测里）由内容侧负责。
    """
# 必须锚定到 article 标签本身：`id="p2"` 这样的子串也可能出现在互引标记或别的属性里
    start = block.index('<article class="card" id="%s">' % card_id)
    end = block.index('</article>', start)
    seg = block[start:end]
    pos = seg.rindex('<p class="card__src">')
    parts = []
    if lead:
        parts.append('<p>%s</p>' % lead)
    parts.append(figure_html)
    if follow:
        parts.append('<p>%s</p>' % follow)
    if check:
        # 理解检查必须可判定对错：问题 + 答案（P2）
        parts.append('<p class="fig__check"><b>检查</b>%s</p>' % check)
    seg = seg[:pos] + '\n            '.join(parts) + '\n            ' + seg[pos:]
    return block[:start] + seg + block[end:]


def insert_figure(block, card_id, figure_html):
    return insert_figure_prose(block, card_id, figure_html)


# dorothy-picture 产出的片段（figs/*.html）：先是数据图型的三张，再是新增的结构图型三张
FIGS = ROOT / 'beta' / 'figs'


def ch08_fig(name):
    return (FIGS / name).read_text(encoding='utf-8').strip()


# 图 5 必须在图 1 之前（都插在 e2 的出处行之前，后插的排后）
# 图 5 的两种形态：交互版用动态图替换静态几何图（同一位置，首帧就是原图 5 的几何）
FIG5 = 'fig-8-bertrand-live.html' if MODE == 'interactive' else 'fig-5-chord.html'
FIG5NO = '8' if MODE == 'interactive' else '5'
block_core = insert_figure_prose(block_core, 'e2', ch08_fig(FIG5),
    lead='在看两条密度之前先问一句：换一种「随机」，同一个事件还是同一件事吗？答案取决于「随机」加在了哪个几何对象上。',
    follow='图 %s 三个圆里，虚线都是弦长恰好等于 √3R 的临界弦（√3R 是内接等边三角形的边长）：左格随机的是端点 B，B 落在下方 120° 弧上时弦变长，分母是弧长；中格随机的是弦心距 d，d < R/2 时弦变长，分母是长度；右格随机的是弦中点 M，M 落在半径 R/2 的内圆里时弦变长，分母是面积。条件「弦心距 < R/2」三格相同，分母不同，于是得出 1/3、1/2、1/4。' % FIG5NO,
    check='三格里的「长弦」判据是同一个吗？（答案：是 —— 都是弦心距 &lt; R/2，等价于弦长 &gt; √3R；三者不同的是随机加在哪个对象上，因而分母分别是弧长、长度、面积。）')
block_core = insert_figure_prose(block_core, 'e2', figures.bertrand_area(),
    lead='两条密度放在一起，差别就看得见了。',
    follow='图 1 中实线是端点随机模型的密度 p(x)、虚线是弦心随机模型的 q(x)；x = √3 右侧的尾面积分别读出 1/3 与 1/4，正是两种「随机」的分歧所在。',
    check='图中实线与虚线分别对应哪种投弦模型？（答案：实线 = 端点随机 p(x)，虚线 = 弦心随机 q(x)。若只看形状不看图例，就会把两条曲线配反。）')
# 图 2 的两种形态：交互版用滑块版替换静态柱状图
FIG2 = ch08_fig('fig-10-poisson-live.html') if MODE == 'interactive' else figures.poisson_bars()
FIG2NO = '10' if MODE == 'interactive' else '2'
block_core = insert_figure_prose(block_core, 'e4', FIG2,
    lead='把 n 从小到大摆在一起，逼近的过程就看得见了。',
    follow='图 %s 里每组柱高来自 B(n, 2/n)，虚线与空心点标的是 Poisson(2) 的取值 λ<sup>k</sup>e<sup>−λ</sup>/k!；n 越大两者越贴，这就是「np → λ」的逐点收敛。' % FIG2NO,
    check='n 从 5 增到 100 时，柱形最高点的位置移动了吗？（答案：基本不动，始终在 k = 2 附近；变的是柱形的宽窄与光滑度 —— 收敛的是形态，不是高度。）')
block_core = insert_figure_prose(block_core, 'c11', figures.memoryless_line(),
    lead='「无记忆」到底是什么意思？先看生存函数。',
    follow='图 3 中 S(t) = e<sup>−λt</sup>（图中取 λ = 1 示意）；S(a)·S(b) 与 S(a+b) 数值相等，就是 ℙ(X ≥ a+b) = ℙ(X ≥ a)·ℙ(X ≥ b)，即式 (8.1)。',
    check='图 3 里 S(a)·S(b) 与 S(a+b) 哪个大？（答案：相等 —— 这正是无记忆性。若认为「已经等了 a」会让剩余概率变小，就把条件化与无记忆混为一谈了。）')
block_core = insert_figure_prose(block_core, 'c3', ch08_fig('fig-4-objmap.html'),
    lead='分布是把概率「搬」到另一个空间上的结果。但 ℙ 与 X 都已知，为什么还要造一个新测度？',
    follow='图 4 左侧是 (Ω, 𝒜, ℙ)，右侧是 (E, ℰ) 与 ℙ<sub>X</sub>；箭头 X 把每个 ω 送到 E，而 ℙ<sub>X</sub>(B) 取的是「X 落入 B 的原像在 ℙ 下的概率」—— 正是定义 8.2 的那一行公式。',
    check='图 4 左侧为什么画了两块区域？（答案：X 可能把 Ω 的多个部分都映进同一个 B，X⁻¹(B) 是它们的并集 —— 所以原像不必与 B 形状相同。）')
block_pit = insert_figure_prose(block_pit, 'p2', ch08_fig('fig-7-marginals.html'),
    lead='边缘分布是从联合分布里把其他变量积分掉得到的。反过来，只知道每个边缘，能不能还原联合？',
    follow='图 7 两格下方的边缘密度（灰阶框里那条曲线）完全相同，都来自同一个 q；但左格是乘积密度 q(x₁)·q(x₂)，右格的点全部落在直线 x₁ = x₂ 上。所以边缘相同推不出联合相同 —— 命题 8.6 之后的注给出的正是这个反例。',
    check='只看两格下方的边缘曲线，能区分哪一格独立、哪一格退化吗？（答案：不能 —— 两格边缘完全相同，这正是「边缘决定不了联合」。试图从边缘形状反推联合，就是这一卡要纠正的错法。）')

if MODE == 'interactive':
    block_pit = insert_figure_prose(block_pit, 'p3', ch08_fig('fig-9-density-band.html'),
        lead='密度函数 p(x) 的数值可以很大，这件事常被读成「这一点的概率很大」。把区间宽度做成可拖动的，两者就不是一回事了。',
        follow='图 9 中色带面积是 ℙ(−w ≤ X ≤ w)：把 w 拖到最小，面积趋近 0；而 x = 0 处那条竖虚线对应的密度值始终是 0.399 —— 单点的概率是 0，密度只是「单位长度上的概率密度」。',
        check='把 w 拖到 0，ℙ(−w ≤ X ≤ w) 与 p(0) 各变成多少？（答案：概率 → 0，而 p(0) 仍是 0.399。把「密度值大」当成「这点概率大」，就是这一卡要纠正的错法。）')
block_core = insert_figure_prose(block_core, 'c5', ch08_fig('fig-6-package.html'),
    lead='分布（律）与分布函数描述的是同一个东西，为什么课本两个都要？',
    follow='图 6 左右两栏用同一套画法对照：定义域一个在 ℰ 上、一个在 ℝ 上；能算的量一个针对事件、一个针对半直线；最后一行最关键 —— F<sub>X</sub> 的跳跃点直接暴露原子，而只看 ℙ<sub>X</sub> 要回去找哪些点带正质量。',
    check='只看 ℙ_X 的清单，能不能直接指出它在哪几个点上有原子？（答案：不能，要逐个集合检验；而看 F_X 的图，跳跃点直接就是原子位置，跳跃高度就是质量 —— 见下方图 11。）')
block_core = insert_figure_prose(block_core, 'c5', ch08_fig('fig-11-cdf-jumps.html'),
    lead='刚才说 F_X 的跳跃点就是原子。跳跃的<b>位置</b>给出原子在哪里，那么跳跃的<b>高度</b>给出什么？',
    follow='图 11 里 F_X 在 t = −1、0.5、2 三处各跳一次，跳跃高度分别是 0.2、0.3、0.5 —— 这三个数正好是这三个原子的质量，加起来为 1；而在两个跳跃之间曲线是平的，说明那些区间里没有原子。',
    check='图 11 中高度为 0.5 的那个跳跃对应哪个原子？（答案：t = 2 处的原子，质量 0.5。把跳跃的横坐标与高度搞混，就会把「原子在哪」和「原子多重」弄反。）')

# ---------------------------------------------------------------- 含图标记（可发现性）
# 卡片收起时也能看出这张卡带图，并直接给出图号
def add_fig_badges(block):
    n = 0
    def repl(m):
        nonlocal n
        cid, body = m.group(1), m.group(2)
        nums = re.findall(r'<figcaption>图\s*(\d+)', body)
        if not nums:
            return m.group(0)
        n += 1
        badge = '<span class="card__figs" title="本卡含图 ' + '、'.join(nums) + '">图</span>'
        return '<article class="card" id="' + cid + '">' + body.replace('</h3>', '</h3>' + badge, 1)
    return re.sub(r'<article class="card" id="([^"]+)">([\s\S]*?)(?=</article>)', repl, block), n


block_core, _nb1 = add_fig_badges(block_core)
block_pit, _nb2 = add_fig_badges(block_pit)
print('含图标记：核心 %d 张卡、易错点 %d 张卡' % (_nb1, _nb2))

# ---------------------------------------------------------------- 概念互引标记
import refs  # noqa: E402
block_core, ref_marks, ref_suppressed, ref_excluded = refs.mark_block(block_core)
print("互引标记 %d 处（同卡重复不标 %d，守卫拦下 %d）" % (
    len(ref_marks), len(ref_suppressed), len(ref_excluded)))

# ---------------------------------------------------------------- 分板块（核心概念三块；自测与习题两块）
# 每块包进一个 role="tabpanel" 的 .board，子标题处放 role="tablist" 的分段控件（等宽、指示条只动
# transform），卡数自动统计。板块可以是 hidden 的：openCard() 会先切到卡片所在板块再展开+滚动。
DIV_TAG = re.compile(r"</?div\b", re.I)


def grab_div(block, at):
    """at = '<div …>' 的起始下标；返回 (innerHTML, 结束位置)。按 div 配对计数。"""
    start = block.index(">", at) + 1      # 切片起点，别用会被游标改写的变量
    pos = start
    depth = 1
    while True:
        m = DIV_TAG.search(block, pos)
        if not m:
            raise ValueError("未闭合的 div @%d" % at)
        depth += -1 if block[m.start() + 1] == "/" else 1
        if depth == 0:
            return block[start:m.start()], m.end()
        pos = m.end()


def grab_stack(block, key):
    return grab_div(block, block.index('<div class="stack" data-accordion="%s">' % key))


def tabs_html(group, label, items):
    out = ['    <div class="tabs%s" role="tablist" aria-label="%s" data-tabs="%s">'
           % (" tabs--two" if len(items) == 2 else "", label, group),
           '      <span class="tabs__ind" aria-hidden="true"></span>']
    for i, (key, name, _attr, _inner, count) in enumerate(items):
        out.append('      <button class="tabs__tab" type="button" role="tab" id="tab-%s"'
                   ' aria-controls="board-%s" aria-selected="%s" tabindex="%s" data-board="%s">'
                   '<span class="tabs__name">%s</span><span class="tabs__n">%d</span></button>'
                   % (key, key, "true" if i == 0 else "false", "0" if i == 0 else "-1",
                      key, name, count))
    out.append("    </div>")
    return "\n".join(out)


def boards_html(items):
    out = []
    for i, (key, _name, attr, inner, _count) in enumerate(items):
        out.append('  <div class="board" id="board-%s" role="tabpanel" aria-labelledby="tab-%s"'
                   ' data-board="%s" tabindex="0"%s>\n'
                   '    <div class="stack"%s>%s\n    </div>\n  </div>'
                   % (key, key, key, "" if i == 0 else " hidden", attr, inner.rstrip()))
    return "\n\n".join(out)


def with_tabs(block, tabs):
    """把分段控件插到 section__head 的 </div> 之前。"""
    head = re.search(r'<div class="section__head">.*?</div>', block, re.S)
    return (block[:head.start()] + block[head.start():head.end()][:-len("</div>")].rstrip()
            + "\n" + tabs + "\n    </div>" + block[head.end():])



# —— 核心概念：定义 / 定理 / 例子 三块 ——
CORE_ITEMS = []
for _key, _name in [("def", "定义"), ("thm", "定理"), ("ex", "例子")]:
    _inner, _ = grab_stack(block_core, "core-" + _key)
    CORE_ITEMS.append((_key, _name, ' data-accordion="core-%s"' % _key, _inner,
                       _inner.count('<article class="card"')))
_first_label = block_core.index('<p class="group-label">', block_core.index('id="core-title"'))
_last_end = grab_stack(block_core, "core-ex")[1]
block_core = (with_tabs(block_core[:_first_label], tabs_html("core", "核心概念分组", CORE_ITEMS))
              + "\n\n" + boards_html(CORE_ITEMS) + block_core[_last_end:])
print("核心概念拆板：" + " / ".join("%s %d 张" % (i[1], i[4]) for i in CORE_ITEMS))

# —— 末页：自测 / 课本章末习题 两块 ——
# 原始的 block_quiz 里只有一个 .stack（Q1–Q10），习题段是另给的 EXERCISES，
# 所以这里一次成型：两块 .board 互为兄弟，绝不嵌套。
_q1 = block_quiz.index('<div class="stack">')
_self_inner, _q_end = grab_div(block_quiz, _q1)
QUIZ_ITEMS = [("self", "自测", "", _self_inner, _self_inner.count('<article class="quiz')),
              ("exercise", "章末习题", "", EXERCISES, EXERCISES.count('<article class="quiz'))]
block_quiz = (with_tabs(block_quiz[:_q1], tabs_html("quiz", "自测与习题分组", QUIZ_ITEMS))
              + "\n\n" + boards_html(QUIZ_ITEMS) + block_quiz[_q_end:])
print("末页拆板：" + " / ".join("%s %d 道" % (i[1], i[4]) for i in QUIZ_ITEMS))


# ---------------------------------------------------------------- 卡片清单
card_re = re.compile(
    r'<article class="(card|quiz)" id="([^"]+)">.*?<span>(DEF|THM|PRF|EX|ERR|MTH)</span>',
    re.S)
titles = dict(re.findall(r'<article class="card" id="([^"]+)">.*?<h3 class="card__title">(.*?)</h3>', raw, re.S))


def plain(html):
    text = re.sub(r"<[^>]+>", "", html)
    return re.sub(r"\s+", " ", text).strip()


def drop_trailing_citation(text):
    """只去掉结尾的出处括号（定义 8.2 / 命题 8.5），保留 f(X)、分布（律）这类正文括号。"""
    return re.sub(r"[（(][^）)]*[）)]\s*$", "", text).strip()


def svg_label(html, limit=15):
    """节点标签：保留 sub/sup 的上下标（转成 tspan），只在超长时退化为纯文本截断。"""
    text = drop_trailing_citation(html.strip())
    text = text.replace('<sub>', '<tspan class="node__sub">').replace('</sub>', '</tspan>')
    text = text.replace('<sup>', '<tspan class="node__sup">').replace('</sup>', '</tspan>')
    if len(plain(text)) > limit:
        return plain(text)[:limit] + '…'
    return text


cards = {}
for kind, cid, code in card_re.findall(raw):
    if kind == "card":
        full = plain(titles.get(cid, cid))
        cards[cid] = {"code": code, "full": full, "label": svg_label(titles.get(cid, cid))}
    else:
        cards[cid] = {"code": "Q", "full": cid.upper(), "label": cid.upper()}

# ---------------------------------------------------------------- 地图布局
EDGES = [
    ("c1", "c2", "可测结构"), ("c2", "c3", "前推"), ("c3", "c4", "f(X) 的积分"),
    ("c3", "c5", "F_X"), ("c5", "t10", "逆变换"), ("c2", "c6", "生成 σ-域"),
    ("c6", "t4", "函数表示"), ("c4", "t1", "尾和"), ("c4", "t2", "换测度"),
    ("c3", "t2", "f(X) 的期望"), ("c3", "t3", "边缘"), ("c4", "c7", "矩"),
    ("c7", "t5", "方差公式"), ("c7", "t6", "不等式"), ("c7", "c8", "协方差"),
    ("c8", "t7", "最佳仿射近似"), ("t7", "e3", "n = 1"), ("c4", "c9", "特征函数"),
    ("c9", "t8", "单射"), ("t8", "e5", "高斯"), ("c7", "c10", "Laplace"),
    ("c10", "t9", "单射"), ("c3", "c11", "经典分布"), ("c11", "e1", "几何"),
    ("c11", "e4", "Poisson 逼近"), ("c2", "e2", "随机试验"), ("c3", "e2", "模型差异"),
    ("e2", "p1", "两种模型"), ("t3", "p2", "边缘 vs 联合"), ("c3", "p3", "密度只在零测集上定"),
    ("c4", "p4", "定义 8.3 的前提"), ("c11", "p5", "P(X=k)=(1−p)p^k"), ("c1", "p6", "σ-域的必要性"),
    ("t4", "p7", "命题 8.9"),
]

COLUMNS = [
    ("concept", "概念 / DEFINITIONS", [f"c{i}" for i in range(1, 12)]),
    ("theorem", "定理与命题 / THEOREMS", [f"t{i}" for i in range(1, 11)]),
    ("example", "例题 / EXAMPLES", [f"e{i}" for i in range(1, 6)]),
    ("pitfall", "易错点 / PITFALLS", [f"p{i}" for i in range(1, 8)]),
]

NODE_W, NODE_H, COL_W, GAP = 330, 78, 640, 128
TOP = 150
pos = {}
colof = {}
for col, (_kind, _label, ids) in enumerate(COLUMNS):
    x = 90 + col * COL_W
    for row, cid in enumerate(ids):
        pos[cid] = (x, TOP + row * GAP)
        colof[cid] = col
max_rows = max(len(ids) for _k, _l, ids in COLUMNS)
height = TOP + (max_rows - 1) * GAP + NODE_H + 60
width = 90 + (len(COLUMNS) - 1) * COL_W + NODE_W + 90


def route(a, b):
    """source→target 的连线路径：默认右缘→左缘三次贝塞尔。"""
    ax, ay = pos[a]
    bx, by = pos[b]
    if bx > ax:                                  # 向右：右缘 → 左缘
        x1, y1 = ax + NODE_W, ay + NODE_H / 2
        x2, y2 = bx, by + NODE_H / 2
        mx = (x1 + x2) / 2
        return f"M{x1:.0f},{y1:.0f} C{mx:.0f},{y1:.0f} {mx:.0f},{y2:.0f} {x2:.0f},{y2:.0f}"
    x1, y1 = ax + NODE_W / 2, ay + NODE_H      # 向下/同列：下缘 → 上缘
    x2, y2 = bx + NODE_W / 2, by
    my = (y1 + y2) / 2
    return f"M{x1:.0f},{y1:.0f} C{x1:.0f},{my:.0f} {x2:.0f},{my:.0f} {x2:.0f},{y2:.0f}"


svg = []
svg.append('<svg id="mapSvg" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid meet" '
           'role="img" aria-label="第 8 章知识点关系图">' % (width, height))
svg.append('<defs>'
           '<marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
           'orient="auto-start-reverse"><path d="M0,1 L10,5 L0,9" fill="none" '
           'stroke="var(--accent-soft)" stroke-width="1.6"/></marker>'
           '</defs>')
svg.append('<g id="mapView">')

# 连线（先画，压在节点下面）：跨列的线默认压暗，hover 时才亮起来
for idx, (a, b, label) in enumerate(EDGES):
    d = route(a, b)
    span = abs(colof.get(b, 0) - colof.get(a, 0))
    far = " edge--far" if span >= 2 else ""
    svg.append(
        f'<g class="edge{far}" data-from="{a}" data-to="{b}" data-span="{span}">'
        f'<path class="edge__line" d="{d}" pathLength="1" marker-end="url(#arrow)" '
        f'style="--i:{idx}"/>'
        f'<text class="edge__label" x="0" y="0"><textPath href="#tp{idx}" startOffset="50%" '
        f'text-anchor="middle">{label}</textPath></text>'
        f'<path id="tp{idx}" d="{d}" fill="none" stroke="none"/></g>')

# 列标题
for col, (_kind, label, _ids) in enumerate(COLUMNS):
    x = 90 + col * COL_W
    svg.append(f'<text class="map__col" x="{x}" y="86">{label}</text>')
    svg.append(f'<line class="map__rule" x1="{x}" y1="104" x2="{x + NODE_W}" y2="104"/>')

# 节点
for col, (kind, _label, ids) in enumerate(COLUMNS):
    for cid in ids:
        x, y = pos[cid]
        info = cards.get(cid, {"code": cid.upper(), "full": cid, "label": cid})
        code = info["code"] if kind != "pitfall" else "ERR"
        full = info["full"]
        svg.append(
            f'<g class="node node--{kind}" data-id="{cid}" transform="translate({x},{y})" '
            f'style="--x:{x}px;--y:{y}px" '
            f'tabindex="0" role="link" aria-label="{full}">'
            f'<title>{full}（点击查看知识卡）</title>'
            f'<rect class="node__box" width="{NODE_W}" height="{NODE_H}"/>'
            f'<rect class="node__bar" width="6" height="{NODE_H}"/>'
            f'<text class="node__code" x="22" y="34">{code}</text>'
            f'<text class="node__title" x="22" y="60">{info["label"]}</text>'
            f'</g>')

svg.append('</g></svg>')
MAP_SVG = "\n".join(svg)

# ---------------------------------------------------------------- 缩略图（导航用）
mini = [f'<svg id="miniSvg" viewBox="0 0 {width} {height}" preserveAspectRatio="xMidYMid meet">']
for a, b, _label in EDGES:
    mini.append(f'<path class="mini__edge" d="{route(a, b)}"/>')
for col, (_kind, _label, ids) in enumerate(COLUMNS):
    for cid in ids:
        x, y = pos[cid]
        mini.append(f'<rect class="mini__node" x="{x}" y="{y}" width="{NODE_W}" height="{NODE_H}"/>')
mini.append(f'<rect id="miniView" x="0" y="0" width="{width}" height="{height}"/>')
mini.append('</svg>')
MINI_SVG = "\n".join(mini)

# ---------------------------------------------------------------- 页面骨架
def page(pid, title, en, inner, cls="", note=""):
    return (f'    <section class="page {cls}" id="{pid}" data-title="{title}" data-en="{en}">\n'
            f'      <div class="page__inner">\n{inner}\n      </div>\n    </section>')


reading_path = "\n".join(
    f'        <li><button class="jump" type="button" data-goto="{pid}">'
    f'<span class="jump__no">{i + 1:02d}</span><span class="jump__tx">{title}</span>'
    f'<span class="jump__en">{en}</span></button></li>'
    for i, (pid, title, en) in enumerate([
        ("p-map", "知识地图", "MAP"), ("p-core", "核心概念", "CORE"),
        ("p-pitfalls", "易错点", "PITFALLS"), ("p-quiz", "自测与习题", "SELF CHECK")]))

OVERVIEW = block_meta + f"""

      <section class="section" aria-labelledby="path-title">
        <div class="section__head">
          <h2 class="bar" id="path-title"><span class="bar__sq" aria-hidden="true"></span><span class="bar__tx">阅读路径</span></h2>
          <span class="bar__en">READING PATH</span>
          <span class="section__note">按 ← → 或点下方按钮翻页</span>
        </div>
        <ul class="path">
{reading_path}
        </ul>
      </section>"""

MAP_PAGE = f"""      <div class="mapwrap">
        <div class="map__hint mono">拖拽平移 · 滚轮 / 双击缩放 · 点击节点跳到对应知识卡</div>
        <div class="map__stage">{MAP_SVG}</div>
        <div class="map__mini" style="aspect-ratio:{width} / {height}">{MINI_SVG}</div>
        <div class="map__tools">
          <button class="tool" type="button" data-zoom="in" aria-label="放大">+</button>
          <button class="tool" type="button" data-zoom="out" aria-label="缩小">−</button>
          <button class="tool tool--wide" type="button" data-zoom="fit">适配</button>
        </div>
        <div class="map__legend mono">C 概念 · T 定理/命题 · E 例题 · ERR 易错点</div>
      </div>"""


# ---------------------------------------------------------------- 双主题（运行时切换，不重新出文件）
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
HTML = f"""<!DOCTYPE html>
<!--
  ============================================================================
  知识笔记 · 第 8 章 概率论基础（beta：宽屏翻页式 + 真地图）
  生成：dorothy-html skill
  内容来源：ch8-概率论基础.md（逐句翻译）正文 · 含 §8.3 课本章末习题 8.1–8.16（课本未给解答，标 [待补充]）
  视觉：暖白纸底 / 加灰的橙 / 细线框 / 黑底白字标签条
  字体：中文 霞鹜文楷（缺字体时回退楷体）· 英文数字 Times New Roman
  动效：缓动与补间沿用 cassette 的 ease / Timeline 思路，reduced-motion 下直接跳到终态
  ============================================================================
-->
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CH08 · 概率论基础 — 知识笔记</title>
<style>
{open(str(ROOT / 'beta' / '_style.css'), encoding='utf-8').read() if (ROOT / 'beta' / '_style.css').exists() else ''}
</style>
{THEME_BOOT}
</head>
<body>
<div class="deck" id="deck">
{DECOR}

  <header class="chrome">
    <p class="chrome__id mono">CH08 / <b>概率论基础</b></p>
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
{page('p-overview', '章节概览', 'OVERVIEW', OVERVIEW)}
{page('p-map', '知识地图', 'KNOWLEDGE MAP', MAP_PAGE, cls='page--map')}
{page('p-core', '核心概念', 'CORE CONCEPTS', block_core)}
{page('p-pitfalls', '易错点', 'COMMON PITFALLS', block_pit)}
{page('p-quiz', '自测与习题', 'SELF CHECK · EXERCISES', block_quiz)}
  </main>

  <footer class="pager">
    <button class="pager__btn" type="button" id="prevPage">← 上一页</button>
    <div class="pager__bar"><span class="pager__fill" id="pageFill"></span></div>
    <div class="pager__dots" id="pageDots"></div>
    <span class="pager__src mono">来源：正文 ch8-概率论基础.md（含 §8.3 习题 8.1–8.16）</span>
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

<script>
{open(str(ROOT / 'beta' / '_app.js'), encoding='utf-8').read() if (ROOT / 'beta' / '_app.js').exists() else ''}
</script>
</body>
</html>
"""

OUT.write_text(HTML, encoding="utf-8")
print("wrote", OUT, len(HTML), "chars")
print("nodes", len(pos), "edges", len(EDGES), "viewBox", width, height)
