import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, redirect, url_for, send_from_directory

app = Flask(__name__)

# 1. RÉSZLET: A 42 DARAB ÚJSÁG CSATORNÁJA KATEGÓRIÁK SZERINT PONTOSAN SZÉTVÁLOGATVA
HIRCATORNAK = {
    "Belföld": [
        {"id": "1", "name": "Origo"}, {"id": "2", "name": "Blikk"}, {"id": "3", "name": "Nők Lapja Café"},
        {"id": "4", "name": "Femina"}, {"id": "5", "name": "Index"}, {"id": "6", "name": "Telex"},
        {"id": "7", "name": "24.hu"}, {"id": "8", "name": "HVG"}, {"id": "9", "name": "444.hu"},
        {"id": "10", "name": "Magyar Nemzet"}, {"id": "11", "name": "RTL Híradó"}, 
        {"id": "12", "name": "TV2 Tények"}, {"id": "13", "name": "Népszava"}, {"id": "14", "name": "BorsOnline"}
    ],
    "Külföld": [
        {"id": "20", "name": "BBC News"}, {"id": "21", "name": "Reuters"}, {"id": "22", "name": "The Guardian"},
        {"id": "23", "name": "Deutsche Welle"}, {"id": "24", "name": "Der Spiegel"}, {"id": "25", "name": "Sky News"},
        {"id": "26", "name": "ABC News"}, {"id": "27", "name": "The Mirror"}, {"id": "28", "name": "The Independent"},
        {"id": "29", "name": "The Times"}, {"id": "30", "name": "CNN"}, {"id": "31", "name": "The New York Times"},
        {"id": "32", "name": "BBC UK"}, {"id": "33", "name": "The Washington Post"}, {"id": "34", "name": "Tagesschau"}
    ],
    "Gazdaság": [
        {"id": "17", "name": "Portfolio"}, {"id": "18", "name": "Pénzcentrum"}, {"id": "19", "name": "Világgazdaság"}
    ],
    "Vallás": [
        {"id": "16", "name": "Hetek Magazin"}
    ],
    "Család & Tech": [
        {"id": "15", "name": "Glamour"}, {"id": "35", "name": "Bunte.de"}, {"id": "36", "name": "Blog.hu"},
        {"id": "37", "name": "Gala"}, {"id": "38", "name": "Bild"}, {"id": "39", "name": "Closer"},
        {"id": "40", "name": "Hello Magazin"}, {"id": "41", "name": "Daily Mail"}, {"id": "42", "name": "The Sun"}
    ]
}

STORED_NEWS = {}

def fake_fetch_news(ujsag_id, ujsag_nev):
    # Kiválasztjuk a megfelelő linket, hogy a kattintás valódi oldalra vigyen
    link = "https://theweeklytwnnews.hu"
    for kat, lista in HIRCATORNAK.items():
        for u in lista:
            if u["id"] == ujsag_id:
                # Egyszerű tesztlinkek hozzárendelése, amik a megnyíló újságok főoldalára mutatnak
                if ujsag_id == "1": link = "https://origo.hu"
                elif ujsag_id == "2": link = "https://blikk.hu"
                elif ujsag_id == "3": link = "https://nlc.hu"
                elif ujsag_id == "16": link = "https://hetek.hu"
                elif ujsag_id == "17": link = "https://portfolio.hu"
                elif ujsag_id == "20": link = "https://bbc.com"
                elif ujsag_id == "22": link = "https://theguardian.com"
                elif ujsag_id == "30": link = "https://cnn.com"
                else: link = "https://index.hu"
    return [
        {"title": f"Vezető hír és friss közéleti riport — {ujsag_nev}", "link": link, "logo": f"{ujsag_id}.jpg.jpg"},
        {"title": f"Rendkívüli beszámoló és helyi elemzés", "link": link, "logo": f"{ujsag_id}.jpg.jpg"}
    ]

def scrape_all_news():
    categories = {"Belföld": [], "Külföld": [], "Gazdaság": [], "Vallás": [], "Család & Tech": []}
    for kat_nev, ujsagok in HIRCATORNAK.items():
        for ujsag in ujsagok:
            categories[kat_nev].append({
                "ujsag_name": ujsag["name"],
                "logo": f"{ujsag['id']}.jpg.jpg",
                "cikkek": fake_fetch_news(ujsag["id"], ujsag["name"])
            })
    return categories
# 2. RÉSZLET: A MOZDÍTHATATLAN (FROZEN) FEJLÉC ÉS A DIZÁJN STÍLUSLAPJA
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>THE WEEKLY TWN NEWS</title>
    <style>
        @import url('https://googleapis.com');

        body { 
            font-family: 'Arial', sans-serif; 
            margin: 0; padding: 0; 
            background-color: #1e293b; /* FIX PRÉMIUM PALASZÜRKE ALAPVILÁG */
            color: #ffffff;
            overflow-x: hidden;
        }
        
        /* TELJESEN RÖGZÍTETT, MOZDÍTHATATLAN FELSŐ SZEKCIÓ */
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
        
        /* LOGÓDIZÁJN HAJSZÁLPONTOS REKREÁCIÓJA EZÜSTÖS SZÍNEKKEL */
        .logo-box-html {
            background-color: transparent;
            padding: 6px 0;
            border-top: 1px solid #e2e8f0;    /* HAJSZÁLVÉKONY EZÜSTÖS FELSŐ CSÍK */
            border-bottom: 1px solid #e2e8f0; /* HAJSZÁLVÉKONY EZÜSTÖS ALSÓ CSÍK */
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
        .logo-twn-badge::after {
            content: '';
            position: absolute;
            bottom: -6px;
            left: 12px;
            width: 0;
            height: 0;
            border-width: 6px 6px 0 0;
            border-style: solid;
            border-color: #2ea6f2 transparent transparent transparent;
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
        
        .nav-bar { background-color: #0f172a; padding: 0px 1rem; display: flex; justify-content: center; border-bottom: 1px solid #475569; }
        .nav-item { color: white; font-family: sans-serif; font-weight: bold; padding: 1.1rem 1.5rem; text-decoration: none; font-size: 1.05rem; }
        .btn-refresh { background-color: #ff2a2a; color: white; padding: 1.1rem 1.5rem; font-family: sans-serif; font-weight: bold; text-transform: uppercase; text-decoration: none; }
        
        /* 3-HASÁBOS PRÉMIUM STRUKTÚRA REKREÁCIÓJA */
        .three-column-grid-container {
            display: grid;
            grid-template-columns: 320px 1fr 320px;
            gap: 2rem;
            max-width: 1700px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        @media (max-width: 1300px) {
            .three-column-grid-container { grid-template-columns: 1fr; }
        }
        
        .side-column-stream { display: flex; flex-direction: column; gap: 25px; }
        .center-news-stream { display: flex; flex-direction: column; align-items: center; }
        
        /* KÖZÉPSŐ FIX MAGAZINBORÍTÓ SZERKEZETE */
        .main-magazine-cover { width: 100%; max-width: 480px; margin: 0 auto 3rem auto; border: 2px solid #fff; box-shadow: 0 6px 20px rgba(0,0,0,0.5); }
        .main-magazine-cover img { width: 100%; height: auto; display: block; }
        
        .rovat-section { margin-bottom: 3.5rem; width: 100%; }
        .rovat-title { font-family: sans-serif; font-size: 1.6rem; font-weight: 900; color: #38bdf8; border-bottom: 3px solid #38bdf8; padding-bottom: 0.3rem; margin-bottom: 1.5rem; text-transform: uppercase; letter-spacing: 0.5px; }
        
        .news-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; width: 100%; }
        .ujsag-box-card { background: #0f172a; border: 1px solid #475569; border-radius: 6px; padding: 15px; box-sizing: border-box; display: flex; flex-direction: column; align-items: center; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
        .ujsag-logo-img { width: 100%; height: auto; border-radius: 6px; margin-bottom: 12px; border: 1px solid #334155; }
        
        .cikk-row { width: 100%; border-top: 1px solid #233142; padding-top: 8px; margin-top: 8px; text-align: left; }
        .cikk-link { font-size: 0.95rem; font-weight: bold; color: #ffffff; text-decoration: none; line-height: 1.4; display: block; }
        .cikk-link:hover { color: #2ea6f2; text-decoration: underline; }

        /* SŰRŰBB, EZÜSTÖS MINI GOOGLE HIRDETÉSI BOXOK */
        .twn-mini-ad { background-color: #1a202c; border: 1px solid #e2e8f0; border-radius: 6px; padding: 12px; width: 100%; box-sizing: border-box; text-align: center; margin: 10px 0; }
        .ad-label { font-size: 0.7rem; color: #a0aec0; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 5px; }
        .ad-text { font-size: 0.85rem; color: #cbd5e1; font-weight: bold; }
    </style>
</head>
"""
# 3. RÉSZLET: A HÁROMHASÁBOS ELRENDEZÉS ÉS A SZERVER INDÍTÁSA
HTML_TEMPLATE += """
<body>

    <!-- A MOZDÍTHATATLAN LEFAGYASZTOTT FELSŐ SÁV (LOGÓ + MENÜ) -->
    <div class="frozen-top-header">
        <header>
            <div class="header-logo-container">
                <div class="logo-box-html">
                    <div class="logo-text-the">THE</div>
                    <div class="logo-right-wrapper">
                        <div class="logo-text-weekly">WEEKLY</div>
                        <div class="logo-bottom-row-wrapper">
                            <div class="logo-twn-badge">
                                <span>T</span><span>W</span><span>N</span>
                            </div>
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
        </div>
    </div>

    <!-- A TÖKÉLETES HÁROMHASÁBOS MAGAZIN STRUKTÚRA -->
    <div class="three-column-grid-container">
        
        <!-- ================= BAL HASÁB ================= -->
        <div class="side-column-stream">
            <!-- ROVAT: VALLÁS -->
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
                        <span class="ad-label">Hirdetés / Google Ad</span>
                        <span class="ad-text">Saját Hirdetési Felület — Helyfoglalás az Adminban!</span>
                    </div>
                {% endfor %}
            </div>

            <!-- ROVAT: GAZDASÁG -->
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
                            <span class="ad-label">Hirdetési zóna</span>
                            <span class="ad-text">Prémium Reklámfelület — TWN Ad Space</span>
                        </div>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- ================= KÖZÉPSŐ HASÁB ================= -->
        <div class="center-news-stream">
            <!-- A FIXEN KÖZÉPRE REKREÁLT NAGY MAGAZINBORÍTÓ -->
            <div class="main-magazine-cover">
                <img src="/friss_magazin.jpg" alt="The Weekly News Címlap">
            </div>

            <!-- ROVAT: BELFÖLD -->
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

            <!-- ROVAT: KÜLFÖLD -->
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
            <!-- ROVAT: CSALÁD & TECH -->
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
                                <span class="ad-label">Hirdetési zóna</span>
                                <span class="ad-text">Saját Hirdetési Felület — Eladó hirdetési hely</span>
                            </div>
                        {% endif %}
                    {% endfor %}
                </div>
            </div>
        </div>

    </div>

</body>
</html>
"""

@app.route("/")
def index():
    global STORED_NEWS
    if not STORED_NEWS:
        STORED_NEWS = scrape_all_news()
    return render_template_string(HTML_TEMPLATE, news=STORED_NEWS)

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
