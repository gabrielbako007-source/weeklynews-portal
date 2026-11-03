import os
import json
import secrets
from datetime import datetime
from flask import Flask, render_template_string, redirect, url_for, request, session, Response

app = Flask(__name__)

app.secret_key = os.environ.get("FLASK_SECRET_KEY", "twn_magazin_admin_super_secret_session_key_2026")

CONFIG_FILE = "twn_config.json"
ADMIN_PASSWORD = "twnadmin2026"

STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "sk_test_placeholder")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_placeholder")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "://etik.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER = os.environ.get("SMTP_USER", "infotwn@etik.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "app_password_placeholder")

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
            "category": "news",
            "author": "Főszerkesztő",
            "read_time": "1 perc",
            "content": "Ez az első minta cikked. A Canva-motorral vizuálisan szerkesztheted, képeket tölthetsz fel, és rovatokba rendezheted a tartalmat.",
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

DRAFT_ARTICLES = None
DRAFT_ADS = None



# ================= VEZÉRLŐPULT HTML SABLONJA (1. RÉSZ) =================
ADMIN_PANEL_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weekly News Szerkesztőség — Canva & Stripe Központ</title>
    
    <!-- GrapesJS Grafikai Motor CDN linkek -->
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
        .gjs-one-bg { background-color: #1e293b !important; }
        .gjs-two-color { color: #cbd5e1 !important; }
        .gjs-three-bg { background-color: #ff2a2a !important; }
        .table-cikkek { width: 100%; border-collapse: collapse; margin-top: 15px; }
        .table-cikkek th, .table-cikkek td { padding: 12px; text-align: left; border-bottom: 1px solid #475569; }
        .table-cikkek th { background: #0f172a; color: #38bdf8; font-weight: bold; }
        .btn-action { padding: 6px 12px; border-radius: 4px; border: 0; cursor: pointer; color: white; font-weight: bold; text-decoration: none; font-size: 0.85rem; display: inline-block; }
        .btn-add { background: #4ade80; color: #000; font-weight: bold; padding: 12px 24px; border: 0; border-radius: 4px; cursor: pointer; font-size: 1rem; }
        .btn-add:hover { background: #22c55e; }
        .status-badge { padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8rem; }
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
            <div style="display:flex; align-items:center; gap:15px;">
                <h2 style="margin:0; color:#ff2a2a; letter-spacing:1px;">WEEKLY NEWS ADMIN KÖZPONT</h2>
                <span style="background:#475569; padding:3px 8px; border-radius:4px; font-size:0.75rem; font-weight:bold;">CANVA & STRIPE ACTIVE</span>
            </div>
            <div>
                <a href="/panel/backup" class="btn-action" style="background:#3b82f6; margin-right:10px;">[Mentés] Biztonsági Mentés</a>
                <a href="/panel/elesites" class="btn-action" style="background:#ef4444; font-size:0.95rem; padding:8px 18px; border:1px solid #f87171;">[Élesítés] VÁLTOZTATÁSOK ÉLESÍTÉSE</a>
                <a href="/logout" style="color:#a1a1aa; margin-left:15px; font-size:0.9rem; text-decoration:none; font-weight:bold;">Kijelentkezés [X]</a>
            </div>
        </div>
        <div class="tabs-header">
            <button class="tab-btn active" onclick="openTab('tab_lista')">Cikkek Áttekintése</button>
            <button class="tab-btn" onclick="openTab('tab_ujcikk')">Új Cikk Írása (Canva-mód)</button>
            <button class="tab-btn" onclick="openTab('tab_hirdetesek')">Hirdetések (Ajánló)</button>
            <button class="tab-btn" onclick="openTab('tab_elofizetok')">Előfizetők Követése</button>
        </div>

        <!-- TABS 1: LISTA & LOKÁLIS FÁJL FELTÖLTŐ -->
        <div id="tab_lista" class="tab-content active">
            <div style="background: #1e293b; padding: 20px; border: 1px dashed #38bdf8; border-radius: 6px; margin-bottom: 25px;">
                <h4 style="color:#38bdf8; margin-top:0; margin-bottom:10px;">Fájl feltöltése a saját számítógépedről</h4>
                <p style="color:#a1a1aa; font-size:0.85rem; margin-bottom:15px;">Válassz ki egy képet a gépedről. Feltöltés után a rendszer ad egy belső linket, amit a Canva-motorban használhatsz.</p>
                <form action="/magazin/titkos-admin/upload-file" method="POST" enctype="multipart/form-data" style="display:flex; gap:15px; align-items:center;">
                    <input type="file" name="file" required style="background:#0f172a; padding:8px; border:1px solid #475569; border-radius:4px; color:#fff; width:auto;">
                    <button type="submit" class="btn-add" style="padding:10px 20px; font-size:0.9rem;">Fájl Feltöltése ➔</button>
                </form>
            </div>

            <h3 style="color:#38bdf8; margin-top:0;">Összes eddig megírt cikk</h3>
            <table class="table-cikkek">
                <thead>
                    <tr>
                        <th>Cím</th>
                        <th>Rovat</th>
                        <th>Szerző</th>
                        <th>Státusz</th>
                        <th>Műveletek</th>
                    </tr>
                </thead>
                <tbody>
                    {% for cikk in cikkek %}
                    <tr>
                        <td><strong>{{ cikk.title }}</strong></td>
                        <td>{{ rovatok_nevei[cikk.category] }}</td>
                        <td>{{ cikk.author }}</td>
                        <td>
                            {% if cikk.published %}<span style="color:#4ade80; font-weight:bold;">[●] Élesítve</span>{% else %}<span style="color:#fbbf24; font-weight:bold;">[○] Vázlat (Rejtett)</span>{% endif %}
                        </td>
                        <td>
                            <a href="/panel/delete/{{ cikk.id }}" class="btn-action" style="background:#ef4444;" onclick="return confirm('Biztosan törölni szeretnéd ezt a cikket?')">Törlés</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <!-- TABS 2: ÚJ CIKK (CANVA-MÓD) -->
        <div id="tab_ujcikk" class="tab-content">
            <h3 style="color:#38bdf8; margin-top:0;">Új magazin tartalom tervezése</h3>
            <form method="POST" action="/panel/add-cikk" onsubmit="syncEditor()">
                <div class="f-group">
                    <label>Cikk Címe</label>
                    <input type="text" name="title" required placeholder="Írd ide a cikk címét...">
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
                    <div class="f-group">
                        <label>Szerző neve</label>
                        <input type="text" name="author" value="Főszerkesztő">
                    </div>
                    <div class="f-group">
                        <label>Rovat kiválasztása</label>
                        <select name="category">
                            <option value="news">News (Friss hírek)</option>
                            <option value="csalad">Család</option>
                            <option value="hit">Hit</option>
                            <option value="erkolcs">Erkölcs</option>
                            <option value="egeszseg">Egészség</option>
                            <option value="media">Média (Multimédia Központ)</option>
                        </select>
                    </div>
                </div>
                <div class="f-group">
                    <label style="margin-bottom: 10px;">Vizuális Blokk-építő és Tervező (Húzd be az elemeket a jobb oldali panelből)</label>
                    <!-- A GrapesJS Canva tervező motor élő felülete -->
                    <div id="gjs" style="height: 500px; overflow: hidden;"></div>
                    <input type="hidden" name="content" id="hidden_content">
                </div>
                <h4 style="color:#38bdf8; margin-top:25px; border-bottom:1px solid #475569; padding-bottom:5px;">Csatolható Extra Média Mezők</h4>
                <div class="f-group">
                    <label>Borítókép Hivatkozás (Helyi vagy online kép URL)</label>
                    <input type="url" name="image" placeholder="pl: /uploads/kepem.jpg vagy külső link">
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
                    <div class="f-group">
                        <label>YouTube Videó ID (A link végén lévő egyedi azonosító kód)</label>
                        <input type="text" name="youtube" placeholder="pl: dQw4w9WgXcQ">
                    </div>
                    <div class="f-group">
                        <label>MP3 Podcast Hanganyag Hivatkozás (Audio URL)</label>
                        <input type="url" name="mp3" placeholder="https://example.com">
                    </div>
                </div>
                <button type="submit" class="btn-add" style="width:100%; margin-top:15px;">[Mentés] Cikk elmentése a szerkesztőségi vázlatok közé</button>
            </form>
        </div>
        <!-- TABS 3: HIRDETÉSEK -->
        <div id="tab_hirdetesek" class="tab-content">
            <h3 style="color:#38bdf8; margin-top:0;">Ajánló hasáb kártyás hirdetései</h3>
            <p style="color:#a1a1aa; font-size:0.9rem; margin-bottom:20px;">Az asztali gépen egymás mellett megjelenő modern partnerhirdetések hozzáadása.</p>
            <form method="POST" action="/panel/add-ad">
                <div class="f-group"><label>Hirdetési kártya címe / megnevezése</label><input type="text" name="ad_title" required placeholder="pl. Hetek Előfizetői Akció"></div>
                <div class="f-group"><label>Banner Kép Hivatkozás (Kép URL)</label><input type="url" name="ad_image" required placeholder="https://example.com"></div>
                <div class="f-group"><label>Cél weboldal címe (Kattintás utáni cél URL)</label><input type="url" name="ad_url" required placeholder="https://hetek.hu"></div>
                <button type="submit" class="btn-add">Kártya elmentése vázlatként</button>
            </form>
        </div>

        <!-- TABS 4: ELŐFIZETŐK KÖVETÉSE (STRIPE STÁTUSZOK) -->
        <div id="tab_elofizetok" class="tab-content">
            <h3 style="color:#38bdf8; margin-top:0;">Regisztrált olvasók és előfizetési státuszok</h3>
            <p style="color:#a1a1aa; font-size:0.9rem; margin-bottom:20px;">A gép éjjel-nappal szinkronizál a Stripe fizetési kapuval. A nem fizetőket automatikusan korlátozza.</p>
            <table class="table-cikkek">
                <thead>
                    <tr>
                        <th>Olvasó E-mail címe</th>
                        <th>Előfizetési Státusz</th>
                        <th>Stripe Ügyfél ID</th>
                        <th>Utolsó Sikeres Levonás</th>
                    </tr>
                </thead>
                <tbody>
                    {% for email, adat in felhasznalok.items() %}
                    <tr>
                        <td style="font-family:monospace; font-size:1rem;">{{ email }}</td>
                        <td>
                            {% if adat.status == 'active' %}
                                <span class="status-badge" style="background:#22c55e; color:#000;">🟢 Aktív (Fizetett)</span>
                            {% elif adat.status == 'past_due' %}
                                <span class="status-badge" style="background:#eab308; color:#000;">🟡 Elmaradás (Újrapróbálás)</span>
                            {% else %}
                                <span class="status-badge" style="background:#ef4444; color:#fff;">🔴 Inaktív (Letiltott)</span>
                            {% endif %}
                        </td>
                        <td style="color:#cbd5e1; font-family:monospace; font-size:0.9rem;">{{ adat.stripe_customer_id }}</td>
                        <td style="color:#cbd5e1;">{{ adat.last_payment }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <!-- GrapesJS Motor Inicializálása és a Canva Beállítások -->
    <script>
        window.onload = function() {
            window.editor = grapesjs.init({
                container: '#gjs',
                fromElement: true,
                height: '500px',
                width: 'auto',
                storageManager: false,
                blockManager: {
                    appendTo: '#blocks',
                    blocks: [
                        {
                            id: 'section',
                            label: '<b>Hasáb szakasz</b>',
                            category: 'Elrendezés',
                            content: '<div style="display:flex; padding:20px; gap:20px; background:#FDFBF7; color:#2C2C2C;"><div style="flex:1; padding:10px; border:1px dashed #ccc;">Bal hasáb</div><div style="flex:1; padding:10px; border:1px dashed #ccc;">Jobb hasáb</div></div>',
                        },
                        {
                            id: 'text',
                            label: 'Szövegtömb',
                            category: 'Tartalom',
                            content: '<p style="color:#2C2C2C; line-height:1.6; font-size:1.05rem; font-family:sans-serif;">Írd ide a bekezdés szövegét...</p>',
                        },
                        {
                            id: 'title',
                            label: 'Főcím (H2)',
                            category: 'Tartalom',
                            content: '<h2 style="color:#0f172a; font-size:2rem; font-weight:bold; margin-bottom:15px; font-family:sans-serif;">Kiemelt alcím szövege</h2>',
                        },
                        {
                            id: 'image',
                            label: 'Kép elem',
                            category: 'Tartalom',
                            content: { type: 'image' },
                            active: true,
                        }
                    ]
                }
            });
            var canvasBody = window.editor.Canvas.getBody();
            canvasBody.style.backgroundColor = '#FDFBF7';
            canvasBody.style.color = '#2C2C2C';
            canvasBody.style.padding = '30px';
        };
        function syncEditor() {
            if(window.editor) {
                document.getElementById('hidden_content').value = window.editor.getHtml();
            }
        }
    </script>
</body>
</html>
"""
# ================= PRÉMIUM OLVASÓI FELÜLET HTML SABLONJA =================
READER_PANEL_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Weekly TWN News — Online Magazin</title>
    <style>
        body { font-family: 'Segoe UI', system-ui, sans-serif; background: #fdfbf7; color: #2c2c2c; margin: 0; padding: 0; }
        .nav-bar { background: #10172a; color: #fff; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 1000; }
        .logo { font-size: 1.5rem; font-weight: bold; color: #ff2a2a; text-decoration: none; letter-spacing: 1px; }
        .rovatok-menu { display: flex; gap: 20px; list-style: none; margin: 0; padding: 0; }
        .rovatok-menu a { color: #cbd5e1; text-decoration: none; font-weight: 600; font-size: 0.95rem; transition: color 0.2s; }
        .rovatok-menu a:hover, .rovatok-menu a.active { color: #ff2a2a; }
        .container { max-width: 1000px; margin: 40px auto; padding: 0 20px; box-sizing: border-box; }
        .cikk-card { background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 35px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .cikk-header { padding: 25px 30px 15px 30px; border-bottom: 1px solid #f1f5f9; }
        .cikk-title { margin: 0 0 10px 0; font-size: 1.8rem; color: #0f172a; }
        .cikk-meta { font-size: 0.85rem; color: #64748b; font-weight: 500; }
        .cikk-body { padding: 30px; line-height: 1.7; font-size: 1.1rem; }
        .media-box { padding: 0 30px 30px 30px; }
        .video-container { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 6px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
        .video-container iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }
        .audio-player { width: 100%; margin-top: 10px; border-radius: 6px; }
        .cover-image { width: 100%; max-height: 400px; object-fit: cover; display: block; border-bottom: 1px solid #e2e8f0; }
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
        <div>
            <a href="/logout" style="color: #a1a1aa; text-decoration: none; font-weight: bold; font-size: 0.9rem;">Kilépés</a>
        </div>
    </div>
    <div class="container">
        {% for cikk in cikkek %}
        <article class="cikk-card">
            {% if cikk.image %}
            <img src="{{ cikk.image }}" class="cover-image" alt="Borítókép">
            {% endif %}
            <div class="cikk-header">
                <h2 class="cikk-title">{{ cikk.title }}</h2>
                <div class="cikk-meta">Szerző: <b>{{ cikk.author }}</b> | Rovat: <b>{{ rovatok[cikk.category] }}</b> | Olvasási idő: <b>{{ cikk.read_time }}</b></div>
            </div>
            <div class="cikk-body">
                {{ cikk.content|safe }}
            </div>
            {% if cikk.youtube or cikk.mp3 %}
            <div class="media-box">
                {% if cikk.youtube %}
                <div class="video-container">
                    <iframe src="https://youtube.com{{ cikk.youtube }}" allowfullscreen></iframe>
                </div>
                {% endif %}
                {% if cikk.mp3 %}
                <audio controls class="audio-player"><source src="{{ cikk.mp3 }}" type="audio/mpeg">A böngésződ nem támogatja az audió lejátszást.</audio>
                {% endif %}
            </div>
            {% endif %}
        </article>
        {% else %}
        <p style="text-align:center; color:#64748b; font-style:italic; margin-top:50px;">Ebben a rovatban még nincsenek élesített prémium tartalmak.</p>
        {% endfor %}
    </div>
</body>
</html>
"""
# ================= BELÉPTETŐ KAPU UTÁK / LOGIKA =================
@app.route("/", methods=["GET", "POST"])
def admin_gate():
    if session.get("magazin_logged_in"):
        return redirect(url_for("admin_panel"))
        
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["magazin_logged_in"] = True
            return redirect(url_for("admin_panel"))
        return '<h3>Hibás szerkesztőségi jelszó! <a href="/">Újra</a></h3>'
        
    return '''
    <body style="font-family:sans-serif; background:#0f172a; color:#fff; text-align:center; padding-top:100px;">
        <form method="POST" style="background:#1e293b; display:inline-block; padding:40px; border-radius:8px; border:1px solid #475569; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
            <h2 style="color:#ff2a2a; margin-top:0;">2. RENDSZER: MAGAZIN ADMIN GATE</h2>
            <p style="color:#cbd5e1; font-size:0.9rem; margin-bottom:20px;">Adja meg a titkos jelszót a szerkesztőség eléréséhez.</p>
            <label style="display:block; margin-bottom:10px; font-weight:bold;">Szerkesztőség Jelszó:</label>
            <input type="password" name="password" style="padding:10px; background:#0f172a; color:#fff; border:1px solid #475569; border-radius:4px; width:200px; text-align:center;" autofocus><br><br>
            <button type="submit" style="background:#ff2a2a; color:#fff; border:0; padding:10px 20px; border-radius:4px; cursor:pointer; font-weight:bold; width:100%;">Belépés a Szerkesztőségbe</button>
        </form>
    </body>
    '''

@app.route("/logout")
def logout():
    session["magazin_logged_in"] = False
    session.pop("user_email", None)
    return redirect(url_for("admin_gate"))

# ================= VEZÉRLŐPULT LOGIKA ÉS FUNKCIÓK =================
@app.route("/panel")
def admin_panel():
    if not session.get("magazin_logged_in"):
        return redirect(url_for("admin_gate"))
        
    global DRAFT_ARTICLES, DRAFT_ADS
    cfg = load_config()
    
    if DRAFT_ARTICLES is None:
        DRAFT_ARTICLES = list(cfg.get("magazin_cikkek", []))
    if DRAFT_ADS is None:
        DRAFT_ADS = list(cfg.get("magazin_ads", []))
        
    return render_template_string(
        ADMIN_PANEL_TEMPLATE, 
        cikkek=DRAFT_ARTICLES, 
        felhasznalok=cfg.get("felhasznalok", {}),
        rovatok_nevei=ROVATOK_MAP
    )

@app.route("/panel/add-cikk", methods=["POST"])
def admin_add_cikk():
    if not session.get("magazin_logged_in"): 
        return "Tiltott hozzáférés", 403
        
    global DRAFT_ARTICLES
    cfg = load_config()
    if DRAFT_ARTICLES is None: 
        DRAFT_ARTICLES = list(cfg.get("magazin_cikkek", []))
    
    uj_id = max([c["id"] for c in DRAFT_ARTICLES], default=0) + 1
    content_raw = request.form.get("content", "")
    
    szavak_szama = len(content_raw.split())
    percek = max(1, szavak_szama // 150)
    
    uj_cikk = {
        "id": uj_id,
        "title": request.form.get("title", "Névtelen cikk"),
        "category": request.form.get("category", "news"),
        "author": request.form.get("author", "Főszerkesztő"),
        "read_time": f"{percek} perc",
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
    if not session.get("magazin_logged_in"): 
        return "Tiltott hozzáférés", 403
        
    global DRAFT_ADS
    cfg = load_config()
    if DRAFT_ADS is None: 
        DRAFT_ADS = list(cfg.get("magazin_ads", []))
    
    uj_ad = {
        "title": request.form.get("ad_title"),
        "image": request.form.get("ad_image"),
        "url": request.form.get("ad_url")
    }
    
    DRAFT_ADS.append(uj_ad)
    return redirect(url_for("admin_panel"))

@app.route("/panel/delete/<int:cikk_id>")
def admin_delete_cikk(cikk_id):
    if not session.get("magazin_logged_in"): 
        return "Tiltott hozzáférés", 403
        
    global DRAFT_ARTICLES
    if DRAFT_ARTICLES is not None:
        DRAFT_ARTICLES = [c for c in DRAFT_ARTICLES if c["id"] != cikk_id]
        
    return redirect(url_for("admin_panel"))

# ================= PRÉMIUM OLVASÓI NÉZET ÚTVONALA =================
@app.route("/magazin/olvaso")
def premium_reader_view():
    cfg = load_config()
    cikkek = [c for c in cfg.get("magazin_cikkek", []) if c.get("published", False)]
    
    kategoria_szuro = request.args.get("category", "all")
    if kategoria_szuro != "all":
        cikkek = [c for c in cikkek if c.get("category") == kategoria_szuro]
        
    return render_template_string(
        READER_PANEL_TEMPLATE,
        cikkek=cikkek,
        rovatok=ROVATOK_MAP,
        current_category=kategoria_szuro
    )
# ================= AUTOMATIKUS E-MAIL KÜLDŐ MODUL (SMTP) =================
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_notification_email(to_email, subject, body_text):
    """Biztonságos e-mail küldő funkció a sikeres/sikertelen fizetések értesítéséhez."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body_text, 'html', 'utf-8'))
        
        # Kapcsolódás a Gmail biztonságos SMTP szerveréhez
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"E-mail küldési hiba: {str(e)}")
        return False

# ================= ADATBÁZIS ÉLESÍTÉS ÉS BIZTONSÁGI MENTÉS =================
@app.route("/panel/elesites")
def admin_elesites():
    if not session.get("magazin_logged_in"): 
        return "Tiltott hozzáférés", 403
        
    global DRAFT_ARTICLES, DRAFT_ADS
    cfg = load_config()
    
    if DRAFT_ARTICLES is not None:
        for cikk in DRAFT_ARTICLES:
            cikk["published"] = True
        cfg["magazin_cikkek"] = DRAFT_ARTICLES
        
    if DRAFT_ADS is not None:
        cfg["magazin_ads"] = DRAFT_ADS
        
    save_config(cfg)
    
    return '''
    <body style="background:#0f172a; color:#fff; text-align:center; padding-top:100px; font-family:sans-serif;">
        <h2>Változtatások sikeresen ÉLESÍTVE és szinkronizálva a közös adatbázissal!</h2>
        <p style="color:#cbd5e1;">A friss cikkek mostantól azonnal láthatóak az olvasók felületén.</p>
        <br>
        <a href="/panel" style="background:#ff2a2a; color:white; padding:10px 20px; text-decoration:none; border-radius:4px; font-weight:bold;">Vissza a Vezérlőpultra</a>
    </body>
    '''

@app.route("/panel/backup")
def admin_backup():
    if not session.get("magazin_logged_in"): 
        return "Tiltott hozzáférés", 403
        
    cfg = load_config()
    json_adatok = json.dumps(cfg, ensure_ascii=False, indent=4)
    
    mai_datum = datetime.now().strftime('%Y%m%d')
    return Response(
        json_adatok,
        mimetype="application/json",
        headers={"Content-disposition": f"attachment; filename=twn_magazin_backup_{mai_datum}.json"}
    )
# ================= STRIPE FIZETÉSI KAPU ÉS WEBHOOK FELDOLGOZÓ =================
import stripe

@app.route("/magazin/stripe-webhook", methods=["POST"])
def stripe_webhook():
    """
    A Stripe szerverétől érkező automatikus jelzések feldolgozása.
    Ez kezeli élesben a sikeres fizetéseket és a nem fizetők letiltását.
    """
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        return f"Webhook hiba: {str(e)}", 400
        
    cfg = load_config()
    felhasznalok = cfg.get("felhasznalok", {})
    
    # 1. ESET: SIKERES HAVIDÍJ LEVONÁS (Azonnali aktiválás + e-mail)
    if event['type'] == 'invoice.payment_succeeded':
        session_obj = event['data']['object']
        customer_email = session_obj.get('customer_email')
        
        if customer_email in felhasznalok:
            felhasznalok[customer_email]["status"] = "active"
            felhasznalok[customer_email]["last_payment"] = datetime.now().strftime("%Y-%m-%d")
            
            # Automatikus sikeres visszaigazoló e-mail küldése
            email_body = f"""
            <h2>Köszönjük az előfizetést!</h2>
            <p>Örömmel értesítjük, hogy a <b>The Weekly TWN News</b> havidíja sikeresen kiegyenlítésre került.</p>
            <p>A prémium rovatok elérése teljes körűen biztosított.</p>
            """
            send_notification_email(customer_email, "Sikeres fizetési jóváhagyás — Weekly News", email_body)
            
    # 2. ESET: SIKERTELEN LEVONÁS / ELMARADÁS (Figyelmeztetés küldése)
    elif event['type'] == 'invoice.payment_failed':
        session_obj = event['data']['object']
        customer_email = session_obj.get('customer_email')
        
        if customer_email in felhasznalok:
            felhasznalok[customer_email]["status"] = "past_due"
            
            email_body = f"""
            <h2>Sikertelen előfizetés-megújítás!</h2>
            <p>Értesítjük, hogy a <b>The Weekly TWN News</b> következő esedékes díját nem tudtuk levonni a kártyájáról.</p>
            <p>Rendszerünk az elkövetkező napokban újra megpróbálja a tranzakciót. Kérjük, ellenőrizze fedezetét.</p>
            """
            send_notification_email(customer_email, "Fizetési figyelmeztetés — Weekly News", email_body)
            
    # 3. ESET: VÉGLEGES ELMARADÁS / LEJÁRT ELŐFIZETÉS (Automatikus letiltás + e-mail)
    elif event['type'] == 'customer.subscription.deleted':
        session_obj = event['data']['object']
        customer_id = session_obj.get('customer')
        
        for email, adat in felhasznalok.items():
            if adat.get("stripe_customer_id") == customer_id:
                adat["status"] = "inactive"
                
                email_body = f"""
                <h2>Előfizetés megszűnése</h2>
                <p>Sajnálattal értesítjük, hogy elmaradt fizetés miatt a <b>The Weekly TWN News</b> prémium tagsága letiltásra került.</p>
                """
                send_notification_email(email, "Tagság megszűnése — Weekly News", email_body)
                break
                
    cfg["felhasznalok"] = felhasznalok
    save_config(cfg)
    return {"status": "success"}

# ================= LOKÁLIS FÁJLFELTÖLTÉS ÉS KÉPKEZELÉS =================
from werkzeug.utils import secure_filename
from flask import send_from_directory

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/magazin/titkos-admin/upload-file', methods=['POST'])
def admin_upload_file():
    if not session.get("magazin_logged_in"): 
        return "Tiltott hozzáférés", 403
        
    if 'file' not in request.files:
        return "Nincs fájl a kérésben", 400
        
    uploaded_file = request.files['file']
    if uploaded_file.filename == '':
        return "Nincs kiválasztott fájl", 400
        
    if uploaded_file and allowed_file(uploaded_file.filename):
        filename = secure_filename(uploaded_file.filename)
        id_prefix = datetime.now().strftime('%H%M%S_')
        filename = id_prefix + filename
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(file_path)
        
        file_url = f"/uploads/{filename}"
        return f"""
        <body style="background:#0f172a; color:#fff; text-align:center; padding-top:50px; font-family:sans-serif;">
            <h3>Sikeres feltöltés a saját gépedről!</h3>
            <p>A fájl online elérési címe a szerveren:</p>
            <input type="text" value="{file_url}" id="urlField" style="padding:10px; width:300px; text-align:center; background:#1e293b; color:#fff; border:1px solid #475569; border-radius:4px;" readonly><br><br>
            <button onclick="navigator.clipboard.writeText('{file_url}'); alert('Link a vágólapra másolva!');" style="background:#10b981; color:white; border:0; padding:10px 20px; border-radius:4px; cursor:pointer; font-weight:bold;">Link Kimásolása</button>
            <br><br>
            <a href="/panel" style="color:#cbd5e1; text-decoration:underline;">Vissza a Vezérlőpultra</a>
        </body>
        """
    return "Nem támogatott fájlformátum", 400

@app.route('/uploads/<filename>')
def uploaded_file_serve(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
