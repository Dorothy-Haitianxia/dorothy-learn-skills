#!/usr/bin/env node
/**
 * dorothy-picture · 渲染核对 / 固化导出
 *
 * 为什么需要它：本机没有别的 SVG 渲染器（cairosvg / inkscape / rsvg / magick 全无，浏览器被沙箱挡），
 * 所以「把图渲成 PNG 亲眼看」这一步只能靠 @resvg/resvg-js（纯本地预编译，无系统依赖）。
 *
 * 两个模式：
 *   默认        注入令牌与 .fig 规则后渲染成 PNG —— 供人（或 agent 的 read_image）核对
 *   --bake      输出「已把 var(--…) 解析成具体色值」的自包含 SVG —— 供图离开宿主页时使用
 *
 * 用法：
 *   node render_fig.js --html <页面.html> --list
 *   node render_fig.js --html <页面.html> --id <figure-id> --out <out.png> [--theme nasapunk] [--width 1280]
 *   node render_fig.js --figure <figs/fig-1.html> --css <style.css> --out <out.png>
 *   node render_fig.js --figure <figs/fig-1.html> --css <style.css> --out <baked.svg> --bake
 */
'use strict';
const fs = require('fs');
const path = require('path');

function argv(name, def) {
  const i = process.argv.indexOf('--' + name);
  if (i < 0) return def;
  const v = process.argv[i + 1];
  return (v === undefined || v.startsWith('--')) ? true : v;
}

const opt = {
  html: argv('html', null),
  figure: argv('figure', null),
  css: argv('css', null),
  id: argv('id', null),
  out: argv('out', null),
  theme: argv('theme', 'lonetrail'),
  width: parseInt(argv('width', '1280'), 10),
  bake: argv('bake', false) === true,
  list: argv('list', false) === true,
  dump: argv('dump', null)
};

function die(msg) { console.error('ERROR ' + msg); process.exit(2); }
function readText(p) { return fs.readFileSync(p, 'utf8').replace(/\r\n/g, '\n'); }

/* ---------- 取输入 ---------- */
let pageHtml = '';
let css = '';
let svg = '';

if (opt.html) {
  pageHtml = readText(opt.html);
  const styles = [];
  const re = /<style[^>]*>([\s\S]*?)<\/style>/g;
  let m;
  while ((m = re.exec(pageHtml))) styles.push(m[1]);
  if (!styles.length) die('页面里没有 <style>：' + opt.html);
  css = styles.sort((a, b) => b.length - a.length)[0];
  if (opt.list) {
    const ids = [];
    const fre = /<figure class="fig"[^>]*id="([^"]+)"/g;
    while ((m = fre.exec(pageHtml))) ids.push(m[1]);
    console.log(ids.join('\n'));
    process.exit(0);
  }
}
if (opt.figure && !css) {
  if (!opt.css) die('--figure 模式需要 --css，或用 --html 提供样式来源');
  css = readText(opt.css);
}
if (opt.css && !css) css = readText(opt.css);

if (opt.html && opt.id) {
  const at = pageHtml.indexOf('id="' + opt.id + '"');
  if (at < 0) die('页面里找不到 id="' + opt.id + '"');
  const seg = pageHtml.slice(at);
  const sm = seg.match(/<svg[\s\S]*?<\/svg>/);
  if (!sm) die('该 figure 里没有 <svg>');
  svg = sm[0];
} else if (opt.figure) {
  const t = readText(opt.figure);
  const sm = t.match(/<svg[\s\S]*?<\/svg>/);
  if (!sm) die('文件里没有 <svg>：' + opt.figure);
  svg = sm[0];
} else if (!opt.list) {
  die('需要 --html --id，或 --figure（--list 需要 --html）');
}

/* ---------- 抽令牌 ---------- */
function blockBody(text, needleRe) {
  const m = needleRe.exec(text);
  if (!m) return '';
  const open = text.indexOf('{', m.index);
  let d = 1, j = open + 1;
  while (j < text.length && d > 0) {
    if (text[j] === '{') d++;
    else if (text[j] === '}') d--;
    j++;
  }
  return text.slice(open + 1, j - 1);
}
function takeTokens(body, map) {
  const re = /(--[a-z0-9-]+)\s*:\s*([^;]+);/gi;
  let m;
  while ((m = re.exec(body))) map[m[1]] = m[2].trim();
}
const tokens = {};
const cleanCss = css.replace(/\/\*[\s\S]*?\*\//g, '');
takeTokens(blockBody(cleanCss, /:root\s*\{/), tokens);
if (opt.theme === 'nasapunk') takeTokens(blockBody(cleanCss, /:root\[data-theme="nasapunk"\]\s*\{/), tokens);
if (!Object.keys(tokens).length) die('没有解析到任何令牌（:root 块为空？）');

function resolveVars(text) {
  return text.replace(/var\(\s*(--[a-z0-9-]+)\s*(?:,\s*([^()]*?))?\)/gi, function (all, name, fb) {
    if (tokens[name] !== undefined) return tokens[name];
    if (fb !== undefined) return fb.trim();
    return all;
  });
}

/* ---------- 抽 .fig 规则（把 .fig 前缀剥掉，好让规则在 <svg> 内部命中） ---------- */
function extractRules(text, theme) {
  const out = [];
  let i = 0;
  while (i < text.length) {
    const open = text.indexOf('{', i);
    if (open < 0) break;
    const sel = text.slice(i, open).trim();
    let d = 1, j = open + 1;
    while (j < text.length && d > 0) {
      if (text[j] === '{') d++;
      else if (text[j] === '}') d--;
      j++;
    }
    const body = text.slice(open + 1, j - 1);
    i = j;
    if (!sel || sel.charAt(0) === '@') continue;                  // @media / @keyframes / @font-face
    if (sel.indexOf('data-theme') >= 0 && theme !== 'nasapunk') continue;
    if (sel.indexOf('figcaption') >= 0 || sel.indexOf('.fig__legend') >= 0) continue;   // 在 SVG 外
    if (!/^\.fig([\s.:]|$)/.test(sel)) continue;                 // 只要以 .fig 开头的规则
    if (/\.panel\.is-in/.test(sel)) continue;                    // 入场动画：静态渲染必须排除，否则元素停在 opacity:0
    const sels = sel.split(',')
      .map(function (x) { return x.trim(); })
      .map(function (x) { return x.replace(/^:root\[[^\]]*\]\s+/, '').replace(/^\.fig\s+/, '').replace(/^\.fig$/, ''); })
      .filter(function (x) { return x && x.indexOf('figcaption') < 0 && x.indexOf('.fig__legend') < 0; });
    if (!sels.length) continue;
    out.push(sels.join(',') + '{' + body.trim() + '}');
  }
  return out;
}
/* extractRules 已经返回 sel{body}，这里只做一次 var() 解析。
   曾经多拼了一个右花括号，usvg 的 CSS 解析器遇到 }} 就放弃后续规则，
   表现是「图只剩 SVG 默认 fill 的元素」——f-* 的 stroke 全丢。 */
const rules = extractRules(cleanCss, opt.theme).map(function (r) {
  const k = r.indexOf('{');
  return r.slice(0, k) + '{' + resolveVars(r.slice(k + 1, r.length - 1)) + '}';
});

/* ---------- 组装自包含 SVG ---------- */
let head = svg.slice(0, svg.indexOf('>') + 1);
if (head.indexOf('xmlns=') < 0) head = head.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"');
const styled = head + '\n<style>' + rules.join('\n') + '</style>' + svg.slice(svg.indexOf('>') + 1);

if (opt.dump) { fs.writeFileSync(opt.dump, styled, 'utf8'); }
if (opt.bake) {
  if (!opt.out) die('--bake 需要 --out <baked.svg>');
  if (!/\.svg$/i.test(opt.out)) { console.error('WARN --bake 的输出建议用 .svg 扩展名（当前 ' + opt.out + '）'); }
  fs.writeFileSync(opt.out, styled, 'utf8');
  console.log('baked svg -> ' + opt.out + '  (' + styled.length + ' chars, ' + rules.length + ' rules)');
  process.exit(0);
}

/* ---------- 渲染 PNG ---------- */
let Resvg;
try { Resvg = require('@resvg/resvg-js').Resvg; }
catch (e) {
  die('装载渲染器失败（' + e.message + '）—— 在 skill 目录跑 pnpm install --ignore-scripts；'
    + '若提示找不到 @resvg/resvg-js-<平台>，再补一次：pnpm add @resvg/resvg-js-win32-x64-msvc@2.6.2');
}
const bg = argv('bg', tokens['--paper'] || '#FFFFFF');
const img = new Resvg(styled, {
  fitTo: { mode: 'width', value: opt.width },
  background: bg,
  font: { loadSystemFonts: true, defaultFontFamily: 'Times New Roman' }
});
if (!opt.out) die('需要 --out <out.png>');
const rendered = img.render();
const png = rendered.asPng();
fs.mkdirSync(path.dirname(path.resolve(opt.out)), { recursive: true });
fs.writeFileSync(opt.out, png);
const w = rendered.width, h = rendered.height;
console.log('rendered -> ' + opt.out + '  ' + w + 'x' + h + '  ' + png.length + ' bytes  theme=' + opt.theme + '  rules=' + rules.length + '  tokens=' + Object.keys(tokens).length);
