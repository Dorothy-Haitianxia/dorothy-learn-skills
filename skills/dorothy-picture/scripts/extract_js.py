# -*- coding: utf-8 -*-
# 抽出 figure 片段里的内联脚本拼成一个文件，交给 node --check 做语法校验。
# 用法：python extract_js.py <临时.js> figs/*.html  →  然后 & '<node>' --check <临时.js>
# （沙箱里 Python 不能捕获 node 子进程输出，所以由 pwsh 侧再调 node --check）
import pathlib, re, sys
dst = pathlib.Path(sys.argv[1])
parts = []
for p in sys.argv[2:]:
    src = pathlib.Path(p).read_text(encoding='utf-8-sig')
    got = re.findall(r'<script[^>]*>([\s\S]*?)</script>', src)
    for s in got:
        parts.append('/* ' + pathlib.Path(p).name + ' */' + chr(10) + s)
if not parts:
    print('no inline script'); sys.exit(0)
dst.write_text((chr(10) + ';' + chr(10)).join(parts), encoding='utf-8')
print('scripts:', len(parts), '->', dst)
