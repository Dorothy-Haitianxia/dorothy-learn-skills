#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 校核制图规划清单：打分 / 七问 / 11 字段 / 编排 / 三层验收 / 锚点
import re
import sys
from pathlib import Path

USAGE = 'python scripts/check_plan.py <产物>_figures-plan.md [--html <产物.html>] [--fields]'

# 11 个必需字段（口径见 reference/plan-contract.md 第二节）
FIELDS = ['对应知识点', '打分', '理解障碍', '教学任务', '插入位置', '编排',
          '视觉顺序', '图文对应', '图后解释', '理解检查', '替代文本']
# 5 个条件字段（触发才填，见第三节）
OPTIONAL = ['标识职责', '不能暗示的错误结论', '图前引导', '图后任务句', '失败原因']
# 旧契约的字段名，出现即说明还在用九字段旧口径
LEGACY = ['前置问题', '首要教学任务', '关键元素', '图型与障碍类型', '插入锚点']
# 只拦主观评价词组；「直观维度」「结构维度」这类是维度名，不算
BANNED = re.compile(r'更清晰|很清晰|非常清晰|清晰明了|更美观|很美观|更直观|很直观|非常直观|更易懂|更易理解|更加清晰|理解不深')
SUBSTITUTE = ['编号回指', '术语表', '解剖图', '排版公式', '缺失的连接', '纯文字', '结构化排版']
STATUSES = ['未开始', '已生成', '已渲染核对', '已内联', '已弃用']
READY = ['已渲染核对', '已内联']
MULTI = ['并且', '同时', '以及', '；']
# 编排：3 默认 + 5 例外
ORCH_DEFAULT = ['并置', '分阶段揭示', '并列对照']
ORCH_EXCEPT = ['先概览后细节', '先提问再给图', '先预测再揭示', '后置总结图', '局部放大']
# 视觉标识：用到就要写「标识职责」
SIGNALS = ['箭头', '编号', '高亮', '颜色', '虚线', '分阶段', '色块']
ANCHOR_HINTS = re.compile(r'(-body|§|第\s*\d+\s*段|第\s*\d+\s*步|面板|公式|列表|表格|之后|之前)')
CARD_ID = re.compile(r'\b([ctep]\d+|q\d+|x8-\d+)\b')
PLACEHOLDER = re.compile(r'^[（(]\s*[）)]$|^……$|^待填|^……|^略$')
ALT_EMPTY = re.compile(r'^[（(]?\s*(无|没有|没有替代|不适用|不需要|暂无|none|n/a)\s*[）)]?$', re.I)


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


def is_blank(val):
    return val is None or not val.strip() or bool(PLACEHOLDER.match(val.strip()))


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
            if is_blank(why):
                errors.append('不出图条目缺「理由」：' + title[:44])
            elif not any(k in text for k in SUBSTITUTE):
                warns.append('[%s] 没写替身手段（编号回指 / 术语表 + 解剖图 / 排版公式 / 缺失的连接 / 纯文字对比）' % title[:30])
            continue
        if not re.match(r'^图\s*\d+\s*·', title):
            continue
        drawn += 1
        tag = '[%s]' % title[:26]
        # --- 11 个必需字段 ---
        for name in FIELDS:
            val = field(text, name)
            if val is None:
                errors.append('%s 缺字段「%s」' % (tag, name))
            elif is_blank(val):
                errors.append('%s 字段「%s」还是占位' % (tag, name))
        # --- 旧字段名残留 ---
        for old in LEGACY:
            if re.search(r'-\s*' + re.escape(old) + r'\s*[：:]', text):
                warns.append('%s 还在用旧字段「%s」（新字段见 --fields）' % (tag, old))
        # --- 打分 ---
        score = field(text, '打分') or ''
        if len(re.findall(r'\d', score)) < 4:
            errors.append('%s 打分必须写四维分数（结构 / 过程 / 直观 / 辨析）' % tag)
        elif '依据' not in score:
            warns.append('%s 打分没写依据（哪句话 / 哪一步 / 哪两个概念让读者卡住）' % tag)
        # --- 理解障碍 ---
        barrier = field(text, '理解障碍') or ''
        hit = BANNED.search(barrier)
        if hit:
            errors.append('%s 理解障碍里出现主观词「%s」——要写读者在哪一步怎么想错' % (tag, hit.group(0)))
        # --- 教学任务 ---
        task = field(text, '教学任务') or ''
        if any(k in task for k in MULTI):
            warns.append('%s 教学任务看着不止一个（含「%s」）' % (tag, [k for k in MULTI if k in task][0]))
        if ('证明' in text[:400] or 'proof' in text[:400]) and ('证明该' in task or '证明结论' in task):
            errors.append('%s 服务证明的图不能把教学任务写成「证明该结论」（图不得替代证明）' % tag)
        # --- 插入位置：锚点 + 位置理由 ---
        anchor = field(text, '插入位置') or ''
        if anchor and '理由' not in anchor:
            errors.append('%s 插入位置只写了锚点、没写「理由」——要说明为什么是这一段' % tag)
        if anchor and not ANCHOR_HINTS.search(anchor):
            warns.append('%s 插入位置看不出具体锚点（应含卡片 id + 段落 / 公式 / 步骤 / 面板）' % tag)
        if ids:
            for cid in CARD_ID.findall(anchor):
                if cid not in ids:
                    errors.append('%s 锚点里的卡片 id 在 HTML 里不存在：%s' % (tag, cid))
        # --- 编排：3 默认 + 5 例外 ---
        orch = field(text, '编排') or ''
        if orch:
            d = [k for k in ORCH_DEFAULT if k in orch]
            e = [k for k in ORCH_EXCEPT if k in orch]
            if not d and not e:
                errors.append('%s 编排不在「3 默认 + 5 例外」之内（%s / %s）' % (tag, '/'.join(ORCH_DEFAULT), '/'.join(ORCH_EXCEPT)))
            elif e and '理由' not in orch:
                warns.append('%s 用了编排例外「%s」，必须写理由' % (tag, e[0]))
        # --- 视觉顺序 + 标识职责 ---
        order = field(text, '视觉顺序') or ''
        if order.count('→') < 2 and '先' not in order:
            warns.append('%s 视觉顺序没写成序列（「先看 … → 再比较 … → 最后得出 …」）' % tag)
        parts = [x for x in re.split(r'[、，,；;→]', order) if x.strip()]
        if len(parts) > 12:
            errors.append('%s 视觉顺序里 %d 项，超过单图上限（≤14 个对象、≤8 个关系），必须拆分' % (tag, len(parts)))
        elif len(parts) > 7:
            warns.append('%s 视觉顺序里 %d 项，偏密（超过 7 项先问能不能拆）' % (tag, len(parts)))
        if any(s in text for s in SIGNALS) and is_blank(field(text, '标识职责')):
            errors.append('%s 用了箭头 / 编号 / 颜色等视觉标识，必须写「标识职责」' % tag)
        # --- 图文对应 ---
        mapping = field(text, '图文对应') or ''
        if mapping and '↔' not in mapping and '对应' not in mapping:
            warns.append('%s 图文对应要逐条写「图中元素 ↔ 哪句正文 / 哪条公式」' % tag)
        # --- 图后解释与理解检查 ---
        chk = field(text, '理解检查') or ''
        if chk and '答案' not in chk:
            errors.append('%s 理解检查必须可判定对错 —— 要写出「（答案：…）」' % tag)
        if is_blank(field(text, '失败原因')):
            warns.append('%s 缺「失败原因」（读者答错时的常见原因）' % tag)
        # --- 替代文本（第 7 问的落点）---
        alt = field(text, '替代文本') or ''
        if alt and ALT_EMPTY.match(alt.strip()):
            errors.append('%s 替代文本不能写「%s」——第 7 问必须真的写出替代方案' % (tag, alt.strip()))
        # --- 状态 ---
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
        status = field(text, '状态') or ''
        if not any(s in status for s in STATUSES):
            errors.append('%s 状态非法：「%s」（应为 %s 之一）' % (tag, status, '/'.join(STATUSES)))
        elif any(s in status for s in READY):
            if not acc.strip():
                errors.append('%s 状态是「%s」但三层验收为空' % (tag, status.strip()))
        if '已弃用' in status and is_blank(field(text, '理由')):
            errors.append('%s 已弃用但没有写理由' % tag)
    if not drawn:
        errors.append('清单里没有任何出图条目')
    return errors, warns, drawn, missing


def main(argv):
    if '--fields' in argv:
        print('必需字段（%d）：%s' % (len(FIELDS), ' / '.join(FIELDS)))
        print('条件字段（%d）：%s' % (len(OPTIONAL), ' / '.join(OPTIONAL)))
        print('编排：默认 %s ｜ 例外 %s' % (' / '.join(ORCH_DEFAULT), ' / '.join(ORCH_EXCEPT)))
        return 0
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
