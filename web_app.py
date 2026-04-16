#!/usr/bin/env python3
import os, io, base64, sqlite3
from datetime import datetime, date, timedelta
from flask import Flask, request, jsonify, render_template_string
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

app = Flask(__name__, static_folder='.', static_url_path='')
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eksoda.db")

CAT_COLORS = {
    "Φαγητό Έξω": "#FF6B6B", "Ποτό": "#4ECDC4", "Delivery": "#FFE66D",
    "Σούπερ Μάρκετ": "#6BCB77", "Συνδρομές": "#4D96FF", "Ψώνια": "#C77DFF", "Διάφορα": "#F4A261",
}

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL, amount REAL NOT NULL,
            category TEXT NOT NULL, notes TEXT DEFAULT '')""")
        conn.execute("""CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, value TEXT NOT NULL)""")
        conn.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('budget', '1000')")
        conn.commit()

HTML = """
<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
<title>💸 Έξοδα</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root { --bg:#0F0F13; --surface:#1A1A22; --surface2:#22222E; --accent:#7C6EF5; --accent2:#F5976E; --text:#EEEEF5; --muted:#7B7B99; --border:#2E2E40; --radius:16px; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:var(--text); font-family:'DM Sans',sans-serif; min-height:100vh; padding-bottom:40px; }
  .header { background:linear-gradient(135deg,#1A1A2E 0%,#16213E 50%,#0F3460 100%); padding:28px 20px 24px; text-align:center; border-bottom:1px solid var(--border); position:relative; overflow:hidden; }
  .header::before { content:''; position:absolute; inset:0; background:radial-gradient(ellipse at 50% -20%,rgba(124,110,245,0.25) 0%,transparent 70%); }
  .header h1 { font-family:'Syne',sans-serif; font-size:26px; font-weight:800; position:relative; }
  .header h1 span { color:var(--accent); }
  .header p { color:var(--muted); font-size:13px; margin-top:4px; position:relative; }
  .tabs { display:flex; background:var(--surface); margin:20px 16px 0; border-radius:var(--radius); padding:4px; border:1px solid var(--border); }
  .tab { flex:1; padding:10px 8px; border:none; background:transparent; color:var(--muted); font-family:'DM Sans',sans-serif; font-size:13px; font-weight:500; border-radius:12px; cursor:pointer; transition:all 0.2s; }
  .tab.active { background:var(--accent); color:white; font-weight:600; box-shadow:0 2px 12px rgba(124,110,245,0.4); }
  .panel { display:none; padding:16px; }
  .panel.active { display:block; }
  .card { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:20px; margin-bottom:14px; }
  .card-title { font-family:'Syne',sans-serif; font-size:13px; font-weight:700; text-transform:uppercase; letter-spacing:1px; color:var(--muted); margin-bottom:14px; }
  .amount-input { width:100%; font-size:40px; font-family:'Syne',sans-serif; font-weight:800; background:transparent; border:none; color:var(--text); text-align:center; outline:none; padding:10px 0; caret-color:var(--accent); }
  .amount-input::placeholder { color:var(--border); }
  .amount-divider { height:2px; background:linear-gradient(90deg,transparent,var(--accent),transparent); margin:0 20px 16px; }
  .euro-hint { text-align:center; color:var(--muted); font-size:13px; margin-bottom:4px; }
  .cat-grid { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
  .cat-btn { padding:12px 8px; border:2px solid var(--border); border-radius:12px; background:var(--surface2); color:var(--text); font-family:'DM Sans',sans-serif; font-size:13px; font-weight:500; cursor:pointer; transition:all 0.18s; text-align:center; display:flex; flex-direction:column; align-items:center; gap:4px; }
  .cat-btn .emoji { font-size:20px; }
  .cat-btn.selected { border-color:var(--accent); background:rgba(124,110,245,0.15); color:white; }
  .cat-btn[data-cat="Φαγητό Έξω"].selected { border-color:#FF6B6B; background:rgba(255,107,107,0.15); }
  .cat-btn[data-cat="Ποτό"].selected { border-color:#4ECDC4; background:rgba(78,205,196,0.15); }
  .cat-btn[data-cat="Delivery"].selected { border-color:#FFE66D; background:rgba(255,230,109,0.15); }
  .cat-btn[data-cat="Σούπερ Μάρκετ"].selected { border-color:#6BCB77; background:rgba(107,203,119,0.15); }
  .cat-btn[data-cat="Συνδρομές"].selected { border-color:#4D96FF; background:rgba(77,150,255,0.15); }
  .cat-btn[data-cat="Ψώνια"].selected { border-color:#C77DFF; background:rgba(199,125,255,0.15); }
  .cat-btn[data-cat="Διάφορα"].selected { border-color:#F4A261; background:rgba(244,162,97,0.15); }
  .save-btn { width:100%; padding:16px; margin-top:14px; background:linear-gradient(135deg,var(--accent),#9B8BFF); border:none; border-radius:var(--radius); color:white; font-family:'Syne',sans-serif; font-size:16px; font-weight:700; cursor:pointer; transition:all 0.2s; box-shadow:0 4px 20px rgba(124,110,245,0.35); }
  .save-btn:hover { transform:translateY(-2px); }
  .save-btn:disabled { opacity:0.4; cursor:not-allowed; transform:none; }
  .toast { position:fixed; bottom:24px; left:50%; transform:translateX(-50%) translateY(80px); background:#1E2D1E; border:1px solid #4CAF50; color:#81C784; padding:12px 24px; border-radius:100px; font-size:14px; font-weight:500; transition:transform 0.3s; z-index:999; white-space:nowrap; }
  .toast.error { background:#2D1E1E; border-color:#F44336; color:#EF9A9A; }
  .toast.show { transform:translateX(-50%) translateY(0); }
  .period-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-bottom:14px; }
  .period-btn { padding:9px 4px; border:1px solid var(--border); border-radius:10px; background:var(--surface2); color:var(--muted); font-family:'DM Sans',sans-serif; font-size:12px; cursor:pointer; transition:all 0.18s; text-align:center; }
  .period-btn.active { border-color:var(--accent2); color:var(--accent2); background:rgba(245,151,110,0.1); }
  .custom-dates { display:none; gap:10px; margin-bottom:14px; }
  .custom-dates.show { display:flex; }
  .date-input { flex:1; padding:10px 12px; background:var(--surface2); border:1px solid var(--border); border-radius:10px; color:var(--text); font-family:'DM Sans',sans-serif; font-size:13px; }
  .date-input:focus { outline:none; border-color:var(--accent); }
  .analyze-btn { width:100%; padding:14px; background:linear-gradient(135deg,var(--accent2),#F5C76E); border:none; border-radius:var(--radius); color:#1A1008; font-family:'Syne',sans-serif; font-size:15px; font-weight:700; cursor:pointer; transition:all 0.2s; box-shadow:0 4px 20px rgba(245,151,110,0.3); }
  .analyze-btn:hover { transform:translateY(-2px); }
  .stats-grid { display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:14px; }
  .stat-card { background:var(--surface2); border:1px solid var(--border); border-radius:12px; padding:14px; text-align:center; }
  .stat-value { font-family:'Syne',sans-serif; font-size:22px; font-weight:800; color:var(--accent); }
  .stat-label { font-size:11px; color:var(--muted); margin-top:3px; }
  .chart-img { width:100%; border-radius:12px; margin-top:10px; }
  .cat-row { margin-bottom:12px; }
  .cat-row-header { display:flex; justify-content:space-between; margin-bottom:5px; }
  .cat-name { font-size:13px; font-weight:500; }
  .cat-amount { font-size:13px; font-weight:700; font-family:'Syne',sans-serif; }
  .bar-track { height:8px; background:var(--surface2); border-radius:100px; overflow:hidden; }
  .bar-fill { height:100%; border-radius:100px; transition:width 0.6s ease; }
  .expense-item { display:flex; align-items:center; gap:10px; padding:12px 0; border-bottom:1px solid var(--border); }
  .expense-item:last-child { border-bottom:none; }
  .exp-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
  .exp-info { flex:1; min-width:0; }
  .exp-cat { font-size:13px; font-weight:500; }
  .exp-date { font-size:11px; color:var(--muted); cursor:pointer; display:flex; align-items:center; gap:4px; }
  .exp-date:hover { color:var(--accent); }
  .exp-amount { font-family:'Syne',sans-serif; font-size:15px; font-weight:700; color:var(--accent2); flex-shrink:0; }
  .del-btn { background:none; border:none; color:var(--muted); font-size:18px; cursor:pointer; padding:4px 8px; border-radius:8px; transition:all 0.15s; flex-shrink:0; }
  .del-btn:hover { color:#FF6B6B; background:rgba(255,107,107,0.12); }
  .modal-overlay { display:none; position:fixed; inset:0; background:rgba(0,0,0,0.7); z-index:100; align-items:center; justify-content:center; padding:20px; }
  .modal-overlay.show { display:flex; }
  .modal { background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:24px; width:100%; max-width:340px; }
  .modal-title { font-family:'Syne',sans-serif; font-weight:700; font-size:16px; margin-bottom:16px; }
  .modal-input { width:100%; padding:12px; background:var(--surface2); border:1px solid var(--border); border-radius:10px; color:var(--text); font-family:'DM Sans',sans-serif; font-size:15px; margin-bottom:14px; }
  .modal-input:focus { outline:none; border-color:var(--accent); }
  .modal-btns { display:flex; gap:10px; }
  .modal-save { flex:1; padding:12px; background:var(--accent); border:none; border-radius:10px; color:white; font-family:'Syne',sans-serif; font-weight:700; cursor:pointer; }
  .modal-cancel { flex:1; padding:12px; background:var(--surface2); border:1px solid var(--border); border-radius:10px; color:var(--muted); font-family:'DM Sans',sans-serif; cursor:pointer; }
  .loader { text-align:center; padding:30px; color:var(--muted); font-size:14px; }
  .empty { text-align:center; padding:40px 20px; color:var(--muted); }
  .empty .empty-icon { font-size:40px; margin-bottom:10px; }
</style>
</head>
<body>

<div class="header">
  <h1>💸 <span>Έξοδα</span></h1>
  <p id="header-total">Φόρτωση...</p>
  <p id="header-remaining" style="font-size:15px;font-weight:700;margin-top:6px;"></p>
</div>

<div class="tabs">
  <button class="tab active" onclick="showTab('add', this)">➕ Καταχώρηση</button>
  <button class="tab" onclick="showTab('analyze', this)">📊 Ανάλυση</button>
  <button class="tab" onclick="showTab('history', this)">🕐 Ιστορικό</button>
</div>

<!-- ADD -->
<div id="tab-add" class="panel active">
  <div class="card">
    <div class="card-title">Ποσό</div>
    <div class="euro-hint">€</div>
    <input type="text" id="amount" class="amount-input" placeholder="0.00" inputmode="decimal">
    <div class="amount-divider"></div>
  </div>
  <div class="card">
    <div class="card-title">Κατηγορία</div>
    <div class="cat-grid">
      <button class="cat-btn" data-cat="Φαγητό Έξω" onclick="selectCat(this)"><span class="emoji">🍽️</span>Φαγητό Έξω</button>
      <button class="cat-btn" data-cat="Ποτό" onclick="selectCat(this)"><span class="emoji">🍻</span>Ποτό</button>
      <button class="cat-btn" data-cat="Delivery" onclick="selectCat(this)"><span class="emoji">🛵</span>Delivery</button>
      <button class="cat-btn" data-cat="Σούπερ Μάρκετ" onclick="selectCat(this)"><span class="emoji">🛒</span>Σούπερ Μάρκετ</button>
      <button class="cat-btn" data-cat="Συνδρομές" onclick="selectCat(this)"><span class="emoji">📱</span>Συνδρομές</button>
      <button class="cat-btn" data-cat="Ψώνια" onclick="selectCat(this)"><span class="emoji">🛍️</span>Ψώνια</button>
      <button class="cat-btn" data-cat="Διάφορα" onclick="selectCat(this)"><span class="emoji">🗂️</span>Διάφορα</button>
    </div>
  </div>
  <div id="notes-section" style="display:none" class="card">
    <div class="card-title">Σχόλιο</div>
    <input type="text" id="notes" placeholder="Προαιρετικό σχόλιο..." style="width:100%;padding:12px;background:var(--surface2);border:1px solid var(--border);border-radius:10px;color:var(--text);font-family:'DM Sans',sans-serif;font-size:14px;">
  </div>
  <button class="save-btn" onclick="saveExpense()">Αποθήκευση</button>
</div>

<!-- ANALYZE -->
<div id="tab-analyze" class="panel">
  <div class="card">
    <div class="card-title">Χρονικό Διάστημα</div>
    <div class="period-grid">
      <button class="period-btn active" data-period="month" onclick="setPeriod(this)">Μήνας</button>
      <button class="period-btn" data-period="30" onclick="setPeriod(this)">30 μέρες</button>
      <button class="period-btn" data-period="90" onclick="setPeriod(this)">90 μέρες</button>
      <button class="period-btn" data-period="year" onclick="setPeriod(this)">Έτος</button>
      <button class="period-btn" data-period="all" onclick="setPeriod(this)">Όλα</button>
      <button class="period-btn" data-period="custom" onclick="setPeriod(this)">Προσαρμ.</button>
    </div>
    <div class="custom-dates" id="custom-dates">
      <input type="date" id="date-from" class="date-input">
      <input type="date" id="date-to" class="date-input">
    </div>
    <button class="analyze-btn" onclick="analyze()">Ανάλυση →</button>
  </div>
  <div id="analyze-results"></div>
  <div class="card" style="margin-top:14px">
    <div class="card-title">💰 Μηνιαίο Budget</div>
    <div style="display:flex;gap:10px;align-items:center">
      <input type="number" id="budget-input" placeholder="π.χ. 500" style="flex:1;padding:12px;background:var(--surface2);border:1px solid var(--border);border-radius:10px;color:var(--text);font-family:'DM Sans',sans-serif;font-size:15px;" inputmode="decimal">
      <button onclick="saveBudget()" style="padding:12px 20px;background:var(--accent);border:none;border-radius:10px;color:white;font-family:'Syne',sans-serif;font-weight:700;cursor:pointer;">Αποθήκευση</button>
    </div>
    <p id="budget-msg" style="font-size:12px;color:var(--muted);margin-top:8px;"></p>
  </div>
</div>

<!-- HISTORY -->
<div id="tab-history" class="panel">
  <div class="card">
    <div class="card-title">Τελευταία Έξοδα</div>
    <div id="history-list"><div class="loader">Φόρτωση...</div></div>
  </div>
</div>

<!-- DATE MODAL -->
<div class="modal-overlay" id="date-modal">
  <div class="modal">
    <div class="modal-title">✏️ Αλλαγή Ημερομηνίας</div>
    <input type="datetime-local" id="modal-date-input" class="modal-input">
    <div class="modal-btns">
      <button class="modal-cancel" onclick="closeModal()">Άκυρο</button>
      <button class="modal-save" onclick="saveDate()">Αποθήκευση</button>
    </div>
  </div>
</div>

<!-- PHOTO OVERLAY -->
<div id="photo-overlay" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:200;align-items:center;justify-content:center;flex-direction:column;gap:16px;">
  <img id="popup-img" style="max-width:80%;max-height:70vh;border-radius:20px;box-shadow:0 0 40px rgba(78,205,196,0.5);">
  <div id="popup-text" style="color:white;font-family:'Syne',sans-serif;font-size:20px;font-weight:800;"></div>
</div>

<div class="toast" id="toast"></div>

<script>
let selectedCat = null;
let currentPeriod = "month";
let editingId = null;

const PHOTOS = {
  'Ποτό': ['/IMG_8312.jpg', '🍻 Cheersss!!!'],
  'Delivery': ['/IMG_8379.jpg', '🥐 Πάλι κρέπα;'],
  'Ψώνια': ['/IMG_4035.jpg', '🛍️ Slay Queen!'],
  'Φαγητό Έξω': ['/IMG_0721.jpg', '🍕 ΜΙΑΜ!'],
  'Διάφορα': ['/IMG_3049.jpg', '🤔 Τι πήραμε πάλι;'],
  'Συνδρομές': ['/IMG_0214.jpg', '📱 Πάλι συνδρομές...']
};

function showTab(tab, btn) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('tab-' + tab).classList.add('active');
  btn.classList.add('active');
  if (tab === 'history') loadHistory();
}

function selectCat(btn) {
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('selected'));
  btn.classList.add('selected');
  selectedCat = btn.dataset.cat;
  document.getElementById('notes-section').style.display = selectedCat === 'Διάφορα' ? 'block' : 'none';
}

function setPeriod(btn) {
  document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  currentPeriod = btn.dataset.period;
  document.getElementById('custom-dates').classList.toggle('show', currentPeriod === 'custom');
}

function showToast(msg, isError=false) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast' + (isError ? ' error' : '') + ' show';
  setTimeout(() => t.classList.remove('show'), 3000);
}

function showPhoto(cat) {
  if (!PHOTOS[cat]) return;
  const o = document.getElementById('photo-overlay');
  document.getElementById('popup-img').src = PHOTOS[cat][0];
  document.getElementById('popup-text').textContent = PHOTOS[cat][1];
  o.style.display = 'flex';
  setTimeout(() => { o.style.display = 'none'; }, 3000);
}

function openDateModal(id, currentDate) {
  editingId = id;
  const parts = currentDate.split(' ');
  const dateParts = parts[0].split('/');
  const formatted = `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}T${parts[1] || '00:00'}`;
  document.getElementById('modal-date-input').value = formatted;
  document.getElementById('date-modal').classList.add('show');
}

function closeModal() {
  document.getElementById('date-modal').classList.remove('show');
  editingId = null;
}

async function saveDate() {
  const val = document.getElementById('modal-date-input').value;
  if (!val) return;
  try {
    const res = await fetch('/update_date', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ id: editingId, date: val })
    });
    const data = await res.json();
    if (data.ok) { showToast('✅ Ημερομηνία ενημερώθηκε!'); closeModal(); loadHistory(); }
    else showToast('❌ Σφάλμα', true);
  } catch(e) { showToast('❌ Σφάλμα σύνδεσης', true); }
}

async function saveExpense() {
  const amount = parseFloat(document.getElementById('amount').value.replace(',', '.'));
  if (!amount || amount <= 0) { showToast('⚠️ Εισάγετε ποσό', true); return; }
  if (!selectedCat) { showToast('⚠️ Επιλέξτε κατηγορία', true); return; }
  const btn = document.querySelector('.save-btn');
  btn.disabled = true; btn.textContent = 'Αποθήκευση...';
  try {
    const res = await fetch('/add', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ amount, category: selectedCat, notes: document.getElementById('notes').value })
    });
    const data = await res.json();
    if (data.ok) {
      showToast('✅ Αποθηκεύτηκε!');
      showPhoto(selectedCat);
      document.getElementById('amount').value = '';
      document.getElementById('notes').value = '';
      document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('selected'));
      document.getElementById('notes-section').style.display = 'none';
      selectedCat = null;
      loadBudget();
    } else showToast('❌ Σφάλμα', true);
  } catch(e) { showToast('❌ Σφάλμα σύνδεσης', true); }
  btn.disabled = false; btn.textContent = 'Αποθήκευση';
}

async function analyze() {
  const res_div = document.getElementById('analyze-results');
  res_div.innerHTML = '<div class="loader">⏳ Υπολογισμός...</div>';
  const params = { period: currentPeriod };
  if (currentPeriod === 'custom') {
    params.from = document.getElementById('date-from').value;
    params.to = document.getElementById('date-to').value;
  }
  try {
    const res = await fetch('/analyze', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(params)
    });
    const data = await res.json();
    if (!data.ok) { res_div.innerHTML = '<div class="empty"><div class="empty-icon">😕</div>Δεν βρέθηκαν δεδομένα</div>'; return; }
    const catColors = {"Φαγητό Έξω":"#FF6B6B","Ποτό":"#4ECDC4","Delivery":"#FFE66D","Σούπερ Μάρκετ":"#6BCB77","Συνδρομές":"#4D96FF","Ψώνια":"#C77DFF","Διάφορα":"#F4A261"};
    let barsHtml = data.categories.map(c => `
      <div class="cat-row">
        <div class="cat-row-header">
          <span class="cat-name">${c.name}</span>
          <span class="cat-amount" style="color:${catColors[c.name]||'#fff'}">${c.amount.toFixed(2)}€</span>
        </div>
        <div class="bar-track"><div class="bar-fill" style="width:${c.pct}%;background:${catColors[c.name]||'#7C6EF5'}"></div></div>
      </div>`).join('');
    res_div.innerHTML = `
      <div class="stats-grid">
        <div class="stat-card"><div class="stat-value">${data.total.toFixed(2)}€</div><div class="stat-label">Σύνολο</div></div>
        <div class="stat-card"><div class="stat-value">${data.count}</div><div class="stat-label">Καταχωρήσεις</div></div>
      </div>
      <div class="card">${barsHtml}</div>
      <img class="chart-img" src="data:image/png;base64,${data.chart}" />`;
  } catch(e) { res_div.innerHTML = '<div class="empty"><div>❌ Σφάλμα</div></div>'; }
}

async function loadHistory() {
  try {
    const res = await fetch('/history');
    const data = await res.json();
    const catColors = {"Φαγητό Έξω":"#FF6B6B","Ποτό":"#4ECDC4","Delivery":"#FFE66D","Σούπερ Μάρκετ":"#6BCB77","Συνδρομές":"#4D96FF","Ψώνια":"#C77DFF","Διάφορα":"#F4A261"};
    if (!data.items || data.items.length === 0) {
      document.getElementById('history-list').innerHTML = '<div class="empty"><div class="empty-icon">📭</div>Δεν υπάρχουν εγγραφές</div>';
      return;
    }
    document.getElementById('history-list').innerHTML = data.items.map(e => `
      <div class="expense-item" id="row-${e.id}">
        <div class="exp-dot" style="background:${catColors[e.category]||'#7C6EF5'}"></div>
        <div class="exp-info">
          <div class="exp-cat">${e.category} &nbsp; <span style="color:var(--muted);font-size:12px">${e.amount.toFixed(2)}€</span></div>
          <div class="exp-date" onclick="openDateModal(${e.id}, '${e.date}')" title="Πάτα για αλλαγή ημερομηνίας">
            📅 ${e.date} <span style="color:var(--accent);font-size:10px">✏️</span>
          </div>
          ${e.notes ? `<div style="font-size:11px;color:var(--muted);margin-top:2px">💬 ${e.notes}</div>` : ''}
        </div>
        <button class="del-btn" onclick="deleteExpense(${e.id})" title="Διαγραφή">✕</button>
      </div>`).join('');
  } catch(e) {}
}

async function deleteExpense(id) {
  if (!confirm('Να διαγραφεί αυτή η καταχώρηση;')) return;
  try {
    const res = await fetch('/delete', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ id })
    });
    const data = await res.json();
    if (data.ok) { document.getElementById('row-' + id)?.remove(); showToast('🗑️ Διαγράφηκε!'); loadBudget(); }
    else showToast('❌ Σφάλμα', true);
  } catch(e) { showToast('❌ Σφάλμα σύνδεσης', true); }
}

async function loadBudget() {
  try {
    const [totalRes, budgetRes] = await Promise.all([fetch('/total'), fetch('/budget')]);
    const totalData = await totalRes.json();
    const budgetData = await budgetRes.json();
    const spent = totalData.total;
    const budget = budgetData.budget;
    const remaining = budget - spent;
    const color = remaining < 0 ? '#FF6B6B' : remaining < budget * 0.2 ? '#FFE66D' : '#6BCB77';
    document.getElementById('header-total').textContent = `Δαπανήθηκαν: ${spent.toFixed(2)}€ / ${budget.toFixed(2)}€`;
    document.getElementById('header-remaining').innerHTML = `<span style="color:${color}">${remaining >= 0 ? '✅ Απομένουν' : '⚠️ Υπέρβαση'}: ${Math.abs(remaining).toFixed(2)}€</span>`;
    document.getElementById('budget-input').value = budget;
  } catch(e) {}
}

async function saveBudget() {
  const val = parseFloat(document.getElementById('budget-input').value);
  if (!val || val <= 0) return;
  try {
    const res = await fetch('/budget', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ budget: val })
    });
    const data = await res.json();
    if (data.ok) {
      document.getElementById('budget-msg').textContent = '✅ Αποθηκεύτηκε!';
      loadBudget();
      setTimeout(() => document.getElementById('budget-msg').textContent = '', 2000);
    }
  } catch(e) {}
}

document.getElementById('date-modal').addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});

loadBudget();
</script>
</body>
</html>
"""

def make_chart(rows, total, label):
    from collections import defaultdict
    sums = defaultdict(float)
    for r in rows:
        sums[r["category"]] += r["amount"]
    sums = dict(sorted(sums.items(), key=lambda x: x[1], reverse=True))
    colors = [CAT_COLORS.get(cat, "#7C6EF5") for cat in sums]
    fig = plt.figure(figsize=(9, 5), facecolor="#1A1A22", layout="constrained")
    fig.suptitle(label, fontsize=12, fontweight="bold", color="#EEEEF5")
    ax = fig.add_subplot(111)
    _, _, autotexts = ax.pie(list(sums.values()), labels=None,
        autopct=lambda p: f"{p:.1f}%" if p > 4 else "",
        colors=colors, startangle=140, pctdistance=0.75,
        wedgeprops={"edgecolor": "#1A1A22", "linewidth": 2})
    for at in autotexts:
        at.set_fontsize(9); at.set_color("white"); at.set_fontweight("bold")
    ax.text(0, 0, f"{total:.2f}\u20ac", ha="center", va="center",
            fontsize=13, fontweight="bold", color="#EEEEF5")
    handles = [mpatches.Patch(color=colors[i], label=f"{cat}  {sums[cat]:.2f}\u20ac")
               for i, cat in enumerate(sums)]
    ax.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.08),
              ncol=3, fontsize=8, frameon=False, labelcolor="#EEEEF5")
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130, facecolor="#1A1A22")
    plt.close()
    return base64.b64encode(buf.getvalue()).decode()

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/add", methods=["POST"])
def add():
    try:
        data = request.json
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        with get_db() as conn:
            conn.execute("INSERT INTO expenses (date, amount, category, notes) VALUES (?, ?, ?, ?)",
                         (now, float(data["amount"]), data["category"], data.get("notes", "")))
            conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        data = request.json
        period = data.get("period", "month")
        today = date.today()
        if period == "month": start = today.replace(day=1).isoformat(); end = None
        elif period == "30": start = (today - timedelta(days=30)).isoformat(); end = None
        elif period == "90": start = (today - timedelta(days=90)).isoformat(); end = None
        elif period == "year": start = today.replace(month=1, day=1).isoformat(); end = None
        elif period == "custom": start = data.get("from"); end = data.get("to")
        else: start = None; end = None
        query = "SELECT * FROM expenses WHERE 1=1"
        params = []
        if start: query += " AND date >= ?"; params.append(start)
        if end: query += " AND date <= ?"; params.append(end + " 23:59")
        with get_db() as conn:
            rows = [dict(r) for r in conn.execute(query, params).fetchall()]
        if not rows: return jsonify({"ok": False})
        total = sum(r["amount"] for r in rows)
        from collections import defaultdict
        sums = defaultdict(float)
        for r in rows: sums[r["category"]] += r["amount"]
        sums = dict(sorted(sums.items(), key=lambda x: x[1], reverse=True))
        label_map = {"month": "Τρέχων μήνας", "30": "30 μέρες", "90": "90 μέρες",
                     "year": f"Έτος {today.year}", "all": "Όλα", "custom": "Προσαρμοσμένο"}
        chart = make_chart(rows, total, label_map.get(period, ""))
        cats = [{"name": k, "amount": v, "pct": v/total*100} for k, v in sums.items()]
        return jsonify({"ok": True, "total": total, "count": len(rows), "categories": cats, "chart": chart})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/history")
def history():
    try:
        with get_db() as conn:
            rows = conn.execute("SELECT * FROM expenses ORDER BY date DESC LIMIT 30").fetchall()
        items = []
        for r in rows:
            dt = datetime.strptime(r["date"], "%Y-%m-%d %H:%M")
            items.append({"id": r["id"], "date": dt.strftime("%d/%m/%Y %H:%M"),
                          "amount": r["amount"], "category": r["category"], "notes": r["notes"] or ""})
        return jsonify({"items": items})
    except:
        return jsonify({"items": []})

@app.route("/delete", methods=["POST"])
def delete():
    try:
        data = request.json
        with get_db() as conn:
            conn.execute("DELETE FROM expenses WHERE id = ?", (int(data["id"]),))
            conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/update_date", methods=["POST"])
def update_date():
    try:
        data = request.json
        new_date = data["date"].replace("T", " ")
        with get_db() as conn:
            conn.execute("UPDATE expenses SET date = ? WHERE id = ?", (new_date, int(data["id"])))
            conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/total")
def total():
    try:
        today = date.today()
        start = today.replace(day=1).isoformat()
        with get_db() as conn:
            result = conn.execute("SELECT SUM(amount) FROM expenses WHERE date >= ?", (start,)).fetchone()
        return jsonify({"total": float(result[0] or 0)})
    except:
        return jsonify({"total": 0})

@app.route("/budget", methods=["GET"])
def get_budget():
    try:
        with get_db() as conn:
            result = conn.execute("SELECT value FROM settings WHERE key='budget'").fetchone()
        return jsonify({"ok": True, "budget": float(result[0])})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@app.route("/budget", methods=["POST"])
def set_budget():
    try:
        data = request.json
        with get_db() as conn:
            conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('budget', ?)",
                         (str(float(data["budget"])),))
            conn.commit()
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

init_db()

if __name__ == "__main__":
    import socket
    try: ip = socket.gethostbyname(socket.gethostname())
    except: ip = "???"
    print(f"\n{'='*50}\n   💸  Εφαρμογή Εξόδων\n{'='*50}")
    print(f"   Τοπικά:     http://localhost:5000")
    print(f"   Κινητό:     http://{ip}:5000\n")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
