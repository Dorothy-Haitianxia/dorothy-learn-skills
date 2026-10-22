# -*- coding: utf-8 -*-
"""教学稿（Teaching Layer）的解析与渲染 —— skill 侧唯一实现。

契约见 skills/dorothy-html/reference/teaching-contract.md。
本模块只做纯函数：所有入口都显式接教学稿路径，不持有全局状态。
  - scripts/inject_teaching.py 用它把教学稿机械地填进卡片

解析失败一律抛异常：宁可构建失败，也不要静默生成一份缺图说的页面。
"""
import pathlib
import re

BQ = chr(96)  # 反引号，行内码标记

UNIT_RE = re.compile(r"^### ([A-F]\d+) (.+)$")
CLUSTER_RE = re.compile(r"^## (.+)$")
FIELD_RE = re.compile(r"^\*\*([^*]+?)\*\*(?:（([^）]*)）)?\s*[：:]\s*(.*)$")
CARD_RE = re.compile(r"(?:^|[^0-9A-Za-z])([ctep]\d+)(?![0-9A-Za-z])")
FIGNO_RE = re.compile(r"图\s*(\d+)")

# 渲染进 HTML 的教学层字段（其余字段只服务于写卡人，不进页面）
HTML_FIELDS = ["直觉", "前置回放", "检查"]
# 每张图三段文案
FIG_FIELDS = {"图前引导": "lead", "图后解释": "follow", "图理解检查": "check"}


def _read(path):
    return pathlib.Path(path).read_text(encoding="utf-8")


def parse(path):
    """返回 (units, clusters)。units 按教学稿顺序；clusters 是 [{title, units}]。"""
    text = _read(path)
    units, clusters = [], []
    state = {"unit": None, "field": None, "cluster": None}

    def flush():
        f = state["field"]
        if f is not None and state["unit"] is not None:
            name, note, buf = f
            body = "\n".join(buf).strip()
            key = name.strip()
            if key in FIG_FIELDS:
                m = FIGNO_RE.search(note or "")
                if not m:
                    raise ValueError("单元 %s 的「%s」缺少「图 N」标注" % (state["unit"]["id"], key))
                fig = state["unit"]["figs"].setdefault(m.group(1), {})
                fig[FIG_FIELDS[key]] = body
            elif key not in state["unit"]["fields"]:
                state["unit"]["fields"][key] = body
            else:
                state["unit"]["fields"][key] += "\n\n" + body
        state["field"] = None

    for ln in text.split("\n"):
        m = UNIT_RE.match(ln)
        if m:
            flush()
            params = m.group(2)
            u = {"id": m.group(1), "title": params, "cards": CARD_RE.findall(params),
                 "fields": {}, "figs": {}, "cluster": state["cluster"]}
            units.append(u)
            if state["cluster"] is not None:
                state["cluster"]["units"].append(u)
            state["unit"] = u
            continue
        if ln.startswith("## ") and not ln.startswith("### "):
            flush()
            head = CLUSTER_RE.match(ln).group(1).strip()
            c = {"title": head, "units": []}
            clusters.append(c)
            state["cluster"] = c
            state["unit"] = None
            continue
        if state["unit"] is None:
            continue
        m = FIELD_RE.match(ln)
        if m:
            flush()
            state["field"] = (m.group(1), m.group(2) or "",
                              [m.group(3)] if m.group(3).strip() else [])
            continue
        if ln.startswith(">"):
            continue
        if state["field"] is not None:
            state["field"][2].append(ln)
    flush()
    return units, clusters


def clusters_with_units(clusters):
    """只要含单元的簇（章首诊断那一节没有单元，排除）。"""
    return [c for c in clusters if c["units"]]


def by_card(units):
    """卡 id → [单元]，一个单元可以管多张卡。"""
    out = {}
    for u in units:
        for c in u["cards"]:
            out.setdefault(c, []).append(u)
    return out


def fig_prose(units, card_id, figno):
    """给正文图插三段文案用；缺字段直接抛错。"""
    for u in units:
        if card_id not in u["cards"]:
            continue
        fig = u["figs"].get(str(figno))
        if fig:
            missing = [k for k in ("lead", "follow", "check") if not fig.get(k)]
            if missing:
                raise ValueError("单元 %s 的图 %s 缺少 %s" % (u["id"], figno, "、".join(missing)))
            return {"lead": fig["lead"], "follow": fig["follow"], "check": fig["check"]}
    raise KeyError("教学稿里找不到卡 %s 的图 %s 文案" % (card_id, figno))


# ---------------------------------------------------------------- markdown 轻量渲染
_INLINE = [
    (re.compile(r"\*\*(.+?)\*\*"), r"<b>\1</b>"),
    (re.compile(r"(?<![\w/])" + BQ + r"([^" + BQ + r"]+?)" + BQ), r"<code>\1</code>"),
]


def inline(text):
    out = text
    for pat, rep in _INLINE:
        out = pat.sub(rep, out)
    return out


def _table(rows):
    # 单元格里允许写 \| 表示竖线本身（附录那条 μ(A) = |A| 会用到）
    cells = [[c.strip().replace("\x00PIPE\x00", "|")
              for c in r.strip().strip("|").replace("\\|", "\x00PIPE\x00").split("|")]
             for r in rows]
    head, body = cells[0], cells[2:]
    out = ['<table class="teach-table"><thead><tr>']
    out += ["<th>%s</th>" % inline(c) for c in head]
    out.append("</tr></thead><tbody>")
    for r in body:
        out.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def md_lite(text):
    """段落 / 无序列表 / 有序列表 / 表格 / 粗体 / 行内码。教学稿只用这些。"""
    lines = text.split("\n")
    blocks, buf, i = [], [], 0

    def flush_para():
        if buf:
            blocks.append("<p>%s</p>" % inline(" ".join(x.strip() for x in buf)))
            del buf[:]

    while i < len(lines):
        s = lines[i].strip()
        if not s:
            flush_para()
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            flush_para()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            blocks.append(_table(rows))
            continue
        if re.match(r"^[-*]\s+", s):
            flush_para()
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(re.sub(r"^[-*]\s+", "", lines[i].strip()))
                i += 1
            blocks.append("<ul>" + "".join("<li>%s</li>" % inline(x) for x in items) + "</ul>")
            continue
        if re.match(r"^\d+\.\s+", s):
            flush_para()
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(re.sub(r"^\d+\.\s+", "", lines[i].strip()))
                i += 1
            blocks.append("<ol>" + "".join("<li>%s</li>" % inline(x) for x in items) + "</ol>")
            continue
        buf.append(s)
        i += 1
    flush_para()
    return "\n".join(blocks)


def is_added(text):
    return "[增补]" in text


def strip_added(text):
    return text.replace("[增补]", "").strip()


# ---------------------------------------------------------------- 卡片正文用：字段拆解
# 教学稿里同一个字段写法不统一（列表 / 单条 / 「无新增」），拆解集中在这里。
RECALL_ITEM = re.compile(r"^\*\*(.+?)\*\*(?:（([^）]*)）)?\s*[：:]\s*([\s\S]*)$")
ANSWER_MARK = re.compile(r"\*\*答案\*\*\s*[：:]?\s*")


# 「无新增」「无」「无（本节只用上面已回放过的概念）」。统一当空表，不落进页面。
NO_RECALL = re.compile(r"^无(?:\s*[（(].*)?$|^无新增")
# 术语名里不该出现的尾巴：写成「**控制收敛定理** 已在 C3 回放」「**A**已回放；此处新增 **B**」
# 这类句子时，截到第一个这类词之前，否则摘要行会被一整句话污染。
TERM_JUNK = re.compile(r"\*\*|已回放|已在|此处|本章已给")


def _term(t):
    return TERM_JUNK.split(t.strip())[0].strip(" 　：:，,。；;")


def recalls(text):
    """「前置回放」→ [(术语, 备注, 正文)]；「无新增」「无（…）」= 空表。"""
    items = []
    for ln in (text or "").strip().split("\n"):
        s = re.sub(r"^[-*]\s+", "", ln.strip()).strip()
        if not s or NO_RECALL.match(s):
            continue
        m = RECALL_ITEM.match(s)
        if m:
            items.append((_term(m.group(1)) or "回放", (m.group(2) or "").strip(), m.group(3).strip()))
            continue
        # 兜底：写成「**术语** 已在 C2 回放，此处只提醒…」这种没有冒号的形式时，
        # 取正文里第一个粗体当术语名，否则整条会挂成「回放 · 1 处：回放」这种空标签。
        b = re.search(r"\*\*(.+?)\*\*", s)
        if b:
            term = b.group(1).strip()
            body = (s[:b.start()] + s[b.end():]).strip(" 　：:，,。")
            items.append((term, "", body))
        else:
            items.append(("回放", "", s))
    return items


def check_parts(text):
    """「检查」→ (问题, 答案)；答案里保留「检查点：…」那半句（它是解释）。"""
    t = (text or "").strip()
    m = ANSWER_MARK.search(t)
    if not m:
        return t, ""
    return t[:m.start()].strip(), t[m.end():].strip()


ADD_MARK = "[增补]"
ADD_SENTINEL = "\x00ADD\x00"


def render_teaching_md(text):
    """教学层 markdown → HTML，并把 [增补] 段落标成 .is-added（逐段可辨）。

    读者要能判断哪句是书、哪句是导师，但正文里不放任何字样标记 —— 只用段落级细线
    区分。[增补] 三个字本身在读稿时删掉。
    """
    html = md_lite((text or "").replace(ADD_MARK, ADD_SENTINEL))

    def fix(m):
        tag = m.group(0)
        if ADD_SENTINEL not in tag:
            return tag
        if tag.startswith("<p>"):
            tag = tag.replace("<p>", '<p class="is-added">', 1)
        elif tag.startswith("<li>"):
            tag = tag.replace("<li>", '<li class="is-added">', 1)
        return tag.replace(" " + ADD_SENTINEL, "").replace(ADD_SENTINEL, "")

    return re.sub(r"<(?:p|li)>[\s\S]*?</(?:p|li)>", fix, html)


APPENDIX_RE = re.compile(r"^#\s*附[:：].*$", re.M)


def appendix(path):
    """文末「我补了什么」清单 → (标题, markdown 正文)；没有就返回 (None, "")。"""
    text = _read(path)
    m = APPENDIX_RE.search(text)
    if not m:
        return None, ""
    rest = text[m.end():]
    nxt = re.search(r"^#\s", rest, re.M)   # 后面还有「验收记录」等章节，读者页不要
    body = rest[:nxt.start()] if nxt else rest
    return m.group(0).lstrip("#").strip(), body.strip()


def unit_view(unit):
    """一张卡要用的教学层内容（缺字段给空串，不抛错：简单单元本来就写得少）。"""
    f = unit["fields"]
    q, a = check_parts(f.get("检查", ""))
    return {
        "id": unit["id"],
        "question": f.get("学习问题", "").strip(),
        "intuition": f.get("直觉", "").strip(),
        "recalls": recalls(f.get("前置回放", "")),
        "check_q": q,
        "check_a": a,
        "source": f.get("来源", "").strip(),
    }
