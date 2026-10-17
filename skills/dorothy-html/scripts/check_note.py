#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验知识笔记 HTML 是否满足 dorothy-html 的硬约束。

用法：
  python scripts/check_note.py <笔记.html> [<笔记.html> ...]
  python scripts/check_note.py --json <笔记.html>

只依赖标准库。ERROR 会以非零退出码结束，WARN/INFO 只打印。
"""
import json
import re
import sys
from collections import Counter

# ---- 常量 ---------------------------------------------------------------
REQUIRED_TOKENS = ['--paper', '--paper-3', '--ink', '--line',
                   '--dark', '--measure']
WIDTH_TOKENS = ['--spine', '--shell']             # 单栏版用 --spine，宽屏版用 --shell
ACCENT_TOKENS = ['--orange', '--accent']          # 两套命名都接受
FONT_TOKENS = ['--font-cjk', '--font-text', '--font-sans', '--font-mono']
REQUIRED_IDS = ['core', 'pitfalls', 'quiz']
MAP_MARKERS = ['id="map"', 'class="mapwrap', 'class="map"']
PAGE_IDS = ['p-overview', 'p-map', 'p-core', 'p-pitfalls', 'p-quiz']
FORBIDDEN_CLASSES = ['hero', 'ticker', 'marquee', 'banner']
REF_LINK = re.compile(r'<a\b[^>]*class="[^"]*\bref\b[^"]*"[^>]*>', re.I)
REF_TARGET = re.compile(r'data-ref\s*=\s*"([^"]+)"')
SEMANTIC_CODES = ['DEF', 'THM', 'PRF', 'EX', 'ERR', 'MTH']

COLOR_LITERAL = re.compile(r'#[0-9A-Fa-f]{3,8}\b|\brgba?\s*\(|\bhsla?\s*\(')
ROOT_BLOCK = re.compile(r':root\s*(\[[^\]]*\])?\s*\{(.*?)\}', re.S)
THEME_PROPS = ['background-color', 'color', 'border-color', 'outline-color', 'fill', 'stroke']
# JS / 构建脚本写进内联 style 的运行时变量（动画序号、进度、地图坐标），不是设计令牌
RUNTIME_TOKENS = {'--i', '--n', '--p', '--tab', '--x', '--y'}
FONT_DECL = re.compile(r'font-family\s*:\s*([^;]+);')
TRANSITION_DECL = re.compile(r'transition(?:-property)?\s*:\s*([^;]+);')
EMOJI = re.compile('[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u2B00-\u2BFF]')
EXTERNAL = re.compile(r'<(?:script|img|link|iframe)\b[^>]*\b(?:src|href)\s*=\s*["\'](?!#)([^"\']+)', re.I)
A11Y_CONTROLS = re.compile(r'aria-controls\s*=\s*"([^"]+)"')
ID_DECL = re.compile(r'\bid\s*=\s*"([^"]+)"')
ANCHOR = re.compile(r'href\s*=\s*"#([^"]+)"')
TOGGLE = re.compile(r'<button[^>]*class="[^"]*\btoggle\b[^"]*"[^>]*>', re.I)


HTML_COMMENT = re.compile(r'<!--.*?-->', re.S)
CSS_COMMENT = re.compile(r'/\*.*?\*/', re.S)
ANCHOR_ATTR = re.compile(r'\b(?:href|id|aria-controls|for)\s*=\s*"[^"]*"')
FONT_FACE = re.compile(r'@font-face\s*\{.*?\}', re.S)


def strip_root(text):
    """把 :root{...} / :root[data-theme=…]{...} 块、注释、锚点属性换成占位。

    返回（剩余文本, 基础令牌块, 主题令牌块列表）。颜色字面量允许出现在这两类令牌块里；
    注释与 #锚点 不参与颜色扫描（注释不渲染，而 #c11 这类锚点会被误认成十六进制颜色）。
    """
    themes = []

    def hold(match):
        if match.group(1):
            themes.append((match.group(1), match.group(2)))
            return 'THEME_BLOCK'
        return ':root{}'

    body = ROOT_BLOCK.sub(hold, text)
    blocks = ROOT_BLOCK.findall(text)
    base = '\n'.join(b[1] for b in blocks if not b[0])
    body = HTML_COMMENT.sub('', body)
    body = CSS_COMMENT.sub('', body)
    for attr in ANCHOR_ATTR.findall(body):
        body = body.replace(attr, 'ANCHOR_ATTR')
    return body, base, themes


def check(path, plan_path=None):
    errors, warns, infos = [], [], []
    with open(path, encoding='utf-8-sig') as handle:
        raw = handle.read()
    body, root, themes = strip_root(raw)

    # 1. 颜色令牌化
    stray = COLOR_LITERAL.findall(body)
    if stray:
        errors.append('颜色字面量出现在 :root 之外 %d 处：%s' % (len(stray), ' '.join(sorted(set(stray))[:8])))
    missing = [tok for tok in REQUIRED_TOKENS if tok + ':' not in root.replace(' ', '')]
    if not any(tok + ':' in root.replace(' ', '') for tok in ACCENT_TOKENS):
        missing.append('强调色令牌（' + ' 或 '.join(ACCENT_TOKENS) + '）')
    fonts_defined = [tok for tok in FONT_TOKENS if tok + ':' in root.replace(' ', '')]
    if len(fonts_defined) < 2:
        missing.append('字体令牌至少两套（中文 + 数字/等宽）')
    if not any(tok + ':' in root.replace(' ', '') for tok in WIDTH_TOKENS):
        missing.append('版心宽度令牌（' + ' 或 '.join(WIDTH_TOKENS) + '）')
    if missing:
        errors.append('设计令牌缺失：' + '、'.join(missing))

    # 1.5 双主题：主题块只许覆盖、不许新增令牌；所有 var() 都要能在基础 :root 里解析
    def token_names(block):
        return set(re.findall(r'(--[a-z0-9-]+)\s*:', block))

    base_tokens = token_names(root)
    used = set(re.findall(r'var\((--[a-z0-9-]+)', body)) | set(re.findall(r'var\((--[a-z0-9-]+)', root))
    unknown = sorted(used - base_tokens - RUNTIME_TOKENS)
    if unknown:
        errors.append('引用了基础 :root 没有定义的令牌：' + '、'.join(unknown))
    for sel, block in themes:
        extra = sorted(token_names(block) - base_tokens)
        if extra:
            errors.append('主题块 %s 新增了基础 :root 没有的令牌（切回默认主题会缺声明）：%s' % (sel, '、'.join(extra)))
    if not themes:
        warns.append('没有 :root[data-theme=…] 主题块：只有一套主题？')

    # 1.6 主题切换接线：控件、记忆、过渡例外都要在，且例外只许放开 6 个颜色属性
    if 'data-theme-set' not in raw:
        errors.append('缺少主题切换控件（[data-theme-set]）')
    if 'data-theme' not in raw or ('setAttribute(\'data-theme\'' not in raw and 'setAttribute("data-theme"' not in raw):
        errors.append('缺少主题切换逻辑：没有写 html[data-theme]')
    if 'localStorage' in raw:
        if 'catch' not in raw:
            errors.append('localStorage 没有 try/catch 兜底（file:// 下会抛错）')
    else:
        warns.append('主题选择没有本地记忆（localStorage）：多章共用一份偏好时会丢')
    if 'is-theming' not in raw:
        errors.append('缺少主题过渡类 .is-theming（颜色只能瞬切）')
    for blob in re.findall(r'html\.is-theming[^{]*\{(.*?)\}', body, re.S):
        prop = re.search(r'transition-property\s*:\s*([^;]+);', blob)
        if prop:
            bad = [p.strip() for p in prop.group(1).split(',') if p.strip() and p.strip() not in THEME_PROPS]
            if bad:
                errors.append('主题过渡放开了不该动的属性：' + '、'.join(bad))
    for np in re.findall(r'<div class="np-chrome"[^>]*>', raw):
        if 'aria-hidden="true"' not in np:
            errors.append('主题装饰件 .np-chrome 缺少 aria-hidden="true"')
    if 'class="np-chrome"' in raw and '.np-chrome{display:none;}' not in body.replace(' ', ''):
        warns.append('.np-chrome 没有在默认主题下 display:none（会在孤星主题里占排布）')

    # 2. 无圆角 / 无阴影
    radius = re.findall(r'border-radius\s*:\s*([^;]+);', body)
    bad_radius = [r for r in radius if r.strip() not in ('0', '0px', '0 0', '0px 0px')]
    if bad_radius:
        errors.append('出现圆角：' + '、'.join(bad_radius))
    shadow = [s for s in re.findall(r'box-shadow\s*:\s*([^;]+);', body) if s.strip() != 'none']
    if shadow:
        errors.append('出现阴影：' + '、'.join(shadow))

    # 3. 字体不超过 3 套，且只能引用令牌
    #    @font-face 是基础设施（数学兜底字体等），先摘出来单独看：
    #    只允许 local() 本机字体，不允许 url() 外链。
    faces = FONT_FACE.findall(body)
    for face in faces:
        if 'url(' in face:
            errors.append('@font-face 引用了外部字体文件：' + face.replace('\n', ' ')[:80])
        if 'local(' not in face and 'url(' not in face:
            errors.append('@font-face 没有 local() 来源：' + face.replace('\n', ' ')[:80])
    body = FONT_FACE.sub('', body)
    fonts = [f.strip() for f in FONT_DECL.findall(body)]
    literal_fonts = [f for f in fonts if not f.startswith('var(--font-')]
    if literal_fonts:
        errors.append('字族未走令牌：' + '；'.join(literal_fonts[:3]))
    families = set(re.findall(r'var\((--font-[a-z-]+)\)', ' '.join(fonts) + root))
    if len(families) > 3:
        errors.append('字族超过 3 套：' + '、'.join(sorted(families)))

    # 4. 无 emoji
    emo = EMOJI.findall(raw)
    if emo:
        errors.append('出现 emoji 字符：' + ' '.join(sorted(set(emo))))

    # 5. 单文件、不依赖外部资源（字体除外）
    ext = [u for u in EXTERNAL.findall(raw) if not u.startswith('data:')]
    if ext:
        errors.append('引用外部资源：' + '、'.join(sorted(set(ext))[:5]))
    if re.search(r'@import|fonts\.googleapis', raw):
        errors.append('出现 @import 或在线字体')

    # 6. 区块与结构
    ids = set(ID_DECL.findall(raw))
    for need in REQUIRED_IDS:
        if need not in ids:
            errors.append('缺少区块 id：#' + need)
    if not any(marker in raw for marker in MAP_MARKERS):
        errors.append('缺少知识地图（#map 或 .mapwrap / .map）')

    # 6.5 翻页结构
    pages = re.findall(r'<section class="page\b[^"]*" id="([^"]+)"', raw)
    if len(pages) < 4:
        errors.append('翻页结构不完整：只找到 %d 个 .page（至少 4 个）' % len(pages))
    for need in PAGE_IDS:
        if need not in pages:
            errors.append('缺少页：#' + need)
    if 'class="pager"' not in raw and 'class="pager ' not in raw:
        errors.append('缺少翻页器 .pager（上一页 / 进度 / 页码点 / 下一页）')

    # 6.6 互引：ref 链接必须指向存在的 id，且不能落在 SVG 里
    svg_spans = [(m.start(), m.end()) for m in re.finditer(r'<svg\b.*?</svg>', raw, re.S)]
    refs = list(REF_LINK.finditer(raw))
    for m in refs:
        target = REF_TARGET.search(m.group(0))
        if not target:
            errors.append('互引链接缺少 data-ref：' + m.group(0)[:60])
            continue
        if target.group(1) not in ids:
            errors.append('互引链接指向不存在的 id：' + target.group(1))
        if any(a <= m.start() < b for a, b in svg_spans):
            errors.append('互引链接落在 SVG 里（SVG 内不放 .ref）：' + target.group(1))
    if refs and 'id="refBox"' not in raw:
        errors.append('有互引链接但没有概念速览浮层 #refBox')
    if 'id="refBox"' in raw:
        box = raw[raw.index('id="refBox"'):]
        if 'role="dialog"' not in box[:600] or 'aria-modal="true"' not in box[:600]:
            errors.append('浮层缺少 role="dialog" / aria-modal="true"')
        if 'id="refBack"' not in raw:
            errors.append('浮层缺少返回键 #refBack')

    # 6.7 插图：读屏属性、图注格式、正文引用、与制图规划清单对得上
    figures = re.findall(r'<figure class="fig".*?</figure>', raw, re.S)
    fig_ids = []
    if figures:
        if raw.count('<figcaption>') != len(figures):
            errors.append('插图数（%d）与 figcaption 数（%d）不一致' % (len(figures), raw.count('<figcaption>')))
        for fig in figures:
            tag_end = fig.index('>') + 1
            fid = re.search(r'id="([^"]+)"', fig[:tag_end])
            if not fid:
                errors.append('插图缺少 id（制图规划清单要靠它对上）：' + fig[:60])
            else:
                fig_ids.append(fid.group(1))
            if '<svg' not in fig:
                errors.append('插图里没有内联 SVG：' + fig[:60])
            else:
                head = fig[:fig.index('>', fig.index('<svg')) + 1]
                if 'role="img"' not in head or 'aria-label="' not in head:
                    errors.append('插图 SVG 缺少 role="img" 或 aria-label：' + fig[:60])
                if '<title>' not in fig:
                    errors.append('插图 SVG 缺少 <title>：' + fig[:60])
            cap = re.search(r'<figcaption>(.*?)</figcaption>', fig, re.S)
            if cap:
                text = re.sub(r'<[^>]+>', '', cap.group(1)).strip()
                if not re.match(r'^图\s*\d+\s*·', text):
                    errors.append('图注格式应为「图 N · 一句话」：' + text[:40])
                if '正文 §' not in text:
                    errors.append('图注缺少正文出处（正文 §X.Y）：' + text[:40])
            if 'fig__legend' not in fig:
                warns.append('插图缺少 .fig__legend（图例/说明）')
        core = raw[raw.index('id="p-core"'):] if 'id="p-core"' in raw else raw
        prose = re.sub(r'<figure class="fig".*?</figure>', '', core, flags=re.S)
        for num in sorted(set(re.findall(r'图\s*(\d+)\s*·', raw)), key=int):
            if not re.search(r'图\s*%s(?![·\d])' % num, prose):
                warns.append('图 %s 在正文里没有被引用（只把图塞进去不行，要写图前引导与图后解释）' % num)
        # 每张图后都要有可判定的理解检查（问题 + 答案）
        n_fig = len(re.findall(r'<figure class="fig"', raw))
        n_chk = len(re.findall(r'class="fig__check"', raw))
        if n_fig and n_chk < n_fig:
            errors.append('有 %d 张图但只有 %d 处图后理解检查：每张图都该配一个可判定对错的检查题' % (n_fig, n_chk))
    if plan_path:
        plan = open(plan_path, encoding='utf-8-sig').read()
        for fid in fig_ids:
            if fid not in plan:
                errors.append('插图 %s 不在制图规划清单里（制图评估是必经步骤）' % fid)
        for listed in sorted(set(re.findall(r'fig-[A-Za-z0-9._-]+', plan))):
            if listed not in fig_ids:
                warns.append('规划清单里的 %s 没有出现在产出里（检查它的状态字段）' % listed)
    for cls in FORBIDDEN_CLASSES:
        if re.search(r'class="[^"]*\b%s\b' % cls, raw):
            errors.append('出现被删除的结构：.%s' % cls)
    if re.search(r'<footer[^>]*>(?:(?!</footer>).)*?<nav\b', raw, re.S):
        errors.append('页脚里出现导航组 <nav>')

    # 6.8 分板块切换（核心概念三块；末页自测 / 章末习题两块）—— 每一组各自校验
    groups = re.findall(r'<div class="tabs[^"]*"[^>]*data-tabs="([^"]+)"[^>]*>(.*?)</div>', raw, re.S)
    board_tags = re.findall(r'<div class="board"[^>]*>', raw)
    all_tabs = re.findall(r'<button[^>]*role="tab"[^>]*>', raw)
    if board_tags or groups:
        if not groups:
            errors.append('有 .board 板块但缺少 role="tablist" 分段控件（[data-tabs]）')
        if len(board_tags) < 2:
            errors.append('板块少于 2 个（定义 / 定理 / 例子要分板块）')
        tags_by_id = {}
        for tag in board_tags:
            if 'role="tabpanel"' not in tag:
                errors.append('板块缺少 role="tabpanel"：' + tag[:70])
            if 'data-board=' not in tag:
                errors.append('板块缺少 data-board：' + tag[:70])
            bid = re.search(r'id="([^"]+)"', tag)
            if not bid:
                errors.append('板块缺少 id：' + tag[:70])
            else:
                tags_by_id[bid.group(1)] = tag
            lab = re.search(r'aria-labelledby="([^"]+)"', tag)
            if not lab or lab.group(1) not in ids:
                errors.append('板块的 aria-labelledby 指向不存在的 tab：' + tag[:70])
        if 'id="core"' in ids and 'id="quiz"' in ids and len(groups) < 2:
            errors.append('核心概念与末页自测/习题都要分板块：只找到 %d 组分段控件' % len(groups))
        for name, inner in groups:
            gtabs = re.findall(r'<button[^>]*role="tab"[^>]*>', inner)
            if len(gtabs) < 2:
                errors.append('分组 %s 的 tab 少于 2 个' % name)
            ctls = []
            for t in gtabs:
                if 'data-board=' not in t:
                    errors.append('分组 %s 的 tab 缺少 data-board' % name)
                ctl = re.search(r'aria-controls="([^"]+)"', t)
                if not ctl:
                    errors.append('分组 %s 的 tab 缺少 aria-controls' % name)
                    continue
                ctls.append(ctl.group(1))
                if ctl.group(1) not in ids:
                    errors.append('分组 %s 的 tab aria-controls 指向不存在的板块：%s' % (name, ctl.group(1)))
            if len(ctls) != len(set(ctls)):
                errors.append('分组 %s 的 tab aria-controls 有重复' % name)
            gsel = [t for t in gtabs if 'aria-selected="true"' in t]
            if len(gsel) != 1:
                errors.append('分组 %s 里 aria-selected="true" 的 tab 应有且只有 1 个，实为 %d' % (name, len(gsel)))
            vis = [b for b in ctls if b in tags_by_id and 'hidden' not in tags_by_id[b]]
            if len(vis) != 1:
                errors.append('分组 %s 初始可见的板块应有且只有 1 个，实为 %d' % (name, len(vis)))
        if 'showBoard' not in raw:
            errors.append('板块切换缺少 JS（showBoard）')
        if "closest('[role=\"tablist\"]')" not in raw:
            errors.append('翻页快捷键没避开板块控件：在 tablist 里按 ←/→ 会翻页而不是切板块')
        if 'boardScroll' not in raw:
            warns.append('板块没有各自记 scrollTop（切回来会丢阅读位置）')
        # 分组栈不能互相嵌套（曾把习题段塞进自测栈里，分组会串位）
        div_tag = re.compile(r'</?div\b', re.I)
        for m in re.finditer(r'<div class="stack"', raw):
            pos, depth = raw.index('>', m.start()) + 1, 1
            close = None
            while True:
                n = div_tag.search(raw, pos)
                if not n:
                    break
                depth += -1 if raw[n.start() + 1] == '/' else 1
                if depth == 0:
                    close = n.start()
                    break
                pos = n.end()
            if close is None:
                errors.append('.stack 没有闭合：@%d' % m.start())
            elif '<div class="stack"' in raw[m.end():close]:
                errors.append('.stack 嵌套在另一个 .stack 里（分组会串位）：@%d' % m.start())

    # 6.9 全局搜索：只索引核心概念，接线要全
    if 'data-search' in raw:
        if '#p-core .card' not in raw:
            errors.append('搜索索引没有限定在 #p-core .card（会搜到易错点 / 自测题）')
        if 'id="searchHits"' not in raw:
            errors.append('搜索缺少结果面板 #searchHits')
        if 'role="combobox"' not in raw or 'aria-expanded' not in raw:
            warns.append('搜索框建议用 role="combobox" + aria-expanded + aria-controls')
        if 'compositionend' not in raw:
            warns.append('搜索框没有处理中文输入法（compositionend），拼字中途会抖')
        if "closest('[data-search]')" not in raw:
            errors.append('翻页快捷键没避开搜索框：在输入框里按 ←/→ 会翻页而不是移光标')
        if '未找到' not in raw:
            errors.append('搜索缺少空结果提示（未找到…）')
        if 'createTextNode' not in raw:
            warns.append('搜索结果片段疑似拼 innerHTML（用户输入未转义），请用 createTextNode')

    # 7. 交互接线
    controls = A11Y_CONTROLS.findall(raw)
    for target in controls:
        if target not in ids:
            errors.append('aria-controls 指向不存在的 id：' + target)
    toggles = TOGGLE.findall(raw)
    # 只统计 .toggle 身上的 aria-controls：板块 tab 也用 aria-controls，不能混进来
    toggle_controls = [t for t in toggles if 'aria-controls' in t]
    if toggles and not toggle_controls:
        errors.append('toggle 按钮缺少 aria-controls')
    if len(toggle_controls) != len(toggles):
        warns.append('toggle 数（%d）与其中带 aria-controls 的（%d）不一致' % (len(toggles), len(toggle_controls)))
    for btn in toggles:
        if 'aria-expanded' not in btn:
            errors.append('toggle 按钮缺少 aria-expanded')
        if 'data-open-label' not in btn or 'data-close-label' not in btn:
            warns.append('toggle 按钮缺少 data-open-label / data-close-label，展开后文字不会切换')

    # 7.5 课本章末习题：题目照抄课本；没有展开按钮就必须有静态答案行
    exercises = re.findall(r'<article class="quiz quiz--ex"[^>]*>.*?</article>', raw, re.S)
    for ex in exercises:
        if 'class="toggle"' not in ex and 'class="quiz__ans"' not in ex:
            errors.append('习题卡既没有展开按钮也没有静态答案行：' + ex[:60])
        if 'quiz__no' not in ex:
            errors.append('习题卡缺少题号 .quiz__no：' + ex[:60])
    if exercises and 'data-tabs="quiz"' not in raw:
        errors.append('有课本章末习题但末页没有分段控件 [data-tabs="quiz"]：自测与习题要分板块')

    # 8. 知识点地图锚点可达
    dead = sorted({a for a in ANCHOR.findall(raw) if a not in ids})
    if dead:
        errors.append('地图锚点指向不存在的 id：' + '、'.join(dead))

    # 9. 动画只动 opacity / transform
    for prop in TRANSITION_DECL.findall(body):
        if re.search(r'\b(height|width|max-height|min-height)\b', prop) and 'opacity' not in prop:
            errors.append('过渡里出现 height/width：' + prop.strip())

    # 10. 排版
    body_font = re.search(r'\bbody\s*\{[^}]*font-size\s*:\s*([0-9.]+)px', body)
    if body_font:
        size = float(body_font.group(1))
        if not 15 <= size <= 16:
            warns.append('正文字号 %.1fpx 不在 15–16px' % size)
    line_height = re.search(r'\bbody\s*\{[^}]*line-height\s*:\s*([0-9.]+)', body)
    if line_height:
        lh = float(line_height.group(1))
        if not 1.7 <= lh <= 1.8:
            warns.append('正文行高 %.2f 不在 1.7–1.8' % lh)
    formula = re.search(r'\.formula\s*\{[^}]*margin\s*:\s*([0-9.]+)em', body)
    if formula and float(formula.group(1)) < 1.5:
        warns.append('公式上下间距 %.2fem 小于 1.5em' % float(formula.group(1)))
    elif not formula:
        warns.append('找不到 .formula 的 margin 声明')

    # 11. 深色块面积代理：深色底只应出现在标签条与页脚
    dark_uses = re.findall(r'background\s*:\s*var\(--(?:dark)\)', body)
    if len(dark_uses) > 6:
        warns.append('深色底使用了 %d 处，检查是否只用于标签条与页脚/页栏' % len(dark_uses))
    if '.bar' not in body:
        warns.append('缺少 .bar（语义标签条）样式')

    # 12. 内容纪律
    cards = re.findall(r'<article class="card"', raw)
    quizzes = re.findall(r'<article class="quiz\b', raw)   # 含 .quiz--ex 课本章末习题
    srcs = re.findall(r'class="card__src"', raw)
    todo = raw.count('[待补充]')
    if cards and len(srcs) < len(cards):
        warns.append('有 %d 张卡没有出处行 .card__src' % (len(cards) - len(srcs)))
    codes = Counter(re.findall(r'<span>(%s)</span>' % '|'.join(SEMANTIC_CODES), raw))
    infos.append('知识卡 %d 张 / 自测题 %d 道 / 课本章末习题 %d 道 / 出处行 %d / 板块 %d 个（%d 组分段控件）' % (len(cards), len(quizzes) - len(exercises), len(exercises), len(srcs), len(board_tags), len(groups)))
    infos.append('语义标签：' + (', '.join('%s×%d' % kv for kv in sorted(codes.items())) or '无'))
    infos.append('[待补充] %d 处' % todo)

    return errors, warns, infos


def main(argv):
    as_json = '--json' in argv
    plan_path = argv[argv.index('--plan') + 1] if '--plan' in argv else None
    skip = {plan_path} if plan_path else set()
    paths = [a for a in argv if not a.startswith('--') and a not in skip]
    if not paths:
        raise SystemExit(__doc__)
    failed = False
    report = {}
    for path in paths:
        errors, warns, infos = check(path, plan_path)
        report[path] = {'errors': errors, 'warns': warns, 'infos': infos}
        if errors:
            failed = True
        if not as_json:
            print('== %s' % path)
            for item in errors:
                print('  ERROR %s' % item)
            for item in warns:
                print('  WARN  %s' % item)
            for item in infos:
                print('  INFO  %s' % item)
            print('  %s' % ('FAIL' if errors else 'OK'))
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
