import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, redirect, url_for

app = Flask(__name__)

# A kért egyedi rovatstruktúra
STORED_NEWS = {
    "Belföld": [],
    "Külföld": [],
    "Gazdaság": [],
    "Vallás, Hit & Erkölcs": [],
    "AI Tech & Tudomány": []
}

# JELENLEGI VIDEÓK (Ezt a következő lépésben tesszük számodra külsőleg kezelhetővé)
SPONSOR_VIDEOS = {
    "Belföld": "https://youtube.com",
    "AI Tech & Tudomány": "https://youtube.com"
}

def get_category_and_image(title, index):
    t = title.lower()
    images = {
        "vallas": ["https://unsplash.com", "https://unsplash.com"],
        "tech": ["https://unsplash.com", "https://unsplash.com"],
        "gazdasag": ["https://unsplash.com", "https://unsplash.com"],
        "belfold": ["https://unsplash.com", "https://unsplash.com"],
        "kulfold": ["https://unsplash.com", "https://unsplash.com"]
    }
    img_idx = index % 2

    if any(w in t for w in ["templom", "vallás", "hit ", "hitélet", "pápa", "egyház", "isten", "biblia", "izrael", "zsidó", "keresztény", "erkölcs"]):
        return "Vallás, Hit & Erkölcs", images["vallas"][img_idx]
    elif any(w in t for w in ["tech", "ai", "mesterséges", "robot", "tudomány", "okostelefon", "drón", "űr", "kütyü", "internet", "google"]):
        return "AI Tech & Tudomány", images["tech"][img_idx]
    elif any(w in t for w in ["gazdaság", "forint", "euró", "pénz", "tőzsde", "részvény", "szankció", "infláció", "hitel", "bank"]):
        return "Gazdaság", images["gazdasag"][img_idx]
    elif any(w in t for w in ["fidesz", "orbán", "kormány", "belföld", "budapest", "parlament", "magyar"]):
        return "Belföld", images["belfold"][img_idx]
    else:
        return "Külföld", images["kulfold"][img_idx]

def scrape_all_news():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    categories = {"Belföld": [], "Külföld": [], "Gazdaság": [], "Vallás, Hit & Erkölcs": [], "AI Tech & Tudomány": []}
    count = 0
    try:
        res = requests.get("https://hirkereso.hu", headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, "html.parser")
            for link in soup.find_all("a", href=True):
                title = link.get_text(strip=True)
                href = link["href"]
                if title and len(title) > 25:
                    cat, img = get_category_and_image(title, count)
                    categories[cat].append({"title": title, "link": href, "image": img, "source": "Hírkereső"})
                    count += 1
                if count >= 30: break
    except Exception as e:
        print(f"Hiba: {e}")

    international_urls = ["https://bbci.co.uk", "https://bbci.co.uk"]
    for url in international_urls:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "xml")
                for item in soup.find_all("item"):
                    title = item.title.get_text(strip=True) if item.title else ""
                    link = item.link.get_text(strip=True) if item.link else ""
                    if title and link:
                        cat, img = get_category_and_image(title, count)
                        source_name = "BBC News" if "bbc" in url else "CNN"
                        categories[cat].append({"title": f"[NEMZETKÖZI] {title}", "link": link, "image": img, "source": source_name})
                        count += 1
                    if count >= 50: break
        except Exception as e:
            print(f"Hiba: {e}")
    return categories
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>THE WEEKLY NEWS</title>
    <style>
        :root {
            --bg-color: #edeef0;
            --card-bg: #ffffff;
            --text-dark: #111111;
            --accent-red: #ff2a2a;
            --nav-blue: #0c1a2c;
            --border-gray: #d1d5db;
        }
        
        body { 
            font-family: 'Georgia', serif; 
            margin: 0; 
            padding: 0; 
            background-color: var(--bg-color); 
            color: var(--text-dark);
        }

        /* PRÉMIUM KÉKES-PALASZÜRKE FEJLÉC HÁTTÉR */
        header { 
            background-color: #334155; 
            padding: 3rem 1rem 1.5rem 1rem; 
            text-align: center;
            border-bottom: 1px solid var(--border-gray);
        }

        .brand-container {
            display: inline-block;
            border-top: 1.5px solid #ffffff;
            border-bottom: 1.5px solid #ffffff;
            padding: 0.6rem 2.5rem;
            margin-bottom: 0.5rem;
        }

        .logo-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 12px;
        }

        .logo-the {
            font-size: 4.8rem;
            font-weight: bold;
            font-family: 'Times New Roman', Times, serif;
            color: #ffffff;
            line-height: 0.75;
            letter-spacing: -3px;
            transform: scaleY(1.1);
            border-right: 1.5px solid #ffffff;
            padding-right: 15px;
        }

        .logo-right-side {
            display: flex;
            flex-direction: column;
            align-items: flex-start;
        }

        .logo-weekly {
            font-size: 2.2rem;
            font-weight: 900;
            font-family: 'Arial Black', Gadget, sans-serif;
            letter-spacing: 2px;
            color: transparent;
            -webkit-text-stroke: 1px #ffffff;
            line-height: 0.9;
        }

        .logo-bottom-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 4px;
        }

        /* ÉLÉNK KÉK CHAT BUBORÉK */
        .logo-twn-bubble {
            background-color: #3ba2ff;
            color: #ffffff;
            font-family: 'Times New Roman', Times, serif;
            font-size: 1.1rem;
            font-weight: bold;
            font-style: italic;
            padding: 2px 10px;
            border-radius: 6px;
            position: relative;
            letter-spacing: 1px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .logo-twn-bubble::after {
            content: '';
            position: absolute;
            bottom: -6px;
            left: 25%;
            border-width: 6px 6px 0;
            border-style: solid;
            border-color: #3ba2ff transparent;
            display: block;
            width: 0;
        }

        .twn-t { color: #f39c12; }
        .twn-w { color: #ffffff; }
        .twn-n { color: #f39c12; }

        .logo-news {
            font-size: 2.6rem;
            font-weight: 900;
            font-family: 'Impact', 'Arial Black', sans-serif;
            color: var(--accent-red);
            letter-spacing: 0.5px;
            line-height: 0.9;
        }

        .sub-slogan {
            font-size: 1rem;
            letter-spacing: 12px;
            text-transform: uppercase;
            font-weight: bold;
            margin-top: 0.8rem;
            color: #cbd5e1;
            font-family: sans-serif;
            text-indent: 12px;
        }

        .nav-bar {
            background-color: var(--nav-blue);
            padding: 0px 1rem;
            display: flex;
            justify-content: center;
            overflow-x: auto;
        }

        .nav-item {
            color: white;
            font-family: sans-serif;
            font-weight: bold;
            padding: 1.1rem 1.5rem;
            text-decoration: none;
            font-size: 1.05rem;
            transition: background 0.2s;
        }

        .nav-item:hover {
            background-color: rgba(255,255,255,0.1);
        }

        .btn-refresh {
            background-color: var(--accent-red);
            color: white;
            border: none;
            padding: 1.1rem 1.5rem;
            font-family: sans-serif;
            font-weight: bold;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 1px;
            text-decoration: none;
        }

        .container { 
            max-width: 1300px; 
            margin: 3rem auto; 
            padding: 0 1.5rem; 
        }

        .rovat-section {
            margin-bottom: 5rem;
        }

        .rovat-title {
            font-family: sans-serif;
            font-size: 1.8rem;
            font-weight: 900;
            color: var(--nav-blue);
            border-bottom: 3px solid var(--nav-blue);
            padding-bottom: 0.3rem;
            margin-bottom: 2rem;
            text-transform: uppercase;
        }

        .magazine-layout {
            display: grid;
            grid-template-columns: 3fr 1fr;
            gap: 2rem;
        }

        @media (max-width: 1024px) {
            .magazine-layout { grid-template-columns: 1fr; }
        }

        .news-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.5rem;
        }

        .news-card { 
            background: var(--card-bg); 
            border: 1px solid var(--border-gray);
            display: flex;
            flex-direction: column;
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .news-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }

        .news-card img {
            width: 100%;
            height: 160px;
            object-fit: cover;
        }

        .card-body {
            padding: 1.2rem;
            display: flex;
            flex-direction: column;
            flex-grow: 1;
        }

        .source-badge {
            font-family: sans-serif;
            font-size: 0.75rem;
            font-weight: bold;
            color: var(--accent-red);
            text-transform: uppercase;
            margin-bottom: 0.5rem;
        }

        .card-body a { 
            color: var(--text-dark); 
            text-decoration: none; 
            font-size: 1.2rem; 
            font-weight: bold; 
            line-height: 1.3;
        }

        .card-body a:hover { 
            color: var(--nav-blue);
            text-decoration: underline;
        }

        .video-ad-box {
            background: #ffffff;
            border: 2px solid var(--nav-blue);
            padding: 1rem;
            align-self: start;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        }

        .video-ad-box h4 {
            margin: 0 0 0.8rem 0;
            font-family: sans-serif;
            font-size: 0.9rem;
            text-transform: uppercase;
            color: var(--accent-red);
            letter-spacing: 1px;
            border-bottom: 1px solid var(--border-gray);
            padding-bottom: 0.3rem;
        }

        .video-container {
            position: relative;
            padding-bottom: 56.25%;
            height: 0;
            overflow: hidden;
        }

        .video-container iframe {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            border: 0;
        }
    </style>
</head>
<body>

    <header>
        <div class="brand-container">
            <div class="logo-row">
                <div class="logo-the">THE</div>
                <div class="logo-right-side">
                    <div class="logo-weekly">WEEKLY</div>
                    <div class="logo-bottom-row">
                        <div class="logo-twn-bubble">
                            <span class="twn-t">T</span>
                            <span class="twn-w">W</span>
                            <span class="twn-n">N</span>
                        </div>
                        <div class="logo-news">NEWS</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="sub-slogan">Közéleti Hetilap</div>
    </header>

    <div class="nav-bar">
        <a href="/frissites" class="btn-refresh">🔄 Frissítés</a>
        <a href="#belfold" class="nav-item">Belföld</a>
        <a href="#kulfold" class="nav-item">Külföld</a>
        <a href="#gazdasag" class="nav-item">Gazdaság</a>
        <a href="#vallas" class="nav-item">Vallás, Hit & Erkölcs</a>
        <a href="#tech" class="nav-item">AI Tech & Tudomány</a>
    </div>

    <div class="container">
        {% for rovat, cikkek in news.items() %}
            {% if cikkek %}
                {% set anchor = "belfold" if rovat == "Belföld" else "kulfold" if rovat == "Külföld" else "gazdasag" if rovat == "Gazdaság" else "vallas" if rovat == "Vallás, Hit & Erkölcs" else "tech" %}
                <div class="rovat-section" id="{{ anchor }}">
                    <div class="rovat-title">{{ rovat }}</div>
                    
                    <div class="magazine-layout">
                        <div class="news-grid">
                            {% for item in cikkek %}
                                <div class="news-card">
                                    <img src="{{ item.image }}" alt="Magazin">
                                    <div class="card-body">
                                        <div class="source-badge">🔴 {{ item.source }}</div>
                                        <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                                    </div>
                                </div>
                            {% endfor %}
                        </div>

                  <div class="sidebar-magazin-block" style="width: 100%; margin-bottom: 25px; font-family: sans-serif;">
    
    <!-- 1. HETI SZÍNES BORÍTÓKÉP (Amit mappa-szinten, kód nélkül cserélsz) -->
    <div style="margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <img src="/static/friss_magazin.jpg" alt="Aktuális Borító" style="width: 100%; height: auto; display: block;">
    </div>

    <!-- 2. REKLÁMVIDEÓ: Közvetlenül alatta némítva, magától indul -->
    <div style="border: 1px solid #e0e0e0; padding: 8px; background: #fafafa; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <h4 style="color: #ff0000; font-size: 11px; text-align: center; letter-spacing: 1px; margin: 5px 0 8px 0; font-weight: bold;">🚨 AJÁNLOTT PARTNER VIDEÓ</h4>
        <iframe 
            width="100%" 
            height="180" 
            src="https://youtube.com" 
            frameborder="0" 
            allow="autoplay; encrypted-media" 
            allowfullscreen
            style="border-radius: 2px;">
        </iframe>
    </div>

</div>

                    </div>

                </div>
            {% endif %}
        {% endfor %}
    </div>

</body>
</html>
"""

@app.route("/")
def index():
    global STORED_NEWS
    if not any(STORED_NEWS.values()):
        STORED_NEWS = scrape_all_news()
    return render_template_string(HTML_TEMPLATE, news=STORED_NEWS, sponsor_videos=SPONSOR_VIDEOS)

@app.route("/frissites")
def refresh():
    global STORED_NEWS
    STORED_NEWS = scrape_all_news()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
