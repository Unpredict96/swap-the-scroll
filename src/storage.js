/*
 * storage.js — persistence layer
 *
 * The prototype ran inside Claude's sandbox and used window.storage, which
 * only exists there. This replaces it with localStorage so state lives on the
 * device and survives with no network and no Claude in the loop.
 *
 * Everything is namespaced under a single key so the whole state can be
 * exported, inspected or wiped in one go.
 */

const KEY = 'swap-the-scroll:v1';

const DEFAULT_STATE = {
  savedIds: [],
  viewedIds: [],
  lastMode: null,
  todayDate: null,
  todayCount: 0,
  lastActiveDate: null,
  streak: 0,
  longestStreak: 0,
  dailyCap: 10
};

function available() {
  try {
    const probe = '__probe__';
    window.localStorage.setItem(probe, '1');
    window.localStorage.removeItem(probe);
    return true;
  } catch (e) {
    return false;
  }
}

const HAS_STORAGE = available();
let memoryFallback = null;

export function loadState() {
  if (!HAS_STORAGE) {
    return memoryFallback ? { ...memoryFallback } : { ...DEFAULT_STATE };
  }
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return { ...DEFAULT_STATE };
    return { ...DEFAULT_STATE, ...JSON.parse(raw) };
  } catch (e) {
    console.warn('Could not read saved state, starting fresh', e);
    return { ...DEFAULT_STATE };
  }
}

export function saveState(state) {
  if (!HAS_STORAGE) {
    memoryFallback = { ...state };
    return false;
  }
  try {
    window.localStorage.setItem(KEY, JSON.stringify(state));
    return true;
  } catch (e) {
    console.warn('Could not save state', e);
    return false;
  }
}

export function clearState() {
  memoryFallback = null;
  if (HAS_STORAGE) window.localStorage.removeItem(KEY);
}

/* Export/import — so a phone and a laptop can be kept in sync by hand,
   and so a browser-data wipe isn't a total loss. */
export function exportState() {
  return JSON.stringify(loadState(), null, 2);
}

export function importState(json) {
  const parsed = JSON.parse(json);
  const merged = { ...DEFAULT_STATE, ...parsed };
  saveState(merged);
  return merged;
}

export const storageAvailable = HAS_STORAGE;
