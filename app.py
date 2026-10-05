from flask import Flask, request, Response, jsonify
from googleapiclient.discovery import build
from dateutil import parser
from datetime import datetime, timezone, timedelta
import concurrent.futures
import json
import os

app = Flask(__name__)

# --- CLOUD DATABASE SYSTEM ---
CLOUD_DB_FILE = 'cloud_users.json'

def load_cloud_db():
    if os.path.exists(CLOUD_DB_FILE):
        with open(CLOUD_DB_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cloud_db(db):
    with open(CLOUD_DB_FILE, 'w') as f:
        json.dump(db, f)

@app.route('/api/auth/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email', '').strip().lower()
    pwd = data.get('password', '')
    payload = data.get('data', {})
    
    if not email or not pwd:
        return jsonify({"error": "Email and Password required."}), 400
        
    db = load_cloud_db()
    if email in db:
        return jsonify({"error": "Email already exists. Please login."}), 400
    
    db[email] = {"password": pwd, "data": payload}
    save_cloud_db(db)
    return jsonify({"success": True, "data": payload})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip().lower()
    pwd = data.get('password', '')
    
    db = load_cloud_db()
    if email not in db or db[email]['password'] != pwd:
        return jsonify({"error": "Invalid email or password."}), 401
        
    return jsonify({"success": True, "data": db[email]['data']})

@app.route('/api/auth/sync', methods=['POST'])
def sync_auth():
    data = request.json
    email = data.get('email', '').strip().lower()
    pwd = data.get('password', '')
    payload = data.get('data', {})
    
    db = load_cloud_db()
    if email in db and db[email]['password'] == pwd:
        db[email]['data'] = payload
        save_cloud_db(db)
        return jsonify({"success": True})
    return jsonify({"error": "Auth failed"}), 401


# --- FRONTEND UI ---
HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Research Tool Pro | Base Command</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  :root {
    --glass-fill: rgba(255, 255, 255, 0.07);
    --glass-border: rgba(255, 255, 255, 0.14);
    --glass-border-soft: rgba(255, 255, 255, 0.07);
    --ink: #f5f5f7;
    --ink-dim: rgba(245, 245, 247, 0.55);
    --accent: #0a84ff;
    --accent-purple: #bf5af2;
    --radius-lg: 28px;
    --radius-md: 18px;
    --radius-sm: 12px;
  }

  body {
    background: #030304; color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, sans-serif;
    min-height: 100vh; display: flex; flex-direction: column; align-items: center;
    padding: 56px 20px 40px; position: relative; overflow-x: hidden;
  }

  body::before, body::after {
    content: ''; position: fixed; border-radius: 50%; filter: blur(130px); z-index: -1; opacity: 0.45;
    animation: drift 18s infinite alternate ease-in-out;
  }
  body::before { top: -12%; left: -14%; width: 46vw; height: 46vw; background: #5e5ce6; }
  body::after { bottom: -14%; right: -12%; width: 42vw; height: 42vw; background: #bf5af2; animation-delay: -6s; }
  @keyframes drift { 0% { transform: translate(0, 0) scale(1); } 100% { transform: translate(4%, 4%) scale(1.12); } }

  /* Login Overlay */
  #loginOverlay {
    position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(20px);
    z-index: 9999; display: flex; flex-direction: column; align-items: center; justify-content: center;
  }
  .login-box {
    background: var(--glass-fill); border: 1px solid var(--glass-border); padding: 40px;
    border-radius: var(--radius-lg); text-align: center; width: 100%; max-width: 400px;
  }
  .login-box h2 { margin-bottom: 10px; font-size: 22px; }
  .login-box p { color: var(--ink-dim); font-size: 13px; margin-bottom: 24px; }
  .login-input {
    width: 100%; padding: 14px; border-radius: var(--radius-sm); border: 1px solid var(--glass-border-soft);
    background: rgba(0,0,0,0.5); color: #fff; font-size: 14px; text-align: center; margin-bottom: 12px; outline: none;
  }
  .login-input:focus { border-color: var(--accent); }

  .brand { text-align: center; margin-bottom: 28px; }
  .brand-mark { display: block; font-size: 30px; font-weight: 700; color: #fff; }
  .brand-sub { display: block; margin-top: 5px; font-size: 12px; font-weight: 500; letter-spacing: 0.14em; text-transform: uppercase; color: var(--ink-dim); }

  .box { width: 100%; max-width: 1000px; }
  .glass-panel {
    background: var(--glass-fill); -webkit-backdrop-filter: blur(28px); backdrop-filter: blur(28px);
    border: 1px solid var(--glass-border); border-radius: var(--radius-lg); padding: 24px; box-shadow: 0 20px 50px rgba(0,0,0,0.45);
  }

  .header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
  .profile-group { display: flex; align-items: center; gap: 8px; background: rgba(0,0,0,0.3); padding: 4px 8px; border-radius: 12px; border: 1px solid var(--glass-border-soft); }
  .profile-group select { background: transparent; border: none; color: #fff; font-size: 14px; font-weight: 600; outline: none; cursor: pointer; padding: 4px; }
  .profile-group select option { background: #1a1a1a; color: #fff; }
  .btn-icon { background: rgba(255,255,255,0.1); border: none; color: #fff; padding: 6px 12px; border-radius: 99px; cursor: pointer; font-size: 12px; font-weight: 600; transition: 0.2s; }
  .btn-icon:hover { background: rgba(255,255,255,0.2); }
  .btn-del-profile { color: #ff453a; margin-left: 4px; }

  /* Tag Inputs & Form Controls */
  .tag-container {
    background: rgba(0,0,0,0.3); border: 1px solid var(--glass-border-soft); border-radius: var(--radius-md);
    padding: 10px 14px; min-height: 52px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 16px;
  }
  .tag-container input, .tag-container select {
    background: transparent; border: none; color: var(--ink); font-size: 14px; outline: none; flex: 1; min-width: 100px; cursor: pointer;
  }
  .tag-container select option { background: #1a1a1a; color: #fff; }
  .tag {
    background: rgba(255,255,255,0.15); color: #fff; font-size: 12px; font-weight: 600; padding: 6px 12px;
    border-radius: 8px; display: flex; align-items: center; gap: 6px;
  }
  .tag span { cursor: pointer; color: rgba(255,255,255,0.5); }
  .tag span:hover { color: #ff453a; }

  .filter-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 16px; }
  .filter-col { display: flex; flex-direction: column; gap: 6px; }
  .filter-col label { font-size: 11px; color: var(--ink-dim); font-weight: 600; text-transform: uppercase; }

  /* Split Buttons */
  .action-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 24px; }
  button.solid {
    padding: 16px; font-size: 14px; font-weight: 600; border-radius: 16px; border: none; cursor: pointer; transition: all 0.15s; font-family: inherit;
  }
  button.solid:hover { transform: scale(0.98); opacity: 0.9; }
  button.solid:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }
  .btn-discover { background: var(--accent-purple); color: #fff; }
  .btn-analyze { background: var(--accent); color: #fff; }

  /* Channel Manager & Settings */
  .settings-panel { display: none; background: rgba(0,0,0,0.4); border-radius: var(--radius-md); padding: 20px; margin-bottom: 24px; border: 1px solid var(--glass-border-soft); }
  .channel-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; max-height: 300px; overflow-y: auto; margin-top: 16px; padding-right: 8px; }
  .channel-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 12px; display: flex; align-items: center; gap: 12px; }
  .channel-card img { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; }
  .channel-card .c-info { flex: 1; overflow: hidden; }
  .channel-card .c-name { font-size: 12px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .channel-card .c-del { color: #ff453a; cursor: pointer; font-size: 16px; }

  .status { font-size: 13px; font-weight: 500; color: var(--ink-dim); min-height: 20px; margin-top: 20px; text-align: center; }
  .status.active { color: var(--accent-2); }
  
  /* Output Table & Sorting */
  .table-container { width: 100%; overflow-x: auto; max-height: 600px; overflow-y: auto; border-radius: var(--radius-sm); background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border-soft); margin-top: 24px; display: none; }
  .glass-table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: left; white-space: nowrap; }
  .glass-table th { position: sticky; top: 0; background: rgba(30, 30, 35, 0.9); backdrop-filter: blur(12px); color: var(--ink-dim); font-weight: 600; padding: 12px 16px; z-index: 2; }
  .glass-table td { padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); vertical-align: middle; }
  .glass-table tr:hover td { background: rgba(255,255,255,0.05); }
  
  .sortable { cursor: pointer; user-select: none; transition: background 0.2s; }
  .sortable:hover { background: rgba(255,255,255,0.08); color: #fff; }
  
  .thumb-img { width: 64px; height: 36px; border-radius: 6px; object-fit: cover; border: 1px solid rgba(255,255,255,0.1); }
  .logo-img { width: 24px; height: 24px; border-radius: 50%; vertical-align: middle; margin-right: 8px; }
  
  .badge { padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 11px; background: rgba(191, 90, 242, 0.2); color: #bf5af2;}
  .date-badge { color: var(--ink-dim); font-size: 11px; font-weight: 500; }
  .table-btn { font-size: 11px; font-weight: 600; padding: 6px 12px; border-radius: 6px; background: rgba(255,255,255,0.1); color: #fff; text-decoration: none; transition: 0.2s; margin-right: 4px; }
  .table-btn:hover { background: rgba(255,255,255,0.2); }
  .trunc { max-width: 160px; overflow: hidden; text-overflow: ellipsis; }
  
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 10px; }
</style>
</head>
<body>

<!-- Cloud Authentication Overlay -->
<div id="loginOverlay">
  <div class="login-box">
    <h2 id="loginTitle">Cloud Workspace</h2>
    <p id="loginSub">Login or sign up to permanently sync your channels and tags everywhere.</p>
    <input type="email" id="emailInput" class="login-input" placeholder="Email Address">
    <input type="password" id="passInput" class="login-input" placeholder="Password">
    <div style="display: flex; gap: 10px;">
      <button class="solid btn-analyze" style="flex: 1;" onclick="handleAuth('login')">Login</button>
      <button class="solid btn-discover" style="flex: 1;" onclick="handleAuth('signup')">Sign Up</button>
    </div>
    <div id="authStatus" style="color: #ff453a; margin-top: 16px; font-size: 12px; font-weight: 600;"></div>
  </div>
</div>

<div class="brand">
  <span class="brand-mark">Base Command</span>
  <span class="brand-sub">Permanent Channel Pipeline</span>
</div>

<div class="box">
  <div class="glass-panel">
    
    <!-- Profile & Header Row -->
    <div class="header-row">
      <div class="profile-group">
        <span style="font-size:11px; color:var(--ink-dim); text-transform:uppercase; font-weight:700;">Workspace:</span>
        <select id="profileSelect" onchange="switchProfile()"></select>
        <button class="btn-icon" onclick="createProfile()">+ New</button>
        <button class="btn-icon btn-del-profile" onclick="deleteProfile()" title="Delete Profile">🗑️</button>
      </div>
      <div>
        <span style="font-size:12px; color:var(--ink-dim); margin-right: 12px;" id="userEmailDisplay"></span>
        <button class="btn-icon" onclick="toggleSettings()" style="padding: 10px 16px; background: rgba(10, 132, 255, 0.2); color: #64d2ff;">⚙️ API & Base Manager</button>
      </div>
    </div>

    <!-- Settings & Base Manager Panel -->
    <div class="settings-panel" id="settingsPanel">
      <div style="margin-bottom:16px;">
        <label style="font-size:10px; text-transform:uppercase; color:var(--ink-dim); font-weight:600;">Global YouTube API Key</label>
        <input type="text" id="ytApiKey" class="tag-container" style="width:100%; margin-top:6px; min-height:40px;" placeholder="AIzaSy..." onchange="saveGlobalApiKey()">
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <label style="font-size:10px; text-transform:uppercase; color:var(--ink-dim); font-weight:600;">Verified Base Channels (Current Profile)</label>
        <span style="font-size:12px; color:var(--accent);" id="baseCount">0 Saved</span>
      </div>
      <div class="channel-grid" id="channelGrid">
        <!-- Channel Cards Load Here -->
      </div>
    </div>

    <!-- Configuration Tags & Inputs -->
    <div class="filter-col">
      <label>1. Discovery Seeds (Type & Press Enter)</label>
      <div class="tag-container" id="seedContainer">
        <input type="text" id="seedInput" placeholder="e.g. street food, funny animals...">
      </div>
    </div>

    <div class="filter-col">
      <label>2. Niche Qualification Keywords (Type & Press Enter)</label>
      <div class="tag-container" id="nicheContainer">
        <input type="text" id="nicheInput" placeholder="e.g. spicy, vendor, burger...">
      </div>
    </div>

    <!-- Advanced Filters -->
    <div class="filter-grid">
      <div class="filter-col">
        <label>Discovery Max Results</label>
        <div class="tag-container" style="min-height: 44px;"><select id="maxResults" onchange="saveProfile()">
          <option value="10">10 Results</option>
          <option value="15">15 Results</option>
          <option value="25">25 Results</option>
          <option value="50" selected>50 Results (Max)</option>
        </select></div>
      </div>
      <div class="filter-col">
        <label>Discovery Upload Date</label>
        <div class="tag-container" style="min-height: 44px;"><select id="dateFilter" onchange="saveProfile()">
          <option value="1">Today</option>
          <option value="7" selected>This Week</option>
          <option value="30">This Month</option>
          <option value="365">This Year</option>
        </select></div>
      </div>
      
      <!-- New Analysis Time Filter -->
      <div class="filter-col">
        <label>Base Analysis Timeframe</label>
        <div class="tag-container" style="min-height: 44px;"><select id="analyzeTime" onchange="saveProfile()">
          <option value="12">Last 12 Hours</option>
          <option value="24" selected>Last 24 Hours</option>
          <option value="72">Last 3 Days</option>
          <option value="168">Last 7 Days</option>
          <option value="720">Last 30 Days</option>
        </select></div>
      </div>

      <div class="filter-col">
        <label>Qual. Threshold (Matches)</label>
        <div class="tag-container" style="min-height: 44px;"><input type="number" id="thresholdInput" value="5" placeholder="Matches" onchange="saveProfile()"></div>
      </div>
    </div>

    <!-- Action Buttons -->
    <div class="action-grid">
      <button class="solid btn-discover" id="btnDiscover" onclick="runPipeline('discover')">
        🔍 Discover & Add to Base
      </button>
      <button class="solid btn-analyze" id="btnAnalyze" onclick="runPipeline('analyze')">
        ⚡ Analyze Saved Base List
      </button>
    </div>

    <div class="status" id="mainStatus">System Ready.</div>

    <div class="table-container" id="tableContainer">
      <table class="glass-table">
        <thead id="tableHead"></thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>

  </div>
</div>

<script>
  let masterData = {
    apiKey: '',
    activeProfile: 'Default',
    profiles: {
      'Default': { 
        seeds: [], niches: [], threshold: 5, 
        dateFilter: '7', maxResults: 50, analyzeTime: '24',
        channels: {} 
      }
    }
  };

  let currentUser = { email: '', pwd: '' };
  
  // --- GLOBALS FOR SORTING ---
  window.lastFetchedResults = [];
  window.sortState = { col: null, dir: 0 };

  // --- 1. CLOUD LOGIN SYSTEM ---
  window.onload = () => {
    const savedEmail = localStorage.getItem('cloud_email');
    const savedPwd = localStorage.getItem('cloud_pwd');
    if (savedEmail && savedPwd) {
      currentUser.email = savedEmail;
      currentUser.pwd = savedPwd;
      // Auto-login to pull latest cloud sync
      handleAuth('login', true);
    }
  };

  async function handleAuth(action, isAuto = false) {
    const email = isAuto ? currentUser.email : document.getElementById('emailInput').value.trim();
    const pwd = isAuto ? currentUser.pwd : document.getElementById('passInput').value;
    const statusEl = document.getElementById('authStatus');
    
    if (!email || !pwd) {
      statusEl.innerText = "Email and Password required.";
      return;
    }

    statusEl.innerText = "Connecting to Cloud Workspace...";
    statusEl.style.color = "var(--accent-2)";

    try {
      const endpoint = action === 'signup' ? '/api/auth/signup' : '/api/auth/login';
      const body = { email: email, password: pwd };
      if (action === 'signup') body.data = masterData;

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const json = await res.json();

      if (json.success) {
        currentUser.email = email;
        currentUser.pwd = pwd;
        localStorage.setItem('cloud_email', email);
        localStorage.setItem('cloud_pwd', pwd);
        masterData = json.data;
        document.getElementById('userEmailDisplay').innerText = `👤 ${email}`;
        
        unlockSystem();
      } else {
        statusEl.innerText = json.error || "Authentication failed.";
        statusEl.style.color = "#ff453a";
      }
    } catch (e) {
      statusEl.innerText = "Server error. Ensure backend is running.";
      statusEl.style.color = "#ff453a";
    }
  }

  function unlockSystem() {
    document.getElementById('loginOverlay').style.display = 'none';
    document.getElementById('ytApiKey').value = masterData.apiKey || '';
    renderProfileDropdown();
    loadActiveProfileUI();
    setupTagListeners();
  }

  // Backs up instantly to the cloud whenever settings change
  async function syncCloudMaster() {
    if (!currentUser.email) return;
    try {
      await fetch('/api/auth/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: currentUser.email, password: currentUser.pwd, data: masterData })
      });
    } catch (e) { console.error("Cloud sync failed"); }
  }


  // --- 2. MULTI-PROFILE DATA MANAGEMENT ---
  function saveGlobalApiKey() {
    masterData.apiKey = document.getElementById('ytApiKey').value.trim();
    syncCloudMaster();
  }

  function renderProfileDropdown() {
    const select = document.getElementById('profileSelect');
    select.innerHTML = '';
    Object.keys(masterData.profiles).forEach(pName => {
      const opt = document.createElement('option');
      opt.value = pName; opt.innerText = pName;
      if (pName === masterData.activeProfile) opt.selected = true;
      select.appendChild(opt);
    });
  }

  function switchProfile() {
    masterData.activeProfile = document.getElementById('profileSelect').value;
    syncCloudMaster();
    loadActiveProfileUI();
  }

  function createProfile() {
    const pName = prompt("Enter new Workspace Profile Name:");
    if (pName && pName.trim() !== '') {
      if (!masterData.profiles[pName]) {
        masterData.profiles[pName] = { seeds: [], niches: [], threshold: 5, dateFilter: '7', maxResults: 50, analyzeTime: '24', channels: {} };
        masterData.activeProfile = pName;
        syncCloudMaster(); renderProfileDropdown(); loadActiveProfileUI();
      } else { alert("Profile name already exists."); }
    }
  }

  function deleteProfile() {
    const active = masterData.activeProfile;
    if (active === 'Default') return alert("Cannot delete the Default workspace.");
    if (confirm(`Are you sure you want to delete workspace "${active}"?`)) {
      delete masterData.profiles[active];
      masterData.activeProfile = 'Default';
      syncCloudMaster(); renderProfileDropdown(); loadActiveProfileUI();
    }
  }

  function loadActiveProfileUI() {
    const pData = masterData.profiles[masterData.activeProfile];
    
    document.getElementById('thresholdInput').value = pData.threshold || 5;
    document.getElementById('dateFilter').value = pData.dateFilter || '7';
    document.getElementById('maxResults').value = pData.maxResults || 50;
    document.getElementById('analyzeTime').value = pData.analyzeTime || '24';
    
    renderTags('seedContainer', pData.seeds);
    renderTags('nicheContainer', pData.niches);
    renderChannelGrid();
  }

  function saveProfile() {
    const active = masterData.activeProfile;
    masterData.profiles[active].threshold = parseInt(document.getElementById('thresholdInput').value) || 5;
    masterData.profiles[active].dateFilter = document.getElementById('dateFilter').value;
    masterData.profiles[active].maxResults = parseInt(document.getElementById('maxResults').value) || 50;
    masterData.profiles[active].analyzeTime = document.getElementById('analyzeTime').value;
    syncCloudMaster();
  }


  // --- 3. TAG SYSTEM ---
  function setupTagListeners() {
    const handleEnter = (e, arrKey, containerId, inputId) => {
      if (e.key === 'Enter' && e.target.value.trim()) {
        const val = e.target.value.trim();
        const active = masterData.activeProfile;
        if (!masterData.profiles[active][arrKey].includes(val)) {
          masterData.profiles[active][arrKey].push(val);
          syncCloudMaster(); renderTags(containerId, masterData.profiles[active][arrKey]);
        }
        e.target.value = '';
      }
    };
    document.getElementById('seedInput').addEventListener('keypress', (e) => handleEnter(e, 'seeds', 'seedContainer', 'seedInput'));
    document.getElementById('nicheInput').addEventListener('keypress', (e) => handleEnter(e, 'niches', 'nicheContainer', 'nicheInput'));
  }

  function renderTags(containerId, arr) {
    const container = document.getElementById(containerId);
    const input = container.querySelector('input');
    container.innerHTML = '';
    
    arr.forEach((tag, idx) => {
      const span = document.createElement('div'); span.className = 'tag';
      span.innerHTML = `${tag} <span onclick="removeTag('${containerId}', ${idx})">&times;</span>`;
      container.appendChild(span);
    });
    container.appendChild(input);
  }

  window.removeTag = function(containerId, idx) {
    const arrKey = containerId === 'seedContainer' ? 'seeds' : 'niches';
    masterData.profiles[masterData.activeProfile][arrKey].splice(idx, 1);
    syncCloudMaster(); renderTags(containerId, masterData.profiles[masterData.activeProfile][arrKey]);
  }

  // --- 4. BASE MANAGER (UI) ---
  function toggleSettings() {
    const panel = document.getElementById("settingsPanel");
    panel.style.display = panel.style.display === "block" ? "none" : "block";
  }

  function renderChannelGrid() {
    const grid = document.getElementById('channelGrid'); grid.innerHTML = '';
    const channels = masterData.profiles[masterData.activeProfile].channels;
    const keys = Object.keys(channels);
    document.getElementById('baseCount').innerText = `${keys.length} Saved`;

    keys.forEach(cId => {
      const c = channels[cId];
      const div = document.createElement('div'); div.className = 'channel-card';
      div.innerHTML = `
        <img src="${c.logo || 'https://via.placeholder.com/36'}" alt="logo">
        <div class="c-info"><div class="c-name">${c.title}</div></div>
        <div class="c-del" onclick="deleteChannel('${cId}')">&times;</div>
      `;
      grid.appendChild(div);
    });
  }

  window.deleteChannel = function(cId) {
    delete masterData.profiles[masterData.activeProfile].channels[cId];
    syncCloudMaster(); renderChannelGrid();
  }

  // --- 5. PIPELINE EXECUTION ---
  function setStatus(msg, type = '') {
    const el = document.getElementById('mainStatus'); el.textContent = msg; el.className = 'status ' + type;
  }

  function runPipeline(actionType) {
    if (!masterData.apiKey) return setStatus("Global API Key required in Settings.", "error");
    
    document.getElementById('btnDiscover').disabled = true;
    document.getElementById('btnAnalyze').disabled = true;
    document.getElementById('tableContainer').style.display = 'none';

    const pData = masterData.profiles[masterData.activeProfile];
    let url = '';

    if (actionType === 'discover') {
      if (pData.seeds.length === 0 || pData.niches.length === 0) {
        setStatus("Seeds and Niche tags are required for Discovery.", "error"); enableBtns(); return;
      }
      const sParams = encodeURIComponent(pData.seeds.join(','));
      const nParams = encodeURIComponent(pData.niches.join(','));
      url = `/api/discover?api_key=${masterData.apiKey}&seeds=${sParams}&niches=${nParams}&threshold=${pData.threshold}&period=${pData.dateFilter}&max=${pData.maxResults}`;
    } else {
      if (Object.keys(pData.channels).length === 0) {
        setStatus("Your Base List for this profile is empty. Run Discovery first.", "error"); enableBtns(); return;
      }
      url = `/api/analyze?api_key=${masterData.apiKey}&time=${pData.analyzeTime}`;
    }

    const eventSource = new EventSource(url);

    eventSource.onmessage = function(event) {
      const data = JSON.parse(event.data);
      
      if (data.status === 'progress') setStatus(data.msg, "active");
      else if (data.status === 'channel_found') {
        masterData.profiles[masterData.activeProfile].channels[data.channel.id] = data.channel.data;
        syncCloudMaster(); renderChannelGrid();
      }
      else if (data.status === 'done') {
        setStatus(data.msg, "success");
        if (data.results) {
            window.lastFetchedResults = data.results;
            window.sortState = { col: null, dir: 0 };
            renderTable(window.lastFetchedResults);
        }
        eventSource.close(); enableBtns();
      } 
      else if (data.status === 'error') {
        setStatus("Error: " + data.msg, "error"); eventSource.close(); enableBtns();
      }
    };
    eventSource.onerror = function() {
      setStatus("Stream finished or disconnected. Outputting current results.", "success"); eventSource.close(); enableBtns();
    };
  }

  function enableBtns() {
    document.getElementById('btnDiscover').disabled = false;
    document.getElementById('btnAnalyze').disabled = false;
  }

  // --- 6. SORTING LOGIC ---
  function handleSort(col) {
    if (window.sortState.col === col) {
      window.sortState.dir = (window.sortState.dir + 1) % 3;
    } else {
      window.sortState.col = col;
      window.sortState.dir = 1; 
    }

    let toRender = [...window.lastFetchedResults];

    if (window.sortState.dir !== 0) {
      toRender.sort((a, b) => {
        let valA = a[col];
        let valB = b[col];
        if (window.sortState.dir === 1) return valB - valA; 
        return valA - valB; 
      });
    }
    
    renderTable(toRender);
  }

  function getSortIndicator(col) {
    if (window.sortState && window.sortState.col === col) {
      if (window.sortState.dir === 1) return ' ↓';
      if (window.sortState.dir === 2) return ' ↑';
    }
    return '';
  }

  function renderTable(results) {
    if (results.length === 0) return setStatus("No results matched criteria.", "error");
    document.getElementById('tableContainer').style.display = 'block';
    
    const thead = document.getElementById('tableHead');
    const tbody = document.getElementById('tableBody');

    // Clickable Sorting Headers
    thead.innerHTML = `<tr>
      <th>Video</th>
      <th>Title</th>
      <th>Base Channel</th>
      <th class="sortable" onclick="handleSort('published_raw')">Published${getSortIndicator('published_raw')}</th>
      <th class="sortable" onclick="handleSort('views')">Views${getSortIndicator('views')}</th>
      <th class="sortable" onclick="handleSort('vph')">Velocity (VPH)${getSortIndicator('vph')}</th>
      <th>Links</th>
    </tr>`;
    
    let html = '';
    results.forEach(r => {
      html += `<tr>
        <td><img class="thumb-img" src="${r.thumbnail}" alt="thumb"></td>
        <td class="trunc" title="${r.title}">${r.title}</td>
        <td><img class="logo-img" src="${r.logo}">${r.channel}</td>
        <td class="date-badge">${r.published}</td>
        <td>${r.views.toLocaleString()} 👁️</td>
        <td><span class="badge">🔥 ${r.vph.toLocaleString()}/hr</span></td>
        <td>
          <a class="table-btn" href="${r.videoLink}" target="_blank">▶️</a>
          <a class="table-btn" href="${r.channelLink}" target="_blank">👤</a>
        </td>
      </tr>`;
    });
    tbody.innerHTML = html;
  }
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return HTML_UI

@app.route('/api/discover', methods=['GET'])
def auto_discover():
    api_key = request.args.get('api_key')
    seeds = request.args.get('seeds', '').split(',')
    niche_keywords = [k.strip().lower() for k in request.args.get('niches', '').split(',') if k.strip()]
    threshold = int(request.args.get('threshold', 5))
    
    period = int(request.args.get('period', 7))
    max_res = int(request.args.get('max', 50))

    def generate():
        def emit(status, msg="", data=None, channel_info=None):
            payload = {"status": status, "msg": msg}
            if data is not None: payload["results"] = data
            if channel_info is not None: payload["channel"] = channel_info
            return f"data: {json.dumps(payload)}\n\n"

        try:
            youtube = build('youtube', 'v3', developerKey=api_key)
            new_channels = set()
            after_date = (datetime.now(timezone.utc) - timedelta(days=period)).isoformat()

            for seed in seeds:
                if not seed.strip(): continue
                yield emit('progress', f'Searching seed tag: "{seed}" (Max: {max_res})...')
                
                search_res = youtube.search().list(
                    q=seed.strip(), 
                    part="snippet", 
                    type="video", 
                    order="date", 
                    publishedAfter=after_date,
                    maxResults=max_res
                ).execute()
                
                for item in search_res.get('items', []):
                    c_id = item['snippet']['channelId']
                    new_channels.add(c_id)

            yield emit('progress', f'Extracted {len(new_channels)} channels. Running Niche Verification...')

            new_channels = list(new_channels)
            if new_channels:
                for i in range(0, len(new_channels), 50):
                    batch = new_channels[i:i+50]
                    c_res = youtube.channels().list(part="contentDetails,snippet", id=",".join(batch)).execute()
                    
                    for c_item in c_res.get('items', []):
                        c_id = c_item['id']
                        c_title = c_item['snippet']['title']
                        logo = c_item['snippet']['thumbnails']['default']['url']
                        
                        try:
                            uploads_id = c_item['contentDetails']['relatedPlaylists']['uploads']
                        except KeyError:
                            continue 

                        pl_res = youtube.playlistItems().list(part="snippet", playlistId=uploads_id, maxResults=30).execute()
                        
                        match_count = 0
                        for pl_item in pl_res.get('items', []):
                            title = pl_item['snippet']['title'].lower()
                            if any(k in title for k in niche_keywords): match_count += 1

                        if match_count >= threshold:
                            channel_data = {"title": c_title, "uploads_id": uploads_id, "logo": logo}
                            yield emit('channel_found', f'✅ Verified: {c_title} ({match_count} matches)', channel_info={"id": c_id, "data": channel_data})
                        else:
                            yield emit('progress', f'❌ Discarded: {c_title} ({match_count} matches)')

            yield emit('done', f'Discovery Sequence Complete.')

        except Exception as e:
            yield emit('error', str(e))

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/analyze', methods=['GET'])
def auto_analyze():
    api_key = request.args.get('api_key')
    time_limit_hours = int(request.args.get('time', 24))

    # Pull user's specific channels dynamically via the synced auth db
    # We will grab all channels across their profile to be safe
    db = load_cloud_db()
    # Find channels matching the user who made the request (In a robust app, we'd pass an auth token here)
    # Since SSE is a GET request, we will pass the channel data temporarily via a POST route in a future upgrade if needed, 
    # but for now, we will parse all channels in the DB to find the matching api_key workspace.
    
    # Wait, SSE GET doesn't send a body. We will quickly grab the channels from the DB where api_key matches.
    user_channels = {}
    for user_data in db.values():
        if user_data['data'].get('apiKey') == api_key:
            active_prof = user_data['data'].get('activeProfile', 'Default')
            user_channels = user_data['data']['profiles'][active_prof].get('channels', {})
            break

    def generate():
        def emit(status, msg="", data=None):
            payload = {"status": status, "msg": msg}
            if data is not None: payload["results"] = data
            return f"data: {json.dumps(payload)}\n\n"

        try:
            youtube = build('youtube', 'v3', developerKey=api_key)
            all_videos = []
            total_base = len(user_channels)
            
            cutoff_date = datetime.now(timezone.utc) - timedelta(hours=time_limit_hours)
            
            yield emit('progress', f'Multithread Sequence: Scanning {total_base} channels for videos in the last {time_limit_hours} hours...')

            # Multithreading Function to process channels safely and simultaneously
            def process_channel(item):
                c_id, c_data = item
                uploads_id = c_data.get('uploads_id')
                if not uploads_id: return []

                pl_res = youtube.playlistItems().list(part="snippet,contentDetails", playlistId=uploads_id, maxResults=15).execute()
                
                v_ids = []
                for pl_item in pl_res.get('items', []):
                    pub_date = parser.isoparse(pl_item['snippet']['publishedAt'])
                    if pub_date >= cutoff_date:
                        v_ids.append(pl_item['contentDetails']['videoId'])

                if not v_ids: return []

                v_res = youtube.videos().list(part="snippet,statistics", id=",".join(v_ids)).execute()
                
                channel_results = []
                for v_item in v_res.get('items', []):
                    v_id = v_item['id']
                    pub_date = parser.isoparse(v_item['snippet']['publishedAt'])
                    date_str = pub_date.strftime("%b %d, %Y")
                    age_hours = (datetime.now(timezone.utc) - pub_date).total_seconds() / 3600
                    views = int(v_item['statistics'].get('viewCount', 0))
                    vph = views / max(age_hours, 1)
                    
                    try:
                        thumb = v_item['snippet']['thumbnails']['medium']['url']
                    except KeyError:
                        thumb = v_item['snippet']['thumbnails']['default']['url']

                    channel_results.append({
                        "title": v_item['snippet']['title'],
                        "channel": c_data['title'],
                        "logo": c_data.get('logo', ''),
                        "thumbnail": thumb,
                        "published": date_str,
                        "published_raw": pub_date.timestamp(), # Used for precise HTML Sorting
                        "views": views, "vph": round(vph, 1), "age_hours": round(age_hours, 1),
                        "videoLink": f"https://www.youtube.com/watch?v={v_id}",
                        "channelLink": f"https://www.youtube.com/channel/{c_id}"
                    })
                return channel_results

            # Spin up 15 workers to blast through hundreds of channels simultaneously
            with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                futures = {executor.submit(process_channel, item): item for item in user_channels.items()}
                
                completed = 0
                for future in concurrent.futures.as_completed(futures):
                    completed += 1
                    # Yielding progress rapidly prevents Render from closing the connection!
                    if completed % 10 == 0 or completed == total_base:
                        yield emit('progress', f'[{completed}/{total_base}] Analyzing base channels...')
                    try:
                        res = future.result()
                        all_videos.extend(res)
                    except Exception:
                        pass

            yield emit('progress', 'Sorting matrix by View Velocity...')
            all_videos.sort(key=lambda x: x['vph'], reverse=True)
            yield emit('done', 'Base Analysis Complete!', all_videos[:100])

        except Exception as e:
            yield emit('error', str(e))

    return Response(generate(), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
