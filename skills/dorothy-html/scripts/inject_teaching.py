# -*- coding: utf-8 -*-
"""把教学稿机械地填进已生成的卡片 HTML（教学层注入）。

用法：
    python -X utf8 scripts/inject_teaching.py '<产出.html>' --teaching '<产物>_teaching.md'
    python -X utf8 scripts/inject_teaching.py ... --dry-run     # 只报数，不写文件

注入位置（与 assets/note-template.html 的骨架一致）：
    卡头（收起可见）  一句话摘要 → .tk-q 学习问题
    panel 内          直觉 .tk-note → 前置回放 details.is-recall → 教材原文 .tk-src（包裹卡内正文）
                      → 理解检查 .fig__check.tk-check + 答案 details.tk-ans → 出处 .card__src

幂等：先剥离该卡已有的教学层，再按教学稿重建。所以重复跑结果不变，
也能把模板自带的占位内容换成真内容（模板里的 .tk-src 包裹保留不重建）。

一个单元管多张卡时（标题里写 c4 t5+t6），教学层只落第一张 —— 学习问题讲的是
「这个单元」，不是「这一张卡」。
"""
import argparse
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent / "lib"))
import teachlib  # noqa: E402

CARD_RE = re.compile(r'<article class="card" id="([^"]+)">[\s\S]*?</article>')
TAGS = ("div", "details", "p")


def remove_element(html, tag, open_re):
    """删掉第一个匹配 open_re 的 <tag>…</tag> 元素（按同名标签配平），返回 (html, 删了几个)。"""
    n = 0
    while True:
        m = open_re.search(html)
        if not m:
            return html, n
        start, j = m.start(), m.end()
        base = "<" + tag
        close = "</" + tag + ">"
        depth = 0
        cut = -1
        while True:
            nxt_open = html.find(base, j)
            nxt_close = html.find(close, j)
            if nxt_close == -1:
                break
            if nxt_open != -1 and nxt_open < nxt_close:
                depth += 1
                j = nxt_open + len(base)
            elif depth == 0:
                cut = nxt_close + len(close)
                break
            else:
                depth -= 1
                j = nxt_close + len(close)
        if cut == -1:
            return html, n
        # 连前面那行缩进/换行一起吃掉，否则重复跑会不断堆积空行
        s0 = start
        while s0 > 0 and html[s0 - 1] in " \t":
            s0 -= 1
        if s0 > 0 and html[s0 - 1] == "\n":
            s0 -= 1
        html = html[:s0] + html[cut:]
        n += 1


STRIP = [
    ("p", re.compile(r'<p class="tk-q">')),
    ("div", re.compile(r'<div class="tk-note[^"]*"')),      # 兼容 0.1/0.2 的 class="tk-note is-added"
    ("details", re.compile(r'<details class="is-recall">')),
    ("div", re.compile(r'<div class="fig__check tk-check">')),
    ("details", re.compile(r'<details class="tk-ans">')),
]


def strip_layer(seg):
    n = 0
    for tag, pat in STRIP:
        seg, k = remove_element(seg, tag, pat)
        n += k
    return seg, n


def question_html(view):
    if not view["question"]:
        return ""
    return '<p class="tk-q"><b>学习问题</b>%s</p>' % teachlib.inline(view["question"])


def recall_html(items):
    if not items:
        return ""
    names = " · ".join(it[0] for it in items)
    body = "".join('<div class="tk-recall"><b>%s</b>%s</div>'
                   % (teachlib.inline(it[0]), teachlib.render_teaching_md(it[2]))
                   for it in items)
    return ('<details class="is-recall"><summary>回放 · %d 处：%s</summary>%s</details>'
            % (len(items), teachlib.inline(names), body))


def lead_html(view):
    out = []
    if view["intuition"]:
        out.append('<div class="tk-note"><span class="tk-label">直觉</span>%s</div>'
                   % teachlib.render_teaching_md(view["intuition"]))
    rec = recall_html(view["recalls"])
    if rec:
        out.append(rec)
    return "\n            ".join(out)


def check_html(view):
    if not view["check_q"]:
        return ""
    out = ['<div class="fig__check tk-check"><b>理解检查</b>']
    out.append(teachlib.render_teaching_md(view["check_q"]))
    if view["check_a"]:
        out.append('<details class="tk-ans"><summary>看答案</summary>%s</details>'
                   % teachlib.render_teaching_md(view["check_a"]))
    out.append("</div>")
    return "\n            ".join(out)


def inject_card(seg, view):
    """在单张卡的 HTML 片段上注入教学层。返回 (新片段, 做了什么)。"""
    did = []
    q = question_html(view)
    if q:
        m = (re.search(r'<p class="card__summary">[\s\S]*?</p>', seg)
             or re.search(r'<div class="card__head">[\s\S]*?</div>', seg))
        if m:
            seg = seg[:m.end()] + "\n        " + q + seg[m.end():]
            did.append("学习问题")

    m = re.search(r'<div class="panel__inner[^"]*">', seg)
    lead, chk = lead_html(view), check_html(view)
    if m and (lead or chk):
        src = seg.find('<p class="card__src"')
        if src == -1:
            src = len(seg)
        inner = seg[m.end():src].strip()
        if not re.search(r'<div class="tk-src[^"]*"', seg):
            if inner:
                inner = ('<div class="tk-src"><p class="tk-src-label">教材原文</p>'
                         '<div class="tk-src-body">%s</div></div>' % inner)
        seg = (seg[:m.end()] + "\n            " + lead + "\n            "
               + inner + "\n            " + chk + "\n            " + seg[src:])
        if lead:
            did.append("直觉/回放")
        if chk:
            did.append("理解检查")
    return seg, did


def main():
    ap = argparse.ArgumentParser(description="把教学稿注入卡片的 HTML")
    ap.add_argument("html")
    ap.add_argument("--teaching", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    page = pathlib.Path(a.html)
    raw = page.read_text(encoding="utf-8")
    units, _clusters = teachlib.parse(a.teaching)
    bc = teachlib.by_card(units)

    cards = set(m.group(1) for m in CARD_RE.finditer(raw))
    done, missing, unstripped, seen = [], [], [], set()
    for unit in units:
        target = next((c for c in unit["cards"] if c in cards), None)
        if target is None:
            missing.append((unit["id"], "/".join(unit["cards"]) or "（单元标题没写卡 id）"))
            continue
        if target in seen:      # 一个单元管多张卡时只落首卡；别的单元又来要同一张卡就跳过
            continue
        seen.add(target)
        anchor = '<article class="card" id="%s">' % target
        start = raw.index(anchor)
        end = raw.index("</article>", start) + len("</article>")
        seg = raw[start:end]
        seg, removed = strip_layer(seg)
        if removed:
            unstripped.append((target, removed))
        seg, did = inject_card(seg, teachlib.unit_view(unit))
        raw = raw[:start] + seg + raw[end:]
        if did:
            done.append((target, unit["id"], did))
        else:
            missing.append((unit["id"], target))

    print("教学稿单元 %d（覆盖卡 %d 张）；注入成功 %d 张" % (len(units), len(bc), len(done)))
    for cid, uid, did in done:
        print("  %-4s ← 单元 %-3s  %s" % (cid, uid, " / ".join(did)))
    if unstripped:
        print("重建前剥离旧教学层 %d 张卡（%s）"
              % (len(unstripped), "、".join("%s×%d" % (c, n) for c, n in unstripped)))
    if missing:
        print("!! %d 处没落上：" % len(missing))
        for uid, cid in missing:
            print("   单元 %s → 卡 %s 在页面里找不到（或教学稿未给内容）" % (uid, cid))

    if a.dry_run:
        print("（--dry-run：没有写文件）")
        return 0
    if not done:
        print("ABORT: 一张卡都没注入，未写文件")
        return 1
    page.write_text(raw, encoding="utf-8")
    print("写入", page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
