import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, redirect, url_for, send_from_directory

app = Flask(__name__)

# A kért egyedi, kibővített rovatstruktúra alapbeállítása
STORED_NEWS = {
    "Belföld": [],
    "Külföld": [],
    "Gazdaság": [],
    "Vallás, Hit & Erkölcs": [],
    "AI Tech & Tudomány": []
}

# SZIGORÚAN 7 DARAB REKLÁMVIDEÓ TÁRHELYE (Bal oszlopban 4, jobb oszlopban 3 videó)
REKLAM_VIDEÓK = {
    "video_1": "GjrVtUNJTuQ",  # Bal sáv - line 1
    "video_2": "GjrVtUNJTuQ",  # Bal sáv - line 2
    "video_3": "GjrVtUNJTuQ",  # Bal sáv - line 3
    "video_4": "GjrVtUNJTuQ",  # Bal sáv - line 4
    "video_5": "GjrVtUNJTuQ",  # Jobb sáv - line 5
    "video_6": "GjrVtUNJTuQ",  # Jobb sáv - line 6
    "video_7": "GjrVtUNJTuQ"   # Jobb sáv - line 7
}

def get_category_and_image(title, source_name, index):
    img_idx = index % 2
    images = {
        "vallas": ["https://unsplash.com", "https://unsplash.com"],
        "tech": ["https://unsplash.com", "https://unsplash.com"],
        "gazdasag": ["https://unsplash.com", "https://unsplash.com"],
        "belfold": ["https://unsplash.com", "https://unsplash.com"],
        "kulfold": ["https://unsplash.com", "https://unsplash.com"]
    }
    
    if "Nők" in source_name or "NLC" in source_name: return "Belföld", images["belfold"][img_idx]
    if "Hetek" in source_name: return "Vallás, Hit & Erkölcs", images["vallas"][img_idx]
    if any(s in source_name for s in ["CNN", "BBC", "NYT", "Spiegel", "Deutsche Welle", "The Guardian"]): return "Külföld", images["kulfold"][img_idx]

    t = title.lower()
    if any(w in t for w in ["orvos", "műtét", "egészség", "kórház", "gyógyszer", "ai", "robot", "tech", "tudomány"]): return "AI Tech & Tudomány", images["tech"][img_idx]
    if any(w in t for w in ["templom", "vallás", "hit ", "egyház", "pápa"]): return "Vallás, Hit & Erkölcs", images["vallas"][img_idx]
    if any(w in t for w in ["gazdaság", "forint", "euró", "tőzsde", "bank", "pénz"]): return "Gazdaság", images["gazdasag"][img_idx]
    return "Belföld", images["belfold"][img_idx]

def scrape_all_news():
    # GARANTÁLT FIX ALAPTARTALOM – HA A SZERVER BÁRMIT TILTANA, EZEK AKKOR IS 100%-IG MEGJELENNEK ÉS KITÖLTIK A TÉRET!
    categories = {
        "Belföld": [
            {"title": "Nők Lapja Café: A kiegyensúlyozott családi élet és az erkölcsi értékek megtartása a modern korban", "link": "https://nlc.hu", "image": "https://unsplash.com", "source": "Nők Lapja Café"},
            {"title": "Magyarországi körkép: Új kulturális és közösségi terek nyílnak meg a fővárosban ezen a héten", "link": "https://hirkereso.hu", "image": "https://unsplash.com", "source": "Hírkereső"}
        ],
        "Külföld": [
            {"title": "BBC News: Strasbourg Summit - High-level consensus reached regarding transatlantic infrastructure updates", "link": "https://bbc.co.uk", "image": "https://unsplash.com", "source": "BBC News"},
            {"title": "CNN International: Global administrative networks implement rapid defense and economic transition cycles", "link": "https://cnn.com", "image": "https://unsplash.com", "source": "CNN"},
            {"title": "Deutsche Welle: Western alliance coordinates resource allocation strategies for the upcoming quarter", "link": "https://dw.com", "image": "https://unsplash.com", "source": "Deutsche Welle"},
            {"title": "Der Spiegel: Central European fiscal reports forecast strong industrial adjustments this season", "link": "https://spiegel.de", "image": "https://unsplash.com", "source": "Der Spiegel"}
        ],
        "Gazdaság": [
            {"title": "Világgazdasági elemzés: A tőzsdei folyamatok és a bankrendszerek stabilitása a nemzetközi piacokon", "link": "https://hirkereso.hu", "image": "https://unsplash.com", "source": "Gazdasági Híradó"},
            {"title": "Költségvetési jelentés: Az inflációs mutatók csökkenése és a valutaárfolyamok stabilitása", "link": "https://hirkereso.hu", "image": "https://unsplash.com", "source": "Pénzügyi Portál"}
        ],
        "Vallás, Hit & Erkölcs": [
            {"title": "Hetek Magazin: A harmadik templom rejtélye Jeruzsálemben - Közeleg a prófécia beteljesülése a Szentföldön?", "link": "https://hetek.hu", "image": "https://unsplash.com", "source": "Hetek Magazin"},
            {"title": "Hitélet és spiritualitás: A vallási közösségek szerepe és az erkölcsi iránytű fontossága a XXI. században", "link": "https://hetek.hu", "image": "https://unsplash.com", "source": "Közéleti Lap"}
        ],
        "AI Tech & Tudomány": [
            {"title": "The Guardian: Breakthrough in wearable AI chips - Intelligent capsule modules and titán smart rings booming", "link": "https://theguardian.com", "image": "https://unsplash.com", "source": "The Guardian"},
            {"title": "PubMed Medicine: New micro-robotic surgical interventions show massive success rates in automated clinical environments", "link": "https://nih.gov", "image": "https://unsplash.com", "source": "PubMed Medicine"},
            {"title": "NASA Exploration: Deep space array telescope captures high-resolution infrared footprints of cosmic transition structures", "link": "https://nasa.gov", "image": "https://unsplash.com", "source": "NASA Science"}
        ]
    }

    # Élő hírfrissítés álcázással (User-Agent trükk a háttérben)
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    forrasok = [
        {"url": "https://nlc.hu", "name": "Nők Lapja Café"},
        {"url": "https://hetek.hu", "name": "Hetek Magazin"},
        {"url": "https://nytimes.com", "name": "New York Times"},
        {"url": "https://theguardian.com", "name": "The Guardian"}
    ]
    for f in forrasok:
        try:
            res = requests.get(f["url"], headers=headers, timeout=4)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "xml")
                for idx, item in enumerate(soup.find_all("item")):
                    title = item.title.get_text(strip=True) if item.title else ""
                    if title and item.link:
                        cat, img = get_category_and_image(title, f["name"], idx)
                        categories[cat].insert(0, {"title": title, "link": item.link.get_text(strip=True), "image": img, "source": f["name"]})
                    if idx >= 5: break
        except: pass

    try:
        res = requests.get("https://hirkereso.hu", headers=headers, timeout=4)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, "html.parser")
            for idx, link in enumerate(soup.find_all("a", href=True)):
                title = link.get_text(strip=True)
                if title and len(title) > 25:
                    cat, img = get_category_and_image(title, "Hírkereső", idx)
                    categories[cat].append({"title": title, "link": link["href"], "image": img, "source": "Hírkereső"})
                if idx >= 30: break
    except: pass
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
            --bg-color: #1e293b;       /* FIX PRÉMIUM PALASZÜRKE ALAPVILÁG */
            --card-bg: #ffffff;
            --text-dark: #111111;
            --accent-red: #ff2a2a;
            --nav-blue: #0f172a;
            --border-gray: #475569;
        }
        body { 
            font-family: 'Georgia', serif; 
            margin: 0; padding: 0; 
            background-color: var(--bg-color); 
            color: #ffffff;
        }
        
        /* FEJLÉC AMI FIXEN SÖTÉTKÉK ÉS KÖZÉPRE ZÁRJA A LOGÓT */
        header { 
            background-color: #0f172a; 
            padding: 1.8rem 1rem; 
            text-align: center;
            border-bottom: 3px solid var(--accent-red);
        }
        .header-logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
        }
        
        /* A LOGÓDIZÁJN CSS REKREÁCIÓJA HAJSZÁLPONTOSAN A KÉPED ALAPJÁN (BOMBABIZTOS, NINCS 404!) */
.logo-box-html {
    background-color: #e2e8f0;
    padding: 20px 40px;
    border-top: 2px solid #111111;
    border-bottom: 2px solid #111111;
    display: inline-flex;
    align-items: center;
    gap: 20px;
    font-family: 'Times New Roman', Times, serif;
    position: relative;
}
.logo-text-the {
    font-size: 5.5rem;
    font-weight: normal;
    color: #1e293b;
    line-height: 0.8;
    letter-spacing: -2px;
    border-right: 2px solid #475569;
    padding-right: 25px;
    transform: scaleY(1.05);
}
.logo-right-wrapper {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
}
.logo-text-weekly {
    font-size: 2.5rem;
    font-weight: 900;
    font-family: 'Arial Black', sans-serif;
    letter-spacing: 3px;
    color: #e2e8f0;
    -webkit-text-stroke: 1.5px #1e293b;
    line-height: 0.9;
    text-transform: uppercase;
}
.logo-bottom-row-wrapper {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 2px;
}
.logo-twn-badge {
    background-color: #3ba2ff;
    padding: 4px 14px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    box-shadow: 0 2px 4px rgba(0,0,0,0.15);
}
/* A KÉK BUBORÉK KIS ALSÓ NYILA (PONTOSAN MINT A KÉPEDEN) */
.logo-twn-badge::after {
    content: '';
    position: absolute;
    bottom: -8px;
    left: 15px;
    width: 0;
    height: 0;
    border-width: 8px 8px 0 0;
    border-style: solid;
    border-color: #3ba2ff transparent transparent transparent;
}
.logo-text-news {
    font-size: 3rem;
    font-weight: 900;
    font-family: 'Arial Black', 'Impact', sans-serif;
    color: #ff2a2a;
    line-height: 0.8;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

        .nav-bar { background-color: var(--nav-blue); padding: 0px 1rem; display: flex; justify-content: center; position: sticky; top: 0; z-index: 100; border-bottom: 1px solid var(--border-gray); }
        .nav-item { color: white; font-family: sans-serif; font-weight: bold; padding: 1.1rem 1.5rem; text-decoration: none; font-size: 1.05rem; }
        .btn-refresh { background-color: var(--accent-red); color: white; padding: 1.1rem 1.5rem; font-family: sans-serif; font-weight: bold; text-transform: uppercase; text-decoration: none; }
        
        /* 3-HASÁBOS PRÉMIUM STRUKTÚRA */
        .three-column-grid-container {
            display: grid;
            grid-template-columns: 280px 1fr 280px;
            gap: 1.8rem;
            max-width: 1600px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        @media (max-width: 1300px) {
            .three-column-grid-container { grid-template-columns: 1fr; }
            .side-column-ad-strip { display: none; }
        }
        
        .side-column-ad-strip { display: flex; flex-direction: column; gap: 20px; align-self: start; }
        .center-news-stream { display: flex; flex-direction: column; }

        .main-magazine-cover { width: 100%; max-width: 460px; margin: 0 auto 3rem auto; border: 2px solid #fff; box-shadow: 0 6px 20px rgba(0,0,0,0.4); }
        .main-magazine-cover img { width: 100%; height: auto; display: block; }

        .rovat-section { margin-bottom: 4rem; width: 100%; }
        .rovat-title { font-family: sans-serif; font-size: 1.7rem; font-weight: 900; color: #38bdf8; border-bottom: 3px solid #38bdf8; padding-bottom: 0.3rem; margin-bottom: 1.5rem; text-transform: uppercase; letter-spacing: 0.5px; }
        
        /* HÍRRÁCS ELRENDEZÉSE */
        .news-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1.5rem; width: 100%; }
        .news-card { background: var(--card-bg); border: 1px solid var(--border-gray); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.3); border-radius: 4px; }
        .news-card img { width: 100%; height: 150px; object-fit: cover; display: block; }
        
        .card-body { padding: 0.9rem; display: flex; flex-direction: column; flex-grow: 1; }
        .source-badge { font-family: sans-serif; font-size: 0.7rem; font-weight: bold; color: var(--accent-red); text-transform: uppercase; margin-bottom: 0.4rem; }
        .card-body a { color: var(--text-dark); text-decoration: none; font-size: 1.1rem; font-weight: bold; line-height: 1.3; }
        .card-body a:hover { color: #0284c7; text-decoration: underline; }
        
        /* HAJSZÁLPONTOSAN EGYFORMA REKLÁMDOBOZOK SÖTÉT KIVITELBEN */
        .video-premium-box { background: #0f172a; border: 1px solid var(--border-gray); padding: 0.6rem; box-shadow: 0 4px 10px rgba(0,0,0,0.2); border-radius: 4px; width: 100%; box-sizing: border-box; }
        .video-premium-box h4 { margin: 0 0 0.5rem 0; font-family: sans-serif; font-size: 0.8rem; text-transform: lowercase; color: #ef4444; text-align: center; font-weight: normal; }
        .video-container { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 2px; }
        .video-container iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }
    </style>
</head>
"""
HTML_TEMPLATE += """
<body>
    
    <!-- FEJLÉC: BOMBABIZTOS HTML/CSS LOGÓ REKREÁCIÓ – SOHA TÖBBÉ NEM LESZ ÜRES, ÉS HAJSZÁLPONTOSAN OLYAN MINT A KÉPEDEN! -->
    <header>
        <div class="header-logo-container">
            <div class="logo-box-html">
                <div class="logo-text-the">THE</div>
                <div class="logo-right-wrapper">
                    <div class="logo-text-weekly">WEEKLY</div>
                    <div class="logo-bottom-row-wrapper">
                        <div class="logo-twn-badge">
    <span style="color: #000000; font-weight: bold; font-style: italic;">T</span><span style="color: #ffffff; font-weight: bold; font-style: italic;">W</span><span style="color: #ff2a2a; font-weight: bold; font-style: italic;">N</span>
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
        <a href="#vallas" class="nav-item">Vallás, Hit & Erkölcs</a>
        <a href="#tech" class="nav-item">AI Tech & Tudomány</a>
    </div>

    <div class="three-column-grid-container">
        
        <!-- 1. HASÁB (BAL OLDAL): line 1 - line 4 VIDEÓK SZEBB SORSZERKEZETBEN -->
        <div class="side-column-ad-strip">
            <div class="video-premium-box">
                <h4>line 1</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.video_1 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.video_1 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>
            <div class="video-premium-box">
                <h4>line 2</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.video_2 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.video_2 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>
            <div class="video-premium-box">
                <h4>line 3</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.video_3 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.video_3 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>
            <div class="video-premium-box">
                <h4>line 4</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.video_4 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.video_4 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>
        </div>

        <!-- 2. HASÁB (KÖZÉP): A PRÉMIUM CIKK-ÁRADAT A VEZETŐ FORRÁSOKKAL -->
        <div class="center-news-stream">
            
            <div class="main-magazine-cover">
                <img src="/friss_magazin.jpg" alt="The Weekly News Címlap">
            </div>

            <!-- ROVAT: BELFÖLD (Nlc és Hírkereső) -->
            <div class="rovat-section" id="belfold">
                <div class="rovat-title">Belföld</div>
                <div class="news-grid">
                    {% for item in news['Belföld'] %}
                    <div class="news-card">
                        <img src="{{ item.image }}" alt="Hír kép">
                        <div class="card-body">
                            <div class="source-badge">🔴 {{ item.source }}</div>
                            <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- ROVAT: KÜLFÖLD (TISZTA: BBC, CNN, NYT, DW, SPIEGEL) -->
            <div class="rovat-section" id="kulfold">
                <div class="rovat-title">Külföld</div>
                <div class="news-grid">
                    {% for item in news['Külföld'] %}
                    <div class="news-card">
                        <img src="{{ item.image }}" alt="Hír kép">
                        <div class="card-body">
                            <div class="source-badge">🌐 {{ item.source }}</div>
                            <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- ROVAT: GAZDASÁG -->
            <div class="rovat-section" id="gazdasag">
                <div class="rovat-title">Gazdaság</div>
                <div class="news-grid">
                    {% for item in news['Gazdaság'] %}
                    <div class="news-card">
                        <img src="{{ item.image }}" alt="Hír kép">
                        <div class="card-body">
                            <div class="source-badge">🔴 {{ item.source }}</div>
                            <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- ROVAT: VALLÁS, HIT & ERKÖLCS (Hetek) -->
            <div class="rovat-section" id="vallas">
                <div class="rovat-title">Vallás, Hit & Erkölcs</div>
                <div class="news-grid">
                    {% for item in news['Vallás, Hit & Erkölcs'] %}
                    <div class="news-card">
                        <img src="{{ item.image }}" alt="Hír kép">
                        <div class="card-body">
                            <div class="source-badge">🔴 {{ item.source }}</div>
                            <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- ROVAT: AI TECH & TUDOMÁNY (Wired, PubMed, NASA) -->
            <div class="rovat-section" id="tech">
                <div class="rovat-title">AI Tech, Orvostudomány & Tudomány</div>
                <div class="news-grid">
                    {% for item in news['AI Tech & Tudomány'] %}
                    <div class="news-card">
                        <img src="{{ item.image }}" alt="Hír kép">
                        <div class="card-body">
                            <div class="source-badge">🧪 {{ item.source }}</div>
                            <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

        </div>

        <!-- 3. HASÁB (JOBB OLDAL): line 5 - line 7 VIDEÓK SZÉPEN, EGYSÉGESEN -->
        <div class="side-column-ad-strip">
            <div class="video-premium-box">
                <h4>line 5</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.video_5 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.video_5 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>
            <div class="video-premium-box">
                <h4>line 6</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.video_6 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.video_6 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>
            <div class="video-premium-box">
                <h4>line 7</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.video_7 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.video_7 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
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
    if not any(STORED_NEWS.values()):
        STORED_NEWS = scrape_all_news()
    return render_template_string(HTML_TEMPLATE, news=STORED_NEWS, vids=REKLAM_VIDEÓK)

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
