import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, redirect, url_for, send_from_directory

app = Flask(__name__)

# A kért egyedi rovatstruktúra
STORED_NEWS = {
    "Belföld": [],
    "Külföld": [],
    "Gazdaság": [],
    "Vallás, Hit & Erkölcs": [],
    "AI Tech & Tudomány": []
}

# PONTOSAN 6 DARAB ELKÜLÖNÍTETT VIDEÓ TÁRHELYE (Összevissza elszórva)
REKLAM_VIDEÓK = {
    "hely_1": "GjrVtUNJTuQ",  # 1. videó helye
    "hely_2": "GjrVtUNJTuQ",  # 2. videó helye
    "hely_3": "GjrVtUNJTuQ",  # 3. videó helye
    "hely_4": "GjrVtUNJTuQ",  # 4. videó helye
    "hely_5": "GjrVtUNJTuQ",  # 5. videó helye
    "hely_6": "GjrVtUNJTuQ"   # 6. videó helye
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
    
    if "Nők Lapja" in source_name: return "Belföld", images["belfold"][img_idx]
    if "Hetek" in source_name: return "Vallás, Hit & Erkölcs", images["vallas"][img_idx]
    if "New York Times" in source_name: return "Külföld", images["kulfold"][img_idx]
    if "The Guardian" in source_name: return "AI Tech & Tudomány", images["tech"][img_idx]

    t = title.lower()
    if any(w in t for w in ["templom", "vallás", "hit ", "hitélet", "pápa", "egyház", "isten", "biblia"]): return "Vallás, Hit & Erkölcs", images["vallas"][img_idx]
    elif any(w in t for w in ["tech", "ai", "mesterséges", "robot", "tudomány", "kütyü", "internet"]): return "AI Tech & Tudomány", images["tech"][img_idx]
    elif any(w in t for w in ["gazdaság", "forint", "euró", "pénz", "tőzsde", "bank"]): return "Gazdaság", images["gazdasag"][img_idx]
    elif any(w in t for w in ["belföld", "budapest", "kormány", "orbán", "magyar"]): return "Belföld", images["belfold"][img_idx]
    return "Külföld", images["kulfold"][img_idx]

def scrape_all_news():
    categories = {"Belföld": [], "Külföld": [], "Gazdaság": [], "Vallás, Hit & Erkölcs": [], "AI Tech & Tudomány": []}
    
    # VALÓDI BÖNGÉSZŐ ÁLCA (Így a külföldi lapok nem tudják letiltani a szervert!)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "hu-HU,hu;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    uj_forrasok = [
        {"url": "https://nlc.hu", "name": "Nők Lapja Café"},
        {"url": "https://hetek.hu", "name": "Hetek Magazin"},
        {"url": "https://nytimes.com", "name": "New York Times"},
        {"url": "https://theguardian.com", "name": "The Guardian"}
    ]
    
    for forras in uj_forrasok:
        try:
            res = requests.get(forras["url"], headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "xml")
                for item in soup.find_all("item"):
                    title = item.title.get_text(strip=True) if item.title else ""
                    link = item.link.get_text(strip=True) if item.link else ""
                    if title and link:
                        cat, img = get_category_and_image(title, forras["name"], len(categories[cat]))
                        categories[cat].insert(0, {"title": title, "link": link, "image": img, "source": forras["name"]})
        except Exception as e:
            print(f"Hiba a letöltéskor ({forras['name']}): {e}")

    try:
        res = requests.get("https://hirkereso.hu", headers=headers, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, "html.parser")
            for idx, link in enumerate(soup.find_all("a", href=True)):
                title = link.get_text(strip=True)
                if title and len(title) > 25:
                    cat, img = get_category_and_image(title, "Hírkereső", idx)
                    categories[cat].append({"title": title, "link": link["href"], "image": img, "source": "Hírkereső"})
                if idx >= 40: break
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
            --bg-color: #edeef0;
            --card-bg: #ffffff;
            --text-dark: #111111;
            --accent-red: #ff2a2a;
            --nav-blue: #0c1a2c;
            --border-gray: #d1d5db;
        }
        body { 
            font-family: 'Georgia', serif; 
            margin: 0; padding: 0; 
            background-color: var(--bg-color); 
            color: var(--text-dark);
        }
        header { 
            background-color: #334155; 
            padding: 2.5rem 1rem 1.2rem 1rem; 
            text-align: center;
            border-bottom: 1px solid var(--border-gray);
        }
        .brand-container {
            display: inline-block;
            border-top: 1.5px solid #ffffff;
            border-bottom: 1.5px solid #ffffff;
            padding: 0.6rem 2.5rem;
        }
        .logo-row { display: flex; align-items: center; justify-content: center; gap: 12px; }
        .logo-the {
            font-size: 4.8rem; font-weight: bold; font-family: 'Times New Roman', serif;
            color: #ffffff; line-height: 0.75; letter-spacing: -3px; transform: scaleY(1.1);
            border-right: 1.5px solid #ffffff; padding-right: 15px;
        }
        .logo-weekly {
            font-size: 2.2rem; font-weight: 900; font-family: 'Arial Black', sans-serif;
            letter-spacing: 2px; color: transparent; -webkit-text-stroke: 1px #ffffff; line-height: 0.9;
        }
        .logo-twn-bubble {
            background-color: #3ba2ff; color: #ffffff; font-family: 'Times New Roman', serif;
            font-size: 1.1rem; font-weight: bold; padding: 2px 10px; border-radius: 6px;
        }
        .logo-news { font-size: 2.6rem; font-weight: 900; font-family: 'Impact', sans-serif; color: var(--accent-red); line-height: 0.9; }
        .sub-slogan { font-size: 1rem; letter-spacing: 12px; text-transform: uppercase; font-weight: bold; margin-top: 0.8rem; color: #cbd5e1; font-family: sans-serif; }
        
        .nav-bar { background-color: var(--nav-blue); padding: 0px 1rem; display: flex; justify-content: center; }
        .nav-item { color: white; font-family: sans-serif; font-weight: bold; padding: 1.1rem 1.5rem; text-decoration: none; font-size: 1.05rem; }
        .btn-refresh { background-color: var(--accent-red); color: white; padding: 1.1rem 1.5rem; font-family: sans-serif; font-weight: bold; text-transform: uppercase; text-decoration: none; }
        
        .container { max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }
        
        /* CSERÉLHETŐ FŐBORÍTÓ KÉP DOBOZA A LAP TETEJÉN */
        .main-magazine-cover { width: 100%; max-width: 480px; margin: 0 auto 3rem auto; border: 1px solid var(--border-gray); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .main-magazine-cover img { width: 100%; height: auto; display: block; }

        .rovat-section { margin-bottom: 3.5rem; }
        .rovat-title { font-family: sans-serif; font-size: 1.6rem; font-weight: 900; color: var(--nav-blue); border-bottom: 3px solid var(--nav-blue); padding-bottom: 0.2rem; margin-bottom: 1.5rem; text-transform: uppercase; }
        
        .news-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem; }
        .news-card { background: var(--card-bg); border: 1px solid var(--border-gray); display: flex; flex-direction: column; overflow: hidden; }
        .news-card img { width: 100%; height: 160px; object-fit: cover; }
        .card-body { padding: 1rem; display: flex; flex-direction: column; flex-grow: 1; }
        .source-badge { font-family: sans-serif; font-size: 0.75rem; font-weight: bold; color: var(--accent-red); text-transform: uppercase; margin-bottom: 0.4rem; }
        .card-body a { color: var(--text-dark); text-decoration: none; font-size: 1.15rem; font-weight: bold; line-height: 1.3; }
        
        /* PONTOSAN 6 DARAB ELOSZTOTT REKLÁMDOBOZ STÍLUSA */
        .scattered-video-box { max-width: 500px; margin: 2rem auto; background: #ffffff; border: 1px solid var(--border-gray); padding: 0.8rem; box-shadow: 0 3px 8px rgba(0,0,0,0.05); }
        .scattered-video-box h4 { margin: 0 0 0.5rem 0; font-family: sans-serif; font-size: 0.8rem; text-transform: uppercase; color: var(--accent-red); text-align: center; font-weight: bold; }
        .video-container { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; }
        .video-container iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }
    </style>
</head>
"""
HTML_TEMPLATE += """
<body>
    <header>
        <div class="brand-container">
            <div class="logo-row">
                <div class="logo-the">THE</div>
                <div class="logo-right-side">
                    <div class="logo-weekly">WEEKLY</div>
                    <div class="logo-bottom-row">
                        <div class="logo-twn-bubble">TWN</div>
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
        
        <!-- FIX CSERÉLHETŐ FŐBORÍTÓ KÉP -->
        <div class="main-magazine-cover">
            <img src="/friss_magazin.jpg" alt="Aktuális Borító">
        </div>

        <!-- BELFÖLD ROVAT (Nlc hírekkel az elején) -->
        <div class="rovat-section" id="belfold">
            <div class="rovat-title">Belföld</div>
            <div class="news-grid">
                {% for item in news['Belföld'] %}
                <div class="news-card">
                    <img src="{{ item.image }}" alt="Hír">
                    <div class="card-body">
                        <div class="source-badge">🔴 {{ item.source }}</div>
                        <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- 1. VIDEÓ HELY -->
        <div class="scattered-video-box">
            <h4>🚨 AJÁNLOTT PARTNER VIDEÓ 1</h4>
            <div class="video-container">
                <iframe src="https://youtube.com{{ vids.hely_1 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.hely_1 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
            </div>
        </div>

        <!-- KÜLFÖLD ROVAT (New York Times-szal) -->
        <div class="rovat-section" id="kulfold">
            <div class="rovat-title">Külföld</div>
            <div class="news-grid">
                {% for item in news['Külföld'] %}
                <div class="news-card">
                    <img src="{{ item.image }}" alt="Hír">
                    <div class="card-body">
                        <div class="source-badge">🔴 {{ item.source }}</div>
                        <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- 2. VIDEÓ HELY -->
        <div class="scattered-video-box">
            <h4>🚨 AJÁNLOTT PARTNER VIDEÓ 2</h4>
            <div class="video-container">
                <iframe src="https://youtube.com{{ vids.hely_2 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.hely_2 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
            </div>
        </div>

        <!-- GAZDASÁG ROVAT -->
        <div class="rovat-section" id="gazdasag">
            <div class="rovat-title">Gazdaság</div>
            <div class="news-grid">
                {% for item in news['Gazdaság'] %}
                <div class="news-card">
                    <img src="{{ item.image }}" alt="Hír">
                    <div class="card-body">
                        <div class="source-badge">🔴 {{ item.source }}</div>
                        <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- 3. VIDEÓ HELY -->
        <div class="scattered-video-box">
            <h4>🚨 AJÁNLOTT PARTNER VIDEÓ 3</h4>
            <div class="video-container">
                <iframe src="https://youtube.com{{ vids.hely_3 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.hely_3 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
            </div>
        </div>

        <!-- VALLÁS ROVAT (Hetek újsággal) -->
        <div class="rovat-section" id="vallas">
            <div class="rovat-title">Vallás, Hit & Erkölcs</div>
            <div class="news-grid">
                {% for item in news['Vallás, Hit & Erkölcs'] %}
                <div class="news-card">
                    <img src="{{ item.image }}" alt="Hír">
                    <div class="card-body">
                        <div class="source-badge">🔴 {{ item.source }}</div>
                        <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- 4. VIDEÓ HELY -->
        <div class="scattered-video-box">
            <h4>🚨 AJÁNLOTT PARTNER VIDEÓ 4</h4>
            <div class="video-container">
                <iframe src="https://youtube.com{{ vids.hely_4 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.hely_4 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
            </div>
        </div>

        <!-- AI TECH & TUDOMÁNY ROVAT (The Guardian hírekkel) -->
        <div class="rovat-section" id="tech">
            <div class="rovat-title">AI Tech & Tudomány</div>
            <div class="news-grid">
                {% for item in news['AI Tech & Tudomány'] %}
                <div class="news-card">
                    <img src="{{ item.image }}" alt="Hír">
                    <div class="card-body">
                        <div class="source-badge">🔴 {{ item.source }}</div>
                        <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- 5. VIDEÓ HELY -->
        <div class="scattered-video-box">
            <h4>🚨 AJÁNLOTT PARTNER VIDEÓ 5</h4>
            <div class="video-container">
                <iframe src="https://youtube.com{{ vids.hely_5 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.hely_5 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
            </div>
        </div>

        <!-- 6. VIDEÓ HELY A LAP LEGALSÓ RÉSZÉN -->
        <div class="scattered-video-box">
            <h4>🚨 AJÁNLOTT PARTNER VIDEÓ 6</h4>
            <div class="video-container">
                <iframe src="https://youtube.com{{ vids.hely_6 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.hely_6 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
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
