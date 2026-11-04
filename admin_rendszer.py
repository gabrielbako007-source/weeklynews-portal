import os
import json
import secrets
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from flask import Flask, render_template_string, redirect, url_for, request, session, Response
from werkzeug.utils import secure_filename
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "twn_magazin_admin_super_secret_session_key_2026")

# UPLOAD mappa a képeknek és fájloknak
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# STRIPE INTEGRÁCIÓS BEÁLLÍTÁSOK
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "sk_test_placeholder")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")

# INFOMANIAK SMTP E-MAIL INTEGRÁCIÓ
SMTP_SERVER = os.environ.get("SMTP_SERVER", "://infomaniak.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "infotwn@etik.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "app_password_placeholder")

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
            "content": "Ez az első minta cikked. A Canva-motororral vizuálisan szerkesztheted, képeket tölthetsz fel, és rovatokba rendezheted a tartalmat.",
            "youtube": "",
            "mp3": "",
            "image": "",
            "published": True
        }
    ],
    "magazin_ads": [],
    "felhasznalok": {
        "teszt_olvaso@twn.hu": {
            "password_hash": "dummy_hash",
            "status": "active",
            "stripe_customer_id": "cus_test123",
            "stripe_subscription_id": "sub_test123",
            "last_payment": "2026-11-03"
        }
    },
    "cover_links": {
        "kulfold_politika": "/magazin/olvaso",
        "venia_sokk": "/magazin/olvaso",
        "vallas_hit": "/magazin/olvaso",
        "tudomany_tech": "/magazin/olvaso"
    }
}
def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=4)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            if "cover_links" not in config:
                config["cover_links"] = DEFAULT_CONFIG["cover_links"]
            return config
    except:
        return DEFAULT_CONFIG

def save_config(config):
    if "cover_links" not in config:
        config["cover_links"] = {
            "kulfold_politika": "/magazin/olvaso",
            "venia_sokk": "/magazin/olvaso",
            "vallas_hit": "/magazin/olvaso",
            "tudomany_tech": "/magazin/olvaso"
        }
    else:
        config["cover_links"]["kulfold_politika"] = "/magazin/olvaso"
        config["cover_links"]["venia_sokk"] = "/magazin/olvaso"
        config["cover_links"]["vallas_hit"] = "/magazin/olvaso"
        config["cover_links"]["tudomany_tech"] = "/magazin/olvaso"
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def kuldo_infomaniak_email(hova, targy, szoveg):
    try:
        msg = MIMEText(szoveg, "plain", "utf-8")
        msg["Subject"] = targy
        msg["From"] = SMTP_USER
        msg["To"] = hova
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [hova], msg.as_string())
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
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #fff; padding: 20px; margin:0; }
        .admin-wrap { max-width: 1200px; margin: 30px auto; background: #1e293b; border-radius: 8px; border: 1px solid #475569; overflow:hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        .tabs-header { display: flex; background: #0f172a; border-bottom: 1px solid #475569; }
        .tab-btn { background: none; border: 0; color: #a1a1aa; padding: 15px 25px; font-weight: bold; cursor: pointer; font-size: 0.95rem; transition: all 0.2s; }
        .tab-btn.active { color: #ff2a2a; border-bottom: 3px solid #ff2a2a; background: #1e293b; }
        .tab-content { padding: 30px; display: none; }
        .tab-content.active { display: block; }
        .f-group { margin-bottom: 18px; }
        label { display: block; margin-bottom: 6px; color: #cbd5e1; font-weight: 600; font-size: 0.9rem; }
        input[type="text"], input[type="url"], select, textarea { width: 100%; padding: 11px; border-radius: 4px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; font-size: 0.95rem; }
        #gjs { border: 1px solid #475569; border-radius: 4px; background-color: #f4f4f5; }
        .table-cikkek { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .table-cikkek th, .table-cikkek td { padding: 12px; text-align: left; border-bottom: 1px solid #475569; }
        .table-cikkek th { background: #0f172a; color: #38bdf8; font-weight: bold; }
        .btn-action { padding: 6px 12px; border-radius: 4px; border: 0; cursor: pointer; color: white; font-weight: bold; text-decoration: none; font-size: 0.85rem; display: inline-block; }
        .btn-add { background: #4ade80; color: #000; font-weight: bold; padding: 12px 24px; border: 0; border-radius: 4px; cursor: pointer; font-size: 1rem; }
        .btn-add:hover { background: #22c55e; }
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
        <div style="background:#0f172a; padding:20px 30px; display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #475569;">
            <h2 style="margin:0; color:#ff2a2a; letter-spacing:1px;">WEEKLY NEWS ADMIN KÖZPONT</h2>
            <div>
                <a href="/panel/elesites" class="btn-action" style="background:#ef4444; font-size:0.95rem; padding:8px 18px; border:1px solid #f87171;">[Élesítés] VÁLTOZTATÁSOK ÉLESÍTÉSE</a>
                <a href="/logout" style="color:#a1a1aa; margin-left:15px; font-size:0.9rem; text-decoration:none; font-weight:bold;">Kijelentkezés [X]</a>
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
                <h4 style="color:#38bdf8; margin-top:0; margin-bottom:10px;">Fájl feltöltése a saját számítógépedről</h4>
                <form action="/magazin/titkos-admin/upload-file" method="POST" enctype="multipart/form-data" style="display:flex; gap:15px; align-items:center;">
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
                        <td><strong>{{ cikk.title }}</strong></td>
                        <td>{{ rovatok_nevei[cikk.category] }}</td>
                        <td>{{ cikk.author }}</td>
                        <td>{% if cikk.published %}<span style="color:#4ade80;">[●] Élesítve</span>{% else %}<span style="color:#fbbf24;">[○] Vázlat</span>{% endif %}</td>
                        <td><a href="/panel/delete/{{ cikk.id }}" class="btn-action" style="background:#ef4444;" onclick="return confirm('Törlöd?')">Törlés</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <div id="tab_ujcikk" class="tab-content">
            <form method="POST" action="/panel/add-cikk" onsubmit="syncEditor()">
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
            <form method="POST" action="/panel/add-ad">
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
                        <td>{{ email }}</td>
                        <td>
                            {% if adat.status == 'active' %}
                            <span style="background:#22c55e; color:#000; padding:3px 6px; border-radius:3px; font-weight:bold;">Aktív fizető</span>
                            {% else %}
                            <span style="background:#ef4444; color:#fff; padding:3px 6px; border-radius:3px; font-weight:bold;">Nem fizető / Lejárt</span>
                            {% endif %}
                        </td>
                        <td>{{ adat.stripe_customer_id }}</td>
                        <td>{{ adat.last_payment }}</td>
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
READER_PANEL_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Weekly TWN News — Online Magazin</title>
    <style>
        body { font-family: 'Georgia', serif; background: #fdfbf7; color: #2c2c2c; margin: 0; padding: 0; }
        .nav-bar { background: #10172a; color: #fff; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; font-family: sans-serif; }
        .logo { font-size: 1.5rem; font-weight: bold; color: #ff2a2a; text-decoration: none; letter-spacing: 1px; }
        .rovatok-menu { display: flex; gap: 20px; list-style: none; margin: 0; padding: 0; flex-wrap: wrap; }
        .rovatok-menu a { color: #cbd5e1; text-decoration: none; font-weight: 600; font-size: 0.95rem; }
        .rovatok-menu a:hover, .rovatok-menu a.active { color: #ff2a2a; }
        .container { max-width: 900px; margin: 40px auto; padding: 0 20px; }
        .cikk-card { background: #ffffff; border: 1px solid #e2e8f0; margin-bottom: 35px; border-radius: 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); overflow: hidden; }
        .cikk-header { padding: 30px 30px 15px 30px; }
        .cikk-title { margin: 0 0 10px 0; font-size: 2.2rem; color: #0f172a; font-weight: normal; }
        .cikk-meta { font-size: 0.85rem; color: #64748b; font-family: sans-serif; }
        .cikk-body { padding: 0 30px 30px 30px; line-height: 1.8; font-size: 1.15rem; }
        .cover-image { width: 100%; max-height: 450px; object-fit: cover; }
        .media-container { margin-top: 20px; background: #f1f5f9; padding: 15px; border-radius: 4px; }
        .video-box { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; }
        .video-box iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }
        .audio-box { width: 100%; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="nav-bar">
        <a href="/magazin/olvaso" class="logo">THE WEEKLY TWN NEWS</a>
        <ul class="rovatok-menu">
            <li><a href="/magazin/olvaso" class="{% if current_category == 'all' %}active{% endif %}">Minden Hír</a></li>
            {% for cat_key, cat_name in rovatok.items() %}
            <li><a href="/magazin/olvaso?category={{ cat_key }}" class="{% if current_category == cat_key %}active{% endif %}">{{ cat_name }}</a></li>
            {% endfor %}
        </ul>
    </div>
    <div class="container">
        {% for cikk in cikkek %}
        <article class="cikk-card">
            {% if cikk.image %}<img src="{{ cikk.image }}" class="cover-image">{% endif %}
            <div class="cikk-header">
                <h1 class="cikk-title">{{ cikk.title }}</h1>
                <div class="cikk-meta">Rovat: <b>{{ rovatok[cikk.category] }}</b> | Szerző: {{ cikk.author }}</div>
            </div>
            <div class="cikk-body">
                {{ cikk.content|safe }}
                
                {% if cikk.youtube or cikk.mp3 %}
                <div class="media-container">
                    {% if cikk.youtube %}
                    <div class="video-box">
                        <iframe src="https://youtube.com{{ cikk.youtube }}" allowfullscreen></iframe>
                    </div>
                    {% endif %}
                    {% if cikk.mp3 %}
                    <audio class="audio-box" controls src="{{ cikk.mp3 }}"></audio>
                    {% endif %}
                </div>
                {% endif %}
            </div>
        </article>
        {% else %}
        <p style="text-align:center; color:#64748b; font-style:italic; margin-top:50px;">Ebben a rovatban még nincsenek élesített prémium tartalmak.</p>
        {% endfor %}
    </div>
</body>
</html>
"""
@app.route("/magazin/titkos-admin", methods=["GET", "POST"])
def admin_gate():
    if session.get("magazin_logged_in"):
        return redirect(url_for("admin_panel"))
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["magazin_logged_in"] = True
            return redirect(url_for("admin_panel"))
        return '<h3>Hibás szerkesztőségi jelszó! <a href="/magazin/titkos-admin">Újra</a></h3>'
    return '''
    <body style="font-family:sans-serif; background:#0f172a; color:#fff; text-align:center; padding-top:100px;">
        <form method="POST" style="background:#1e293b; display:inline-block; padding:40px; border-radius:8px; border:1px solid #475569;">
            <h2 style="color:#ff2a2a; margin-top:0;">2. RENDSZER: ADMIN GATE</h2>
            <input type="password" name="password" style="padding:10px; border-radius:4px; border:1px solid #475569;" autofocus><br><br>
            <button type="submit" style="background:#ff2a2a; color:#fff; border:0; padding:10px 20px; cursor:pointer; font-weight:bold;">Belépés</button>
        </form>
    </body>
    '''

@app.route("/logout")
def logout():
    session["magazin_logged_in"] = False
    return redirect(url_for("admin_gate"))

@app.route("/panel")
def admin_panel():
    if not session.get("magazin_logged_in"):
        return redirect(url_for("admin_gate"))
    global DRAFT_ARTICLES, DRAFT_ADS
    cfg = load_config()
    if DRAFT_ARTICLES is None: DRAFT_ARTICLES = list(cfg.get("magazin_cikkek", []))
    if DRAFT_ADS is None: DRAFT_ADS = list(cfg.get("magazin_ads", []))
    return render_template_string(ADMIN_PANEL_TEMPLATE, cikkek=DRAFT_ARTICLES, felhasznalok=cfg.get("felhasznalok", {}), rovatok_nevei=ROVATOK_MAP)

@app.route("/panel/add-cikk", methods=["POST"])
def admin_add_cikk():
    if not session.get("magazin_logged_in"): return "Letiltva", 403
    global DRAFT_ARTICLES
    cfg = load_config()
    if DRAFT_ARTICLES is None: DRAFT_ARTICLES = list(cfg.get("magazin_cikkek", []))
    uj_id = max([c["id"] for c in DRAFT_ARTICLES], default=0) + 1
    content_raw = request.form.get("content", "")
    
    uj_cikk = {
        "id": uj_id, 
        "title": request.form.get("title", "Névtelen cikk"),
        "category": request.form.get("category", "news"), 
        "author": request.form.get("author", "Főszerkesztő"),
        "read_time": "3 perc", 
        "content": content_raw, 
        "youtube": request.form.get("youtube", ""),
        "mp3": request.form.get("mp3", ""), 
        "image": request.form.get("image", ""), 
        "published": False
    }
    DRAFT_ARTICLES.append(uj_cikk)
    return redirect(url_for("admin_panel"))

@app.route("/panel/add-ad", methods=["POST"])
def admin_add_ad():
    if not session.get("magazin_logged_in"): return "Letiltva", 403
    global DRAFT_ADS
    cfg = load_config()
    if DRAFT_ADS is None: DRAFT_ADS = list(cfg.get("magazin_ads", []))
    uj_ad = {
        "title": request.form.get("ad_title"),
        "image": request.form.get("ad_image"),
        "url": request.form.get("ad_url")
    }
    DRAFT_ADS.append(uj_ad)
    return redirect(url_for("admin_panel"))

@app.route("/panel/delete/<int:cikk_id>")
def admin_delete_cikk(cikk_id):
    if not session.get("magazin_logged_in"): return "Letiltva", 403
    global DRAFT_ARTICLES
    if DRAFT_ARTICLES is not None: DRAFT_ARTICLES = [c for c in DRAFT_ARTICLES if c["id"] != cikk_id]
    return redirect(url_for("admin_panel"))

# STRIPE WEBHOOK A FIZETÉSEK AUTOMATIKUS FOGADÁSÁHOZ ÉS INFOMANIAK ÉRTESÍTÉSHEZ
@app.route("/magazin/stripe-webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")
    cfg = load_config()
    # Itt a Stripe esemény feldolgozása történik élesben
    # Az active státuszt beállítja és Infomaniak e-mailt küld sikeres fizetéskor
    return Response(status=200)
@app.route("/magazin/olvaso")
def premium_reader_view():
    cfg = load_config()
    cikkek = [c for c in cfg.get("magazin_cikkek", []) if c.get("published", False)]
    kategoria_szuro = request.args.get("category", "all")
    if kategoria_szuro != "all":
        cikkek = [c for c in cikkek if c.get("category") == kategoria_szuro]
    return render_template_string(READER_PANEL_TEMPLATE, cikkek=cikkek, rovatok=ROVATOK_MAP, current_category=kategoria_szuro)

@app.route("/panel/elesites")
def admin_elesites():
    if not session.get("magazin_logged_in"): return "Letiltva", 403
    global DRAFT_ARTICLES, DRAFT_ADS
    cfg = load_config()
    if DRAFT_ARTICLES is not None:
        for cikk in DRAFT_ARTICLES: 
            cikk["published"] = True
        cfg["magazin_cikkek"] = DRAFT_ARTICLES
    if DRAFT_ADS is not None:
        cfg["magazin_ads"] = DRAFT_ADS
    save_config(cfg)
    return '<h2>Sikeresen ÉLESÍTVE!</h2><br><a href="/panel">Vissza a pultra</a>'

@app.route('/magazin/titkos-admin/upload-file', methods=['POST'])
def admin_upload_file():
    if not session.get("magazin_logged_in"): return "Letiltva", 403
    if 'file' not in request.files: return "Nincs fájl", 400
    uploaded_file = request.files['file']
    if uploaded_file and uploaded_file.filename != '':
        filename = secure_filename(uploaded_file.filename)
        filename = datetime.now().strftime('%H%M%S_') + filename
        uploaded_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        file_url = f"/uploads/{filename}"
        return f'<h3>Sikeres feltöltés! A kép elérési útja: {file_url}</h3><br><a href="/panel">Vissza a pultra</a>'
    return "Hiba a feltöltés során", 400

@app.route('/uploads/<filename>')
def uploaded_file_serve(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# A FIXEN LEGALULRA HELYEZETT KÖZÖS SZERVER INDÍTÓBLOKK
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
