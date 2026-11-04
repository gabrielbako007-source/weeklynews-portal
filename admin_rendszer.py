import os
import json
import secrets
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from flask import Blueprint, render_template_string, redirect, url_for, request, session, Response, send_from_directory
from werkzeug.utils import secure_filename

# Blueprint modul konfigurálása az 1. rendszer általi közös indításhoz
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/magazin')

CONFIG_FILE = "twn_config.json"
ADMIN_PASSWORD = "twnadmin2026"
UPLOAD_FOLDER = 'uploads'

# A PONTOS, ÖSSZEVONT ROVATSTRUKTÚRA MAPPING
ROVATOK_MAP = {
    "news": "NEWS",
    "hit_csalad_erkolcs": "HIT, CSALÁD & ERKÖLCS",
    "egeszseg": "EGÉSZSÉG",
    "media": "MÉDIA (Videó & Podcast)",
    "tech_tudomany": "TECH-TUDOMÁNY",
    "ajanlo_hirdetes": "AJÁNLÓ & HIRDETÉS"
}

DEFAULT_CONFIG = {
    "magazin_cikkek": [
        {
            "id": 1,
            "title": "Üdvözöljük a The Weekly TWN News Prémium Rendszerében!",
            "category": "hit_csalad_erkolcs",
            "author": "Főszerkesztő",
            "read_time": "1 perc",
            "content": "Ez az első minta cikked. A Canva-motorral vizuálisan szerkesztheted, képeket tölthetsz fel, and rovatokba rendezheted a tartalmat.",
            "youtube": "",
            "mp3": "",
            "image": "",
            "published": True
        }
    ],
        "magazin_ads": [],
    "ads": [],
    "felhasznalok": {
        "teszt_olvaso@twn.hu": {
            "password_hash": "dummy_hash",
            "status": "active",
            "stripe_customer_id": "cus_test123",
            "stripe_subscription_id": "sub_test123",
            "last_payment": "2026-11-04"
        }
    }
}
def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def kuldo_infomaniak_email(hova, targy, szoveg):
    try:
        msg = MIMEText(szoveg, "plain", "utf-8")
        msg["Subject"] = targy
        msg["From"] = os.environ.get("SMTP_USER", "infotwn@etik.com")
        msg["To"] = hova
        with smtplib.SMTP(os.environ.get("SMTP_SERVER", "://infomaniak.com"), int(os.environ.get("SMTP_PORT", 587))) as server:
            server.starttls()
            server.login(os.environ.get("SMTP_USER", "infotwn@etik.com"), os.environ.get("SMTP_PASSWORD", "app_password_placeholder"))
            server.sendmail(os.environ.get("SMTP_USER", "infotwn@etik.com"), [hova], msg.as_string())
        return True
    except:
        return False

DRAFT_ARTICLES = None
DRAFT_ADS = None
ADMIN_PANEL_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly News Szerkesztőség — Canva & Stripe Központ</title>
        <link rel="stylesheet" href="https://unpkg.com">
    <script src="https://unpkg.com"></script>
    <style>
        body { font-family: 'Arial', sans-serif; background: #1e293b; color: #fff; padding: 0; margin:0; }
        .admin-wrap { max-width: 1400px; margin: 30px auto; background: #0f172a; border-radius: 8px; border: 1px solid #475569; overflow:hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .tabs-header { display: flex; background: #0f172a; border-bottom: 2px solid #ff2a2a; flex-wrap: wrap; }
        .tab-btn { background: none; border: 0; color: #cbd5e1; padding: 15px 25px; font-weight: bold; cursor: pointer; font-size: 0.95rem; transition: all 0.2s; text-transform: uppercase; }
        .tab-btn.active { color: #ffffff; background: #ff2a2a; }
        .tab-content { padding: 30px; display: none; background: #0f172a; }
        .tab-content.active { display: block; }
        .f-group { margin-bottom: 18px; }
        label { display: block; margin-bottom: 6px; color: #cbd5e1; font-weight: 600; font-size: 0.9rem; }
        input[type="text"], input[type="url"], select, textarea { width: 100%; padding: 11px; border-radius: 4px; border: 1px solid #475569; background: #1e293b; color: #fff; box-sizing: border-box; font-size: 0.95rem; }
        #gjs { border: 1px solid #475569; border-radius: 4px; background-color: #f4f4f5; }
        .table-cikkek { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .table-cikkek th, .table-cikkek td { padding: 12px; text-align: left; border-bottom: 1px solid #475569; }
        .table-cikkek th { background: #1e293b; color: #38bdf8; font-weight: bold; text-transform: uppercase; font-size: 0.85rem; }
        .btn-action { padding: 6px 12px; border-radius: 4px; border: 0; cursor: pointer; color: white; font-weight: bold; text-decoration: none; font-size: 0.85rem; display: inline-block; text-transform: uppercase; }
        .btn-add { background: #ff2a2a; color: #fff; font-weight: bold; padding: 12px 24px; border: 0; border-radius: 4px; cursor: pointer; font-size: 1rem; text-transform: uppercase; }
        .btn-add:hover { background: #d92222; }
    </style>
    <script>
        function openTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
            if(tabId === 'tab_ujcikk' && window.editor) { window.editor.refresh(); }
        }
    </script>
</head>
<body>
    <div class="admin-wrap">
        <div style="background:#0f172a; padding:20px 30px; display:flex; justify-content:space-between; align-items:center; border-bottom:3px solid #ff2a2a; flex-wrap:wrap; gap:15px;">
            <div style="display:flex; align-items:center; gap:20px;">
                <img src="/logo.png.png" style="max-width: 220px; height: auto; display: block;">
                <h2 style="margin:0; color:#ffffff; letter-spacing:1px; font-size:1.4rem; font-weight:900;">ADMIN KÖZPONT</h2>
            </div>
            <div>
                <a href="/magazin/panel/elesites" class="btn-action" style="background:#ff2a2a; font-size:0.95rem; padding:10px 20px; border:1px solid #ff5555;">VÁLTOZTATÁSOK ÉLESÍTÉSE</a>
                <a href="/magazin/logout" style="color:#cbd5e1; margin-left:20px; font-size:0.95rem; text-decoration:none; font-weight:bold; text-transform:uppercase;">Kijelentkezés [X]</a>
            </div>
        </div>
        <div class="tabs-header">
            <button class="tab-btn active" onclick="openTab('tab_lista')">Cikkek Áttekintése</button>
            <button class="tab-btn" onclick="openTab('tab_ujcikk')">Új Cikk Írása (Canva-mód)</button>
            <button class="tab-btn" onclick="openTab('tab_hirdetesek')">Hirdetések (Ajánló)</button>
            <button class="tab-btn" onclick="openTab('tab_elofizetok')">Előfizetők Követése (Stripe)</button>
        </div>
        <div id="tab_lista" class="tab-content active">
            <div style="background: #1e293b; padding: 20px; border: 1px dashed #38bdf8; border-radius: 6px; margin-bottom: 25px;">
                <h4 style="color:#38bdf8; margin-top:0; margin-bottom:10px; text-transform:uppercase;">Fájl feltöltése a saját számítógépedről</h4>
                <form action="/magazin/titkos-admin/upload-file" method="POST" enctype="multipart/form-data" style="display:flex; gap:15px; align-items:center; flex-wrap:wrap;">
                    <input type="file" name="file" required style="background:#0f172a; padding:8px; border:1px solid #475569; border-radius:4px; color:#fff; width:auto;">
                    <button type="submit" class="btn-add" style="padding:10px 20px; font-size:0.9rem;">Fájl Feltöltése ➔</button>
                </form>
            </div>
            <table class="table-cikkek">
                <thead>
                    <tr><th>Cím</th><th>Rovat</th><th>Szerző</th><th>Státusz</th><th>Műveletek</th></tr>
                </thead>
                <tbody>
                    {% for cikk in cikkek %}
                    <tr>
                        <td><strong style="color:#fff;">{{ cikk.title }}</strong></td>
                        <td style="color:#cbd5e1;">{{ rovatok_nevei[cikk.category] }}</td>
                        <td style="color:#cbd5e1;">{{ cikk.author }}</td>
                        <td>{% if cikk.published %}<span style="color:#4ade80; font-weight:bold;">[●] Élesítve</span>{% else %}<span style="color:#fbbf24; font-weight:bold;">[○] Vázlat</span>{% endif %}</td>
                        <td><a href="/magazin/panel/delete/{{ cikk.id }}" class="btn-action" style="background:#ff2a2a;" onclick="return confirm('Biztosan törlöd ezt a cikket?')">Törlés</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <div id="tab_ujcikk" class="tab-content">
            <form method="POST" action="/magazin/panel/add-cikk" onsubmit="syncEditor()">
                <div class="f-group"><label>Cikk Címe</label><input type="text" name="title" required></div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
                    <div class="f-group"><label>Szerző</label><input type="text" name="author" value="Főszerkesztő"></div>
                    <div class="f-group">
                        <label>Rovat</label>
                        <select name="category">
                            {% for k, v in rovatok_nevei.items() %}
                            <option value="{{ k }}">{{ v }}</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>
                <div class="f-group">
                    <div id="gjs"></div>
                    <input type="hidden" name="content" id="hidden_content">
                </div>
                <div class="f-group"><label>Borítókép URL / Feltöltött fájl elérési útja</label><input type="text" name="image"></div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
                    <div class="f-group"><label>YouTube Videó ID (csak az azonosító a beágyazáshoz)</label><input type="text" name="youtube"></div>
                    <div class="f-group"><label>MP3 Hanganyag URL (lejátszóhoz)</label><input type="url" name="mp3"></div>
                </div>
                <button type="submit" class="btn-add" style="width:100%;">Cikk Mentése Vázlatként</button>
            </form>
        </div>
        <div id="tab_hirdetesek" class="tab-content">
            <form method="POST" action="/magazin/panel/add-ad">
                <div class="f-group"><label>Hirdetés Megnevezése</label><input type="text" name="ad_title" required></div>
                <div class="f-group"><label>Hirdetési Banner / Kép URL</label><input type="url" name="ad_image" required></div>
                <div class="f-group"><label>Cél URL (hova vigyen a kattintás)</label><input type="url" name="ad_url" required></div>
                <button type="submit" class="btn-add">Hirdetés Mentése</button>
            </form>
        </div>
        <div id="tab_elofizetok" class="tab-content">
            <table class="table-cikkek">
                <thead><tr><th>E-mail cím</th><th>Státusz</th><th>Stripe Customer ID</th><th>Utolsó sikeres fizetés</th></tr></thead>
                <tbody>
                    {% for email, adat in felhasznalok.items() %}
                    <tr>
                        <td style="color:#fff;">{{ email }}</td>
                        <td>
                            {% if adat.status == 'active' %}
                            <span style="background:#22c55e; color:#000; padding:4px 8px; border-radius:3px; font-weight:bold; font-size:0.8rem; text-transform:uppercase;">Aktív fizető</span>
                            {% else %}
                            <span style="background:#ef4444; color:#fff; padding:4px 8px; border-radius:3px; font-weight:bold; font-size:0.8rem; text-transform:uppercase;">Nem fizető / Lejárt</span>
                            {% endif %}
                        </td>
                        <td style="color:#cbd5e1;">{{ adat.stripe_customer_id }}</td>
                        <td style="color:#cbd5e1;">{{ adat.last_payment }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <script>
        window.onload = function() {
ADMIN_PANEL_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly News Szerkesztőség - Canva & Stripe Központ</title>
    <link rel="stylesheet" href="https://unpkg.com">
    <script src="https://unpkg.com"></script>
        <style>
        body { font-family: 'Arial', sans-serif; background: #1e293b; color: #fff; padding: 0; margin: 0; }
        .admin-wrap { max-width: 1400px; margin: 30px auto; background: #0f172a; border-radius: 8px; border: 1px solid #475569; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .tabs-header { display: flex; background: #0f172a; border-bottom: 2px solid #ff2a2a; flex-wrap: wrap; }
        .tab-btn { background: none; border: 0; color: #cbd5e1; padding: 15px 25px; font-weight: bold; cursor: pointer; font-size: 0.95rem; transition: all 0.2s; text-transform: uppercase; }
        .tab-btn.active { color: #ffffff; background: #ff2a2a; }
        .tab-content { padding: 30px; display: none; background: #0f172a; }
        .tab-content.active { display: block; }
        .f-group { margin-bottom: 18px; }
        label { display: block; margin-bottom: 6px; color: #cbd5e1; font-weight: 600; font-size: 0.9rem; }
        input[type="text"], input[type="url"], select, textarea { width: 100%; padding: 11px; border-radius: 4px; border: 1px solid #475569; background: #1e293b; color: #fff; box-sizing: border-box; font-size: 0.95rem; }
        #gjs { border: 1px solid #475569; border-radius: 4px; background-color: #f4f4f5; }
        .table-cikkek { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .table-cikkek th, .table-cikkek td { padding: 12px; text-align: left; border-bottom: 1px solid #475569; }
        .table-cikkek th { background: #1e293b; color: #38bdf8; font-weight: bold; text-transform: uppercase; font-size: 0.85rem; }
        .btn-action { padding: 6px 12px; border-radius: 4px; border: 0; cursor: pointer; color: white; font-weight: bold; text-decoration: none; font-size: 0.85rem; display: inline-block; text-transform: uppercase; }
        .btn-add { background: #ff2a2a; color: #fff; font-weight: bold; padding: 12px 24px; border: 0; border-radius: 4px; cursor: pointer; font-size: 1rem; text-transform: uppercase; }
        .btn-add:hover { background: #d92222; }
    </style>
    <script>
        function openTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
            if(tabId === 'tab_ujcikk' && window.editor) { window.editor.refresh(); }
        }
    </script>
</head>
<body>
    <div class="admin-wrap">
        <div style="background:#0f172a; padding:20px 30px; display:flex; justify-content:space-between; align-items:center; border-bottom:3px solid #ff2a2a; flex-wrap:wrap; gap:15px;">
            <div style="display:flex; align-items:center; gap:20px;">
                <img src="/logo.png.png" style="max-width: 220px; height: auto; display: block;">
                <h2 style="margin:0; color:#ffffff; letter-spacing:1px; font-size:1.4rem; font-weight:900;">ADMIN KÖZPONT</h2>
            </div>
            <div>
                <a href="/magazin/panel/elesites" class="btn-action" style="background:#ff2a2a; font-size:0.95rem; padding:10px 20px; border:1px solid #ff5555;">VÁLTOZTATÁSOK ÉLESÍTÉSE</a>
                <a href="/magazin/logout" style="color:#cbd5e1; margin-left:20px; font-size:0.95rem; text-decoration:none; font-weight:bold; text-transform:uppercase;">Kijelentkezés [X]</a>
            </div>
        </div>
        <div class="tabs-header">
            <button class="tab-btn active" onclick="openTab('tab_lista')">Cikkek Áttekintése</button>
            <button class="tab-btn" onclick="openTab('tab_ujcikk')">Új Cikk Írása (Canva-mód)</button>
            <button class="tab-btn" onclick="openTab('tab_hirdetesek')">Hirdetések (Ajánló)</button>
            <button class="tab-btn" onclick="openTab('tab_elofizetok')">Előfizetők Követése (Stripe)</button>
        </div>
        <div id="tab_lista" class="tab-content active">
            <div style="background: #1e293b; padding: 20px; border: 1px dashed #38bdf8; border-radius: 6px; margin-bottom: 25px;">
                <h4 style="color:#38bdf8; margin-top:0; margin-bottom:10px; text-transform:uppercase;">Fájl feltöltése a saját számítógépedről</h4>
                <form action="/magazin/titkos-admin/upload-file" method="POST" enctype="multipart/form-data" style="display:flex; gap:15px; align-items:center; flex-wrap:wrap;">
                    <input type="file" name="file" required style="background:#0f172a; padding:8px; border:1px solid #475569; border-radius:4px; color:#fff; width:auto;">
                    <button type="submit" class="btn-add" style="padding:10px 20px; font-size:0.9rem;">Fájl Feltöltése ➔</button>
                </form>
            </div>
            <table class="table-cikkek">
                <thead>
                    <tr><th>Cím</th><th>Rovat</th><th>Szerző</th><th>Státusz</th><th>Műveletek</th></tr>
                </thead>
                <tbody>
                    {% for cikk in cikkek %}
                    <tr>
                        <td><strong style="color:#fff;">{{ cikk.title }}</strong></td>
                        <td style="color:#cbd5e1;">{{ rovatok_nevei[cikk.category] }}</td>
                        <td style="color:#cbd5e1;">{{ cikk.author }}</td>
                        <td>{% if cikk.published %}<span style="color:#4ade80; font-weight:bold;">[●] Élesítve</span>{% else %}<span style="color:#fbbf24; font-weight:bold;">[○] Vázlat</span>{% endif %}</td>
                        <td><a href="/magazin/panel/delete/{{ cikk.id }}" class="btn-action" style="background:#ff2a2a;" onclick="return confirm('Biztosan törlöd ezt a cikket?')">Törlés</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <div id="tab_ujcikk" class="tab-content">
            <form method="POST" action="/magazin/panel/add-cikk" onsubmit="syncEditor()">
                <div class="f-group"><label>Cikk Címe</label><input type="text" name="title" required></div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
                    <div class="f-group"><label>Szerző</label><input type="text" name="author" value="Főszerkesztő"></div>
                    <div class="f-group">
                        <label>Rovat</label>
                        <select name="category">
                            {% for k, v in rovatok_nevei.items() %}
                            <option value="{{ k }}">{{ v }}</option>
                            {% endfor %}
                        </select>
                    </div>
                </div>
                <div class="f-group">
                    <div id="gjs"></div>
                    <input type="hidden" name="content" id="hidden_content">
                </div>
                <div class="f-group"><label>Borítókép URL / Feltöltött fájl elérési útja</label><input type="text" name="image"></div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
                    <div class="f-group"><label>YouTube Videó ID (csak az azonosító a beágyazáshoz)</label><input type="text" name="youtube"></div>
                    <div class="f-group"><label>MP3 Hanganyag URL (lejátszóhoz)</label><input type="url" name="mp3"></div>
                </div>
                <button type="submit" class="btn-add" style="width:100%;">Cikk Mentése Vázlatként</button>
            </form>
        </div>
        <div id="tab_hirdetesek" class="tab-content">
            <form method="POST" action="/magazin/panel/add-ad">
                <div class="f-group"><label>Hirdetés Megnevezése</label><input type="text" name="ad_title" required></div>
                <div class="f-group"><label>Hirdetési Banner / Kép URL</label><input type="url" name="ad_image" required></div>
                <div class="f-group"><label>Cél URL (hova vigyen a kattintás)</label><input type="url" name="ad_url" required></div>
                <button type="submit" class="btn-add">Hirdetés Mentése</button>
            </form>
        </div>
        <div id="tab_elofizetok" class="tab-content">
            <table class="table-cikkek">
                <thead><tr><th>E-mail cím</th><th>Státusz</th><th>Stripe Customer ID</th><th>Utolsó sikeres fizetés</th></tr></thead>
                <tbody>
                    {% for email, adat in felhasznalok.items() %}
                    <tr>
                        <td style="color:#fff;">{{ email }}</td>
                        <td>
                            {% if adat.status == 'active' %}
                            <span style="background:#22c55e; color:#000; padding:4px 8px; border-radius:3px; font-weight:bold; font-size:0.8rem; text-transform:uppercase;">Aktív fizető</span>
                            {% else %}
                            <span style="background:#ef4444; color:#fff; padding:4px 8px; border-radius:3px; font-weight:bold; font-size:0.8rem; text-transform:uppercase;">Nem fizető / Lejárt</span>
                            {% endif %}
                        </td>
                        <td style="color:#cbd5e1;">{{ adat.stripe_customer_id }}</td>
                        <td style="color:#cbd5e1;">{{ adat.last_payment }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <script>
        window.onload = function() {
            window.editor = grapesjs.init({
                container: '#gjs', fromElement: true, height: '500px', storageManager: false,
                blockManager: {
                    blocks: [
                        { id: 'section', label: 'Hasáb szakasz', category: 'Elrendezés', content: '<div style="display:flex; padding:20px; gap:20px; background:#FDFBF7;"><div style="flex:1;">Bal hasáb</div><div style="flex:1;">Jobb hasáb</div></div>' },
                        { id: 'text', label: 'Szövegtömb', category: 'Tartalom', content: '<p style="color:#2C2C2C; font-size:1.05rem; line-height:1.8;">Írd ide a bekezdést...</p>' },
                        { id: 'title', label: 'Címsor', category: 'Tartalom', content: '<h2 style="color:#0f172a; font-family:sans-serif;">Címsor szövege</h2>' }
                    ]
                }
            });
        };
        function syncEditor() { document.getElementById('hidden_content').value = window.editor.getHtml(); }
    </script>
</body>
</html>
"""
