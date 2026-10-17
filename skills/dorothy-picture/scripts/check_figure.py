#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校核单张 figure 片段：dorothy-picture 的硬约束。

用法： python scripts/check_figure.py figs/*.html
只依赖标准库。ERROR 以非零退出码结束。
"""
import re
import sys
from pathlib import Path

FIG_OPEN = re.compile(r'<figure class="fig" id="([^"]+)"')
SVG_OPEN = re.compile(r'<svg[^>]*viewBox="([^"]+)"', re.I)
ARIA = re.compile(r'aria-label="([^"]*)"')
TITLE = re.compile(r'<title>(.*?)</title>', re.S)
CAPTION = re.compile(r'<figcaption>(.*?)</figcaption>', re.S)
FONT = re.compile(r'font-size="([0-9.]+)"')
COLOR = re.compile(r'#[0-9A-Fa-f]{3,8}\b|\brgba?\s*\(|\bhsla?\s*\(')
PAINT_ATTR = re.compile(r'\b(stroke|fill|stop-color|flood-color|color)="([^"]*)"')
CLASSES = re.compile(r'class="([^"]+)"')
EXTERNAL = re.compile(r'https?://|@import|url\((?!\s*#)')

STROKE_CLASSES = {
    'f-grid', 'f-axis', 'f-rail', 'f-hair', 'f-hair--acc', 'f-hair-thin', 'f-rung',
    'f-line', 'f-line--acc', 'f-line--acc-dash', 'f-rule-dash', 'f-rule-dash-sm',
    'f-bracket', 'f-box', 'f-box--acc', 'f-link',
}
FILL_CLASSES = {'f-arrow', 'f-dot', 'f-dot--acc', 'f-dot-hollow', 'f-tick', 'f-band', 'f-hl', 'f-hl-edge'}
TEXT_CLASSES = {'t-num', 't-lab', 't-note', 't-halo'}
ANIM_CLASSES = {'f-fade'}
OUTSIDE_CLASSES = {'fig', 'fig__legend', 'sw', 'sw--ink', 'sw--acc', 'fig__ctl'}
ALLOWED = STROKE_CLASSES | FILL_CLASSES | TEXT_CLASSES | ANIM_CLASSES | OUTSIDE_CLASSES


def check(path):
    errors, warns = [], []
    raw = Path(path).read_text(encoding='utf-8-sig')
    figs = FIG_OPEN.findall(raw)
    if len(figs) != 1:
        errors.append('应恰好含 1 个 <figure class="fig" id="…">，实为 %d' % len(figs))
    svg = SVG_OPEN.search(raw)
    if not svg:
        errors.append('缺少带 viewBox 的 <svg>')
    aria = ARIA.search(raw)
    if not aria or not aria.group(1).strip():
        errors.append('缺少非空 aria-label')
    if not TITLE.search(raw):
        errors.append('缺少 <title>（读屏用）')
    cap = CAPTION.search(raw)
    if not cap:
        errors.append('缺少 <figcaption>')
    else:
        text = re.sub(r'<[^>]+>', '', cap.group(1)).strip()
        if not re.match(r'^图\s*\d+\s*·', text):
            errors.append('图注格式应为「图 N · 一句话」，实为：' + text[:40])
        if '正文 §' not in text:
            errors.append('图注缺少正文出处（正文 §X.Y）')
    body = re.sub(r'<figcaption>.*?</figcaption>', '', raw, flags=re.S)
    lit = COLOR.findall(body)
    if lit:
        errors.append('图内出现颜色字面量 %d 处：%s' % (len(lit), ' '.join(sorted(set(lit))[:6])))
    for _, val in PAINT_ATTR.findall(body):
        if val.strip().lower() not in ('none', 'currentcolor', '') and not val.startswith('url(#'):
            errors.append('图内直接写了颜色属性值：' + val)
    for size in FONT.findall(body):
        if float(size) < 11:
            errors.append('字号 %.1fpx 低于下限 11px' % float(size))
    # 动态图（图内含内联脚本）：静态首帧必须自立，且不许出现外链字面量
    if '<script' in body:
        if re.search(r'<script[^>]*\bsrc=', body):
            errors.append('图内脚本必须内联，不允许 src 外链')
        if re.search(r'https?://|//cdn\.|unpkg\.com|jsdelivr', body):
            errors.append('图内脚本出现外链字面量 —— 单文件离线会失效（createElementNS 请复用 SVG.namespaceURI）')
        if len(re.findall(r'<(line|path|circle|rect|polygon|text)\b', body)) < 4:
            warns.append('动态图的静态首帧太空：首帧就要能独立读懂，JS 只是加料')
        if '<button' in body and 'fig__ctl' not in body:
            warns.append('控件容器应加 class="fig__ctl"（否则按钮是浏览器默认样式）')
    # 字面转义残留：生成脚本把换行写成两个字符时会命中；在 JS 里会直接语法错误
    lit = re.findall(r'\\[ntr]', raw)
    if lit:
        errors.append('出现字面转义 %s —— 生成脚本多半把换行写成了两个字符（JS 里会直接报语法错误）' % '、'.join(sorted(set(lit))))
    if EXTERNAL.search(raw):
        errors.append('出现外链或 @import（必须离线自包含）')
    unknown = set()
    for cls in CLASSES.findall(raw):
        for c in cls.split():
            if c not in ALLOWED:
                unknown.add(c)
    if unknown:
        warns.append('出现未登记的类名（需在 design-spec 登记）：' + '、'.join(sorted(unknown)))
    elems = len(re.findall(r'<(line|path|circle|rect|polygon|text|ellipse)\b', body))
    objs = len(re.findall(r'<(circle|rect|polygon)\b', body)) + len(re.findall(r'<path[^>]*d="[^"]*[Zz]"', body))
    rels = len(re.findall(r'<line\b', body)) + len(re.findall(r'<path(?![^>]*[Zz])[^>]*d="', body))
    # 数据类图元（点阵 / 发丝 / 横档）占多数时按「数据分布图」处理，不计对象上限
    datapts = len(re.findall(r'class="[^"]*\bf-(dot|dot--acc|tick|hair|hair--acc|hair-thin|rung)\b', body))
    if elems > 120 and datapts * 2 > elems:
        warns.append('图元 %d 个，其中数据类 %d 个（点阵 / 发丝 / 横档）—— 按数据分布图处理，不计对象上限' % (elems, datapts))
    elif elems > 120:
        warns.append('图元 %d 个（对象约 %d、关系约 %d），密度偏高；结构 / 几何 / 证明 / 对照类图应 ≤14 对象、≤8 关系' % (elems, objs, rels))
    return errors, warns, elems


def main(argv):
    paths = [a for a in argv if not a.startswith('--')]
    if not paths:
        raise SystemExit(__doc__)
    bad = False
    for p in paths:
        try:
            errors, warns, elems = check(p)
        except Exception as exc:
            print('== %s\n  ERROR 读取失败：%s' % (p, exc))
            bad = True
            continue
        bad = bad or bool(errors)
        print('== %s' % p)
        for item in errors:
            print('  ERROR %s' % item)
        for item in warns:
            print('  WARN  %s' % item)
        print('  INFO  图元 %d 个' % elems)
        print('  %s' % ('FAIL' if errors else 'OK'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
