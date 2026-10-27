import os
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, redirect, url_for, send_from_directory, request, session

app = Flask(__name__)
app.secret_key = "twn_super_secret_key_for_session"
CONFIG_FILE = "twn_config.json"
ADMIN_PASSWORD = "twnadmin2026"

DEFAULT_CONFIG = {
    "cover_links": {
        "kulfold_politika": "https://twnnews.hu",
        "venia_sokk": "https://twnnews.hu",
        "vallas_hit": "https://twnnews.hu",
        "tudomany_tech": "https://twnnews.hu"
    },
    "ads": {
        "egyes_ad": {"type": "text", "content": "Saját Hirdetési Felület — Egyes helyfoglalás", "url": "/hirdetes"},
        "kettes_ad": {"type": "text", "content": "Prémium Reklámfelület — Kettes helyfoglalás", "url": "/hirdetes"},
        "harmas_ad": {"type": "text", "content": "Saját Hirdetési Felület — Hármas helyfoglalás", "url": "/hirdetes"},
        "negyes_ad": {"type": "text", "content": "Saját Hirdetési Felület — Negyes helyfoglalás", "url": "/hirdetes"},
        "otos_ad": {"type": "text", "content": "Saját Hirdetési Felület — Ötös helyfoglalás", "url": "/hirdetes"},
        "hatos_ad": {"type": "text", "content": "Saját Hirdetési Felület — Hatos helyfoglalás", "url": "/hirdetes"},
        "hetes_ad": {"type": "text", "content": "Saját Hirdetési Felület — Hetes helyfoglalás", "url": "/hirdetes"},
        "nyolcas_ad": {"type": "text", "content": "Saját Hirdetési Felület — Nyolcas helyfoglalás", "url": "/hirdetes"},
        "kilences_ad": {"type": "text", "content": "Saját Hirdetési Felület — Kilences helyfoglalás", "url": "/hirdetes"},
        "kulon_hasab_ad": {"type": "text", "content": "Kiemelt Oldalsó Hirdetési Hasáb — Helyfoglalás", "url": "/hirdetes"}
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
HIRCATORNAK = {
    "Belföld": [
        {"id": "1", "name": "Origo", "site": "https://origo.hu"}, 
        {"id": "2", "name": "Blikk", "site": "https://blikk.hu"}, 
        {"id": "3", "name": "Nők Lapja Café", "site": "https://nlc.hu"},
        {"id": "4", "name": "Femina", "site": "https://femina.hu"}, 
        {"id": "5", "name": "Index", "site": "https://index.hu"}, 
        {"id": "6", "name": "Telex", "site": "https://telex.hu"},
        {"id": "7", "name": "24.hu", "site": "https://24.hu"}, 
        {"id": "8", "name": "HVG", "site": "https://hvg.hu"}, 
        {"id": "9", "name": "444.hu", "site": "https://444.hu"},
        {"id": "10", "name": "Magyar Nemzet", "site": "https://magyarnemzet.hu"}, 
        {"id": "11", "name": "RTL Híradó", "site": "https://rtl.hu"}, 
        {"id": "12", "name": "TV2 Tények", "site": "https://tenyek.hu"}, 
        {"id": "13", "name": "Népszava", "site": "https://nepszava.hu"}, 
        {"id": "14", "name": "BorsOnline", "site": "https://borsonline.hu"}
    ],
    "Külföld": [
        {"id": "20", "name": "BBC News", "site": "https://bbc.com"}, 
        {"id": "21", "name": "Reuters", "site": "https://reuters.com"}, 
        {"id": "22", "name": "The Guardian", "site": "https://theguardian.com"},
        {"id": "23", "name": "Deutsche Welle", "site": "https://dw.com"}, 
        {"id": "24", "name": "Der Spiegel", "site": "https://spiegel.de"}, 
        {"id": "25", "name": "Sky News", "site": "https://sky.com"},
        {"id": "26", "name": "ABC News", "site": "https://go.com"}, 
        {"id": "27", "name": "The Mirror", "site": "https://mirror.co.uk"}, 
        {"id": "28", "name": "The Independent", "site": "https://independent.co.uk"},
        {"id": "29", "name": "The Times", "site": "https://thetimes.com"}, 
        {"id": "30", "name": "CNN", "site": "https://cnn.com"}, 
        {"id": "31", "name": "The New York Times", "site": "https://nytimes.com"},
        {"id": "32", "name": "BBC UK", "site": "https://bbc.co.uk"}, 
        {"id": "33", "name": "The Washington Post", "site": "https://washingtonpost.com"}, 
        {"id": "34", "name": "Tagesschau", "site": "https://tagesschau.de"}
    ],
    "Gazdaság": [
        {"id": "17", "name": "Portfolio", "site": "https://portfolio.hu"}, 
        {"id": "18", "name": "Pénzcentrum", "site": "https://penzcentrum.hu"}, 
        {"id": "19", "name": "Világgazdaság", "site": "https://vg.hu"}
    ],
    "Vallás": [
        {"id": "16", "name": "Hetek Magazin", "site": "https://hetek.hu"}
    ],
    "Család & Tech": [
        {"id": "15", "name": "Glamour", "site": "https://glamour.hu"}, 
        {"id": "35", "name": "Bunte.de", "site": "https://bunte.de"}, 
        {"id": "36", "name": "Blog.hu", "site": "https://blog.hu"},
        {"id": "37", "name": "Gala", "site": "https://gala.de"}, 
        {"id": "38", "name": "Bild", "site": "https://bild.de"}, 
        {"id": "39", "name": "Closer", "site": "https://closerweekly.com"},
        {"id": "40", "name": "Hello Magazin", "site": "https://hellomagazine.com"}, 
        {"id": "41", "name": "Daily Mail", "site": "https://dailymail.co.uk"}, 
        {"id": "42", "name": "The Sun", "site": "https://thesun.co.uk"}
    ]
}

STORED_NEWS = {}

def fake_fetch_news(ujsag_id, ujsag_nev, ujsag_link):
    return [
        {"title": f"Vezető hír és friss közéleti riport — {ujsag_nev}", "link": ujsag_link, "logo": f"{ujsag_id}.jpg.jpg"},
        {"title": f"Rendkívüli beszámoló és helyi elemzés", "link": ujsag_link, "logo": f"{ujsag_id}.jpg.jpg"}
    ]

def scrape_all_news():
    categories = {"Belföld": [], "Külföld": [], "Gazdaság": [], "Vallás": [], "Család & Tech": []}
    for kat_nev, ujsagok in HIRCATORNAK.items():
        for ujsag in ujsagok:
            categories[kat_nev].append({
                "ujsag_name": ujsag["name"],
                "logo": f"{ujsag['id']}.jpg.jpg",
                "cikkek": fake_fetch_news(ujsag["id"], ujsag["name"], ujsag["site"])
            })
    return categories
AD_MACRO = """
{% macro render_ad(ad_data, ad_id) %}
<div class="twn-mini-ad">
    <span class="ad-label">Hirdetés / Premium Ad</span>
    {% if ad_data.type == 'video' %}
        <div style="position: relative; width: 100%; aspect-ratio: 16/9; overflow: hidden; background-color: #000; border-radius: 4px;">
            <video id="video-{{ ad_id }}" autoplay muted loop playsinline style="width: 100%; height: 100%; object-fit: cover;">
                <source src="{{ ad_data.content }}" type="video/mp4">
            </video>
            <button type="button" onclick="toggleSound('video-{{ ad_id }}', this)" style="position: absolute; bottom: 8px; right: 8px; background: rgba(0, 0, 0, 0.6); border: 1px solid rgba(255, 255, 255, 0.5); border-radius: 50%; width: 30px; height: 30px; cursor: pointer; display: flex; align-items: center; justify-content: center; z-index: 10;">
                <svg viewBox="0 0 24 24" fill="white" width="16px" height="16px">
                    <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM3 9v6h4l5 5V4L7 9H3z"/>
                </svg>
            </button>
        </div>
    {% elif ad_data.type == 'image' %}
        <a href="{{ ad_data.url }}" target="_blank"><img src="{{ ad_data.content }}" class="ad-img"></a>
    {% else %}
        <a href="{{ ad_data.url }}" target="_blank" class="ad-text">{{ ad_data.content }}</a>
    {% endif %}
</div>
{% endmacro %}
"""

HTML_TEMPLATE = AD_MACRO + """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>THE WEEKLY TWN NEWS</title>
    <style>
        body { font-family: 'Arial', sans-serif; margin: 0; padding: 0; background-color: #1e293b; color: #ffffff; overflow-x: hidden; }
        .frozen-top-header { position: sticky; top: 0; z-index: 1000; width: 100%; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
        header { background-color: #0f172a; padding: 1.5rem 1rem; text-align: center; border-bottom: 3px solid #ff2a2a; }
        .header-logo-container { display: flex; justify-content: center; align-items: center; width: 100%; }
        .logo-box-html { background-color: transparent; padding: 6px 0; border-top: 1px solid #e2e8f0; border-bottom: 1px solid #e2e8f0; display: inline-flex; align-items: stretch; font-family: 'Bodoni Moda', serif; position: relative; }
        .logo-text-the { font-size: 78px; font-weight: 400; color: #e2e8f0; line-height: 0.85; letter-spacing: -3px; padding-right: 14px; display: flex; align-items: center; }
        .logo-right-wrapper { display: flex; flex-direction: column; justify-content: space-between; width: 215px; padding-left: 2px; }
        .logo-text-weekly { font-family: 'Bodoni Moda', serif; font-size: 40px; font-weight: 700; letter-spacing: 1.5px; color: transparent; -webkit-text-stroke: 1px #e2e8f0; line-height: 0.95; text-transform: uppercase; width: 100%; }
        .logo-bottom-row-wrapper { display: flex; align-items: center; justify-content: space-between; width: 100%; margin-top: auto; }
        .logo-twn-badge { background-color: #2ea6f2; padding: 1px 7px; border-radius: 5px; display: inline-flex; align-items: center; justify-content: center; position: relative; font-family: 'Bodoni Moda', serif; font-style: italic; font-weight: 700; font-size: 24px; line-height: 1; }
        .logo-twn-badge span:nth-child(1) { color: #111827; }
        .logo-twn-badge span:nth-child(2) { color: #ffffff; }
        .logo-twn-badge span:nth-child(3) { color: #e62129; }
        .logo-text-news { font-family: 'Oswald', sans-serif; font-size: 38px; font-weight: 700; color: #e62129; line-height: 0.9; letter-spacing: 0.5px; text-transform: uppercase; }
        .nav-bar { background-color: #0f172a; padding: 0px 1rem; display: flex; justify-content: center; border-bottom: 1px solid #475569; flex-wrap: wrap; }
        .nav-item { color: white; font-family: sans-serif; font-weight: bold; padding: 1.1rem 1.5rem; text-decoration: none; font-size: 1.05rem; }
        .nav-item-marketing { color: #38bdf8; border-left: 1px solid #475569; }
        .btn-refresh { background-color: #ff2a2a; color: white; padding: 1.1rem 1.5rem; font-family: sans-serif; font-weight: bold; text-transform: uppercase; text-decoration: none; }
        
        .three-column-grid-container { display: grid; grid-template-columns: 320px 1fr 320px 300px; gap: 2rem; max-width: 1900px; margin: 2rem auto; padding: 0 1rem; }
        @media (max-width: 1600px) { .three-column-grid-container { grid-template-columns: 320px 1fr 320px; } .marketing-sidebar-column { display: none; } }
        @media (max-width: 1300px) { .three-column-grid-container { grid-template-columns: 1fr; } }
        
        .side-column-stream { display: flex; flex-direction: column; gap: 25px; }
        .center-news-stream { display: flex; flex-direction: column; align-items: center; }
        .marketing-sidebar-column { display: flex; flex-direction: column; gap: 25px; background: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #334155; height: fit-content; }
        .main-magazine-cover { width: 100%; max-width: 480px; margin: 0 auto 3rem auto; border: 2px solid #fff; box-shadow: 0 6px 20px rgba(0,0,0,0.5); position: relative; }
        .main-magazine-cover img { width: 100%; height: auto; display: block; }
        .cover-hotspot { position: absolute; background: rgba(255,255,255,0); transition: background 0.2s ease; cursor: pointer; }
        .cover-hotspot:hover { background: rgba(255,255,255,0.15); }
        .hs-kulfold { top: 35%; left: 35%; width: 28%; height: 5%; border-radius: 10px; }
        .hs-venia { top: 66%; left: 52%; width: 44%; height: 16%; }
        .hs-vallas { top: 76%; left: 3%; width: 45%; height: 12%; }
        .hs-tech { top: 88%; left: 51%; width: 46%; height: 9%; border-radius: 10px; }
        .rovat-section { margin-bottom: 3.5rem; width: 100%; }
        .rovat-title { font-family: sans-serif; font-size: 1.6rem; font-weight: 900; color: #38bdf8; border-bottom: 3px solid #38bdf8; padding-bottom: 0.3rem; margin-bottom: 1.5rem; text-transform: uppercase; letter-spacing: 0.5px; }
        .news-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; width: 100%; }
        .ujsag-box-card { background: #0f172a; border: 1px solid #475569; border-radius: 6px; padding: 15px; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .ujsag-logo-img { width: 100%; height: auto; border-radius: 6px; margin-bottom: 12px; border: 1px solid #334155; }
        .cikk-row { width: 100%; border-top: 1px solid #233142; padding-top: 8px; margin-top: 8px; text-align: left; }
        .cikk-link { font-size: 0.95rem; font-weight: bold; color: #ffffff; text-decoration: none; line-height: 1.4; display: block; }
        .cikk-link:hover { color: #2ea6f2; text-decoration: underline; }
        footer { background-color: #737373; padding: 30px 20px; margin-top: 5rem; border-top: 4px solid #ff2a2a; }
        .footer-top-container { max-width: 1400px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 30px; }
        .footer-logo-area { background: #fff; padding: 15px 25px; border-radius: 8px; display: inline-block; }
        .footer-logo-text { color: #1e293b; font-family: 'Bodoni Moda', serif; font-size: 2.2rem; font-weight: bold; }
        .footer-links-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px 30px; }
        .footer-link { color: #ffffff; text-decoration: none; font-size: 0.9rem; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }
        .footer-bottom-dark-bar { background-color: #171717; padding: 25px 20px; font-size: 0.8rem; color: #a3a3a3; line-height: 1.6; }
        .footer-bottom-container { max-width: 1400px; margin: 0 auto; }
    </style>
</head>
"""
HTML_TEMPLATE += """
<body>
    <div class="three-column-grid-container">
        <div class="side-column-stream">
            <div class="rovat-section" id="vallas">
                <div class="rovat-title">Hit & Erkölcs</div>
                {% for ujsag in news['Vallás'] %}
                    <div class="ujsag-box-card">
                        <img src="/logo_kepek/{{ ujsag.logo }}" class="ujsag-logo-img" alt="Logó">
                        {% for cikk in ujsag.cikkek %}
                            <div class="cikk-row"><a href="{{ cikk.link }}" target="_blank" class="cikk-link">{{ cikk.title }}</a></div>
                        {% endfor %}
                    </div>
                    {% if loop.index == 1 %}
                        {{ render_ad(cfg.ads.egyes_ad, 'egyes') }}
                    {% else %}
                        {{ render_ad(cfg.ads.kettes_ad, 'kettes') }}
                    {% endif %}
                {% endfor %}
            </div>
            
            <div class="rovat-section" id="gazdasag">
                <div class="rovat-title">Gazdaság</div>
                {% for ujsag in news['Gazdaság'] %}
                    <div class="ujsag-box-card">
                        <img src="/logo_kepek/{{ ujsag.logo }}" class="ujsag-logo-img" alt="Logó">
                        {% for cikk in ujsag.cikkek %}
                            <div class="cikk-row"><a href="{{ cikk.link }}" target="_blank" class="cikk-link">{{ cikk.title }}</a></div>
                        {% endfor %}
                    </div>
                    {% if loop.index == 1 %}
                        {{ render_ad(cfg.ads.harmas_ad, 'harmas') }}
                    {% elif loop.index == 2 %}
                        {{ render_ad(cfg.ads.negyes_ad, 'negyes') }}
                    {% else %}
                        {{ render_ad(cfg.ads.otos_ad, 'otos') }}
                    {% endif %}
                {% endfor %}
            </div>
        </div>
        
        <div class="center-news-stream">
            <div class="main-magazine-cover">
                <img src="/friss_magazin.jpg" alt="The Weekly News Címlap">
                <a href="{{ cfg.cover_links.kulfold_politika }}" target="_blank" class="cover-hotspot hs-kulfold" title="Külföld & Politika"></a>
                <a href="{{ cfg.cover_links.venia_sokk }}" target="_blank" class="cover-hotspot hs-venia" title="Venia-Sokk"></a>
                <a href="{{ cfg.cover_links.vallas_hit }}" target="_blank" class="cover-hotspot hs-vallas" title="Vallás, Hit & Erkölcs"></a>
                <a href="{{ cfg.cover_links.tudomany_tech }}" target="_blank" class="cover-hotspot hs-tech" title="Tudomány & Tech"></a>
            </div>
            
            <div class="rovat-section" id="belfold">
                <div class="rovat-title">Belföld hírei</div>
                <div class="news-grid">
                    {% for ujsag in news['Belföld'] %}
                        <div class="ujsag-box-card">
                            <img src="/logo_kepek/{{ ujsag.logo }}" class="ujsag-logo-img" alt="Logó">
                            {% for cikk in ujsag.cikkek %}
                                <div class="cikk-row"><a href="{{ cikk.link }}" target="_blank" class="cikk-link">{{ cikk.title }}</a></div>
                            {% endfor %}
                        </div>
                    {% endfor %}
                </div>
            </div>
            
            <div class="rovat-section" id="kulfold">
                <div class="rovat-title">Külföldi Sajtó</div>
                <div class="news-grid">
                    {% for ujsag in news['Külföld'] %}
                        <div class="ujsag-box-card">
                            <img src="/logo_kepek/{{ ujsag.logo }}" class="ujsag-logo-img" alt="Logó">
                            {% for cikk in ujsag.cikkek %}
                                <div class="cikk-row"><a href="{{ cikk.link }}" target="_blank" class="cikk-link">{{ cikk.title }}</a></div>
                            {% endfor %}
                        </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <div class="side-column-stream">
            <div class="rovat-section" id="tech">
                <div class="rovat-title">Család & Tech</div>
                {% for ujsag in news['Család & Tech'] %}
                    <div class="ujsag-box-card">
                        <img src="/logo_kepek/{{ ujsag.logo }}" class="ujsag-logo-img" alt="Logó">
                        {% for cikk in ujsag.cikkek %}
                            <div class="cikk-row"><a href="{{ cikk.link }}" target="_blank" class="cikk-link">{{ cikk.title }}</a></div>
                        {% endfor %}
                    </div>
                    {% if loop.index == 1 %}
                        {{ render_ad(cfg.ads.hatos_ad, 'hatos') }}
                    {% elif loop.index == 2 %}
                        {{ render_ad(cfg.ads.hetes_ad, 'hetes') }}
                    {% elif loop.index == 3 %}
                        {{ render_ad(cfg.ads.nyolcas_ad, 'nyolcas') }}
                    {% else %}
                        {{ render_ad(cfg.ads.kilences_ad, 'kilences') }}
                    {% endif %}
                {% endfor %}
            </div>
        </div>

        <div class="marketing-sidebar-column">
            <div style="text-align: center; border-bottom: 2px solid #ff2a2a; padding-bottom: 5px; margin-bottom: 10px;">
                <strong style="color: #ff2a2a; text-transform: uppercase; font-size: 1.1rem; letter-spacing: 1px;">Kiemelt Partnerünk</strong>
            </div>
            {{ render_ad(cfg.ads.kulon_hasab_ad, 'kulon_hasab') }}
        </div>
    </div>

    <footer>
        <div class="footer-top-container">
            <div class="footer-logo-area"><div class="footer-logo-text">TWN News</div></div>
            <div class="footer-links-grid">
                <a href="/impresszum" class="footer-link">I Impresszum</a>
                <a href="/aszf" class="footer-link">I ÁSZF</a>
                <a href="/adatvedelem" class="footer-link">I Adatvédelem</a>
                <a href="/hirdetes" class="footer-link">I Médiaajánlat</a>
                <a href="/hirdetes" class="footer-link">I Kapcsolat</a>
                <a href="/admin" class="footer-link" style="color: #38bdf8;">I Admin belépés</a>
            </div>
        </div>
    </footer>
    <div class="footer-bottom-dark-bar">
        <div class="footer-bottom-container">
            &copy; 2026 THE WEEKLY TWN NEWS — Minden jog fenntartva. NMHH Nyilvántartási szám: Folyamatban.
        </div>
    </div>

    <script>
    function toggleSound(id, btn) {
        var video = document.getElementById(id);
        if (video) {
            video.muted = !video.muted;
            btn.style.background = video.muted ? "rgba(0, 0, 0, 0.6)" : "rgba(0, 128, 0, 0.8)";
        }
    }
    </script>
</body>
</html>
"""
        # 1. Ha nincs belépve, ezt az űrlapot mutatjuk neki:
        admin_login_html = (
            '<body style="font-family:sans-serif; background:#0f172a; color:#fff; text-align:center; padding-top:100px;">'
            '<form method="POST" style="background:#1e293b; display:inline-block; padding:30px; border-radius:8px; border:1px solid #475569;">'
            '<label style="display:block; margin-bottom:10px;">Admin Jelszó:</label>'
            '<input type="password" name="password" style="padding:8px; background:#0f172a; color:#fff; border:1px solid #475569;"><br><br>'
            '<button type="submit" style="background:#ff2a2a; color:#fff; border:0; padding:8px 15px; border-radius:4px; cursor:pointer;">Belépés</button>'
            '</form></body>'
        )
        return admin_login_html
    
    # 2. Ha már be van lépve, betöltjük a konfigurációt és kezeljük a mentést:
    current_config = load_config()
    if request.method == "POST":
        current_config["cover_links"]["kulfold_politika"] = request.form.get("cover_kulfold")
        current_config["cover_links"]["venia_sokk"] = request.form.get("cover_venia")
        current_config["cover_links"]["vallas_hit"] = request.form.get("cover_vallas")
        current_config["cover_links"]["tudomany_tech"] = request.form.get("cover_tech")
        
        current_config["ads"]["kulon_hasab_ad"]["type"] = request.form.get("kulon_hasab_ad_type")
        current_config["ads"]["kulon_hasab_ad"]["content"] = request.form.get("kulon_hasab_ad_content")
        current_config["ads"]["kulon_hasab_ad"]["url"] = request.form.get("kulon_hasab_ad_url")
        
        ad_keys = ['egyes_ad', 'kettes_ad', 'harmas_ad', 'negyes_ad', 'otos_ad', 'hatos_ad', 'hetes_ad', 'nyolcas_ad', 'kilences_ad']
        for key in ad_keys:
            current_config["ads"][key]["type"] = request.form.get(f"{key}_type")
            current_config["ads"][key]["content"] = request.form.get(f"{key}_content")
            current_config["ads"][key]["url"] = request.form.get(f"{key}_url")
            
        save_config(current_config)
        return redirect(url_for("index"))
        
    return render_template_string(ADMIN_TEMPLATE, cfg=current_config)

@app.route("/admin/logout")
def logout():
    session["logged_in"] = False
    return redirect(url_for("index"))

@app.route('/logo_kepek/<path:filename>')
def serve_logos(filename):
    return send_from_directory('.', filename)

@app.route('/friss_magazin.jpg')
def serve_friss_magazin():
    return send_from_directory('.', 'friss_magazin.jpg')

@app.route("/frissites")
def refresh():
    global STORED_NEWS
    STORED_NEWS = scrape_all_news()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
