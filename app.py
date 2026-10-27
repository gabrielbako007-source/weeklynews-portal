import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, redirect, url_for, send_from_directory

app = Flask(__name__)

# 1. RÉSZLET: A 42 DARAB ÚJSÁG HIVATALOS HÍRFORRÁSAINAK LISTÁJA SORSZÁMOK SZERINT
HIRCATORNAK = {
    "1": {"name": "Origo", "url": "https://origo.hu"},
    "2": {"name": "Blikk", "url": "https://blikk.hu"},
    "3": {"name": "Nők Lapja Café", "url": "https://nlc.hu"},
    "4": {"name": "Femina", "url": "https://femina.hu"},
    "5": {"name": "Index", "url": "https://index.hu"},
    "6": {"name": "Telex", "url": "https://telex.hu"},
    "7": {"name": "24.hu", "url": "https://24.hu"},
    "8": {"name": "HVG", "url": "https://hvg.hu"},
    "9": {"name": "444.hu", "url": "https://444.hu"},
    "10": {"name": "Magyar Nemzet", "url": "https://magyarnemzet.hu"},
    "11": {"name": "RTL Híradó", "url": "https://rtl.hu"},
    "12": {"name": "TV2 Tények", "url": "https://tenyek.hu"},
    "13": {"name": "Népszava", "url": "https://nepszava.hu"},
    "14": {"name": "BorsOnline", "url": "https://borsonline.hu"},
    "15": {"name": "Glamour", "url": "https://glamour.hu"},
    "16": {"name": "Hetek Magazin", "url": "https://hetek.hu"},
    "17": {"name": "Portfolio", "url": "https://portfolio.hu"},
    "18": {"name": "Pénzcentrum", "url": "https://penzcentrum.hu"},
    "19": {"name": "Világgazdaság", "url": "https://vg.hu"},
    "20": {"name": "BBC News", "url": "https://bbci.co.uk"},
    "21": {"name": "Reuters", "url": "https://reutersagency.com"},
    "22": {"name": "The Guardian", "url": "https://theguardian.com"},
    "23": {"name": "Deutsche Welle", "url": "https://dw.com"},
    "24": {"name": "Der Spiegel", "url": "https://spiegel.de"},
    "25": {"name": "Sky News", "url": "https://skynews.com"},
    "26": {"name": "ABC News", "url": "https://go.com"},
    "27": {"name": "The Mirror", "url": "https://mirror.co.uk"},
    "28": {"name": "The Independent", "url": "https://independent.co.uk"},
    "29": {"name": "The Times", "url": "https://thetimes.com"},
    "30": {"name": "CNN", "url": "http://cnn.com"},
    "31": {"name": "The New York Times", "url": "https://nytimes.com"},
    "32": {"name": "BBC UK", "url": "https://bbci.co.uk"},
    "33": {"name": "The Washington Post", "url": "https://washingtonpost.com"},
    "34": {"name": "Tagesschau", "url": "https://tagesschau.de"},
    "35": {"name": "Bunte.de", "url": "https://bunte.de"},
    "36": {"name": "Blog.hu", "url": "https://blog.hu"},
    "37": {"name": "Gala", "url": "https://gala.de"},
    "38": {"name": "Bild", "url": "https://bild.de"},
    "39": {"name": "Closer", "url": "https://closerweekly.com"},
    "40": {"name": "Hello Magazin", "url": "https://hellomagazine.com"},
    "41": {"name": "Daily Mail", "url": "https://dailymail.co.uk"},
    "42": {"name": "The Sun", "url": "https://thesun.co.uk"}
}

STORED_NEWS = {}

def scrape_all_news():
    categories = {}
    for sorszam, info in HIRCATORNAK.items():
        categories[sorszam] = [
            {"title": f"Vezető hír és friss közéleti riport — {info['name']}", "link": info['url']},
            {"title": f"Rendkívüli gazdasági és nemzetközi összefoglaló", "link": info['url']}
        ]
    return categories
# 2. RÉSZLET: A PORTÁL TELJES STÍLUSA ÉS DIZÁJN SABLONJA
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
            background-color: #1e293b; /* PRÉMIUM PALASZÜRKE ALAPVILÁG */
            color: #ffffff;
        }
        
        header { 
            background-color: #0f172a; 
            padding: 1.8rem 1rem; 
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
        
        .nav-bar { background-color: #0f172a; padding: 0px 1rem; display: flex; justify-content: center; position: sticky; top: 0; z-index: 100; border-bottom: 1px solid #475569; }
        .btn-refresh { background-color: #ff2a2a; color: white; padding: 1.1rem 1.5rem; font-family: sans-serif; font-weight: bold; text-transform: uppercase; text-decoration: none; }
        
        /* 42-HASÁBOS AUTOMATIKUS PORTÁL ELRENDEZÉS */
        .portal-layout {
            display: flex;
            flex-wrap: wrap;
            gap: 25px;
            max-width: 1600px;
            width: 95%;
            margin: 2rem auto;
            justify-content: center;
        }

        .ujsag-column {
            background-color: #0f172a;
            border: 1px solid #475569;
            border-radius: 8px;
            width: 300px;
            padding: 15px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .ujsag-logo {
            width: 100%;
            height: auto;
            border-radius: 6px;
            margin-bottom: 15px;
            border: 1px solid #334155;
        }

        .cikk-card {
            width: 100%;
            border-top: 1px solid #334155;
            padding-top: 10px;
            margin-top: 10px;
        }

        .cikk-title {
            font-size: 0.95rem;
            font-weight: bold;
            color: #ffffff;
            text-decoration: none;
            line-height: 1.4;
            display: block;
        }
        .cikk-title:hover { color: #2ea6f2; text-decoration: underline; }

        /* GOOGLE-STÍLUSÚ MINI HIRDETÉSI BOX STÍLUSA */
        .twn-mini-ad {
            background-color: #1a202c;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 12px;
            width: 100%;
            box-sizing: border-box;
            text-align: center;
            margin-top: auto;
            padding-top: 15px;
        }
        .ad-label {
            font-size: 0.7rem;
            color: #a0aec0;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: block;
            margin-bottom: 5px;
        }
        .ad-text {
            font-size: 0.85rem;
            color: #cbd5e1;
            font-weight: bold;
        }
    </style>
</head>
<body>
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
    </div>

    <div class="portal-layout">
        {% for i in range(1, 43) %}
            {% set sorszam_str = i|string %}
            <div class="ujsag-column">
                <!-- BETÖLTI A JÓVÁHAGYOTT .jpg.jpg KÉPEKET HIBÁTLANUL -->
                <img src="/logo_kepek/{{ i }}.jpg.jpg" class="ujsag-logo" alt="Logó">
                
                {% for cikk in news[sorszam_str] %}
                    <div class="cikk-card">
                        <a href="{{ cikk.link }}" target="_blank" class="cikk-title">{{ cikk.title }}</a>
                    </div>
                {% endfor %}
                
                {% if i % 3 == 0 %}
                    <div class="twn-mini-ad">
                        <span class="ad-label">Hirdetés / Google Ad</span>
                        <span class="ad-text">Saját Hirdetési Felület — Helyfoglalás az Adminban!</span>
                    </div>
                {% endif %}
            </div>
        {% endfor %}
    </div>
</body>
</html>
"""
# 3. RÉSZLET: SZERVER INDÍTÁSA ÉS A .jpg.jpg KÉPEK KISZOLGÁLÁSA
@app.route("/")
def index():
    global STORED_NEWS
    if not STORED_NEWS:
        STORED_NEWS = scrape_all_news()
    return render_template_string(HTML_TEMPLATE, news=STORED_NEWS)

# BIZTONSÁGI CSATORNA: Egyenesen a főkönyvtárból olvassa be a képeket törés nélkül
@app.route('/logo_kepek/<path:filename>')
def serve_logos(filename):
    return send_from_directory('.', filename)

@app.route("/frissites")
def refresh():
    global STORED_NEWS
    STORED_NEWS = scrape_all_news()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
