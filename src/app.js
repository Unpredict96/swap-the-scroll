import { loadState, saveState, storageAvailable } from './storage.js';

let state = loadState();
let allCards = [];
let trackEl, startEl, feedEl, loadingEl;

/* ---------- dates ---------- */

function todayStr(d = new Date()) {
  return d.getFullYear() + '-' +
    String(d.getMonth() + 1).padStart(2, '0') + '-' +
    String(d.getDate()).padStart(2, '0');
}

function isYesterday(dateStr) {
  if (!dateStr) return false;
  const y = new Date();
  y.setDate(y.getDate() - 1);
  return dateStr === todayStr(y);
}

function ensureDayFresh() {
  const t = todayStr();
  if (state.todayDate !== t) {
    state.todayDate = t;
    state.todayCount = 0;
    saveState(state);
  }
}

function registerActivity() {
  const t = todayStr();
  if (state.lastActiveDate !== t) {
    state.streak = isYesterday(state.lastActiveDate) ? (state.streak || 0) + 1 : 1;
    state.lastActiveDate = t;
    if (state.streak > (state.longestStreak || 0)) state.longestStreak = state.streak;
  }
  state.todayCount = (state.todayCount || 0) + 1;
  saveState(state);
  paintStreak();
}

function paintStreak() {
  document.querySelectorAll('.streak-num').forEach(el => {
    el.textContent = state.streak || 0;
  });
}

/* ---------- deck ---------- */

function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function isExpired(card) {
  if (card.kind !== 'signal' || !card.added) return false;
  const maxDays = card.source && /FT|Reuters|Bloomberg/i.test(card.source) ? 7 : 30;
  const added = new Date(card.added);
  const ageDays = (Date.now() - added.getTime()) / 86400000;
  return ageDays > maxDays;
}

function poolForMode(mode) {
  const live = allCards.filter(c => !isExpired(c));
  if (mode === 'macro') return live.filter(c => c.group === 'macro');
  if (mode === 'general') return live.filter(c => c.group === 'general');
  return live.slice();
}

/* Prefer cards never seen before, then fall back to review. */
function prioritise(pool) {
  const seen = new Set(state.viewedIds);
  const fresh = shuffle(pool.filter(c => !seen.has(c.id)));
  const review = shuffle(pool.filter(c => seen.has(c.id)));
  return fresh.concat(review);
}

/* ---------- rendering ---------- */

function cardClass(c) {
  if (c.kind === 'signal') return 'signal';
  if (c.kind === 'quiz') return c.group === 'macro' ? 'quiz-macro' : 'quiz-general';
  return c.group;
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, ch => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[ch]));
}

function attributionHtml(c) {
  if (!c.source) return '';
  const unverified = c.confidence === 'unverified';
  const label = unverified
    ? `${escapeHtml(c.source)} — verify before citing`
    : escapeHtml(c.source);
  const inner = c.sourceUrl
    ? `<a href="${escapeHtml(c.sourceUrl)}" target="_blank" rel="noopener noreferrer">${label}</a>`
    : label;
  return `<p class="card-source${unverified ? ' unverified' : ''}">${inner}</p>`;
}

function hintFor(c) {
  if (c.kind === 'quiz') return 'Tap to reveal the answer';
  if (c.kind === 'signal') return 'Tap for context';
  return 'Tap for why it matters';
}

function renderCard(c, posLabel) {
  const div = document.createElement('div');
  div.className = 'card ' + cardClass(c);
  div.dataset.id = c.id;
  div.innerHTML = `
    <span class="card-index">${escapeHtml(posLabel)}</span>
    <p class="card-tag">${escapeHtml(c.tag || '')}</p>
    <p class="card-hook">${escapeHtml(c.hook)}</p>
    <div class="card-detail">
      <p>${escapeHtml(c.detail)}</p>
      ${attributionHtml(c)}
    </div>
    <p class="card-hint"><span class="hint-pulse"></span>${hintFor(c)}</p>
    <div class="card-actions">
      <button class="action-btn save-btn ${state.savedIds.includes(c.id) ? 'saved' : ''}"
              aria-label="Save this card" aria-pressed="${state.savedIds.includes(c.id)}">
        <span class="action-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M6 3h12a1 1 0 0 1 1 1v16l-7-4-7 4V4a1 1 0 0 1 1-1z"/></svg>
        </span>
        <span class="action-label">Save</span>
      </button>
    </div>
  `;

  div.addEventListener('click', e => {
    if (e.target.closest('.save-btn') || e.target.closest('a')) return;
    const wasRevealed = div.classList.contains('revealed');
    div.classList.toggle('revealed');
    if (!wasRevealed) {
      if (!state.viewedIds.includes(c.id)) state.viewedIds.push(c.id);
      registerActivity();
    }
  });

  div.querySelector('.save-btn').addEventListener('click', e => {
    e.stopPropagation();
    const btn = e.currentTarget;
    const idx = state.savedIds.indexOf(c.id);
    if (idx > -1) {
      state.savedIds.splice(idx, 1);
      btn.classList.remove('saved');
      btn.setAttribute('aria-pressed', 'false');
    } else {
      state.savedIds.push(c.id);
      btn.classList.add('saved');
      btn.setAttribute('aria-pressed', 'true');
    }
    document.getElementById('saved-total').textContent = state.savedIds.length;
    saveState(state);
  });

  return div;
}

function renderEndCard(leftover) {
  const div = document.createElement('div');
  div.className = 'card end-card';
  const done = state.todayCount || 0;
  div.innerHTML = `
    <svg class="end-flame" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2c1 3-2 4-2 7a4 4 0 0 0 8 0c0-1-.5-2-1-2 1 4-1 5-2 5a2.5 2.5 0 0 1-2.5-2.5c0-2 1.5-3 1.5-5C14 3 12 2 12 2zM7 14a5 5 0 0 0 10 0c0-1.5-.7-2.6-1.3-3.4.2 2-1 3.2-2.2 3.9A4 4 0 0 1 12 16a4 4 0 0 1-4-4c0-.9.3-1.6.7-2.2C7.7 10.6 7 12.1 7 14z"/></svg>
    <p class="end-streak-num streak-num">${state.streak || 0}</p>
    <p class="end-streak-label">day streak</p>
    <p class="end-title">That's your set for today</p>
    <p class="end-sub">${done} card${done === 1 ? '' : 's'} today. Streaks reward turning up, not long sessions — come back tomorrow.</p>
    ${leftover.length ? '<button class="end-btn" id="keep-browsing-btn">Keep browsing anyway</button>' : ''}
  `;
  const btn = div.querySelector('#keep-browsing-btn');
  if (btn) {
    btn.addEventListener('click', () => {
      btn.remove();
      prioritise(leftover).forEach(card => {
        trackEl.appendChild(renderCard(card, 'bonus'));
      });
      observeCards();
    });
  }
  return div;
}

function renderDeck(mode) {
  ensureDayFresh();
  trackEl.innerHTML = '';
  const pool = prioritise(poolForMode(mode));
  const cap = state.dailyCap || 10;
  const remaining = Math.max(cap - (state.todayCount || 0), 0);
  const todays = pool.slice(0, remaining);
  const leftover = pool.slice(remaining);

  todays.forEach((c, i) => {
    trackEl.appendChild(renderCard(c, `${i + 1} / ${todays.length}`));
  });
  trackEl.appendChild(renderEndCard(leftover));

  document.getElementById('saved-total').textContent = state.savedIds.length;
  paintStreak();
  observeCards();
}

function observeCards() {
  const cards = Array.from(trackEl.children);
  const progress = document.getElementById('progress-text');
  const obs = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting && entry.intersectionRatio > 0.6) {
        const idx = cards.indexOf(entry.target);
        progress.textContent = `${idx + 1} / ${cards.length}`;
      }
    });
  }, { root: trackEl, threshold: [0.6] });
  cards.forEach(c => obs.observe(c));
}

/* ---------- screens ---------- */

function showScreen(el) {
  [loadingEl, startEl, feedEl].forEach(s => s.classList.add('hidden'));
  el.classList.remove('hidden');
}

/* ---------- init ---------- */

async function loadCards() {
  const res = await fetch('./data/cards.json');
  if (!res.ok) throw new Error('Could not load cards.json');
  const json = await res.json();
  return Array.isArray(json) ? json : json.cards;
}

async function init() {
  loadingEl = document.getElementById('loading');
  startEl = document.getElementById('start');
  feedEl = document.getElementById('feed-screen');
  trackEl = document.getElementById('track');

  try {
    allCards = await loadCards();
  } catch (e) {
    loadingEl.textContent = 'Could not load the card deck. Check data/cards.json.';
    console.error(e);
    return;
  }

  ensureDayFresh();
  paintStreak();

  const streakText = document.getElementById('streak-text');
  if (state.streak > 0) {
    streakText.innerHTML = `<strong class="streak-num">${state.streak}</strong> day streak — keep it going`;
  } else if (state.viewedIds.length) {
    streakText.textContent = 'Streak paused — jump back in to restart it';
  } else {
    streakText.textContent = 'Start your streak today';
  }
  paintStreak();

  if (!storageAvailable) {
    const warn = document.createElement('p');
    warn.className = 'storage-warning';
    warn.textContent = 'Your browser is blocking local storage, so your streak will not be saved between visits.';
    startEl.querySelector('.start-top').appendChild(warn);
  }

  document.querySelectorAll('.mode-row').forEach(btn => {
    btn.addEventListener('click', () => {
      state.lastMode = btn.dataset.mode;
      saveState(state);
      trackEl.scrollTop = 0;
      renderDeck(btn.dataset.mode);
      showScreen(feedEl);
    });
  });

  document.getElementById('back-btn').addEventListener('click', () => showScreen(startEl));

  showScreen(startEl);
}

init();

if ('serviceWorker' in navigator && location.protocol !== 'file:') {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js').catch(err => {
      console.warn('Service worker not registered', err);
    });
  });
}
