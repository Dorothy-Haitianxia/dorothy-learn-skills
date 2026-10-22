/* ============================================================
   交互层
   缓动 / 阻尼 / 补间思路参考 zcy83821448/cassette 的 src/anim.js 与 styles.css：
     · ease 曲线与 4 档时长（press .12 / fast .22 / swift .34 / med .5）
     · damp() 帧率无关阻尼（拖动 14 / 松手 7 / 缩放 6）
     · cascadeIn 级联入场（--i × 34ms）
     · 读数滚动用 WAAPI，落地交给定时器而不是动画 finish
   reduced-motion：CSS 侧通配降级 + 这里直接落位。
   ============================================================ */
(function () {
  'use strict';

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var dialogOpen = false;          /* 浮层打开时屏蔽翻页快捷键 */
  var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };
  var lerp = function (a, b, t) { return a + (b - a) * t; };
  var damp = function (a, b, l, dt) { return lerp(a, b, 1 - Math.exp(-l * dt)); };

  /* ---------------------------------------------------- 主题（孤星 ⇄ NASA-punk）
     记忆：localStorage 键 dorothy:theme —— 大型知识库里各章共用同一份偏好；
           file:// 或隐私模式下 localStorage 可能抛错，try/catch 兜住，失败即用默认孤星。
     过渡：颜色过渡是唯一的具名例外，只在 .is-theming 存活期内生效（CSS 1.6 节）；
           进度条只动 transform:scaleX（不动 width），读数走等宽百分比。 */
  var THEME_KEY = 'dorothy:theme';
  var THEME_MS = 340;                                  /* 必须与 CSS 的 --t-theme 一致 */
  var THEME_CODE = { lonetrail: 'LONE', nasapunk: 'NASA' };
  var rootEl = document.documentElement;
  var themeOpts = Array.prototype.slice.call(document.querySelectorAll('[data-theme-set]'));
  var themeBox = document.querySelector('.theme');
  var themeFill = document.getElementById('themeFill');
  var themeRead = document.getElementById('themeRead');
  var themeCur = rootEl.getAttribute('data-theme') === 'nasapunk' ? 'nasapunk' : 'lonetrail';
  var themeClassTimer = 0, themeHoldTimer = 0, themeRaf = 0;

  function themeStore(name) {
    try { window.localStorage.setItem(THEME_KEY, name); } catch (err) { /* 不可用则忽略 */ }
  }

  function themePaint(name) {
    themeOpts.forEach(function (btn) {
      btn.setAttribute('aria-pressed', btn.getAttribute('data-theme-set') === name ? 'true' : 'false');
    });
    if (themeRead && !themeRaf) themeRead.textContent = THEME_CODE[name] || '';
  }

  function themeStop() {
    if (themeRaf) { window.cancelAnimationFrame(themeRaf); themeRaf = 0; }
    if (themeHoldTimer) { window.clearTimeout(themeHoldTimer); themeHoldTimer = 0; }
    if (themeClassTimer) { window.clearTimeout(themeClassTimer); themeClassTimer = 0; }
    if (themeBox) themeBox.classList.remove('is-running');
    if (themeFill) themeFill.style.setProperty('--p', 0);
  }

  function setTheme(name) {
    if (!THEME_CODE[name] || name === themeCur) { themePaint(themeCur); return; }
    themeStop();
    themeCur = name;
    /* 具名例外：加类 -> 强制重排 -> 换主题，颜色才从旧值过渡到新值 */
    rootEl.classList.add('is-theming');
    void rootEl.offsetHeight;
    rootEl.setAttribute('data-theme', name);
    themeStore(name);
    themePaint(name);
    /* 降级分支：类要当场摘掉。
       不能交给 themeStop()（它会清掉 themeClassTimer），否则 .is-theming 会永远留在 html 上，
       之后卡片边框一类过渡都会误用这 340ms 的曲线。 */
    if (reduce || !themeFill || !themeBox || !window.requestAnimationFrame) {
      rootEl.classList.remove('is-theming');
      themeStop();
      return;
    }

    themeClassTimer = window.setTimeout(function () {
      rootEl.classList.remove('is-theming');
      themeClassTimer = 0;
    }, THEME_MS + 20);
    themeBox.classList.add('is-running');
    var t0 = null;
    var step = function (now) {
      if (t0 === null) t0 = now;
      var p = Math.min(1, (now - t0) / THEME_MS);
      themeFill.style.setProperty('--p', p.toFixed(3));
      if (themeRead) themeRead.textContent = Math.round(p * 100) + '%';
      if (p < 1) { themeRaf = window.requestAnimationFrame(step); return; }
      themeRaf = 0;
      /* 完成态：条满格驻留 240ms -> 淡出（CSS 的 opacity 过渡）-> 归零并写回主题代号 */
      themeHoldTimer = window.setTimeout(function () {
        themeHoldTimer = 0;
        themeBox.classList.remove('is-running');
        themeFill.style.setProperty('--p', 0);
        if (themeRead) themeRead.textContent = THEME_CODE[themeCur] || '';
      }, 240);
    };
    themeRaf = window.requestAnimationFrame(step);
  }

  themeOpts.forEach(function (btn) {
    btn.addEventListener('click', function () { setTheme(btn.getAttribute('data-theme-set')); });
  });
  themePaint(themeCur);

  /* ---------------------------------------------------- 翻页 */
  var pages = Array.prototype.slice.call(document.querySelectorAll('.page'));
  var pagesBox = document.getElementById('pages');
  var dotsBox = document.getElementById('pageDots');
  var nowEl = document.getElementById('pageNow');
  var allEl = document.getElementById('pageAll');
  var fillEl = document.getElementById('pageFill');
  var prevBtn = document.getElementById('prevPage');
  var nextBtn = document.getElementById('nextPage');
  var navBtns = Array.prototype.slice.call(document.querySelectorAll('.chrome__nav .navlink'));
  var current = 0;

  function pad(n) { return (n < 10 ? '0' : '') + n; }
  allEl.textContent = pad(pages.length);

  function roll(el, text) {
    if (reduce || !el.animate) { el.textContent = text; return; }
    el.animate(
      [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(-.5em)' }],
      { duration: 150, easing: 'cubic-bezier(.4,0,1,1)', fill: 'forwards' });
    window.setTimeout(function () {
      el.textContent = text;
      el.animate(
        [{ opacity: 0, transform: 'translateY(.5em)' }, { opacity: 1, transform: 'none' }],
        { duration: 300, easing: 'cubic-bezier(.16,1,.3,1)' });
    }, 150);
  }

  function indexOfPage(id) {
    for (var i = 0; i < pages.length; i++) { if (pages[i].id === id) return i; }
    return -1;
  }

  function goTo(index, opts) {
    opts = opts || {};
    index = clamp(index, 0, pages.length - 1);
    if (index === current && !opts.force) return;
    var leaving = pages[current];
    var entering = pages[index];
    var back = index < current;

    leaving.classList.remove('is-active');
    leaving.classList.toggle('dir-prev', !back);
    entering.classList.toggle('dir-prev', back);
    if (leaving.id === 'p-map') { mapSetIn(false); }

    /* 先落到起始位再入场，避免首帧跳变 */
    void entering.offsetHeight;
    entering.classList.add('is-active');
    current = index;

    if (entering.id === 'p-map') {
      mapSetIn(true);
      if (!mapFramed) { mapFramed = true; focusMap(); }   /* 只框一次，之后保留用户取景 */
    }
    boardPlayIn(entering);                                /* 进页时重放该页板块的入场（核心概念 / 自测与习题） */
    if (leaving !== entering && (opts.scrollTop !== false)) {
      entering.querySelector('.page__inner').scrollTop = 0;
    }

    roll(nowEl, pad(current + 1));
    fillEl.style.setProperty('--p', ((current + 1) / pages.length).toFixed(3));
    prevBtn.disabled = current === 0;
    nextBtn.disabled = current === pages.length - 1;
    Array.prototype.forEach.call(dotsBox.children, function (dot, i) {
      dot.classList.toggle('is-current', i === current);
      dot.setAttribute('aria-current', i === current ? 'true' : 'false');
    });
    navBtns.forEach(function (btn) {
      btn.classList.toggle('is-current', btn.dataset.goto === entering.id);
    });
    /* file:// 下 replaceState 会抛 SecurityError，安静跳过 */
    try {
      if (location.hash !== '#' + entering.id) {
        history.replaceState(null, '', '#' + entering.id);
      }
    } catch (err) { /* 忽略 */ }
  }

  pages.forEach(function (page, i) {
    var dot = document.createElement('button');
    dot.type = 'button';
    dot.className = 'dot';
    dot.setAttribute('aria-label', page.dataset.title || ('第 ' + (i + 1) + ' 页'));
    dot.addEventListener('click', function () { goTo(i); });
    dotsBox.appendChild(dot);
  });

  navBtns.forEach(function (btn) {
    btn.addEventListener('click', function () { goTo(indexOfPage(btn.dataset.goto)); });
  });
  Array.prototype.forEach.call(document.querySelectorAll('[data-goto]'), function (btn) {
    if (btn.closest('.chrome__nav')) return;
    btn.addEventListener('click', function () { goTo(indexOfPage(btn.dataset.goto)); });
  });
  prevBtn.addEventListener('click', function () { goTo(current - 1); });
  nextBtn.addEventListener('click', function () { goTo(current + 1); });

  document.addEventListener('keydown', function (event) {
    if (dialogOpen) return;                      /* 浮层里用 Esc 关，不翻页 */
    if (event.metaKey || event.ctrlKey || event.altKey) return;
    var key = event.key;
    var target = event.target;
    if (target && target.closest && target.closest('[role="tablist"]')) return;   /* 板块控件里 ←/→ 切板块 */
    if (target && target.closest && target.closest('[data-search]')) return;      /* 搜索框里 ←/→ 是光标，不能翻页 */
    if (target && target.closest && target.closest('.toggle') &&
        (key === 'ArrowUp' || key === 'ArrowDown')) return;   /* 组内移动焦点 */
    if (key === 'ArrowRight' || key === 'PageDown') { event.preventDefault(); goTo(current + 1); }
    else if (key === 'ArrowLeft' || key === 'PageUp') { event.preventDefault(); goTo(current - 1); }
    else if (key === 'Home') { event.preventDefault(); goTo(0); }
    else if (key === 'End') { event.preventDefault(); goTo(pages.length - 1); }
  });

  /* ---------------------------------------------------- 知识卡展开（同组互斥） */
  var SETTLE = reduce ? 0 : 280;

  function panelOf(btn) { return document.getElementById(btn.getAttribute('aria-controls')); }

  function labelOf(btn, open) {
    var text = open ? btn.getAttribute('data-open-label') : btn.getAttribute('data-close-label');
    var slot = btn.querySelector('.toggle__tx');
    var ico = btn.querySelector('.toggle__ico');
    if (slot && text) slot.textContent = text;
    if (ico) ico.textContent = open ? '−' : '+';
  }

  function expand(btn) {
    var panel = panelOf(btn);
    if (!panel) return;
    var card = btn.closest('.card, .quiz');
    btn.setAttribute('aria-expanded', 'true');
    if (card) card.classList.add('is-open');
    labelOf(btn, true);
    panel.hidden = false;
    void panel.offsetHeight;
    panel.classList.add('is-in');
  }

  function collapse(btn) {
    var panel = panelOf(btn);
    if (!panel) return;
    var card = btn.closest('.card, .quiz');
    btn.setAttribute('aria-expanded', 'false');
    if (card) card.classList.remove('is-open');
    labelOf(btn, false);
    panel.classList.remove('is-in');
    var done = false;
    var hide = function () {
      if (done) return;
      done = true;
      panel.removeEventListener('transitionend', onEnd);
      if (!panel.classList.contains('is-in')) panel.hidden = true;
    };
    var onEnd = function (event) {
      if (event.target === panel || event.target === panel.firstElementChild) hide();
    };
    panel.addEventListener('transitionend', onEnd);
    window.setTimeout(hide, SETTLE);
  }

  document.addEventListener('click', function (event) {
    var btn = event.target.closest && event.target.closest('.toggle');
    if (!btn) return;
    var open = btn.getAttribute('aria-expanded') === 'true';
    var group = btn.closest('[data-accordion]');
    if (group && !open) {
      Array.prototype.forEach.call(group.querySelectorAll('.toggle[aria-expanded="true"]'), function (other) {
        if (other !== btn) collapse(other);
      });
    }
    if (open) collapse(btn); else expand(btn);
  });

  document.addEventListener('keydown', function (event) {
    var btn = event.target.closest && event.target.closest('.toggle');
    if (!btn) return;
    var key = event.key;
    if (key !== 'ArrowDown' && key !== 'ArrowUp' && key !== 'Home' && key !== 'End') return;
    var scope = btn.closest('[data-accordion]') || document;
    var list = Array.prototype.slice.call(scope.querySelectorAll('.toggle'));
    var index = list.indexOf(btn);
    if (index < 0) return;
    var next = key === 'ArrowDown' ? index + 1 : key === 'ArrowUp' ? index - 1
      : key === 'Home' ? 0 : list.length - 1;
    if (next < 0 || next >= list.length) return;
    event.preventDefault();
    list[next].focus();
  });

  /* ---------------------------------------------------- 分板块切换（核心概念三块；自测与习题两块）
     每组 [data-tabs] 里有 N 个 role="tab" + N 个 role="tabpanel" 的 .board，
     任一时刻只显示一块（默认第一块）；每块各自记 scrollTop；切换只做 opacity + translateY。
     同一套逻辑服务两组（data-board 全局唯一：def / thm / ex / self / exercise）。 */
  var tabGroups = Array.prototype.slice.call(document.querySelectorAll('[data-tabs]')).map(function (box) {
    var tabs = Array.prototype.slice.call(box.querySelectorAll('[role="tab"]'));
    return {
      box: box,
      tabs: tabs,
      boards: tabs.map(function (tab) { return document.getElementById(tab.getAttribute('aria-controls')); }),
      boardScroll: {},
      cur: 0
    };
  });

  function boardKey(group, i) { return group.tabs[i] ? group.tabs[i].getAttribute('data-board') : ''; }

  function boardIndex(group, key) {
    for (var i = 0; i < group.tabs.length; i++) { if (boardKey(group, i) === key) { return i; } }
    return -1;
  }

  function groupByKey(key) {
    for (var i = 0; i < tabGroups.length; i++) { if (boardIndex(tabGroups[i], key) >= 0) { return tabGroups[i]; } }
    return null;
  }

  function groupOfBoard(board) {
    for (var i = 0; i < tabGroups.length; i++) { if (tabGroups[i].boards.indexOf(board) >= 0) { return tabGroups[i]; } }
    return null;
  }

  function boardPlay(group) {
    var board = group.boards[group.cur];
    if (!board || board.hidden) return;
    board.classList.remove('is-in');
    void board.offsetHeight;                       /* 强制重排，让 boardIn 每次都能重播 */
    board.classList.add('is-in');
  }

  /* 进入某页时重放该页板块的入场（与地图的 mapSetIn 同思路） */
  function boardPlayIn(page) {
    tabGroups.forEach(function (group) {
      if (page && page.contains && page.contains(group.box)) { boardPlay(group); }
    });
  }

  function showBoard(key, opts) {
    opts = opts || {};
    var group = opts.group || groupByKey(key);
    if (!group || !group.tabs.length) return;
    var index = boardIndex(group, key);
    if (index < 0) return;
    var board = group.boards[index];
    var inner = board ? board.closest('.page').querySelector('.page__inner') : null;
    if (inner) { group.boardScroll[boardKey(group, group.cur)] = inner.scrollTop; }   /* 先存离场板块的位置 */
    group.tabs.forEach(function (tab, i) {
      var on = i === index;
      tab.setAttribute('aria-selected', on ? 'true' : 'false');
      tab.tabIndex = on ? 0 : -1;
      if (group.boards[i]) { group.boards[i].hidden = !on; }
    });
    group.box.style.setProperty('--tab', String(index));
    group.cur = index;
    boardPlay(group);
    /* 回到该板块上次读到的位置（首次进入为 0）；openCard 用 keepScroll 自己精确滚动 */
    if (inner && !opts.keepScroll) { inner.scrollTop = group.boardScroll[key] || 0; }
  }

  tabGroups.forEach(function (group) {
    group.tabs.forEach(function (tab, i) {
      tab.addEventListener('click', function () {
        if (tab.getAttribute('aria-selected') !== 'true') showBoard(boardKey(group, i), { group: group });
      });
      tab.addEventListener('keydown', function (event) {
        var key = event.key, next = -1;
        if (key === 'ArrowRight' || key === 'ArrowDown') { next = (i + 1) % group.tabs.length; }
        else if (key === 'ArrowLeft' || key === 'ArrowUp') { next = (i - 1 + group.tabs.length) % group.tabs.length; }
        else if (key === 'Home') { next = 0; }
        else if (key === 'End') { next = group.tabs.length - 1; }
        if (next < 0) { return; }
        event.preventDefault();
        group.tabs[next].focus();
        showBoard(boardKey(group, next), { group: group });   /* 自动激活：焦点到哪一块就切到哪一块 */
      });
    });
  });

  /* ---------------------------------------------------- 全局搜索（只索引核心概念）
     索引：扫 #p-core 的 .card（语义标签 / 标题 / 摘要 / 条件结论 / 展开正文，剔除出处行）。
     多词 AND；权重 标题 3 > 摘要 2 > 正文 1；片段取命中处前后窗口，命中词用 <mark>（全部走
     createTextNode，不拼 innerHTML）。跳转复用 openCard()：它会先切板块再展开+滚动+闪一下。 */
  var searchBox = document.querySelector('[data-search]');
  var searchIn = document.getElementById('searchIn');
  var searchHits = document.getElementById('searchHits');
  var searchIndex = [];
  var hits = [];
  var hitCur = -1;
  var composing = false;

  function sq(s) { return (s || '').replace(/\s+/g, ' ').trim(); }
  function fold(s) { return (s || '').replace(/\u3000/g, ' ').toLowerCase(); }   /* 保长度，下标可直接映射回原文 */

  function buildIndex() {
    var cards = document.querySelectorAll('#p-core .card');
    Array.prototype.forEach.call(cards, function (card) {
      var tag = card.querySelector('.tag span');
      var title = card.querySelector('.card__title');
      var summary = card.querySelector('.card__summary');
      var facts = card.querySelector('.facts');
      var panel = card.querySelector('.panel__inner');
      var parts = [];
      if (facts) { parts.push(facts.textContent); }
      Array.prototype.forEach.call(panel ? panel.children : [], function (node) {
        if (!(node.classList && node.classList.contains('card__src'))) { parts.push(node.textContent); }
      });
      searchIndex.push({
        id: card.id,
        code: tag ? sq(tag.textContent) : '',
        title: sq(title ? title.textContent : card.id),
        summary: sq(summary ? summary.textContent : ''),
        body: sq(parts.join(' '))
      });
    });
  }

  function snippet(text, at, len) {
    var start = Math.max(0, at - 26);
    var end = Math.min(text.length, at + len + 44);
    return { text: text.slice(start, end), lead: start > 0, tail: end < text.length, marks: [] };
  }

  function search(query) {
    var terms = sq(query).split(' ').filter(Boolean);
    var out = [];
    if (!terms.length) { return out; }
    searchIndex.forEach(function (item) {
      var score = 0, snip = null;
      for (var i = 0; i < terms.length; i++) {
        var t = fold(terms[i]), hit = null;          /* 查询词也要折叠，否则「Fourier」这类大写词永远搜不到 */
        var pTitle = fold(item.title).indexOf(t);
        var pSum = fold(item.summary).indexOf(t);
        var pBody = fold(item.body).indexOf(t);
        if (pTitle < 0 && pSum < 0 && pBody < 0) { return; }        /* 多词 AND：有一个没命中就出局 */
        if (pTitle >= 0) { score += 3; hit = { at: pTitle, text: item.title }; }
        if (pSum >= 0) { score += 2; if (!hit || hit.text !== item.summary) { hit = hit || { at: pSum, text: item.summary }; } }
        if (pBody >= 0) { score += 1; }
        /* 片段优先取摘要，其次正文，最后标题 */
        if (!snip) {
          if (pSum >= 0) { snip = snippet(item.summary, pSum, t.length); }
          else if (pBody >= 0) { snip = snippet(item.body, pBody, t.length); }
          else { snip = snippet(item.title, pTitle, t.length); }
        }
      }
      if (snip) { snip.terms = terms.map(fold); }     /* 高亮定位也在折叠后的文本里找，切片仍取原文（保住大小写） */
      out.push({ item: item, score: score, snip: snip });
    });
    out.sort(function (a, b) { return b.score - a.score || 0; });
    return out.slice(0, 20);
  }

  function appendMarked(host, snip) {
    if (snip.lead) { host.appendChild(document.createTextNode('…')); }
    var text = snip.text, folded = fold(text), spans = [];
    snip.terms.forEach(function (t) {
      var from = 0, k;
      while (t && (k = folded.indexOf(t, from)) >= 0) { spans.push([k, k + t.length]); from = k + t.length; }
    });
    spans.sort(function (a, b) { return a[0] - b[0]; });
    var pos = 0;
    spans.forEach(function (sp) {
      if (sp[0] < pos) { return; }                                   /* 重叠的跳过 */
      if (sp[0] > pos) { host.appendChild(document.createTextNode(text.slice(pos, sp[0]))); }
      var m = document.createElement('mark');
      m.textContent = text.slice(sp[0], sp[1]);
      host.appendChild(m);
      pos = sp[1];
    });
    if (pos < text.length) { host.appendChild(document.createTextNode(text.slice(pos))); }
    if (snip.tail) { host.appendChild(document.createTextNode('…')); }
  }

  function openHits(on) {
    if (searchBox) { searchBox.classList.toggle('is-open', !!on); }
    if (searchIn) { searchIn.setAttribute('aria-expanded', on ? 'true' : 'false'); }
  }

  function clearHits() {
    hits = [];
    hitCur = -1;
    if (searchHits) { while (searchHits.firstChild) { searchHits.removeChild(searchHits.firstChild); } }
    if (searchIn) { searchIn.removeAttribute('aria-activedescendant'); }
  }

  function renderHits(query) {
    if (!searchHits) { return; }
    clearHits();
    hits = search(query);
    if (!hits.length) {
      var none = document.createElement('li');
      none.className = 'hits__none';
      none.setAttribute('role', 'presentation');
      none.appendChild(document.createTextNode('未找到 '));
      var b = document.createElement('b');
      b.textContent = '「' + sq(query) + '」';
      none.appendChild(b);
      none.appendChild(document.createTextNode(' 。搜索范围仅限核心概念（定义 / 定理 / 例子），不含易错点与自测题。'));
      searchHits.appendChild(none);
      openHits(true);
      return;
    }
    hits.forEach(function (row, i) {
      var li = document.createElement('li');
      li.className = 'hits__item';
      li.id = 'hit-' + i;
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', 'false');
      var head = document.createElement('p');
      var tag = document.createElement('span');
      tag.className = 'hits__tag';
      tag.textContent = row.item.code;
      var title = document.createElement('span');
      title.className = 'hits__title';
      title.textContent = row.item.title;
      head.appendChild(tag);
      head.appendChild(title);
      li.appendChild(head);
      if (row.snip) {
        var p = document.createElement('p');
        p.className = 'hits__snip';
        appendMarked(p, row.snip);
        li.appendChild(p);
      }
      li.addEventListener('click', function () { jumpTo(i); });
      searchHits.appendChild(li);
    });
    var note = document.createElement('li');
    note.className = 'hits__note';
    note.textContent = '共 ' + hits.length + ' 条 · 仅核心概念 · ↑↓ 选择，Enter 跳转，Esc 清空';
    searchHits.appendChild(note);
    openHits(true);
  }

  function setHit(i) {
    if (!searchHits || !hits.length) { return; }
    hitCur = (i + hits.length) % hits.length;
    Array.prototype.forEach.call(searchHits.querySelectorAll('.hits__item'), function (el, k) {
      el.classList.toggle('is-active', k === hitCur);
      el.setAttribute('aria-selected', k === hitCur ? 'true' : 'false');
    });
    if (searchIn) { searchIn.setAttribute('aria-activedescendant', 'hit-' + hitCur); }
    var el = document.getElementById('hit-' + hitCur);
    if (el && el.scrollIntoView) { el.scrollIntoView({ block: 'nearest' }); }
  }

  function jumpTo(i) {
    var row = hits[i];
    if (!row) { return; }
    var id = row.item.id;
    if (searchIn) { searchIn.value = ''; }          /* 跳转后清空搜索栏，免得挡住卡片 */
    clearHits();
    openHits(false);
    openCard(id);                                   /* 先切板块，再展开 + 滚到卡片 + 闪一下 */
    window.setTimeout(function () {                 /* 焦点交回卡片，键盘用户接着往下走 */
      var card = document.getElementById(id);
      var btn = card ? card.querySelector('.toggle') : null;
      if (btn && btn.focus) { btn.focus({ preventScroll: true }); }
    }, reduce ? 0 : 260);
  }

  function runSearch() {
    var q = searchIn ? searchIn.value : '';
    if (!sq(q)) { clearHits(); openHits(false); return; }
    renderHits(q);
  }

  if (searchIn) {
    searchIn.addEventListener('input', function () { if (!composing) { runSearch(); } });
    /* 中文输入法：拼字过程中不要搜，compositionend 再搜 */
    searchIn.addEventListener('compositionstart', function () { composing = true; });
    searchIn.addEventListener('compositionend', function () { composing = false; runSearch(); });
    searchIn.addEventListener('focus', function () { if (sq(searchIn.value)) { runSearch(); } });
    searchIn.addEventListener('keydown', function (event) {
      var key = event.key;
      if (key === 'ArrowDown') { event.preventDefault(); if (hits.length) { openHits(true); setHit(hitCur + 1); } }
      else if (key === 'ArrowUp') { event.preventDefault(); setHit(hitCur - 1); }
      else if (key === 'Enter') { event.preventDefault(); if (hitCur >= 0) { jumpTo(hitCur); } }
      else if (key === 'Escape') { event.preventDefault(); if (searchIn.value) { searchIn.value = ''; runSearch(); } else { openHits(false); } }
    });
  }
  document.addEventListener('click', function (event) {
    if (searchBox && !searchBox.contains(event.target)) { openHits(false); }
  });
  buildIndex();

  /* ---------------------------------------------------- 概念互引浮层 */
  var refBox = document.getElementById('refBox');
  var refBody = document.getElementById('refBoxBody');
  var refBack = document.getElementById('refBack');
  var refLabel = document.getElementById('refStackLabel');
  var refStack = [];
  var refReturn = null;

  function coreInner() {
    var page = document.getElementById('p-core');
    return page ? page.querySelector('.page__inner') : null;
  }

  /* 用目标卡的原件拼出浮层内容：标签 + 标题 + 摘要/条件结论 + 展开内容 + 出处 */
  function refBuild(id) {
    var card = document.getElementById(id);
    if (!card) return null;
    var box = document.createElement('div');
    var tag = card.querySelector('.tag');
    if (tag) box.appendChild(tag.cloneNode(true));
    var title = card.querySelector('.card__title');
    if (title) {
      var head = title.cloneNode(true);
      head.id = 'refBoxTitle';
      box.appendChild(head);
    }
    var summary = card.querySelector('.card__summary');
    if (summary) box.appendChild(summary.cloneNode(true));
    var facts = card.querySelector('.facts');
    if (facts) box.appendChild(facts.cloneNode(true));
    var panel = card.querySelector('.panel__inner');
    var holder = document.createElement('div');
    holder.className = 'panel is-in';          /* is-in 让展开内容与插图动画立即生效 */
    if (panel) holder.appendChild(panel.cloneNode(true));
    box.appendChild(holder);
    var src = card.querySelector('.card__src');
    if (src) box.appendChild(src.cloneNode(true));
    return box;
  }

  function refRender() {
    var id = refStack[refStack.length - 1];
    var built = refBuild(id);
    if (!built) return false;
    refBody.innerHTML = '';
    refBody.appendChild(built);
    refLabel.textContent = refStack.length > 1
      ? ('返回栈 · 第 ' + refStack.length + ' 层') : '概念速览';
    refBack.querySelector('.refbox__tx').textContent =
      refStack.length > 1 ? '返回上一层' : '返回原处';
    refBody.scrollTop = 0;
    return true;
  }

  function refOpen(id, trigger) {
    if (!document.getElementById(id)) return;
    if (!refStack.length) {
      var inner = coreInner();
      refReturn = { scroll: inner ? inner.scrollTop : 0, trigger: trigger || null };
    }
    refStack.push(id);
    if (!refRender()) { refStack.pop(); return; }
    refBox.hidden = false;
    void refBox.offsetHeight;
    refBox.classList.add('is-in');
    dialogOpen = true;
    refBack.focus();
  }

  function refClose() {
    refBox.classList.remove('is-in');
    var finish = function () {
      refBox.hidden = true;
      refBody.innerHTML = '';
      dialogOpen = false;
      var back = refReturn;
      refStack = [];
      refReturn = null;
      if (!back) return;
      var inner = coreInner();
      if (inner) inner.scrollTop = back.scroll;      /* 回到点开时的那一处 */
      var trigger = back.trigger;
      if (trigger && trigger.focus) {
        try { trigger.focus({ preventScroll: true }); } catch (err) { trigger.focus(); }
      }
      if (trigger && trigger.classList && !reduce) {
        trigger.classList.add('is-flash');
        window.setTimeout(function () { trigger.classList.remove('is-flash'); }, 1600);
      }
    };
    window.setTimeout(finish, reduce ? 0 : 300);
  }

  if (refBox) {
    document.addEventListener('click', function (event) {
      var link = event.target.closest && event.target.closest('.ref');
      if (!link) return;
      event.preventDefault();
      refOpen(link.getAttribute('data-ref'), link);
    });
    refBack.addEventListener('click', function () {
      if (refStack.length > 1) { refStack.pop(); refRender(); }
      else refClose();
    });
    refBox.addEventListener('click', function (event) {
      if (event.target.classList && event.target.classList.contains('refbox__scrim')) refClose();
    });
    document.addEventListener('keydown', function (event) {
      if (refBox.hidden) return;
      if (event.key === 'Escape') { event.preventDefault(); refClose(); return; }
      if (event.key !== 'Tab') return;
      var items = refBox.querySelectorAll('a[href], button');
      if (!items.length) return;
      var first = items[0];
      var last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    });
  }

  /* ---------------------------------------------------- 知识地图：平移 / 缩放 / 高亮 */
  var wrap = document.querySelector('.mapwrap');
  var svg = document.getElementById('mapSvg');
  var view = document.getElementById('mapView');
  var miniBox = document.querySelector('.map__mini');
  var miniView = document.getElementById('miniView');
  var nodes = Array.prototype.slice.call(document.querySelectorAll('.node'));
  var edges = Array.prototype.slice.call(document.querySelectorAll('.edge'));
  var VB = { w: 3000, h: 1600 };

  var st = { s: 1, tx: 0, ty: 0 };            /* 当前（屏幕像素空间） */
  var want = { s: 1, tx: 0, ty: 0 };          /* 目标 */
  var drag = null;
  var mapFramed = false;
  var vel = { x: 0, y: 0, lastX: 0, lastY: 0, lastT: 0 };
  var MIN_S = 0.9, MAX_S = 3.4;

  /* 级联序号写进 --n / --i，节奏与上限交给 CSS 的 min()（cassette 的 cascadeIn 写法） */
  nodes.forEach(function (node, i) { node.style.setProperty('--n', String(i)); });
  edges.forEach(function (edge, i) { edge.style.setProperty('--i', String(i)); });

  function geom() {
    var box = wrap.getBoundingClientRect();
    var k = Math.min(box.width / VB.w, box.height / VB.h);
    return { box: box, k: k, ox: (box.width - VB.w * k) / 2, oy: (box.height - VB.h * k) / 2 };
  }

  /* 平移：内容不能被拖出视野（缩放后贴边即停，缩小时居中） */
  function clampPan() {
    var g = geom();
    var contentW = VB.w * g.k * want.s;
    var contentH = VB.h * g.k * want.s;
    if (contentW <= g.box.width) {
      want.tx = (g.box.width - contentW) / 2 - g.ox;
    } else {
      want.tx = clamp(want.tx, g.box.width - g.ox - contentW, -g.ox);
    }
    if (contentH <= g.box.height) {
      want.ty = (g.box.height - contentH) / 2 - g.oy;
    } else {
      want.ty = clamp(want.ty, g.box.height - g.oy - contentH, -g.oy);
    }
  }

  function panBy(dx, dy) {
    want.tx += dx;
    want.ty += dy;
    clampPan();
    st.tx = want.tx;
    st.ty = want.ty;
  }

  function apply() {
    var g = geom();
    view.setAttribute('transform',
      'translate(' + (st.tx / g.k).toFixed(2) + ' ' + (st.ty / g.k).toFixed(2) + ') scale(' + st.s.toFixed(4) + ')');
    updateMini(g);
  }

  /* 缩略图上的视野框：把当前可见区域换算回内容坐标 */
  function updateMini(g) {
    if (!miniView) return;
    g = g || geom();
    var scale = g.k * st.s;
    var left = (0 - g.ox - st.tx) / scale;
    var top = (0 - g.oy - st.ty) / scale;
    var w = g.box.width / scale;
    var h = g.box.height / scale;
    left = clamp(left, 0, VB.w);
    top = clamp(top, 0, VB.h);
    miniView.setAttribute('x', left.toFixed(1));
    miniView.setAttribute('y', top.toFixed(1));
    miniView.setAttribute('width', Math.min(w, VB.w - left).toFixed(1));
    miniView.setAttribute('height', Math.min(h, VB.h - top).toFixed(1));
  }

  /* 屏幕坐标 ↔ 内容坐标：sx = ox + tx + k·s·c  （ox/oy 来自 preserveAspectRatio 的居中留白） */
  function setZoom(s, cx, cy) {
    var g = geom();
    s = clamp(s, MIN_S, MAX_S);
    if (cx === undefined) { cx = g.box.width / 2; cy = g.box.height / 2; }
    var contentX = (cx - g.ox - st.tx) / (g.k * st.s);
    var contentY = (cy - g.oy - st.ty) / (g.k * st.s);
    st.s = s;
    st.tx = cx - g.ox - contentX * s * g.k;
    st.ty = cy - g.oy - contentY * s * g.k;
    want.s = s; want.tx = st.tx; want.ty = st.ty;
    clampPan();
    st.tx = want.tx; st.ty = want.ty;
    apply();
  }

  /* 把内容坐标 (cx, cy) 摆到舞台中心 */
  function focusOn(cx, cy, s) {
    var g = geom();
    s = clamp(s, MIN_S, MAX_S);
    st.s = s;
    st.tx = g.box.width / 2 - g.ox - cx * s * g.k;
    st.ty = g.box.height / 2 - g.oy - cy * s * g.k;
    want.s = s; want.tx = st.tx; want.ty = st.ty;
    clampPan();
    st.tx = want.tx; st.ty = want.ty;
    apply();
  }

  function mapFit(animate) {
    want.s = 1; want.tx = 0; want.ty = 0;
    if (!animate || reduce) { st.s = 1; st.tx = 0; st.ty = 0; apply(); }
  }

  function mapSetIn(on) {
    if (!wrap) return;
    if (on) {
      wrap.classList.remove('is-in');
      if (!reduce) { void wrap.offsetWidth; wrap.classList.add('is-in'); }
    } else {
      wrap.classList.remove('is-in');
    }
  }

  function focusMap() {
    /* 初始取景：概念列与定理列之间（内容坐标），放大到可读 */
    focusOn(700, 800, 1.6);
  }

  function hotFor(id) {
    var related = [];
    edges.forEach(function (edge) {
      var hit = edge.dataset.from === id || edge.dataset.to === id;
      edge.classList.toggle('is-hot', hit);
      edge.classList.toggle('is-muted', !hit);
      if (hit) related.push(edge.dataset.from, edge.dataset.to);
    });
    nodes.forEach(function (node) {
      var self = node.dataset.id === id;
      node.classList.toggle('is-hot', self || related.indexOf(node.dataset.id) >= 0);
      node.classList.toggle('is-muted', !(self || related.indexOf(node.dataset.id) >= 0));
    });
  }

  function clearHot() {
    edges.forEach(function (edge) { edge.classList.remove('is-hot', 'is-muted'); });
    nodes.forEach(function (node) { node.classList.remove('is-hot', 'is-muted'); });
  }

  function openCard(id) {
    var card = document.getElementById(id);
    if (!card) return;
    /* 卡片可能在别的板块里：先切板块（不动滚动），再交给下面精确滚到卡片 */
    var board = card.closest && card.closest('.board');
    if (board) { showBoard(board.getAttribute('data-board'), { group: groupOfBoard(board), keepScroll: true }); }
    var page = card.closest('.page');
    var index = indexOfPage(page.id);
    goTo(index);
    var inner = page.querySelector('.page__inner');
    window.setTimeout(function () {
      var btn = card.querySelector('.toggle');
      if (btn && btn.getAttribute('aria-expanded') !== 'true' && card.classList.contains('card')) {
        var group = btn.closest('[data-accordion]');
        if (group) {
          Array.prototype.forEach.call(group.querySelectorAll('.toggle[aria-expanded="true"]'), function (other) {
            if (other !== btn) collapse(other);
          });
        }
        expand(btn);
      }
      if (inner) {
        var top = card.getBoundingClientRect().top - inner.getBoundingClientRect().top + inner.scrollTop - 96;
        inner.scrollTo({ top: top, behavior: reduce ? 'auto' : 'smooth' });
      }
      card.classList.remove('is-flash');
      void card.offsetWidth;
      if (!reduce) card.classList.add('is-flash');
      window.setTimeout(function () { card.classList.remove('is-flash'); }, 1600);
    }, reduce ? 0 : 220);
  }

  var dragMoved = false;
  nodes.forEach(function (node) {
    node.addEventListener('pointerenter', function () { hotFor(node.dataset.id); });
    node.addEventListener('focus', function () { hotFor(node.dataset.id); });
    node.addEventListener('pointerleave', clearHot);
    node.addEventListener('blur', clearHot);
    node.addEventListener('click', function () {
      if (dragMoved) return;
      openCard(node.dataset.id);
    });
    node.addEventListener('keydown', function (event) {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openCard(node.dataset.id);
      }
    });
  });

  if (wrap) {
    wrap.addEventListener('pointerdown', function (event) {
      if (event.target.closest('.map__tools') || event.target.closest('.map__mini')) return;
      drag = { x: event.clientX, y: event.clientY, id: event.pointerId, moved: false };
      dragMoved = false;
      vel.x = 0; vel.y = 0;
      vel.lastX = event.clientX; vel.lastY = event.clientY; vel.lastT = performance.now();
      /* 不在 pointerdown 抓指针：那会把后续 click 派发到容器，节点就点不动了。
         只有真的开始拖动（超过阈值）才捕获。 */
    });

    wrap.addEventListener('pointermove', function (event) {
      if (!drag || event.pointerId !== drag.id) return;
      var dx = event.clientX - drag.x;
      var dy = event.clientY - drag.y;
      if (!drag.moved) {
        if (Math.abs(event.clientX - drag.x) + Math.abs(event.clientY - drag.y) < 3) return;
        drag.moved = true;
        dragMoved = true;
        wrap.classList.add('is-grabbing');
        try { wrap.setPointerCapture(event.pointerId); } catch (err) { /* 忽略 */ }
      }
      drag.x = event.clientX; drag.y = event.clientY;
      panBy(dx, dy);
      /* 速度用 px/s 记，方向与拖动一致；不再乘系数、不再取反 */
      var now = performance.now();
      var dt = Math.max(now - vel.lastT, 1) / 1000;
      vel.x = (event.clientX - vel.lastX) / dt;
      vel.y = (event.clientY - vel.lastY) / dt;
      vel.lastX = event.clientX; vel.lastY = event.clientY; vel.lastT = now;
      apply();
    });

    var release = function (event) {
      if (!drag) return;
      var wasDrag = drag.moved;
      drag = null;
      wrap.classList.remove('is-grabbing');
      /* 手停住之后再松手，不该再甩出去：速度太旧或太大都直接归零 */
      var stale = performance.now() - vel.lastT > 80;
      var speed = Math.sqrt(vel.x * vel.x + vel.y * vel.y);
      if (!wasDrag || stale || speed < 40) { vel.x = 0; vel.y = 0; }
      else if (speed > 1400) { vel.x *= 1400 / speed; vel.y *= 1400 / speed; }
      if (wasDrag && wrap.hasPointerCapture && event.pointerId !== undefined) {
        try { wrap.releasePointerCapture(event.pointerId); } catch (err) { /* 已释放 */ }
      }
    };
    wrap.addEventListener('pointerup', release);
    wrap.addEventListener('pointercancel', release);

    wrap.addEventListener('wheel', function (event) {
      event.preventDefault();
      var g = geom();
      var box = g.box;
      var factor = Math.exp(-event.deltaY * 0.0011);
      setZoom(want.s * factor, event.clientX - box.left, event.clientY - box.top);
    }, { passive: false });

    wrap.addEventListener('dblclick', function (event) {
      if (event.target.closest('.node')) return;
      var g = geom();
      var box = g.box;
      setZoom(want.s < 1.6 ? want.s * 1.6 : 1, event.clientX - box.left, event.clientY - box.top);
    });

    Array.prototype.forEach.call(document.querySelectorAll('.map__tools .tool'), function (btn) {
      btn.addEventListener('click', function () {
        var kind = btn.dataset.zoom;
        if (kind === 'in') setZoom(want.s * 1.25);
        else if (kind === 'out') setZoom(want.s / 1.25);
        else { want.s = 1; want.tx = 0; want.ty = 0; if (reduce) mapFit(false); }
      });
    });
  }

  if (miniBox) {
    var miniJump = function (event) {
      var box = miniBox.getBoundingClientRect();
      var cx = (event.clientX - box.left) / box.width * VB.w;
      var cy = (event.clientY - box.top) / box.height * VB.h;
      focusOn(cx, cy, st.s);
    };
    miniBox.addEventListener('pointerdown', function (event) {
      event.stopPropagation();
      miniJump(event);
      miniBox.setPointerCapture(event.pointerId);
    });
    miniBox.addEventListener('pointermove', function (event) {
      if (miniBox.hasPointerCapture && miniBox.hasPointerCapture(event.pointerId)) miniJump(event);
    });
  }

  /* 帧循环：阻尼跟随 + 惯性（拖动 14 / 松手 7 / 缩放 6） */
  var last = performance.now();
  function frame(now) {
    var dt = Math.min((now - last) / 1000, 0.05);
    last = now;
    if (wrap) {
      /* 惯性：只有新鲜且够快的甩动才滑行；衰减更狠、阈值更高，避免"飘" */
      if (!drag && (Math.abs(vel.x) > 45 || Math.abs(vel.y) > 45)) {
        want.tx += vel.x * dt;
        want.ty += vel.y * dt;
        clampPan();
        var decay = Math.exp(-5 * dt);
        vel.x *= decay; vel.y *= decay;
      } else if (!drag) {
        vel.x = 0; vel.y = 0;
      }
      var rate = drag ? 40 : 14;
      var prevS = st.s, prevX = st.tx, prevY = st.ty;
      st.s = damp(st.s, want.s, 6, dt);
      st.tx = damp(st.tx, want.tx, rate, dt);
      st.ty = damp(st.ty, want.ty, rate, dt);
      if (Math.abs(st.s - prevS) > 1e-5 || Math.abs(st.tx - prevX) > 0.05 || Math.abs(st.ty - prevY) > 0.05) {
        apply();
      }
    }
    window.requestAnimationFrame(frame);
  }
  window.requestAnimationFrame(frame);

  window.addEventListener('resize', function () {
    clampPan();
    apply();
  });

  /* ---------------------------------------------------- 启动 */
  var start = indexOfPage((location.hash || '').slice(1));
  current = start < 0 ? 0 : start;
  pages[current].classList.add('is-active');
  if (pages[current].id === 'p-map') { mapSetIn(true); mapFramed = true; }
  fillEl.style.setProperty('--p', ((current + 1) / pages.length).toFixed(3));
  nowEl.textContent = pad(current + 1);
  prevBtn.disabled = current === 0;
  nextBtn.disabled = current === pages.length - 1;
  Array.prototype.forEach.call(dotsBox.children, function (dot, i) {
    dot.classList.toggle('is-current', i === current);
  });
  navBtns.forEach(function (btn) {
    btn.classList.toggle('is-current', btn.dataset.goto === pages[current].id);
  });
  focusMap();

  /* 首屏深链：#c3 这类知识卡锚点 → 切到它所在的板块并展开卡片
     （页锚点 #p-xxx 已由上面的启动块处理；这里只补卡片） */
  function bootHash() {
    var id = '';
    try { id = (window.location.hash || '').replace(/^#/, ''); } catch (err) { return; }
    if (!id) { return; }
    var card = document.getElementById(id);
    if (card && card.closest && card.closest('.page')) { openCard(id); }
  }
  bootHash();
})();
