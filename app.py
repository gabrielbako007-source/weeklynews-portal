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
        "kulon_hasab_ad": {"type": "text", "content": "Kiemelt Címlapi Hirdetés — Helyfoglalás", "url": "/hirdetes"}
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
        
        .three-column-grid-container { display: grid; grid-template-columns: 320px 1fr 320px; gap: 2rem; max-width: 1700px; margin: 2rem auto; padding: 0 1rem; }
        @media (max-width: 1300px) { .three-column-grid-container { grid-template-columns: 1fr; } }
        
        .side-column-stream { display: flex; flex-direction: column; gap: 25px; }
        .center-news-stream { display: flex; flex-direction: column; align-items: center; }
        .ujsag-box-card { background: #0f172a; border: 1px solid #475569; border-radius: 6px; padding: 15px; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .ujsag-logo-img { width: 100%; height: auto; border-radius: 6px; margin-bottom: 12px; border: 1px solid #334155; }
        .cikk-row { width: 100%; border-top: 1px solid #233142; padding-top: 8px; margin-top: 8px; text-align: left; }
        .cikk-link { font-size: 0.95rem; font-weight: bold; color: #ffffff; text-decoration: none; line-height: 1.4; display: block; }
        .cikk-link:hover { color: #2ea6f2; text-decoration: underline; }
        .twn-mini-ad { background-color: #1a202c; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; width: 100%; box-sizing: border-box; text-align: center; margin: 10px 0; overflow: hidden; }
        .ad-label { font-size: 0.7rem; color: #a0aec0; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 5px; }
        .ad-text { font-size: 0.85rem; color: #cbd5e1; font-weight: bold; text-decoration: none; }
        .ad-img { width: 100%; height: auto; border-radius: 4px; display: block; }
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
    <div class="frozen-top-header">
        <header>
            <div class="header-logo-container">
                <div class="logo-box-html">
                    <div class="logo-text-the">THE</div>
                    <div class="logo-right-wrapper">
                        <div class="logo-text-weekly">WEEKLY</div>
                        <div class="logo-bottom-row-wrapper">
                            <div class="logo-twn-badge"><span>T</span><span>W</span><span>N</span></div>
                            <div class="logo-text-news">NEWS</div>
                        </div>
                    </div>
                </div>
            </div>
        </header>
        <div class="nav-bar">
            <a href="/frissites" class="btn-refresh">🔄 Frissítés</a>
            <a href="#belfold" class="nav-item">Belföld</a>
            <a href="#kulfold" class="nav-item">Külföld</a>
            <a href="#gazdasag" class="nav-item">Gazdaság</a>
            <a href="#vallas" class="nav-item">Vallás</a>
            <a href="#tech" class="nav-item">Család & Tech</a>
            <a href="/hirdetes" class="nav-item nav-item-marketing">💼 Hirdetés feladás</a>
        </div>
    </div>

    <div class="three-column-grid-container">
        <!-- ================= BAL HASÁB ================= -->
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
                    {% endif %}
                {% endfor %}
            </div>
        </div>
        
        <!-- ================= KÖZÉPSŐ HASÁB ================= -->
        <div class="center-news-stream">
            <div class="main-magazine-cover">
                <img src="/friss_magazin.jpg" alt="The Weekly News Címlap">
                <a href="{{ cfg.cover_links.kulfold_politika }}" target="_blank" class="cover-hotspot hs-kulfold" title="Külföld & Politika"></a>
                <a href="{{ cfg.cover_links.venia_sokk }}" target="_blank" class="cover-hotspot hs-venia" title="Venia-Sokk"></a>
                <a href="{{ cfg.cover_links.vallas_hit }}" target="_blank" class="cover-hotspot hs-vallas" title="Vallás, Hit & Erkölcs"></a>
                <a href="{{ cfg.cover_links.tudomany_tech }}" target="_blank" class="cover-hotspot hs-tech" title="Tudomány & Tech"></a>
            </div>

            {{ render_ad(cfg.ads.kulon_hasab_ad, 'kulon_hasab_top') }}
            
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
                        {% if loop.index == 1 %}
                            {{ render_ad(cfg.ads.negyes_ad, 'negyes') }}
                        {% elif loop.index == 2 %}
                            {{ render_ad(cfg.ads.otos_ad, 'otos') }}
                        {% endif %}
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
                        {% if loop.index == 1 %}
                            {{ render_ad(cfg.ads.hatos_ad, 'hatos') }}
                        {% elif loop.index == 2 %}
                            {{ render_ad(cfg.ads.hetes_ad, 'hetes') }}
                        {% endif %}
                    {% endfor %}
                </div>
            </div>
        </div>
        
        <!-- ================= JOBB HASÁB ================= -->
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
                        {{ render_ad(cfg.ads.nyolcas_ad, 'nyolcas') }}
                    {% elif loop.index == 2 %}
                        {{ render_ad(cfg.ads.kilences_ad, 'kilences') }}
                    {% endif %}
                {% endfor %}
            </div>
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
JOGI_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <title>{{ cim }} — THE WEEKLY TWN NEWS</title>
    <style>
        body { font-family: sans-serif; background-color: #1e293b; color: #fff; padding: 40px 20px; line-height: 1.6; }
        .box { max-width: 800px; margin: 0 auto; background: #0f172a; padding: 40px; border-radius: 8px; border: 1px solid #475569; }
        h1 { color: #38bdf8; border-bottom: 2px solid #38bdf8; padding-bottom: 10px; }
        .back { display: inline-block; margin-top: 30px; background: #ff2a2a; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="box">
        <h1>{{ cim }}</h1>
        <div>{{ tartalom | safe }}</div>
        <a href="/" class="back">⬅ Vissza a főoldalra</a>
    </div>
</body>
</html>
"""

MARKETING_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <title>Hirdessen a TWN News-on</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #1e293b; color: #fff; text-align: center; padding: 50px 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #0f172a; padding: 30px; border-radius: 8px; border: 1px solid #475569; }
        h1 { color: #38bdf8; }
        p { line-height: 1.6; color: #cbd5e1; }
        .back-btn { display: inline-block; margin-top: 20px; background: #ff2a2a; color: #fff; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <h1>TWN News Médiaajánlat</h1>
        <p>Szeretné termékét, szolgáltatását vagy hirdetését elhelyezni a felületünkön?</p>
        <p>Kapcsolatfelvétel: <strong>info@twnnews.hu</strong></p>
        <a href="/" class="back-btn">⬅ Vissza a címlapra</a>
    </div>
</body>
</html>
"""

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <title>TWN News — Szuper Admin</title>
    <style>
        body { font-family: sans-serif; background: #0f172a; color: #fff; padding: 20px; }
        .panel { max-width: 800px; margin: 0 auto; background: #1e293b; padding: 25px; border-radius: 8px; border: 1px solid #475569; }
        h2, h3 { color: #38bdf8; border-bottom: 1px solid #475569; padding-bottom: 8px; }
        .form-group { margin-bottom: 20px; background: #151f32; padding: 15px; border-radius: 6px; border-left: 4px solid #2ea6f2; }
        .ad-row { display: flex; gap: 15px; flex-wrap: wrap; margin-top: 8px; }
        .ad-col { flex: 1; min-width: 200px; }
        label { display: block; font-weight: bold; margin-bottom: 5px; color: #cbd5e1; font-size: 0.85rem; text-transform: uppercase; }
        input[type="text"], select { width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #475569; background: #0f172a; color: #fff; box-sizing: border-box; }
        .btn-save { background: #ff2a2a; color: #fff; border: 0; padding: 15px 25px; font-weight: bold; border-radius: 4px; cursor: pointer; font-size: 1.1rem; width: 100%; margin-top: 20px; text-transform: uppercase; letter-spacing: 1px; }
    </style>
</head>
<body>
    <div class="panel">
        <a href="/admin/logout" style="float:right; color:#ff2a2a; text-decoration:none; font-weight:bold;">Kijelentkezés ✖</a>
        <h2>TWN News Szuper Vezérlőpult</h2>
        <form method="POST">
            <h3>1. Kattintható Magazinborító Linkek</h3>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; background:#151f32; padding:15px; border-radius:6px; margin-bottom:25px;">
                <div><label>Külföld & Politika</label><input type="text" name="cover_kulfold" value="{{ cfg.cover_links.kulfold_politika }}"></div>
                <div><label>VENIA-SOKK</label><input type="text" name="cover_venia" value="{{ cfg.cover_links.venia_sokk }}"></div>
                <div><label>Vallás & Hit</label><input type="text" name="cover_vallas" value="{{ cfg.cover_links.vallas_hit }}"></div>
                <div><label>Tudomány & Tech</label><input type="text" name="cover_tech" value="{{ cfg.cover_links.tudomany_tech }}"></div>
            </div>

            <h3>2. Kiemelt Címlapi Hirdetés (Borító alatt)</h3>
            <div class="form-group" style="border-left: 4px solid #ff2a2a;">
                <strong style="color: #ff2a2a; font-size: 1.1rem;">KIEMELT CÍMLAPI BANNER</strong>
                <div class="ad-row">
                    <div style="width: 180px;">
                        <label>Típus</label>
                        <select name="kulon_hasab_ad_type">
                            <option value="text" {% if cfg.ads.kulon_hasab_ad.type == 'text' %}selected{% endif %}>Sima Szöveg</option>
                            <option value="image" {% if cfg.ads.kulon_hasab_ad.type == 'image' %}selected{% endif %}>Banner (Kép URL)</option>
                            <option value="video" {% if cfg.ads.kulon_hasab_ad.type == 'video' %}selected{% endif %}>Google Videó (Direct MP4 URL)</option>
                        </select>
                    </div>
                    <div class="ad-col">
                        <label>Tartalom</label>
                        <input type="text" name="kulon_hasab_ad_content" value="{{ cfg.ads.kulon_hasab_ad.content }}">
                    </div>
                    <div class="ad-col">
                        <label>Cél URL</label>
                        <input type="text" name="kulon_hasab_ad_url" value="{{ cfg.ads.kulon_hasab_ad.url }}">
                    </div>
                </div>
            </div>

            <h3>3. A 9 Sorszámozott Reklámfelület Kezelése</h3>
            {% set ad_keys = [
                ('egyes_ad', 'Egyes Felület'), ('kettes_ad', 'Kettes Felület'), ('harmas_ad', 'Hármas Felület'),
                ('negyes_ad', 'Negyes Felület'), ('otos_ad', 'Ötös Felület'), ('hatos_ad', 'Hatos Felület'),
                ('hetes_ad', 'Hetes Felület'), ('nyolcas_ad', 'Nyolcas Felület'), ('kilences_ad', 'Kilences Felület')
            ] %}
            {% for key, label in ad_keys %}
            <div class="form-group">
                <strong style="color: #2ea6f2; font-size: 1.1rem;">{{ label }}</strong>
                <div class="ad-row">
                    <div style="width: 180px;">
                        <label>Típus</label>
                        <select name="{{ key }}_type">
                            <option value="text" {% if cfg.ads[key].type == 'text' %}selected{% endif %}>Sima Szöveg</option>
                            <option value="image" {% if cfg.ads[key].type == 'image' %}selected{% endif %}>Banner (Kép URL)</option>
                            <option value="video" {% if cfg.ads[key].type == 'video' %}selected{% endif %}>Google Videó (Direct MP4 URL)</option>
                        </select>
                    </div>
                    <div class="ad-col">
                        <label>Tartalom</label>
                        <input type="text" name="{{ key }}_content" value="{{ cfg.ads[key].content }}">
                    </div>
                    <div class="ad-col">
                        <label>Cél URL</label>
                        <input type="text" name="{{ key }}_url" value="{{ cfg.ads[key].url }}">
                    </div>
                </div>
            </div>
            {% endfor %}
            <button type="submit" class="btn-save">💾 Összes Beállítás Mentése És Élesítése</button>
        </form>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    global STORED_NEWS
    if not STORED_NEWS:
        STORED_NEWS = scrape_all_news()
    current_config = load_config()
    return render_template_string(HTML_TEMPLATE, news=STORED_NEWS, cfg=current_config)

@app.route("/hirdetes")
def hirdetes():
    return render_template_string(MARKETING_TEMPLATE)

@app.route("/impresszum")
def impresszum():
    szoveg = "<h3>Alapító-főszerkesztő és Tulajdonos:</h3><p>[A Te Neved]<br>E-mail: info@twnnews.hu</p>"
    return render_template_string(JOGI_TEMPLATE, cim="Impresszum", tartalom=szoveg)

@app.route("/aszf")
def aszf():
    szoveg = "<h3>1. Általános feltételek</h3><p>A használattal elfogadja az ÁSZF-et.</p>"
    return render_template_string(JOGI_TEMPLATE, cim="Általános Szerződési Feltételek (ÁSZF)", tartalom=szoveg)

@app.route("/adatvedelem")
def adatvedelem():
    szoveg = "<h3>1. Adatkezelés</h3><p>A TWN News megfelel a GDPR szabályoknak.</p>"
    return render_template_string(JOGI_TEMPLATE, cim="Adatvédelmi Tájékoztató (GDPR)", tartalom=szoveg)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not session.get("logged_in"):
        if request.method == "POST":
            if request.form.get("password") == ADMIN_PASSWORD:
                session["logged_in"] = True
                return redirect(url_for("admin"))
            return '<h3>Hibás jelszó! <a href="/admin">Újra</a></h3>'
        
        admin_login_html = (
            '<body style="font-family:sans-serif; background:#0f172a; color:#fff; text-align:center; padding-top:100px;">'
            '<form method="POST" style="background:#1e293b; display:inline-block; padding:30px; border-radius:8px; border:1px solid #475569;">'
            '<label style="display:block; margin-bottom:10px;">Admin Jelszó:</label>'
            '<input type="password" name="password" style="padding:8px; background:#0f172a; color:#fff; border:1px solid #475569;"><br><br>'
            '<button type="submit" style="background:#ff2a2a; color:#fff; border:0; padding:8px 15px; border-radius:4px; cursor:pointer;">Belépés</button>'
            '</form></body>'
        )
        return admin_login_html
    
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
