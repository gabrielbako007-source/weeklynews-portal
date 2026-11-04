import os
import json
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, redirect, url_for, send_from_directory, request, session

# A 2. RENDSZER BLUEPRINT MOTORJÁNAK BEEMELÉSE
from admin_rendszer import admin_bp

app = Flask(__name__)
app.secret_key = "twn_super_secret_key_for_session"

# A 2. RENDSZER BLUEPRINT REGISZTRÁCIÓJA
app.register_blueprint(admin_bp)

CONFIG_FILE = "twn_config.json"
ADMIN_PASSWORD = "twnadmin2026"

# AZ EREDETI CONFIG STRUKTÚRA TELJES VISSZAÁLLÍTÁSA
DEFAULT_CONFIG = {
    "cover_links": {
        "kulfold_politika": "https://twnnews.hu",
        "venia_sokk": "https://twnnews.hu",
        "vallas_hit": "https://twnnews.hu",
        "tudomany_tech": "https://twnnews.hu"
    },
    "ads": {
        "vallas_ad": {"type": "text", "content": "Saját Hirdetési Felület — Helyfoglalás az Adminban!", "url": "/hirdetes"},
        "gazdasag_ad": {"type": "text", "content": "Prémium Reklámfelület — TWN Ad Space", "url": "/hirdetes"},
        "tech_ad": {"type": "text", "content": "Saját Hirdetési Felület — Eladó hirdetési hely", "url": "/hirdetes"}
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>THE WEEKLY TWN NEWS</title>
    <style>
        body { 
            font-family: 'Arial', sans-serif; 
            margin: 0; padding: 0; 
            background-color: #1e293b; 
            color: #ffffff;
            overflow-x: hidden;
        }
        
        .frozen-top-header {
            position: sticky;
            top: 0;
            z-index: 1000;
            width: 100%;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
        }
        header { 
            background-color: #0f172a; 
            padding: 1.5rem 1rem; 
            text-align: center;
            border-bottom: 3px solid #ff2a2a;
        }
        .header-logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
        }
        
        .logo-box-html {
            background-color: transparent;
            padding: 6px 0;
            border-top: 1px solid #e2e8f0;    
            border-bottom: 1px solid #e2e8f0; 
            display: inline-flex;
            align-items: stretch;
            font-family: 'Bodoni Moda', serif;
            position: relative;
        }
        .logo-text-the {
            font-size: 78px;
            font-weight: 400;
            color: #e2e8f0;
            line-height: 0.85;
            letter-spacing: -3px;
            padding-right: 14px;
            display: flex;
            align-items: center;
        }
        .logo-right-wrapper {
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            width: 215px;
            padding-left: 2px;
        }
        .logo-text-weekly {
            font-family: 'Bodoni Moda', serif;
            font-size: 40px;
            font-weight: 700;
            letter-spacing: 1.5px;
            color: transparent;
            -webkit-text-stroke: 1px #e2e8f0;
            line-height: 0.95;
            text-transform: uppercase;
            width: 100%;
        }
        .logo-bottom-row-wrapper {
            display: flex;
            align-items: center;
            justify-content: space-between;
            width: 100%;
            margin-top: auto;
        }
        .logo-twn-badge {
            background-color: #2ea6f2;
            padding: 1px 7px;
            border-radius: 5px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            position: relative;
            font-family: 'Bodoni Moda', serif;
            font-style: italic;
            font-weight: 700;
            font-size: 24px;
            line-height: 1;
        }
        .logo-twn-badge span:nth-child(1) { color: #111827; }
        .logo-twn-badge span:nth-child(2) { color: #ffffff; }
        .logo-twn-badge span:nth-child(3) { color: #e62129; }
        
        .logo-text-news {
            font-family: 'Oswald', sans-serif;
            font-size: 38px;
            font-weight: 700;
            color: #e62129;
            line-height: 0.9;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .news-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; width: 100%; }
        .ujsag-box-card { background: #0f172a; border: 1px solid #475569; border-radius: 6px; padding: 15px; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .ujsag-logo-img { width: 100%; height: auto; border-radius: 6px; margin-bottom: 12px; border: 1px solid #334155; }
      
        .cikk-row { width: 100%; border-top: 1px solid #233142; padding-top: 8px; margin-top: 8px; text-align: left; }
        .cikk-link { font-size: 0.95rem; font-weight: bold; color: #ffffff; text-decoration: none; line-height: 1.4; display: block; }
        .cikk-link:hover { color: #2ea6f2; text-decoration: underline; }
        
        .twn-mini-ad { background-color: #1a202c; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; width: 100%; box-sizing: border-box; text-align: center; margin: 10px 0; overflow: hidden; }
        .ad-label { font-size: 0.7rem; color: #a0aec0; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 5px; }
        .ad-text { font-size: 0.85rem; color: #cbd5e1; font-weight: bold; text-decoration: none; }
        .ad-img { width: 100%; height: auto; border-radius: 4px; display: block; }
        .video-container { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; background: #000; border-radius: 4px; }
        .video-container iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }
        footer {
            background-color: #737373; 
            padding: 30px 20px;
            margin-top: 5rem;
            border-top: 4px solid #ff2a2a;
        }
        .footer-top-container {
            max-width: 1400px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 30px;
        }
        .footer-logo-area {
            background: #fff;
            padding: 15px 25px;
            border-radius: 8px;
            display: inline-block;
        }
        .footer-logo-text {
            color: #1e293b;
            font-family: 'Bodoni Moda', serif;
            font-size: 2.2rem;
            font-weight: bold;
        }
        .footer-links-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px 30px;
        }
        .footer-link {
            color: #ffffff;
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .footer-bottom-dark-bar {
            background-color: #171717; 
            padding: 25px 20px;
            font-size: 0.8rem;
            color: #a3a3a3;
            line-height: 1.6;
        }
        .footer-bottom-container { max-width: 1400px; margin: 0 auto; }
@media (max-width: 768px) {
    .frozen-top-header {
        position: sticky !important;
        top: 0 !important;
        z-index: 1000 !important;
        width: 100% !important;
        display: block !important;
    }
    .three-column-grid-container {
        margin-top: 10px !important;
        padding-top: 0 !important;
    }
    .nav-bar {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        white-space: nowrap !important;
        width: 100% !important;
        padding: 2px 5px !important;
        box-sizing: border-box !important;
        -webkit-overflow-scrolling: touch;
    }
    .nav-bar a.nav-item, .nav-bar a.btn-refresh {
        display: inline-block !important;
        flex-shrink: 0 !important;
        margin-right: 15px !important;
        float: none !important;
    }
    .nav-bar a.nav-item-marketing, [href*="hirdetes"] {
        display: block !important;
        width: 90% !important;
        margin: 15px auto 5px auto !important;
        text-align: center !important;
        clear: both !important;
        float: none !important;
    }
    .footer-bottom-dark-bar, footer, .footer {
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        text-align: center !important;
        gap: 10px !important;
        padding: 20px !important;
        width: 100% !important;
        box-sizing: border-box !important;
    }
    .footer-bottom-dark-bar div, footer div, .footer div {
        display: flex !important;
        flex-wrap: wrap !important;
        justify-content: center !important;
        gap: 10px !important;
        width: 100% !important;
    }
    .footer-bottom-dark-bar a, footer a, .footer a {
        display: inline-block !important;
        font-size: 13px !important;
        white-space: nowrap !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    .footer-bottom-dark-bar p, footer p, .footer-bottom-dark-bar span, .footer p {
        display: block !important;
        width: 100% !important;
        white-space: nowrap !important;
        font-size: 12px !important;
        text-align: center !important;
        margin-top: 10px !important;
    }
}
@media (min-width: 769px) {
    .footer-bottom-dark-bar div, footer div, .footer div, .footer-links-grid {
        display: flex !important;
        flex-direction: row !important;
        justify-content: center !important;
        gap: 25px !important;
        width: 100% !important;
    }
    .footer-bottom-dark-bar a, footer a, .footer a {
        display: inline-block !important;
        white-space: nowrap !important;
    }
}
    </style>
</head>
<body>
    <div class="frozen-top-header">
        <header>
            <div class="header-logo-container">
                <img src="/twn_logo.png" style="max-width: 480px; width: 100%; height: auto; display: block; margin: 0 auto; padding: 0; mix-blend-mode: screen;">
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
                            <div class="cikk-row">
                                <a href="{{ cikk.link }}" target="_blank" class="cikk-link">{{ cikk.title }}</a>
                            </div>
                        {% endfor %}
                    </div>
                    
                    <div class="twn-mini-ad">
                        <span class="ad-label">Hirdetés / Premium Ad</span>
                        {% if cfg.ads.vallas_ad.type == 'youtube' %}
                            <div class="video-container">
                                <iframe src="https://youtube.com{{ cfg.ads.vallas_ad.content }}" allowfullscreen></iframe>
                            </div>
                        {% elif cfg.ads.vallas_ad.type == 'image' %}
                            <a href="{{ cfg.ads.vallas_ad.url }}" target="_blank"><img src="{{ cfg.ads.vallas_ad.content }}" class="ad-img"></a>
                        {% else %}
                            <a href="{{ cfg.ads.vallas_ad.url }}" target="_blank" class="ad-text">{{ cfg.ads.vallas_ad.content }}</a>
                        {% endif %}
                    </div>
                {% endfor %}
            </div>
            <div class="rovat-section" id="gazdasag">
                <div class="rovat-title">Gazdaság</div>
                <div class="side-column-stream">
                    {% for ujsag in news['Gazdaság'] %}
                        <div class="ujsag-box-card">
                            <img src="/logo_kepek/{{ ujsag.logo }}" class="ujsag-logo-img" alt="Logó">
                            {% for cikk in ujsag.cikkek %}
                                <div class="cikk-row">
                                    <a href="{{ cikk.link }}" target="_blank" class="cikk-link">{{ cikk.title }}</a>
                                </div>
                            {% endfor %}
                        </div>
                        
                        <div class="twn-mini-ad">
                            <span class="ad-label">Hirdetés / Premium Ad</span>
                            {% if cfg.ads.gazdasag_ad.type == 'youtube' %}
                                <div class="video-container">
                                    <iframe src="https://youtube.com{{ cfg.ads.gazdasag_ad.content }}" allowfullscreen></iframe>
                                </div>
                            {% elif cfg.ads.gazdasag_ad.type == 'image' %}
                                <a href="{{ cfg.ads.gazdasag_ad.url }}" target="_blank"><img src="{{ cfg.ads.gazdasag_ad.content }}" class="ad-img"></a>
                            {% else %}
                                <a href="{{ cfg.ads.gazdasag_ad.url }}" target="_blank" class="ad-text">{{ cfg.ads.gazdasag_ad.content }}</a>
                            {% endif %}
                        </div>
                    {% endfor %}
                </div>
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
            <div class="rovat-section" id="belfold">
                <div class="rovat-title">Belföld hírei</div>
                <div class="news-grid">
                    {% for ujsag in news['Belföld'] %}
                        <div class="ujsag-box-card">
                            <img src="/logo_kepek/{{ ujsag.logo }}" class="ujsag-logo-img" alt="Logó">
                            {% for cikk in ujsag.cikkek %}
                                <div class="cikk-row">
                                    <a href="{{ cikk.link }}" target="_blank" class="cikk-link">{{ cikk.title }}</a>
                                </div>
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
                                <div class="cikk-row">
                                    <a href="{{ cikk.link }}" target="_blank" class="cikk-link">{{ cikk.title }}</a>
                                </div>
                            {% endfor %}
                        </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        <!-- ================= JOBB HASÁB ================= -->
        <div class="side-column-stream">
            <div class="rovat-section" id="tech">
                <div class="rovat-title">Család & Tech</div>
                <div class="side-column-stream">
                    {% for ujsag in news['Család & Tech'] %}
                        <div class="ujsag-box-card">
                            <img src="/logo_kepek/{{ ujsag.logo }}" class="ujsag-logo-img" alt="Logó">
                            {% for cikk in ujsag.cikkek %}
                                <div class="cikk-row">
                                    <a href="{{ cikk.link }}" target="_blank" class="cikk-link">{{ cikk.title }}</a>
                                </div>
                            {% endfor %}
                        </div>
                        
                        {% if loop.index % 2 == 0 %}
                            <div class="twn-mini-ad">
                                <span class="ad-label">Hirdetés / Premium Ad</span>
                                {% if cfg.ads.tech_ad.type == 'youtube' %}
                                    <div class="video-container">
                                        <iframe src="https://youtube.com{{ cfg.ads.tech_ad.content }}" allowfullscreen></iframe>
                                    </div>
                                {% elif cfg.ads.tech_ad.type == 'image' %}
                                    <a href="{{ cfg.ads.tech_ad.url }}" target="_blank"><img src="{{ cfg.ads.tech_ad.content }}" class="ad-img"></a>
                                {% else %}
                                    <a href="{{ cfg.ads.tech_ad.url }}" target="_blank" class="ad-text">{{ cfg.ads.tech_ad.content }}</a>
                                {% endif %}
                            </div>
                        {% endif %}
                    {% endfor %}
                </div>
            </div>
        </div>
    </div> <!-- GRID LEZÁRÁSA -->
    <footer>
        <div class="footer-top-container">
            <div class="footer-links-grid">
                <a href="/impresszum" class="footer-link">I Impresszum</a>
                <a href="/aszf" class="footer-link">I ÁSZF</a>
                <a href="/adatvedelem" class="footer-link">I Adatvédelem</a>
                <a href="/hirdetes" class="footer-link">I Médiaajánlat</a>
                <a href="/magazin/titkos-admin" class="footer-link" style="color: #ff2a2a; text-shadow: 0 0 10px rgba(255,42,42,0.3);">I Szerkesztőségi Belépés</a>
            </div>
        </div>
    </footer>
    
    <div class="footer-bottom-dark-bar">
        <div class="footer-bottom-container">
            <p>&copy; 2026 THE WEEKLY TWN NEWS. Minden jog fenntartva.</p>
        </div>
    </div>
</body>
</html>
"""

# ================= JOGI ÉS MARKETING SABLONOK =================
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
        h3 { color: #ff2a2a; margin-top: 25px; }
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
        <p><strong>Elérhető felületeink:</strong> Kiemelt képes bannerek, beágyazott hirdetések a hasábok között, és egyedi PR cikkek.</p>
        <p>Kapcsolatfelvétel: <strong>info@twnnews.hu</strong></p>
        <a href="/" class="back-btn">⬅ Vissza a címlapra</a>
    </div>
</body>
</html>
"""

# ================= FLASK ÚTVONALAK (ROUTES) =================
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
    szoveg = "<h3>Alapító-főszerkesztő és Tulajdonos:</h3><p>Weekly News Szerkesztőség<br>E-mail: info@twnnews.hu</p><h3>Felelősségi nyilatkozat:</h3><p>A TWN News felületén megjelenő hírek jelentős része egy automatizált rendszeren keresztül, külső sajtóorgánumok nyilvánosan elérhető RSS csatornáiból származik.</p>"
    return render_template_string(JOGI_TEMPLATE, cim="Impresszum", tartalom=szoveg)

@app.route("/aszf")
def aszf():
    szoveg = "<h3>1. Általános feltételek</h3><p>A twnnews.hu használatával minden látogató automatikusan elfogadja a jelen Általános Szerződési Feltételeket.</p><h3>2. Hirdetések</h3><p>A hasábok között megjelenő egyedi reklámhelyeket a Hirdetők az Adminisztrációs felületen kezelhetik.</p>"
    return render_template_string(JOGI_TEMPLATE, cim="Általános Szerződési Feltételek (ÁSZF)", tartalom=szoveg)

@app.route("/adatvedelem")
def adatvedelem():
    szoveg = "<h3>1. Adatkezelés</h3><p>A TWN News kizárólag üzleti kapcsolattartás céljából kezel személyes adatokat (nevet és e-mail címet).</p>"
    return render_template_string(JOGI_TEMPLATE, cim="Adatvédelmi Tájékoztató (GDPR)", tartalom=szoveg)

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

@app.route("/twn_logo.png")
def serve_top_logo():
    return send_from_directory(os.getcwd(), "twn_logo.png")

# A FIXEN LEGALULRA HELYEZETT KÖZÖS SZERVER INDÍTÓBLOKK
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
