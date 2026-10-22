# -*- coding: utf-8 -*-
"""核心概念区的互引标记。

规则（按已确认的四项决定 + 两项补充）：
  · 只在 #core 里的 .panel__inner（展开内容）中标记；出处行与插图 SVG 内不标；
  · 目标可以是任何“更早的卡”（概念 / 定理 / 例题，按文档顺序）；
  · 同一张卡里，同一个目标只标文中最早那一处；
  · 降噪：随机变量 / 随机向量 / 期望 / 分布 / 方差 这类每张卡都出现的基础词不标，
    只留编号引用、记号（𝔼[X]、var(X)、cov、F_X…）与专有概念名；
  · 边界守卫：编号后不能紧跟数字（定义 8.1 ≠ 定义 8.12），
    术语前后不能接续成别的专名（分布·函数 / 协·方差）。

输出：<a href="#c3" class="ref" data-ref="c3">…</a>
      用 <a> 而不是 <button>：没有 JS 时退化为原生锚点跳转。
"""
import pathlib
import re
import sys
from collections import defaultdict

# 不设默认路径：产物在哪儿只有调用方知道（产物含教材衍生内容，一律不入库）
HTML_PATH = None

# ── 别名表：(目标卡, 术语（纯文本形态）, 是否正则, 备注) ──────────────────
ALIASES = [
    ("c1", "概率空间", None, "基础对象，出现少且有信息量"),
    ("c1", "Kolmogorov 公理", None, ""),
    ("c2", "定义 8.1", r"定义\s*8\.1(?!\d)", "正则"),
    ("c2", "可测函数", None, "定义 8.1 的等价说法"),
    ("c3", "定义 8.2", r"定义\s*8\.2(?!\d)", "正则"),
    ("c3", "分布（律）", None, "本章对 law 的固定写法"),
    ("c3", "分布律", None, ""),
    ("c3", "同分布", None, ""),
    ("c4", "定义 8.3", r"定义\s*8\.3(?!\d)", "正则"),
    ("c4", "数学期望", None, ""),
    ("c4", "𝔼[X]", None, "记号，出现多但每卡只标一处"),
    ("c5", "分布函数", None, "专有概念名"),
    ("c5", "FX", None, "记号 F_X（上下标已并成纯文本）"),
    ("c6", "定义 8.8", r"定义\s*8\.8(?!\d)", "正则"),
    ("c6", "σ(X)", r"σ\(X\)", "正则"),
    ("c6", "由 X 生成的 σ-域", None, ""),
    ("c7", "定义 8.10", r"定义\s*8\.10(?!\d)", "正则"),
    ("c7", "var(X)", None, "记号"),
    ("c7", "标准差", None, ""),
    ("c7", "绝对矩", None, ""),
    ("c8", "定义 8.12", r"定义\s*8\.12(?!\d)", "正则"),
    ("c8", "协方差矩阵", None, ""),
    ("c8", "协方差", None, "专有概念名"),
    ("c8", "cov(X,Y)", None, ""),
    ("c9", "定义 8.14", r"定义\s*8\.14(?!\d)", "正则"),
    ("c9", "命题 8.17", r"命题\s*8\.17(?!\d)", "正则"),
    ("c9", "特征函数", None, ""),
    ("c9", "ΦX", None, "记号 Φ_X"),
    ("c9", "Fourier 变换", None, ""),
    ("c10", "定义 8.18", r"定义\s*8\.18(?!\d)", "正则"),
    ("c10", "定义 8.20", r"定义\s*8\.20(?!\d)", "正则"),
    ("c10", "Laplace 变换", None, ""),
    ("c10", "生成函数", None, ""),
    ("c10", "LX", None, "记号 L_X"),
    ("c10", "gX", None, "记号 g_X"),
    ("c11", "Bernoulli 分布", None, "经典分布清单条目"),
    ("c11", "二项分布", None, ""),
    ("c11", "几何分布", None, ""),
    ("c11", "Poisson 分布", None, ""),
    ("c11", "指数分布", None, ""),
    ("c11", "Gamma 分布", None, ""),
    ("c11", "Cauchy 分布", None, ""),
    ("c11", "高斯分布", None, ""),
    ("c11", "正态分布", None, ""),
    ("c11", "无记忆性", None, "指数分布的特征性质"),
    ("t1", "命题 8.4", r"命题\s*8\.4(?!\d)", "正则"),
    ("t2", "命题 8.5", r"命题\s*8\.5(?!\d)", "正则"),
    ("t3", "命题 8.6", r"命题\s*8\.6(?!\d)", "正则"),
    ("t3", "边缘分布", None, ""),
    ("t3", "边缘密度", None, ""),
    ("t4", "命题 8.9", r"命题\s*8\.9(?!\d)", "正则"),
    ("t5", "命题 8.11", r"命题\s*8\.11(?!\d)", "正则"),
    ("t6", "Markov 不等式", None, ""),
    ("t6", "Bienaymé–Chebyshev 不等式", None, ""),
    ("t6", "Chebyshev", None, ""),
    ("t7", "命题 8.13", r"命题\s*8\.13(?!\d)", "正则"),
    ("t7", "线性回归", None, ""),
    ("t7", "最佳仿射近似", None, ""),
    ("t8", "定理 8.16", r"定理\s*8\.16(?!\d)", "正则"),
    ("t8", "引理 8.15", r"引理\s*8\.15(?!\d)", "正则"),
    ("t9", "定理 8.19", r"定理\s*8\.19(?!\d)", "正则"),
    ("t10", "引理 8.7", r"引理\s*8\.7(?!\d)", "正则"),
    ("e2", "Bertrand 悖论", None, ""),
    ("e3", "回归直线", None, ""),
    ("e4", "二项逼近", None, ""),
]

# ── 左侧守卫：命中前面这些词说明它属于别的专名 ──
EXCLUDE = {
    "c3": ["二项", "Bernoulli", "几何", "均匀", "指数", "Gamma", "Γ", "Cauchy", "高斯", "正态",
            "边缘", "条件", "联合", "离散", "连续", "复合", "退", "超几何", "稳定", "先验", "后验"],
    "c4": ["条件", "数学"],
    "c7": ["协"],
    "c8": [],
}
# ── 右侧守卫：命中后面紧跟这些词说明它是更长专名的一部分 ──
SUFFIX_BLOCK = {
    "c3": ["函数", "律", "列", "族"],
    "c7": ["矩阵"],          # 方差矩阵不存在，这里是兜底；协方差矩阵已由前缀挡掉
    "c5": ["FX"],            # 防 F_X 被 D 等前缀吞并（占位，实际不触发）
}

INLINE_TAGS = {'sub', 'sup', 'strong', 'em', 'i', 'b', 'code', 'span', 'tspan', 'small', 'u'}
MASK_PATTERNS = [r'<svg\b.*?</svg>', r'<p class="card__src">.*?</p>']
FOREIGN_REFS = r"(?:定理|命题|引理|推论|定义|例)\s*(?:1|2|3|4|5|7|9|10|11|14)\.\d+"


# ─────────────────────────────────────────────────────────────
def mask(html, patterns):
    """把不参与标记的区域替换成等长空格：偏移不变，但匹配不到。"""
    chars = list(html)
    for pat in patterns:
        for m in re.finditer(pat, html, re.S):
            for i in range(m.start(), m.end()):
                if chars[i] not in '\r\n':
                    chars[i] = ' '
    return ''.join(chars)


def plain_with_map(html):
    """去标签得纯文本 + 每个字符对应的 HTML 下标。

    行内标签（sub/sup/strong…）不插占位，于是 F<sub>X</sub> 读作 FX；
    块级标签插一个空格，避免跨元素误配。
    """
    text, spans, i = [], [], 0
    for m in re.finditer(r'<[^>]+>', html):
        for k, ch in enumerate(html[i:m.start()]):
            text.append(ch)
            spans.append(i + k)
        name = re.match(r'<\s*/?\s*([a-zA-Z0-9]+)', m.group(0))
        inline = name and name.group(1).lower() in INLINE_TAGS
        # 行内标签不占位（否则列表下标与拼接后的字符串下标会整体错位）；
        # 块级标签占一个空格，避免跨元素误配。
        if not inline:
            text.append(' ')
            spans.append(None)
        i = m.end()
    for k, ch in enumerate(html[i:]):
        text.append(ch)
        spans.append(i + k)
    return ''.join(text), spans


def extract_cards(html, section_id='core'):
    """按文档顺序取卡片：id、标题、展开内容 HTML、以及它在 html 里的区间。"""
    start = html.index('id="%s"' % section_id)
    end = html.index('</section>', start)
    section = html[start:end]
    cards = []
    for m in re.finditer(r'<article class="card" id="([^"]+)">', section):
        cid = m.group(1)
        art_end = section.index('</article>', m.end())
        block = section[m.end():art_end]
        title = re.search(r'<h3 class="card__title">(.*?)</h3>', block, re.S)
        panel = re.search(r'<div class="panel__inner[^"]*">', block)
        if panel:
            body_start = m.end() + panel.end()
            body_end = m.end() + block.rindex('</div>')
            body = section[body_start:body_end]
        else:
            body_start = body_end = m.end()
            body = ''
        cards.append({
            "id": cid,
            "title": re.sub(r'<[^>]+>', '', title.group(1)) if title else cid,
            "body": body,
            "b0": start + body_start,
            "b1": start + body_end,
        })
    return cards


def numbered_guard(text, end, term):
    if not term[-1].isdigit():
        return False
    after = text[end:end + 2]
    if after[:1].isdigit():
        return True
    return after[:2].startswith('.') and len(after) > 1 and after[1].isdigit()


def resolve(text, card, order, compiled, sink=None):
    """在一张卡里挑出要标的区间：先消解重叠，再对每个目标只留最早一处。"""
    index = order[card["id"]]
    cands = []
    for target, term, rx, note in compiled:
        if target not in order or order[target] >= index:
            continue
        for m in rx.finditer(text):
            s, e = m.start(), m.end()
            if numbered_guard(text, e, term):
                continue
            before = text[max(0, s - 6):s]
            bad = [w for w in EXCLUDE.get(target, []) if before.endswith(w)]
            if bad and sink is not None:
                sink.append((card["id"], target, term,
                             text[max(0, s - 14):e + 10].replace('\n', ' '), '前接 ' + bad[0]))
                continue
            if bad:
                continue
            after = text[e:e + 2]
            tail = [w for w in SUFFIX_BLOCK.get(target, []) if after.startswith(w)]
            if tail and sink is not None:
                sink.append((card["id"], target, term,
                             text[max(0, s - 14):e + 10].replace('\n', ' '), '后接 ' + tail[0]))
                continue
            if tail:
                continue
            cands.append((s, e, target, term))

    cands.sort(key=lambda c: (c[0], -(c[1] - c[0])))
    used, picked = [], []
    for s, e, target, term in cands:
        if any(s < b and a < e for a, b in used):
            continue
        used.append((s, e))
        picked.append((s, e, target, term))

    first, later = {}, []
    for s, e, target, term in sorted(picked):
        if target in first:
            later.append((card["id"], target, term,
                          text[max(0, s - 14):e + 10].replace('\n', ' ')))
        else:
            first[target] = (s, e, target, term)
    return list(first.values()), later


def compile_aliases():
    return [(t, term, re.compile(pat if pat else re.escape(term)), note)
            for t, term, pat, note in ALIASES]


def balanced_span(html, start, end):
    """把 [start, end) 扩展到行内标签的完整边界。

    纯文本里的 FX 往往来自 F<sub>X</sub>：直接按字符偏移插桩会得到
    L<sub>X</a></sub> 这种坏嵌套，所以要把 <sub>…</sub> 整体纳进来。
    """
    changed = True
    while changed:
        changed = False
        seg = html[start:end]
        stack = []
        for m in re.finditer(r'<(/?)([a-zA-Z]+)[^>]*>', seg):
            closing, name = m.group(1), m.group(2).lower()
            if name not in INLINE_TAGS:
                continue
            if closing:
                if stack and stack[-1] == name:
                    stack.pop()
            else:
                stack.append(name)
        if stack:                                   # 有行内标签在区间内未闭合
            name = stack[-1]
            close = html.find('</%s>' % name, end)
            if close == -1:
                break
            end = close + len(name) + 3
            changed = True
            continue
        prefix = html[:start]                       # start 是否落在某个行内标签内部
        for m in reversed(list(re.finditer(r'<(/?)([a-zA-Z]+)[^>]*>', prefix))):
            closing, name = m.group(1), m.group(2).lower()
            if name not in INLINE_TAGS:
                continue
            if not closing and not re.search(r'</%s>' % name, html[m.end():start]):
                start = m.start()
                changed = True
            break
    return start, end


def mark_block(block):
    """把 #core 区块里的互引术语包成 <a class="ref">，返回（新 HTML, 统计）。"""
    cards = extract_cards(block)
    order = {c["id"]: n for n, c in enumerate(cards)}
    compiled = compile_aliases()
    edits = []
    total, suppressed, excluded = [], [], []
    for card in cards:
        text, spans = plain_with_map(mask(card["body"], MASK_PATTERNS))
        marks, later = resolve(text, card, order, compiled, sink=excluded)
        suppressed.extend(later)
        for s, e, target, term in marks:
            hs, he = spans[s], spans[e - 1]
            if hs is None or he is None:
                continue
            edits.append((card["b0"] + hs, card["b0"] + he + 1, target, card["id"], term))
            total.append((card["id"], target, term, text[max(0, s - 16):e + 14]))
    for start, end, target, _src, _term in sorted(edits, key=lambda t: -t[0]):
        start, end = balanced_span(block, start, end)
        snippet = block[start:end]
        if '<a ' in snippet or '<svg' in snippet or '<figure' in snippet:
            continue
        wrapped = '<a href="#%s" class="ref" data-ref="%s">%s</a>' % (target, target, snippet)
        block = block[:start] + wrapped + block[end:]
    return block, total, suppressed, excluded


def write_report(cards, marks, suppressed, excluded, foreign, path):
    order = {c["id"]: n for n, c in enumerate(cards)}
    title = {c["id"]: c["title"] for c in cards}
    out = ['# 核心概念互引 · 标记清单（已写入页面）\n',
           '规则：只在核心概念区的展开内容里标记；目标可以是任何更早的卡；',
           '同一张卡里同一目标只标最早一处；出处行与插图 SVG 内不标；基础通用词不标。\n',
           '\n## 一、别名表\n', '| 目标卡 | 术语 | 类型 | 备注 |', '|---|---|---|---|']
    for target, term, pat, note in ALIASES:
        out.append('| %s %s | `%s` | %s | %s |' % (
            target.upper(), title.get(target, '')[:12], term, '正则' if pat else '字面', note))
    out.append('\n## 二、守卫词表\n')
    out.append('**左侧（命中前面这些词则不标）**\n')
    for target, words in EXCLUDE.items():
        if words:
            out.append('- %s：%s' % (target.upper(), '、'.join(words)))
    out.append('\n**右侧（命中后面这些词则不标）**\n')
    for target, words in SUFFIX_BLOCK.items():
        out.append('- %s：%s' % (target.upper(), '、'.join(words)))
    out.append('\n## 三、会标出的位置（共 %d 处）\n' % len(marks))
    by_src = defaultdict(list)
    for src, target, term, ctx in marks:
        by_src[src].append((order[target], target, term, ctx))
    for card in cards:
        items = sorted(by_src.get(card["id"], []))
        if not items:
            continue
        out.append('### %s %s' % (card["id"].upper(), title[card["id"]]))
        for _n, target, term, ctx in items:
            out.append('- 「%s」→ **%s** %s  \n  `…%s…`' % (
                term, target.upper(), title.get(target, '')[:14], ctx.strip()))
        out.append('')
    out.append('\n## 四、同卡重复出现、按规则不标（%d 处）\n' % len(suppressed))
    for src, target, term, ctx in suppressed:
        out.append('- %s：`%s` → %s　`…%s…`' % (src.upper(), term, target.upper(), ctx.strip()[:60]))
    out.append('\n## 五、被守卫拦下（%d 处）\n' % len(excluded))
    for src, target, term, ctx, why in excluded:
        out.append('- %s：`%s`（%s，本来会连到 %s）　`…%s…`' % (
            src.upper(), term, why, target.upper(), ctx.strip()[:56]))
    out.append('\n## 六、属于其它章节的编号引用（保持普通文本）\n')
    for name, n in sorted(foreign.items(), key=lambda kv: -kv[1]):
        out.append('- `%s` ×%d' % (name, n))
    path.write_text('\n'.join(out), encoding='utf-8')


def core_section(html):
    """取出包含 id="core" 的整个 <section>…</section>。"""
    anchor = html.index('id="core"')
    start = html.rindex('<section', 0, anchor)
    end = html.index('</section>', anchor) + len('</section>')
    return start, end


def main(argv):
    path = HTML_PATH
    if '--file' in argv:
        path = pathlib.Path(argv[argv.index('--file') + 1]).resolve()
    elif path is None:
        raise SystemExit(__doc__)
    raw = path.read_text(encoding="utf-8")

    if '--apply' in argv:
        start, end = core_section(raw)
        marked, total, suppressed, _excluded = mark_block(raw[start:end])
        out = pathlib.Path(argv[argv.index('--out') + 1]).resolve() if '--out' in argv \
            else path.with_name(path.stem + '-marked.html')
        out.write_text(raw[:start] + marked + raw[end:], encoding="utf-8")
        print("已写入 %d 处互引标记（同卡重复不标 %d）→ %s" % (len(total), len(suppressed), out))
        return 0

    cards = extract_cards(raw)
    order = {c["id"]: n for n, c in enumerate(cards)}
    compiled = compile_aliases()
    marks, suppressed, excluded, foreign = [], [], [], defaultdict(int)
    for card in cards:
        text, _spans = plain_with_map(mask(card["body"], MASK_PATTERNS))
        for m in re.finditer(FOREIGN_REFS, text):
            foreign[m.group(0)] += 1
        got, later = resolve(text, card, order, compiled, sink=excluded)
        suppressed.extend(later)
        for s, e, target, term in got:
            marks.append((card["id"], target, term,
                          text[max(0, s - 16):e + 14].replace('\n', ' ')))
    report = path.with_name(path.stem + '_refs-review.md')
    write_report(cards, marks, suppressed, excluded, foreign, report)
    print("会标出 %d 处；同卡重复不标 %d 处；被守卫拦下 %d 处" % (
        len(marks), len(suppressed), len(excluded)))
    print("报告：%s" % report)
    by_src = defaultdict(list)
    for src, target, term, ctx in marks:
        by_src[src].append((order[target], target, term))
    for card in cards:
        items = sorted(by_src.get(card["id"], []))
        if items:
            print("  %-4s %s" % (card["id"].upper(),
                                 '；'.join('「%s」→%s' % (t, tg.upper()) for _n, tg, t in items)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
