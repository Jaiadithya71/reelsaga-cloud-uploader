/**
 * ReelSaga index private analytics endpoint.
 * Ingestion-only web app: accepts beacon events, writes to the private Sheet.
 * No read API, no stats exposure, no identity in the endpoint.
 * Bounds: salted+hashed visitor ids; 35-day hash retention; daily new-hash cap;
 * hard total/per-day event caps; per-hash rate bound and per-day event cap;
 * one 'view' per visitor per series per day; active-time clamped per ping and
 * per visitor per day. qa=1 is a client-supplied test label only (no trust):
 * QA hits are written to a separate QA sheet and never touch real aggregates.
 */
var SHEET_ID = '1mFJaysmS6J27HzlT3fGkZqwkAQ2Sb1cfeERIg7Wa7uY';
var TZ = 'Asia/Calcutta';
var SALT = 'rs-idx-2026-11-04';
var RETENTION_DAYS = 35;
var DAILY_HASH_CAP = 2000;        // max new visitor hashes stored per day
var EVENTS_HARD_CAP = 90000;      // fail closed above this total rows
var EVENTS_PER_DAY_CAP = 5000;    // stop accepting events for the day beyond this
var EVENTS_PER_HASH_DAY = 300;    // per-visitor per-day event cap
var RATE_MIN_MS = 1000;           // min gap between accepted events per visitor
var MAX_SECS_PER_PING = 60;       // clamp a single active-time ping
var MAX_SECS_PER_DAY = 3600;      // clamp active seconds per visitor per day

function sheet_(name, cols) {
  var ss = SpreadsheetApp.openById(SHEET_ID);
  var s = ss.getSheetByName(name);
  if (!s) { s = ss.insertSheet(name); s.appendRow(cols); }
  return s;
}
function dayOf_(d) { return Utilities.formatDate(d, TZ, 'yyyy-MM-dd'); }
function hash_(id) {
  var b = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, SALT + ':' + id);
  return b.map(function(x){ return ('0' + (x & 255).toString(16)).slice(-2); }).join('').slice(0, 24);
}

function doGet(e) {
  var p = (e && e.parameter) || {};
  var now = new Date();
  var day = dayOf_(now);
  var type = String(p.t || 'view').slice(0, 12);
  if (['view','time','tap'].indexOf(type) < 0) type = 'view';
  var series = String(p.s || '').slice(0, 24);
  var target = String(p.x || '').slice(0, 24);
  var secs = Math.max(0, Math.min(MAX_SECS_PER_PING, Math.floor(parseInt(p.ms || '0', 10) / 1000)));
  var src = String(p.src || '').slice(0, 12);
  var qa = p.qa === '1';
  var vid = String(p.v || '').slice(0, 40);
  var h = vid ? hash_(vid) : 'anon';
  var isNew = false, isReturning = false;

  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    if (qa) {
      // isolated: QA sheet only, never counted in real aggregates
      sheet_('QA', ['ts','type','series','target','secs','src','note'])
        .appendRow([now, type, series, target, secs, src, 'qa']);
      return ContentService.createTextOutput('ok');
    }

    var es = sheet_('Events', ['ts','day_ist','type','series','target','secs','src','hash','new','returning']);
    // hard caps
    var eLast = es.getLastRow();
    if (eLast >= EVENTS_HARD_CAP) return ContentService.createTextOutput('ok');
    var evals = eLast > 1 ? es.getRange(2, 1, eLast - 1, 10).getValues() : [];
    var todayRows = [];
    for (var i = evals.length - 1; i >= 0; i--) {
      if (dayOf_(new Date(evals[i][0])) === day) todayRows.push(evals[i]); else break;
    }
    if (todayRows.length >= EVENTS_PER_DAY_CAP) return ContentService.createTextOutput('ok');
    // per-hash bounds
    var hashToday = 0, lastTs = 0, secsToday = 0, viewDup = false;
    for (var j = 0; j < todayRows.length; j++) {
      var r = todayRows[j];
      if (r[7] === h) {
        hashToday++;
        var ts = new Date(r[0]).getTime();
        if (ts > lastTs) lastTs = ts;
        if (r[2] === 'time') secsToday += Number(r[5]) || 0;
        if (type === 'view' && r[2] === 'view' && r[3] === series) viewDup = true;
      }
    }
    if (hashToday >= EVENTS_PER_HASH_DAY) return ContentService.createTextOutput('ok');
    if (lastTs && now.getTime() - lastTs < RATE_MIN_MS) return ContentService.createTextOutput('ok');
    if (viewDup) return ContentService.createTextOutput('ok');
    if (type === 'time') {
      var room = MAX_SECS_PER_DAY - secsToday;
      if (room <= 0) return ContentService.createTextOutput('ok');
      if (secs > room) secs = room;
    }

    // visitor dedupe + bounded retention hash set
    var hs = sheet_('Hashes', ['day','hash']);
    var hLast = hs.getLastRow();
    var hvals = hLast > 1 ? hs.getRange(2, 1, hLast - 1, 2).getValues() : [];
    var seenToday = false, seenBefore = false, todayCount = 0;
    for (var k = hvals.length - 1; k >= 0; k--) {
      var rday = dayOf_(new Date(hvals[k][0]));
      if (hvals[k][1] === h) { if (rday === day) seenToday = true; else seenBefore = true; }
      if (rday === day) todayCount++;
    }
    if (!seenToday && todayCount < DAILY_HASH_CAP) {
      hs.appendRow([now, h]);
      isNew = !seenBefore; isReturning = seenBefore;
    } else if (seenToday) {
      isReturning = seenBefore;
    }
    // retention prune (hashes older than RETENTION_DAYS)
    var cutoff = new Date(now.getTime() - RETENTION_DAYS * 86400000);
    var del = 0;
    for (var m = 0; m < hvals.length; m++) { if (new Date(hvals[m][0]) < cutoff) del++; else break; }
    if (del > 0) hs.deleteRows(2, del);

    es.appendRow([now, day, type, series, target, secs, src, h, isNew, isReturning]);
  } finally {
    lock.releaseLock();
  }
  return ContentService.createTextOutput('ok');
}
