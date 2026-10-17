#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 校核制图规划清单：打分 / 六问 / 八字段 / 图示规格 / 三层验收 / 锚点
import re
import sys
from pathlib import Path

USAGE = 'python scripts/check_plan.py <产物>_figures-plan.md [--html <产物.html>]'

FIELDS = ['对应知识点', '打分', '插入锚点', '前置问题', '首要教学任务', '关键元素',
          '图后解释', '理解检查', '图型与障碍类型']
SPEC_ITEMS = ['数学对象与符号', '对象之间的关系', '阅读顺序', '标识职责表',
              '与正文术语的对应', '不能暗示的错误结论']
# 只拦主观评价词组；「直观维度」「结构维度」这类是维度名，不算
BANNED = re.compile(r'更清晰|很清晰|非常清晰|清晰明了|更美观|很美观|更直观|很直观|非常直观|更易懂|更易理解|更加清晰')
SUBSTITUTE = ['编号回指', '术语表', '解剖图', '排版公式', '缺失的连接', '纯文字', '结构化排版']
STATUSES = ['未开始', '已生成', '已渲染核对', '已内联', '已弃用']
READY = ['已渲染核对', '已内联']
MULTI = ['并且', '同时', '以及', '；']
ANCHOR_HINT = re.compile(r'(-body|§|第\s*\d+\s*段|第\s*\d+\s*步|面板|公式|列表|表格|之后|之前)')
CARD_ID = re.compile(r'\b([ctep]\d+|q\d+|x8-\d+)\b')
PLACEHOLDER = re.compile(r'^[（(]\s*[）)]$|^……$|^待填')


def blocks(md):
    out, cur = [], None
    for line in md.split('\n'):
        if line.startswith('### '):
            if cur:
                out.append(cur)
            cur = [line[4:].strip(), []]
        elif cur is not None:
            cur[1].append(line)
    if cur:
        out.append(cur)
    return out


def field(text, name):
    m = re.search(r'-\s*' + re.escape(name) + r'\s*[：:]\s*(.*)', text)
    return m.group(1).strip() if m else None


def section(text, name):
    m = re.search(r'-\s*' + re.escape(name) + r'\s*[：:]([\s\S]*?)(?=\n- |\n### |\Z)', text)
    return m.group(1) if m else None


def check(path, html=None):
    errors, warns = [], []
    md = Path(path).read_text(encoding='utf-8-sig')
    if '评估强度' not in md:
        errors.append('缺少「评估强度」行（全量 / 抽样，抽样要写规则）')
    if not re.search(r'\|\s*知识点\s*\|\s*打分\s*\|', md):
        errors.append('汇总表表头应为 | 知识点 | 打分 | 结论 | …（要能一眼看出每条的分数与结论）')
    ids = set()
    if html:
        raw = Path(html).read_text(encoding='utf-8-sig')
        ids = set(re.findall(r'id="([^"]+)"', raw))
    drawn = missing = 0
    for title, body in blocks(md):
        text = '\n'.join(body)
        if '不出图' in title or '不出图' in text[:80]:
            missing += 1
            score = field(text, '打分')
            if not score:
                errors.append('不出图条目缺「打分」：' + title[:44])
            why = field(text, '理由')
            if not why or PLACEHOLDER.match(why or ''):
                errors.append('不出图条目缺「理由」：' + title[:44])
            elif not any(k in text for k in SUBSTITUTE):
                warns.append('[%s] 没写替身手段（编号回指 / 术语表 + 解剖图 / 排版公式 / 缺失的连接 / 纯文字对比）' % title[:30])
            continue
        if not re.match(r'^图\s*\d+\s*·', title):
            continue
        drawn += 1
        tag = '[%s]' % title[:26]
        for name in FIELDS:
            val = field(text, name)
            if val is None:
                errors.append('%s 缺字段「%s」' % (tag, name))
            elif not val or PLACEHOLDER.match(val):
                errors.append('%s 字段「%s」还是占位' % (tag, name))
        score = field(text, '打分') or ''
        if len(re.findall(r'\d', score)) < 4:
            errors.append('%s 打分必须写四维分数（结构 / 过程 / 直观 / 辨析）' % tag)
        for item in SPEC_ITEMS:
            if item not in text:
                errors.append('%s 图示规格缺「%s」' % (tag, item))
        acc = section(text, '三层验收') or ''
        if not acc.strip():
            errors.append('%s 缺「三层验收」（数学正确性 / 视觉表达 / 教学有效性分开记）' % tag)
        else:
            for layer in ('数学', '视觉', '教学'):
                if layer not in acc:
                    errors.append('%s 三层验收缺「%s」这一层' % (tag, layer))
            hit = BANNED.search(acc)
            if hit:
                errors.append('%s 验收记录里出现主观词「%s」——要写具体条目' % (tag, hit.group(0)))
        # 理解检查必须可判定对错（带答案），并记录失败原因
        chk = field(text, '理解检查') or ''
        if '答案' not in chk:
            errors.append('%s 理解检查必须可判定对错 —— 要写出「（答案：…）」' % tag)
        if not field(text, '失败原因'):
            warns.append('%s 缺「失败原因」（读者答错时的常见原因）' % tag)
        status = field(text, '状态') or ''
        if not any(s in status for s in STATUSES):
            errors.append('%s 状态非法：「%s」（应为 %s 之一）' % (tag, status, '/'.join(STATUSES)))
        elif any(s in status for s in READY):
            if not acc.strip():
                errors.append('%s 状态是「%s」但三层验收为空' % (tag, status.strip()))
        if '已弃用' in status and not field(text, '理由'):
            errors.append('%s 已弃用但没有写理由' % tag)
        task = field(text, '首要教学任务') or ''
        if any(k in task for k in MULTI):
            warns.append('%s 首要教学任务看着不止一个（含「%s」）' % (tag, [k for k in MULTI if k in task][0]))
        kind = field(text, '图型与障碍类型') or ''
        if ('证明' in kind or 'proof' in kind) and ('证明该' in task or '证明结论' in task):
            errors.append('%s 服务证明的图不能把教学任务写成「证明该结论」（图不得替代证明）' % tag)
        key = field(text, '关键元素') or ''
        n = len([x for x in re.split(r'[、，,；;]', key) if x.strip()])
        if n > 12:
            errors.append('%s 关键元素 %d 项，超过单图上限（≤14 个对象、≤8 个关系），必须拆分' % (tag, n))
        elif n > 7:
            warns.append('%s 关键元素 %d 项，偏密（超过 7 项先问能不能拆）' % (tag, n))
        anchor = field(text, '插入锚点') or ''
        if not ANCHOR_HINT.search(anchor):
            warns.append('%s 插入锚点看不出具体位置（应含卡 id + 段落 / 公式 / 步骤 / 面板）' % tag)
        if ids:
            for cid in CARD_ID.findall(anchor):
                if cid not in ids:
                    errors.append('%s 锚点里的卡片 id 在 HTML 里不存在：%s' % (tag, cid))
    if not drawn:
        errors.append('清单里没有任何出图条目')
    return errors, warns, drawn, missing


def main(argv):
    html = None
    if '--html' in argv:
        html = argv[argv.index('--html') + 1]
    skip = {html} if html else set()
    paths = [a for a in argv if not a.startswith('--') and a not in skip]
    if not paths:
        raise SystemExit(USAGE)
    bad = False
    for p in paths:
        errors, warns, drawn, missing = check(p, html)
        bad = bad or bool(errors)
        print('== %s' % p)
        for item in errors:
            print('  ERROR %s' % item)
        for item in warns:
            print('  WARN  %s' % item)
        print('  INFO  出图 %d 张 · 不出图 %d 条' % (drawn, missing))
        print('  %s' % ('FAIL' if errors else 'OK'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
