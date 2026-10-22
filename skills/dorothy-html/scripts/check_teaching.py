#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""check_teaching.py — 校验教学稿是否符合 reference/teaching-contract.md

用法：
    python scripts/check_teaching.py beta/ch08-概率论基础_teaching.md
    python scripts/check_teaching.py <教学稿> --html <页面> --plan <清单>

退出码：0 全部通过；1 有错误。
"""
import io
import re
import sys

REQUIRED = ["学习问题", "正式", "检查", "图示任务", "前置回放", "来源"]
LEVEL_RE = re.compile(r"档位[^\n]{0,24}?(A\+|A|B|C)")
BT = chr(96)
CARD_RE = re.compile(BT + r"(c\d+|t\d+|e\d+|p\d+)" + BT)
SCORE_RE = re.compile(r"\d\s*/\s*\d\s*/\s*\d\s*/\s*\d")
BANNED = ["更清晰", "更美观", "更直观", "更易懂"]
FIG_RE = re.compile(r"\*\*图示任务\*\*[^\n]*出图")


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


UNIT_HEAD = re.compile(r"^### ([A-F]\d+) ")


def split_units(text):
    """按 '### <簇字母><序号> ' 切单元，返回 [(标题, 块文本)]。"""
    units, cur_title, cur_buf = [], None, []
    for ln in text.split("\n"):
        if UNIT_HEAD.match(ln):
            if cur_title is not None:
                units.append((cur_title, "\n".join(cur_buf)))
            cur_title, cur_buf = ln[4:].strip(), []
        elif ln.startswith("## ") or ln.startswith("# "):
            if cur_title is not None:
                units.append((cur_title, "\n".join(cur_buf)))
                cur_title, cur_buf = None, []
        elif cur_title is not None:
            cur_buf.append(ln)
    if cur_title is not None:
        units.append((cur_title, "\n".join(cur_buf)))
    return units


def is_fig_unit(chunk):
    return bool(FIG_RE.search(chunk)) and "不出图" not in chunk


def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 1
    path = argv[0]
    html_path = argv[argv.index("--html") + 1] if "--html" in argv else None
    plan_path = argv[argv.index("--plan") + 1] if "--plan" in argv else None

    text = read(path)
    errors, warns = [], []

    cut = text.find("\n# 附：")
    body = text[:cut] if cut > 0 else text
    tail = text[cut:] if cut > 0 else ""

    m = LEVEL_RE.search(text[:3000])
    if not m:
        errors.append("缺少读者档位声明（A / A+ / B / C）")
    level = m.group(1) if m else "?"

    clusters = re.findall(r"^## (.+)$", body, re.M)
    clusters = [c for c in clusters if "簇" in c]
    if len(clusters) < 2:
        errors.append("分簇不足：找到 %d 个分簇标题（至少 2）" % len(clusters))

    units = split_units(body)
    if not units:
        errors.append("没有找到任何 ### 单元")
    for title, chunk in units:
        for f in REQUIRED:
            if ("**%s**" % f) not in chunk:
                errors.append("单元 %s 缺必需字段：%s" % (title.split("（")[0], f))
        for ln in chunk.split("\n"):
            if "**检查**" in ln and "**答案**" not in ln:
                errors.append("单元 %s 的检查没有答案" % title.split("（")[0])
                break
        for ln in chunk.split("\n"):
            if "**图示任务**" in ln:
                if "不出图" in ln:
                    if not SCORE_RE.search(ln):
                        errors.append("单元 %s 不出图但缺四维分数" % title.split("（")[0])
                    if "理由" not in ln:
                        errors.append("单元 %s 不出图但缺理由" % title.split("（")[0])
                elif "出图" not in ln:
                    errors.append("单元 %s 图示任务未写『出图』或『不出图』" % title.split("（")[0])
                break

    n_mark = sum(1 for ln in body.split("\n")
                 if "[增补]" in ln and not ln.lstrip().startswith(">"))
    rows = re.findall(r"^\|\s*\d+\s*\|", tail, re.M)
    if n_mark != len(rows):
        errors.append("增补标记 %d 处 / 附表 %d 行，不一致" % (n_mark, len(rows)))

    for w in BANNED:
        if w in body:
            errors.append("出现禁用词：%s" % w)

    covered = set()
    for title, _ in units:
        covered.update(CARD_RE.findall(title))

    have = set()
    if html_path:
        html = read(html_path)
        have = set(re.findall(r'<article class="card" id="([a-z]+\d+)"', html))
        miss = sorted(covered - have)
        extra = sorted(have - covered)
        if miss:
            errors.append("教学稿引用了页面里不存在的卡：%s" % ", ".join(miss))
        if extra:
            errors.append("页面里有卡未被教学稿覆盖：%s" % ", ".join(extra))

    fig_ids = []
    for title, chunk in units:
        if is_fig_unit(chunk):
            fig_ids.extend(CARD_RE.findall(title))
    if plan_path:
        plan = read(plan_path)
        plan_figs = set(re.findall(
            r"^\|\s*(c\d+|t\d+|e\d+|p\d+)[^|]*\|[^|]*\|[^|]*\*\*出图\*\*", plan, re.M))
        if not plan_figs:
            warns.append("清单里没解析到出图条目，跳过出图对账")
        else:
            for title, chunk in units:
                if not is_fig_unit(chunk):
                    continue
                ids = CARD_RE.findall(title)
                if not (set(ids) & plan_figs):
                    errors.append("单元 %s 标了出图，但清单把这批卡都判为不出图"
                                  % title.split("（")[0])

    print("教学稿 %s" % path)
    line = "  档位 %s · 分簇 %d · 单元 %d · 增补 %d 处 / 附表 %d 行" % (
        level, len(clusters), len(units), n_mark, len(rows))
    print(line)
    if html_path:
        print("  卡片覆盖 %d / %d" % (len(covered & have), len(have)))
    if fig_ids:
        print("  标出图的卡：%s" % ", ".join(fig_ids))
    for w in warns:
        print("  [warn] %s" % w)
    if errors:
        print("  发现 %d 个问题：" % len(errors))
        for e in errors:
            print("    - %s" % e)
        print("FAIL")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
