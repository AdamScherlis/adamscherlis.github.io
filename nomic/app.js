// Constitutional Promptocracy — frontend.
// Served from GitHub Pages (finds the game server via backend.json) or
// directly by the game server (same origin).
(() => {
'use strict';

const params = new URLSearchParams(location.search);
const PROJECTOR = params.get('view') === 'projector';
const NARROW = window.matchMedia('(max-width: 1000px)');
const $ = (id) => document.getElementById(id);
const el = (tag, cls, text) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
};
const store = {
  get(k) { try { return localStorage.getItem(k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch {} },
  del(k) { try { localStorage.removeItem(k); } catch {} },
};
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const isVP = (item) => /^\s*victory\s*points?\s*$/i.test(item);

let API = null;
let token = store.get('nomic_token');
let S = null;           // public game state
let me = null;          // my player view, if logged in
let rootInfo = null;    // extra info for root
let version = -1;
let lastLogId = -1;
let gameId = null;
let clockOffset = 0;    // server clock minus client clock, seconds
let pollAbort = null;
let immediate = true;
let prevRules = null;
let settingsFilled = false;
let lastClaudeKey = null;

// ---------------------------------------------------------------- API

async function resolveApi() {
  const override = params.get('api');
  if (override) return override.replace(/\/+$/, '');
  try {
    const r = await fetch('backend.json?t=' + Date.now(), { cache: 'no-store' });
    if (r.ok) {
      const j = await r.json();
      if (j.api) return j.api.replace(/\/+$/, '');
    }
  } catch {}
  return location.origin;
}

async function api(path, { method = 'GET', body, signal } = {}) {
  const headers = {};
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = 'Bearer ' + token;
  const r = await fetch(API + path, {
    method, headers, signal,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await r.text();   // let an abort propagate rather than look like bad JSON
  let j = null;
  try { j = JSON.parse(text); } catch {}
  if (!r.ok) throw new Error((j && j.error) || `Server error (${r.status})`);
  if (j === null) throw new Error('Unexpected response from the game server');
  return j;
}

function kick() {  // fetch fresh state now instead of waiting for the long poll
  immediate = true;
  if (pollAbort) pollAbort.abort();
}

async function pollLoop() {
  let failures = 0;
  for (;;) {
    pollAbort = new AbortController();
    const timer = setTimeout(() => pollAbort.abort(), 40000);
    const wait = immediate ? 0 : 1;
    immediate = false;
    try {
      const j = await api(`/api/state?v=${version}&log_after=${lastLogId}&wait=${wait}`,
                          { signal: pollAbort.signal });
      failures = 0;
      setBanner(null);
      applyState(j);
    } catch (e) {
      if (e.name === 'AbortError' && immediate) continue;   // kicked
      console.warn('poll failed:', e);
      failures++;
      if (failures >= 2) setBanner('Can’t reach the game server. Retrying…');
      await sleep(Math.min(1000 * 2 ** failures, 15000));
      if (failures % 3 === 0) API = await resolveApi();     // the tunnel URL may have changed
      immediate = true;
    } finally {
      clearTimeout(timer);
    }
  }
}

function setBanner(text) {
  const b = $('banner');
  b.hidden = !text;
  b.textContent = text || '';
}

function applyState(j) {
  const s = j.state;
  clockOffset = s.now - Date.now() / 1000;
  if (gameId !== null && gameId !== s.game_id && !j.log_reset) {
    // The game was reset: start over with a full fetch.
    gameId = s.game_id;
    lastLogId = -1; version = -1; immediate = true; prevRules = null;
    $('log').replaceChildren();
    return;
  }
  gameId = s.game_id;
  S = s;
  version = s.version;
  me = j.me || null;
  rootInfo = j.root || null;
  if (token && !me) { token = null; store.del('nomic_token'); }
  if (j.log_reset) {
    $('log').replaceChildren();
    $('log-older').hidden = j.log.length < 300;
  }
  appendLog(j.log);
  render();
}

// ---------------------------------------------------------------- rendering

function render() {
  renderAccount();
  renderPlay();
  renderPlayers();
  renderRules();
  renderClaude();
  renderRoot();
  tick();
}

function fmtClock(sec) {
  sec = Math.max(0, Math.ceil(sec));
  const d = Math.floor(sec / 86400), h = Math.floor(sec % 86400 / 3600);
  const m = Math.floor(sec % 3600 / 60), s = sec % 60;
  const pad = (n) => String(n).padStart(2, '0');
  if (d) return `${d}d ${h}h ${pad(m)}m`;
  if (h) return `${h}:${pad(m)}:${pad(s)}`;
  return `${m}:${pad(s)}`;
}

function tick() {
  if (!S) return;
  const phase = $('phase'), name = $('phase-name'), timer = $('phase-timer');
  phase.classList.toggle('claude', S.phase === 'claude');
  $('phase-round').textContent = S.round ? `Round ${S.round}` : '';
  timer.classList.remove('urgent');
  name.classList.remove('dots');
  if (S.status === 'lobby') {
    name.textContent = 'Waiting for the game to start';
    timer.textContent = '';
  } else if (S.phase === 'claude') {
    name.textContent = 'Claude Phase — Claude is deliberating';
    name.classList.add('dots');
    timer.textContent = '';
  } else if (S.paused) {
    name.textContent = 'Paused';
    timer.textContent = S.paused_remaining != null ? fmtClock(S.paused_remaining) + ' left' : '';
  } else {
    const left = S.phase_ends_at - (Date.now() / 1000 + clockOffset);
    name.textContent = 'Player Phase';
    timer.textContent = fmtClock(left);
    timer.classList.toggle('urgent', left < 10);
    if (left <= 0) {
      if (S.round_action_count === 0 && S.settings.skip_idle) {
        name.textContent = 'Player Phase — waiting for someone to act';
      } else {
        name.textContent = 'Player Phase ending';
        name.classList.add('dots');
      }
      timer.textContent = '';
    }
  }
}

function renderAccount() {
  const box = $('account');
  box.replaceChildren();
  if (me) {
    box.append(el('span', null, me.name));
    const out = el('button', 'link', 'Log out');
    out.onclick = async () => {
      try { await api('/api/logout', { method: 'POST', body: {} }); } catch {}
      token = null; me = null; store.del('nomic_token');
      kick(); render();
    };
    box.append(out);
  } else {
    const b = el('button', 'link', 'Sign up / Log in');
    b.onclick = () => { showTab('play'); $('auth-name').focus(); };
    box.append(b);
  }
}

function actionAvailable(a) {
  return a.players == null || a.players.some((n) => n.toLowerCase() === me.name.toLowerCase());
}

function renderPlay() {
  $('auth').hidden = !!me;
  $('you').hidden = !me;
  if (!me) return;
  const max = S.settings.max_actions_per_round;
  const canAct = S.status === 'running' && S.phase === 'player' && !S.paused;
  const outOfActions = me.total_used >= max;
  $('actions-used').textContent = S.status === 'running' ? `${me.total_used}/${max} used this round` : '';

  const box = $('actions');
  const mine = S.actions.filter(actionAvailable);
  const existing = new Map([...box.children].map((n) => [n.dataset.name, n]));
  const keep = new Set(mine.map((a) => a.name));
  for (const [name, node] of existing) if (!keep.has(name)) node.remove();
  mine.forEach((a, i) => {
    let node = existing.get(a.name);
    if (!node) node = makeActionNode(a.name);
    if (box.children[i] !== node) box.insertBefore(node, box.children[i] || null);
    node.querySelector('.desc').textContent = a.description || '';
    node.querySelector('.desc').hidden = !a.description;
    const used = me.actions_used[a.name] || 0;
    const bits = [];
    if (a.per_round_limit != null) bits.push(`${used}/${a.per_round_limit} this round`);
    if (a.players != null) bits.push('only for ' + a.players.join(', '));
    node.querySelector('.meta').textContent = bits.join(' · ');
    const limited = a.per_round_limit != null && used >= a.per_round_limit;
    node.querySelector('button').disabled = !canAct || outOfActions || limited;
    node.querySelector('textarea').maxLength = S.settings.max_text_len;
  });
  if (!mine.length) box.replaceChildren(el('p', 'muted', 'No Actions are available to you right now.'));
  else box.querySelector(':scope > p')?.remove();

  const inv = $('my-inventory');
  const mineP = S.players.find((p) => p.id === me.id);
  fillItems(inv, mineP ? mineP.inventory : []);
}

function makeActionNode(name) {
  const node = el('div', 'action');
  node.dataset.name = name;
  const form = el('form');
  const ta = el('textarea');
  ta.rows = 2;
  ta.placeholder = name === 'Propose Rule' ? 'Your proposed rule…' : 'Details…';
  const btn = el('button', 'primary', name);
  btn.type = 'submit';
  form.append(ta, btn);
  const err = el('p', 'error');
  node.append(el('p', 'desc'), form, el('div', 'meta'), err);
  ta.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); form.requestSubmit(); }
  });
  form.onsubmit = async (e) => {
    e.preventDefault();
    if (btn.disabled) return;
    btn.disabled = true;
    err.textContent = '';
    try {
      await api('/api/act', { method: 'POST', body: { action: node.dataset.name, text: ta.value } });
      ta.value = '';
      kick();
    } catch (ex) {
      err.textContent = ex.message;
      btn.disabled = false;
    }
  };
  return node;
}

// Claude sometimes writes **bold**; render just that, safely.
function richText(text) {
  const frag = document.createDocumentFragment();
  text.split(/\*\*(.+?)\*\*/gs).forEach((part, i) => {
    frag.append(i % 2 ? el('strong', null, part) : document.createTextNode(part));
  });
  return frag;
}

function fillItems(ul, inventory) {
  ul.replaceChildren();
  const sorted = [...inventory].sort((a, b) => isVP(b.item) - isVP(a.item));
  for (const it of sorted) {
    const li = el('li', isVP(it.item) ? 'vp' : null, `${it.qty} × ${it.item}`);
    ul.append(li);
  }
}

function renderPlayers() {
  const ol = $('players');
  ol.replaceChildren();
  const players = [...S.players].sort((a, b) => b.vp - a.vp || a.name.localeCompare(b.name));
  let rank = 0, prevVp = null;
  players.forEach((p, i) => {
    if (p.vp !== prevVp) { rank = i + 1; prevVp = p.vp; }
    const li = el('li', me && me.id === p.id ? 'me' : null);
    li.append(el('span', 'rank', rank + '.'));
    const name = el('span', 'name', p.name);
    if (p.is_root) name.append(el('span', 'tag', 'root'));
    li.append(name);
    const vp = el('span', 'vpcount', String(p.vp));
    vp.append(el('small', null, ' VP'));
    li.append(vp);
    const items = el('ul', 'items');
    fillItems(items, p.inventory.filter((it) => !isVP(it.item)));
    li.append(items);
    ol.append(li);
  });
  if (!players.length) ol.append(el('li', 'muted', 'No players yet.'));
}

function renderRules() {
  const key = JSON.stringify(S.rules);
  const ol = $('rules');
  if (ol.dataset.key === key) return;
  ol.dataset.key = key;
  const before = prevRules;
  prevRules = new Map(S.rules.map((r) => [r.num, r.text]));
  ol.replaceChildren();
  for (const r of S.rules) {
    const li = el('li');
    li.id = 'rule-' + r.num;
    li.append(el('span', 'num', `Rule ${r.num}.`), el('span', 'text', r.text));
    const meta = [];
    if (r.proposer) meta.push(`proposed by ${r.proposer}`);
    if (r.round) meta.push(`adopted round ${r.round}`);
    if (r.amended_round) meta.push(`amended round ${r.amended_round}`);
    if (meta.length) li.append(el('div', 'meta', meta.join(' · ')));
    if (before && before.get(r.num) !== r.text) li.classList.add('flash');
    ol.append(li);
  }
  if (!S.rules.length) ol.append(el('li', 'muted', 'The Constitution is empty. Anarchy reigns.'));
}

function renderClaude() {
  const t = S.claude;
  const panel = $('panel-claude');
  panel.hidden = !t;
  if (!t) return;
  const running = t.status === 'running';
  const status = { done: '', running: '', aborted: ' (cut short)', timeout: ' (timed out)',
                   error: ' (failed)', interrupted: ' (interrupted)' }[t.status] || '';
  $('claude-title').textContent = running
    ? `Claude is deliberating on Round ${t.round}…`
    : `Claude’s notes on Round ${t.round}${status}`;
  const details = $('claude-details');
  const key = `${t.round}:${t.status}`;
  if (key !== lastClaudeKey) {
    if (running || PROJECTOR) details.open = true;
    lastClaudeKey = key;
  }
  const box = $('claude-notes');
  box.replaceChildren();
  for (const n of t.notes) {
    if (n.type === 'tool') { box.append(el('span', 'n-tool', '→ ' + n.text)); continue; }
    if (!n.text.trim()) continue;
    const div = el('div', 'n-' + n.type);
    div.append(richText(n.text.trim()));
    box.append(div);
  }
  if (t.error) box.append(el('div', 'n-error', t.error));
  if (!box.children.length) box.append(el('div', 'n-thinking', running ? 'Thinking…' : 'No notes.'));
  if (running) panel.scrollTop = panel.scrollHeight;
}

function renderRoot() {
  const isRoot = !!(me && me.is_root);
  $('root').hidden = !isRoot;
  if (!isRoot) return;
  const running = S.status === 'running';
  const show = {
    start: S.status === 'lobby',
    pause: running && !S.paused,
    resume: running && S.paused,
    end_phase: running && S.phase === 'player' && !S.paused,
    abort_claude: S.phase === 'claude',
  };
  for (const b of document.querySelectorAll('[data-root]')) b.hidden = !show[b.dataset.root];

  const form = $('settings-form');
  if (!settingsFilled && rootInfo) {
    fillSelect(form.model, rootInfo.models, S.settings.model);
    fillSelect(form.effort, rootInfo.efforts, S.settings.effort);
    form.player_phase_seconds.value = S.player_phase_seconds;
    for (const k of ['max_actions_per_round', 'max_text_len', 'claude_timeout_s', 'log_context_entries']) {
      form[k].value = S.settings[k];
    }
    form.skip_idle.checked = S.settings.skip_idle;
    settingsFilled = true;
  }
  if (rootInfo) {
    const u = rootInfo.usage;
    const inTok = u.input_tokens || 0, out = u.output_tokens || 0;
    const cr = u.cache_read_input_tokens || 0, cw = u.cache_creation_input_tokens || 0;
    const cost = (inTok * 4 + cw * 5 + cr * 0.2 + out * 20) / 1e6;
    $('root-usage').textContent =
      `Claude usage so far: ${u.api_calls || 0} API calls, ${(inTok + cr + cw).toLocaleString()} input ` +
      `tokens (${cr.toLocaleString()} cached), ${out.toLocaleString()} output tokens ` +
      `≈ $${cost.toFixed(2)} at Opus 5.5 prices.`;
  }
}

function fillSelect(sel, options, value) {
  sel.replaceChildren(...options.map((o) => { const op = el('option', null, o); op.value = o; return op; }));
  sel.value = value;
}

// ---------------------------------------------------------------- log

function scroller() {
  return NARROW.matches ? document.scrollingElement : $('panel-log');
}
function logVisible() {
  return !NARROW.matches || $('panel-log').classList.contains('shown');
}
function nearBottom() {
  const s = scroller();
  return s.scrollHeight - s.scrollTop - s.clientHeight < 120;
}
function scrollLogToBottom() {
  const s = scroller();
  s.scrollTop = s.scrollHeight;
  $('log-jump').hidden = true;
}

function fmtTime(ts) {
  return new Date(ts * 1000).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
}

function logItem(e) {
  const li = el('li', 'k-' + e.kind);
  li.dataset.id = e.id;
  const t = el('time', null, fmtTime(e.ts));
  t.title = new Date(e.ts * 1000).toLocaleString();
  li.append(t);
  const prefix = `${e.actor} did ${e.action}`;
  if (e.kind === 'action' && e.text.startsWith(prefix)) {
    const rest = e.text.slice(prefix.length).replace(/^: /, '').replace(/^\.$/, '');
    li.append(el('span', 'who', e.actor), el('span', 'act', e.action));
    if (rest) li.append(document.createTextNode(rest));
  } else if (e.kind === 'claude') {
    li.append(el('span', 'who', 'Claude: '), richText(e.text));
  } else {
    li.append(document.createTextNode(e.text));
  }
  return li;
}

function appendLog(entries) {
  if (!entries.length) return;
  const wasNear = nearBottom() || lastLogId < 0;
  const ol = $('log');
  for (const e of entries) {
    if (e.id <= lastLogId) continue;
    ol.append(logItem(e));
    lastLogId = e.id;
  }
  if (!logVisible()) return;
  if (wasNear) scrollLogToBottom();
  else $('log-jump').hidden = false;
}

async function loadOlder() {
  const first = $('log').firstElementChild;
  if (!first) return;
  const s = scroller();
  const h = s.scrollHeight;
  try {
    const j = await api(`/api/log?before=${first.dataset.id}&limit=200`);
    const frag = document.createDocumentFragment();
    for (const e of j.log) frag.append(logItem(e));
    $('log').prepend(frag);
    s.scrollTop += s.scrollHeight - h;
    $('log-older').hidden = j.log.length < 200;
  } catch {}
}

// ---------------------------------------------------------------- tabs

function showTab(name) {
  for (const b of document.querySelectorAll('#tabs button')) b.classList.toggle('active', b.dataset.tab === name);
  for (const p of document.querySelectorAll('[data-panel]')) p.classList.toggle('shown', p.dataset.panel === name);
  store.set('nomic_tab', name);
  if (name === 'log') scrollLogToBottom();
}

// ---------------------------------------------------------------- wiring

function wire() {
  for (const b of document.querySelectorAll('#tabs button')) b.onclick = () => showTab(b.dataset.tab);
  showTab(store.get('nomic_tab') || 'play');
  document.documentElement.style.setProperty('--sticky-top', $('top').offsetHeight + 'px');

  $('log-older').onclick = loadOlder;
  $('log-jump').onclick = scrollLogToBottom;
  scroller().addEventListener('scroll', () => { if (nearBottom()) $('log-jump').hidden = true; });

  $('auth-form').onsubmit = async (e) => {
    e.preventDefault();
    const mode = (e.submitter && e.submitter.dataset.mode) || 'login';
    $('auth-error').textContent = '';
    try {
      const j = await api('/api/' + mode, {
        method: 'POST', body: { name: $('auth-name').value, password: $('auth-pw').value },
      });
      token = j.token;
      store.set('nomic_token', token);
      me = j.me;
      $('auth-pw').value = '';
      kick();
      if (S) render();
    } catch (ex) {
      $('auth-error').textContent = ex.message;
    }
  };

  for (const b of document.querySelectorAll('[data-root]')) {
    b.onclick = () => rootCmd(b.dataset.root, {});
  }
  $('announce-form').onsubmit = async (e) => {
    e.preventDefault();
    if (await rootCmd('announce', { text: $('announce-text').value })) $('announce-text').value = '';
  };
  $('settings-form').onsubmit = async (e) => {
    e.preventDefault();
    const f = e.target;
    const body = { model: f.model.value, effort: f.effort.value, skip_idle: f.skip_idle.checked };
    for (const k of ['player_phase_seconds', 'max_actions_per_round', 'max_text_len',
                     'claude_timeout_s', 'log_context_entries']) body[k] = Number(f[k].value);
    if (await rootCmd('settings', body)) settingsFilled = false;
  };
  $('reset-btn').onclick = async () => {
    if (!confirm('Reset the game? The Constitution, Log, Actions and Inventories go back to the ' +
                 'start (a backup is kept on the server). Accounts are kept.')) return;
    await rootCmd('reset', { confirm: 'RESET' });
  };

  if (PROJECTOR) {
    document.body.classList.add('projector');
    showJoinQr();
  }
  setInterval(tick, 250);
}

async function rootCmd(cmd, body) {
  $('root-error').textContent = '';
  try {
    await api('/api/root/' + cmd, { method: 'POST', body });
    kick();
    return true;
  } catch (ex) {
    $('root-error').textContent = ex.message;
    return false;
  }
}

function showJoinQr() {
  const url = location.origin + location.pathname;
  $('join-url').textContent = url.replace(/^https?:\/\//, '').replace(/\/$/, '');
  $('join-qr').hidden = false;
  const s = document.createElement('script');
  s.src = 'https://cdnjs.cloudflare.com/ajax/libs/qrcodejs/1.0.0/qrcode.min.js';
  s.onload = () => {
    /* global QRCode */
    new QRCode($('qr'), { text: url, width: 180, height: 180, correctLevel: QRCode.CorrectLevel.M });
  };
  document.head.append(s);
}

async function main() {
  wire();
  API = await resolveApi();
  pollLoop();
}

main();
})();
