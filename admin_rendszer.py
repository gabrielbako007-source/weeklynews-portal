import os
import re
import json
import smtplib
import subprocess
import datetime
import requests
from email.mime.text import MIMEText
from flask import Blueprint, render_template_string, redirect, url_for, request, session
from werkzeug.utils import secure_filename

# ============================================================
# BLUEPRINT + ALAP KONFIG
# ============================================================
admin_bp = Blueprint('admin_bp', __name__, url_prefix='/magazin')

CONFIG_FILE = "twn_config.json"
ADMIN_PASSWORD = "twnadmin2026"
UPLOAD_FOLDER = 'uploads'

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
            "content": "<p>Ez az első minta cikked. A szerkesztőben szerkesztheted, képeket tölthetsz fel, és rovatokba rendezheted a tartalmat.</p>",
            "youtube": "",
            "mp3": "",
            "image": "",
            "published": True
        }
    ],
    "magazin_ads": [],
    "felhasznalok": {}
}


def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
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
        with smtplib.SMTP(os.environ.get("SMTP_SERVER", "mail.infomaniak.com"),
                          int(os.environ.get("SMTP_PORT", 587))) as server:
            server.starttls()
            server.login(os.environ.get("SMTP_USER", "infotwn@etik.com"),
                         os.environ.get("SMTP_PASSWORD", ""))
            server.sendmail(os.environ.get("SMTP_USER", "infotwn@etik.com"), [hova], msg.as_string())
        return True
    except Exception:
        return False


# ============================================================
# INFOMANIAK kDrive WEBDAV
# ============================================================
INFOMANIAK_USER = os.environ.get("INFOMANIAK_USER", "infotwn@etik.com")
INFOMANIAK_PASS = os.environ.get("INFOMANIAK_PASS", "")
KDRIVE_ID = "2469838"
WEBDAV_URL = f"https://{KDRIVE_ID}.connect.kdrive.infomaniak.com"
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'pdf'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def webdav_request(method, remote_path, data=None):
    url = f"{WEBDAV_URL}/{remote_path.lstrip('/')}"
    auth = (INFOMANIAK_USER, INFOMANIAK_PASS)
    if method == "PUT":
        return requests.put(url, data=data, auth=auth)
    if method == "MKCOL":
        return requests.request("MKCOL", url, auth=auth)
    if method == "PROPFIND":
        return requests.request("PROPFIND", url, auth=auth, headers={"Depth": "0"})
    return None


def ensure_remote_folder(remote_folder_path):
    resp = webdav_request("PROPFIND", remote_folder_path)
    if resp is not None and resp.status_code in [200, 207]:
        return True
    parts = remote_folder_path.strip('/').split('/')
    current_path = ""
    for part in parts:
        current_path = f"{current_path}/{part}"
        resp = webdav_request("PROPFIND", current_path)
        if resp is not None and resp.status_code in [200, 207]:
            continue
        resp = webdav_request("MKCOL", current_path)
        if resp is not None and resp.status_code not in [201, 207, 405]:
            print(f"WebDAV hiba mappakészítésnél: {current_path} -> {resp.status_code}")
            return False
    return True


def upload_to_infomaniak_felho(helyi_fajl_ut, felho_fajl_ut):
    remote_folder = os.path.dirname(felho_fajl_ut)
    if not ensure_remote_folder(remote_folder):
        print(f"Nem sikerült létrehozni a mappát: {remote_folder}")
        return False
    try:
        with open(helyi_fajl_ut, 'rb') as f:
            resp = requests.put(f"{WEBDAV_URL}/{felho_fajl_ut.lstrip('/')}",
                                data=f, auth=(INFOMANIAK_USER, INFOMANIAK_PASS))
        return resp.status_code in [201, 204]
    except Exception as e:
        print(f"WebDAV hiba: {e}")
        return False


# ============================================================
# OLVASÓ / SZERKESZTŐ — KÖZÖS SABLON (ugyanaz a kinézet)
# ============================================================
MAGAZIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Weekly News</title>
    <style>
        /* Törtfehér publikálási oldalalap */
        body { font-family:'Arial',sans-serif; margin:0; background:#FDFBF7; color:#1e293b; }
        .wrap { max-width:1200px; margin:0 auto; padding:20px; }
        
        /* Megnövelt, szélesebb sötétkék fejléc a logó kényelmes elhelyezéséhez */
        .header-bg { background:#27313e; border-bottom:3px solid #ff2a2a; padding:14px 0; width:100%; box-sizing: border-box; }
        .header-container { max-width:1400px; margin:0 auto; display:flex; justify-content:space-between; align-items:center; padding:0 30px; flex-wrap:wrap; gap: 20px; }
        
        /* A GitHubon lévő twn_logo.png pontos, fix méretezése */
        .header-logo { max-width:320px; width: 100%; height:auto; display:block; }
        
        /* Rovat-felsorolások a fejléc jobb oldalán */
        .rovat-nav { display:flex; gap:12px; flex-wrap:wrap; align-items: center; }
        .rovat-link { color:#cbd5e1; font-weight:bold; text-decoration:none; text-transform:uppercase; font-size:0.85rem; padding:8px 12px; border-radius:4px; transition:0.2s; }
        .rovat-link:hover { color:#fff; background:#ff2a2a; }
        
        /* Tartalmi elemek stílusai */
        .rovat { margin:50px 0; scroll-margin-top:140px; }
        .rovat-title { font-size:1.6rem; font-weight:900; color:#0f172a; border-bottom:3px solid #ff2a2a; padding-bottom:6px; text-transform:uppercase; }
        .cikk { background:#1e2530; border:1px solid #384556; border-radius:8px; padding:30px; margin:25px 0; box-shadow:0 4px 12px rgba(0,0,0,0.15); }
        .cikk h2 { color:#0f172a; margin-top:0; }
        .cikk .body { color:#334155; line-height:1.8; font-size:1.1rem; }
        .empty { text-align:center; color:#64748b; padding:80px 20px; font-style: italic; }
        .back { display:inline-block; margin:15px 5px; background:#0f172a; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold; text-transform:uppercase; font-size:0.85rem; }
        .edit-bar { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:15px; background:#f1f5f9; padding:10px; border-radius:6px; }
        .edit-bar input, .edit-bar select { padding:8px; background:#fff; color:#000; border:1px solid #cbd5e1; border-radius:4px; }
        .body[contenteditable] { outline:2px dashed #38bdf8; padding:15px; border-radius:4px; background:#fff; color:#000; }
        .btn-save { background:#22c55e; color:#fff; border:0; padding:8px 16px; border-radius:4px; font-weight:bold; cursor:pointer; text-transform:uppercase; }
    </style>
</head>
<body>
    <!-- Szélesített sötétkék fejrész a bal oldali grafikus logóval és a felsorolásokkal -->
    <div class="header-bg">
        <div class="header-container">
            <a href="/"><img src="/twn_logo.png" class="header-logo" alt="THE WEEKLY TWN NEWS"></a>
            <div class="rovat-nav">
                <a href="#news" class="rovat-link">News</a>
                <a href="#hit_csalad_erkolcs" class="rovat-link">Hit, Család & Erkölcs</a>
                <a href="#egeszseg" class="rovat-link">Egészség</a>
                <a href="#media" class="rovat-link">Média (Video & Podcast)</a>
                <a href="#tech_tudomany" class="rovat-link">Tech-Tudomány</a>
                <a href="#ajanlo_hirdetes" class="rovat-link">Ajánló & Hirdetés</a>
            </div>
        </div>
    </div>
    <div class="wrap">
        <div style="margin-top:10px;">
            <a href="/" class="back">⬅ Vissza a hírportálra</a>
        {% if mod == 'szerk' %}
            <a href="/magazin/panel" class="back" style="background:#38bdf8;color:#000;">Admin / Vázlatok</a>
            <a href="/magazin/import-pdf" class="back" style="background:#a855f7;">PDF import</a>
            <a href="/magazin/panel/elesites" class="back" style="background:#fbbf24;color:#000;">Élesítés</a>
        {% endif %}

        {% if not cikkek %}
            <div class="empty"><h3>Még nincs publikált tartalom.</h3></div>
        {% endif %}

        {% for rovat_kulcs, rovat_nev in rovatok.items() %}
            {% set rovat_cikkek = cikkek | selectattr("category", "equalto", rovat_kulcs) | list %}
            {% if rovat_cikkek %}
            <div class="rovat">
                <div class="rovat-title">{{ rovat_nev }}</div>
                {% for cikk in rovat_cikkek %}
                <div class="cikk">
                    {% if mod == 'szerk' %}
                    <form method="POST" action="/magazin/panel/save/{{ cikk.id }}" onsubmit="sync(this)">
                        <div class="edit-bar">
                            <input name="title" value="{{ cikk.title }}" style="flex:2;min-width:200px;">
                            <select name="category">
                                {% for k, v in rovatok.items() %}
                                <option value="{{ k }}" {% if k == cikk.category %}selected{% endif %}>{{ v }}</option>
                                {% endfor %}
                            </select>
                            <input name="image" placeholder="Borító kép URL" value="{{ cikk.image }}" style="flex:1;min-width:140px;">
                            <button class="btn-save" type="submit">Mentés</button>
                        </div>
                        <div class="body" contenteditable="true">{{ cikk.content | safe }}</div>
                        <input type="hidden" name="content">
                    </form>
                    {% else %}
                    <h2>{{ cikk.title }}</h2>
                    <div class="meta">{{ cikk.author }} - {{ cikk.read_time }}</div>
                    {% if cikk.image %}<img src="{{ cikk.image }}" class="borito">{% endif %}
                    {% if cikk.youtube %}
                        <div class="video-container"><iframe src="https://www.youtube.com/embed/{{ cikk.youtube }}" allowfullscreen></iframe></div>
                    {% endif %}
                    {% if cikk.mp3 %}<audio controls src="{{ cikk.mp3 }}" style="width:100%;margin:12px 0;"></audio>{% endif %}
                    <div class="body">{{ cikk.content | safe }}</div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% endif %}
        {% endfor %}
    </div>
    <script>
        function sync(form){ form.querySelector('input[name=content]').value = form.querySelector('.body').innerHTML; }
    </script>
</body>
</html>
"""


# ============================================================
# ADMIN PANEL SABLON (GrapesJS Canva-mód + feltöltés)
# ============================================================
ADMIN_PANEL_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly News - Admin Központ</title>
    <link rel="stylesheet" href="https://unpkg.com/grapesjs/dist/css/grapes.min.css">
    <script src="https://unpkg.com/grapesjs"></script>
    <style>
        body { font-family: 'Arial', sans-serif; background: #1e293b; color: #fff; padding: 0; margin: 0; }
        .admin-wrap { max-width: 1400px; margin: 30px auto; background: #0f172a; border-radius: 8px; border: 1px solid #475569; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .tabs-header { display: flex; background: #0f172a; border-bottom: 2px solid #ff2a2a; flex-wrap: wrap; }
        .tab-btn { background: none; border: 0; color: #cbd5e1; padding: 15px 25px; font-weight: bold; cursor: pointer; font-size: 0.95rem; text-transform: uppercase; }
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
            <h2 style="margin:0; color:#ffffff; letter-spacing:1px; font-size:1.4rem; font-weight:900;">ADMIN KÖZPONT</h2>
            <div>
                <a href="/magazin/szerkeszto" class="btn-action" style="background:#38bdf8;color:#000;">Vizuális szerkesztő</a>
                <a href="/magazin/panel/elesites" class="btn-action" style="background:#ff2a2a;">Változtatások élesítése</a>
                <a href="/magazin/logout" style="color:#cbd5e1; margin-left:20px; font-size:0.95rem; text-decoration:none; font-weight:bold; text-transform:uppercase;">Kijelentkezés</a>
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
                    <button type="submit" class="btn-add" style="padding:10px 20px; font-size:0.9rem;">Fájl Feltöltése</button>
                </form>
            </div>
            <table class="table-cikkek">
                <thead><tr><th>Cím</th><th>Rovat</th><th>Szerző</th><th>Státusz</th><th>Műveletek</th></tr></thead>
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
                    <div class="f-group"><label>Rovat</label>
                        <select name="category">{% for k, v in rovatok_nevei.items() %}<option value="{{ k }}">{{ v }}</option>{% endfor %}</select>
                    </div>
                </div>
                <div class="f-group"><div id="gjs"></div><input type="hidden" name="content" id="hidden_content"></div>
                <div class="f-group"><label>Borítókép URL</label><input type="text" name="image"></div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
                    <div class="f-group"><label>YouTube Videó ID</label><input type="text" name="youtube"></div>
                    <div class="f-group"><label>MP3 Hanganyag URL</label><input type="url" name="mp3"></div>
                </div>
                <button type="submit" class="btn-add" style="width:100%;">Cikk Mentése Vázlatként</button>
            </form>
        </div>
        <div id="tab_hirdetesek" class="tab-content">
            <form method="POST" action="/magazin/panel/add-ad">
                <div class="f-group"><label>Hirdetés Megnevezése</label><input type="text" name="ad_title" required></div>
                <div class="f-group"><label>Hirdetési Banner / Kép URL</label><input type="url" name="ad_image" required></div>
                <div class="f-group"><label>Cél URL</label><input type="url" name="ad_url" required></div>
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
                        <td>{% if adat.status == 'active' %}<span style="background:#22c55e;color:#000;padding:4px 8px;border-radius:3px;font-weight:bold;font-size:0.8rem;">Aktív fizető</span>{% else %}<span style="background:#ef4444;color:#fff;padding:4px 8px;border-radius:3px;font-weight:bold;font-size:0.8rem;">Nem fizető / Lejárt</span>{% endif %}</td>
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
                blockManager: { blocks: [
                    { id: 'section', label: 'Hasáb szakasz', category: 'Elrendezés', content: '<div style="display:flex; padding:20px; gap:20px; background:#FDFBF7;"><div style="flex:1;">Bal hasáb</div><div style="flex:1;">Jobb hasáb</div></div>' },
                    { id: 'text', label: 'Szövegtömb', category: 'Tartalom', content: '<p style="color:#2C2C2C; font-size:1.05rem; line-height:1.8;">Írd ide a bekezdést...</p>' },
                    { id: 'title', label: 'Címsor', category: 'Tartalom', content: '<h2 style="color:#0f172a; font-family:sans-serif;">Címsor szövege</h2>' }
                ] }
            });
        };
        function syncEditor() { document.getElementById('hidden_content').value = window.editor.getHtml(); }
    </script>
</body>
</html>
"""


# ============================================================
# ÚTVONALAK — BELÉPÉS
# ============================================================
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if session.get("magazin_logged_in"):
        return redirect(url_for('admin_bp.admin_panel'))
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["magazin_logged_in"] = True
            return redirect(url_for('admin_bp.admin_panel'))
        return '<h3 style="font-family:sans-serif;color:#ff2a2a;">Hibás jelszó! <a href="/magazin/login">Újra</a></h3>'
    return '''
    <body style="font-family:sans-serif; background:#0f172a; color:#fff; text-align:center; padding-top:100px;">
        <form method="POST" style="background:#1e293b; display:inline-block; padding:30px; border-radius:8px; border:1px solid #475569;">
            <label style="display:block; margin-bottom:10px;">Szerkesztői Jelszó:</label>
            <input type="password" name="password" style="padding:8px; background:#0f172a; color:#fff; border:1px solid #475569;"><br><br>
            <button type="submit" style="background:#ff2a2a; color:#fff; border:0; padding:8px 15px; border-radius:4px; cursor:pointer;">Belépés</button>
        </form>
    </body>
    '''


@admin_bp.route('/logout')
def admin_logout():
    session["magazin_logged_in"] = False
    return redirect(url_for('admin_bp.admin_panel'))


# ============================================================
# ÚTVONALAK — ADMIN PANEL
# ============================================================
@admin_bp.route('/panel')
def admin_panel():
    if not session.get("magazin_logged_in"):
        return redirect(url_for('admin_bp.admin_login'))
    cfg = load_config()
    return render_template_string(
        ADMIN_PANEL_TEMPLATE,
        cikkek=cfg.get("magazin_cikkek", []),
        rovatok_nevei=ROVATOK_MAP,
        felhasznalok=cfg.get("felhasznalok", {})
    )


@admin_bp.route('/panel/add-cikk', methods=['POST'])
def admin_add_cikk():
    if not session.get("magazin_logged_in"):
        return "Letiltva", 403
    cfg = load_config()
    uj_id = max([c["id"] for c in cfg["magazin_cikkek"]], default=0) + 1
    cfg["magazin_cikkek"].append({
        "id": uj_id,
        "title": request.form.get("title", "Névtelen cikk"),
        "category": request.form.get("category", "news"),
        "author": request.form.get("author", "Ismeretlen"),
        "read_time": "1 perc",
        "content": request.form.get("content", ""),
        "youtube": request.form.get("youtube", ""),
        "mp3": request.form.get("mp3", ""),
        "image": request.form.get("image", ""),
        "published": False
    })
    save_config(cfg)
    return redirect(url_for('admin_bp.admin_panel'))


@admin_bp.route('/panel/delete/<int:cikk_id>')
def admin_delete_cikk(cikk_id):
    if not session.get("magazin_logged_in"):
        return "Letiltva", 403
    cfg = load_config()
    cfg["magazin_cikkek"] = [c for c in cfg["magazin_cikkek"] if c["id"] != cikk_id]
    save_config(cfg)
    return redirect(url_for('admin_bp.admin_panel'))


@admin_bp.route('/panel/add-ad', methods=['POST'])
def admin_add_ad():
    if not session.get("magazin_logged_in"):
        return "Letiltva", 403
    cfg = load_config()
    cfg.setdefault("magazin_ads", []).append({
        "title": request.form.get("ad_title", ""),
        "image": request.form.get("ad_image", ""),
        "url": request.form.get("ad_url", "")
    })
    save_config(cfg)
    return redirect(url_for('admin_bp.admin_panel'))


@admin_bp.route('/panel/elesites')
def admin_elesites():
    if not session.get("magazin_logged_in"):
        return "Letiltva", 403
    cfg = load_config()
    for cikk in cfg["magazin_cikkek"]:
        cikk["published"] = True
    save_config(cfg)
    return '''
    <body style="font-family:sans-serif; background:#0f172a; color:#fff; text-align:center; padding-top:100px;">
        <h3 style="color:#4ade80;">Összes változtatás élesítve!</h3>
        <a href="/magazin/panel" style="background:#ff2a2a; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold;">Vissza a pultra</a>
    </body>
    '''


@admin_bp.route('/panel/save/<int:cikk_id>', methods=['POST'])
def panel_save(cikk_id):
    if not session.get("magazin_logged_in"):
        return "Letiltva", 403
    cfg = load_config()
    for cikk in cfg["magazin_cikkek"]:
        if cikk["id"] == cikk_id:
            cikk["title"] = request.form.get("title", cikk["title"])
            cikk["category"] = request.form.get("category", cikk["category"])
            cikk["image"] = request.form.get("image", cikk["image"])
            cikk["content"] = request.form.get("content", cikk["content"])
            break
    save_config(cfg)
    return redirect(url_for('admin_bp.szerkeszto'))


# ============================================================
# ÚTVONALAK — OLVASÓ + VIZUÁLIS SZERKESZTŐ
# ============================================================
@admin_bp.route('/')
def olvaso():
    cfg = load_config()
    publikaltak = [c for c in cfg.get("magazin_cikkek", []) if c.get("published")]
    return render_template_string(MAGAZIN_TEMPLATE, cikkek=publikaltak, rovatok=ROVATOK_MAP, mod='olvaso')


@admin_bp.route('/szerkeszto')
def szerkeszto():
    if not session.get("magazin_logged_in"):
        return redirect(url_for('admin_bp.admin_login'))
    cfg = load_config()
    return render_template_string(MAGAZIN_TEMPLATE, cikkek=cfg.get("magazin_cikkek", []), rovatok=ROVATOK_MAP, mod='szerk')


# ============================================================
# ÚTVONAL — FÁJLFELTÖLTÉS A KDRIVE-BA (WebDAV)
# ============================================================
@admin_bp.route('/titkos-admin/upload-file', methods=['POST'])
def admin_upload_file():
    if not session.get("magazin_logged_in"):
        return "Letiltva", 403
    if 'file' not in request.files:
        return "Nincs fájl a kérésben", 400
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return "Nincs kiválasztott fájl", 400
    if not allowed_file(uploaded_file.filename):
        return "Nem támogatott fájlformátum! Csak .jpg, .jpeg vagy .pdf tölthető fel.", 400

    filename = secure_filename(uploaded_file.filename)
    mai_datum = datetime.datetime.now()
    idokiiratas = mai_datum.strftime('%Y-%m')
    het_szama = mai_datum.isocalendar()[1]

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    vegleges_fajlnev = mai_datum.strftime('%H%M%S_') + filename
    helyi_fajl_ut = os.path.join(UPLOAD_FOLDER, vegleges_fajlnev)
    uploaded_file.save(helyi_fajl_ut)

    felho_fajl_ut = f"archivum/{idokiiratas}/{het_szama}_het/{vegleges_fajlnev}"
    sikeres = upload_to_infomaniak_felho(helyi_fajl_ut, felho_fajl_ut)

    if os.path.exists(helyi_fajl_ut):
        os.remove(helyi_fajl_ut)

    if not sikeres:
        return '''
        <body style="font-family:sans-serif; background:#0f172a; color:#fff; text-align:center; padding:40px;">
            <h3 style="color:#ff2a2a;">HIBA A FELTÖLTÉSNÉL!</h3>
            <p>Ellenőrizd a kDrive ID-t és az alkalmazási jelszót.</p>
            <a href="/magazin/panel" style="background:#ff2a2a; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold;">Vissza a pultra</a>
        </body>
        ''', 500

    return f'''
    <body style="font-family:sans-serif; background:#0f172a; color:#fff; text-align:center; padding-top:100px;">
        <h3 style="color:#38bdf8;">Sikeres feltöltés a kDrive-ba!</h3>
        <p>Mentési hely: <b>{idokiiratas} / {het_szama}. hét</b></p>
        <p>Fájl: <b>{vegleges_fajlnev}</b></p>
        <br><a href="/magazin/panel" style="background:#ff2a2a; color:#fff; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold; text-transform:uppercase;">Vissza a pultra</a>
    </body>
    '''


# ============================================================
# ÚTVONAL — PDF MOTOR (PDF -> Word -> HTML -> szerkeszthető cikk)
# ============================================================
@admin_bp.route('/import-pdf')
def import_pdf_form():
    if not session.get("magazin_logged_in"):
        return "Letiltva", 403
    return '''
    <body style="font-family:sans-serif;background:#0f172a;color:#fff;text-align:center;padding-top:80px;">
      <form method="POST" action="/magazin/import-pdf" enctype="multipart/form-data"
            style="background:#1e293b;display:inline-block;padding:30px;border-radius:8px;border:1px solid #475569;">
        <p>Válassz PDF-et — a motor átalakítja szerkeszthető cikké (elrendezéssel, képekkel):</p>
        <input type="file" name="file" accept="application/pdf" required>
        <br><br><button type="submit" style="background:#a855f7;color:#fff;border:0;padding:8px 16px;border-radius:4px;">Importálás</button>
      </form>
      <br><a href="/magazin/szerkeszto" style="color:#38bdf8;">Vissza a szerkesztőbe</a>
    </body>
    '''


@admin_bp.route('/import-pdf', methods=['POST'])
def import_pdf_do():
    if not session.get("magazin_logged_in"):
        return "Letiltva", 403
    f = request.files.get('file')
    if not f or f.filename == '':
        return "Nincs fájl", 400
    if not allowed_file(f.filename):
        return "Csak PDF tölthető fel!", 400

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    pdf_ut = os.path.join(UPLOAD_FOLDER, secure_filename(f.filename))
    f.save(pdf_ut)

    try:
        from pdf2docx import Converter
        docx_ut = pdf_ut.rsplit('.', 1)[0] + ".docx"
        cv = Converter(pdf_ut)
        cv.convert(docx_ut)
        cv.close()
    except Exception as e:
        return f"PDF átalakítási hiba: {e}", 500

    try:
        import mammoth
        with open(docx_ut, "rb") as fh:
            html = mammoth.convert_to_html(fh).value
    except Exception as e:
        html = f"<p>[A Word-fájl HTML-lé alakítása nem sikerült: {e}]</p>"

    cfg = load_config()
    uj_id = max([c["id"] for c in cfg["magazin_cikkek"]], default=0) + 1
    cfg["magazin_cikkek"].append({
        "id": uj_id,
        "title": f"Importált: {secure_filename(f.filename)}",
        "category": "news",
        "author": "PDF import",
        "read_time": "1 perc",
        "content": html,
       "youtube": "",
        "mp3": "",
        "image": "",
        "published": False
    })
    save_config(cfg)

    # Ideiglenes fájlok takarítása a Renderről
    for ut in (pdf_ut, docx_ut):
        if os.path.exists(ut):
            os.remove(ut)

    return redirect(url_for('admin_bp.szerkeszto'))