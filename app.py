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

# SZIGORÚAN 7 DARAB REKLÁMVIDEÓ TÁRHELYE (Bal oszlopban 4, jobb oszlopban 3 videó)
REKLAM_VIDEÓK = {
    "video_1": "GjrVtUNJTuQ",  # Bal sáv - 1. videó
    "video_2": "GjrVtUNJTuQ",  # Bal sáv - 2. videó
    "video_3": "GjrVtUNJTuQ",  # Bal sáv - 3. videó
    "video_4": "GjrVtUNJTuQ",  # Bal sáv - 4. videó
    "video_5": "GjrVtUNJTuQ",  # Jobb sáv - 5. videó
    "video_6": "GjrVtUNJTuQ",  # Jobb sáv - 6. videó
    "video_7": "GjrVtUNJTuQ"   # Jobb sáv - 7. videó
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
    if any(s in source_name for s in ["CNN", "BBC", "NYT", "Spiegel", "Deutsche Welle", "The Guardian"]): return "Külföld", images["kulfold"][img_idx]

    t = title.lower()
    if any(w in t for w in ["templom", "vallás", "hit ", "hitélet", "pápa", "egyház", "isten", "biblia"]): return "Vallás, Hit & Erkölcs", images["vallas"][img_idx]
    elif any(w in t for w in ["tech", "ai", "mesterséges", "robot", "tudomány", "kütyü", "internet"]): return "AI Tech & Tudomány", images["tech"][img_idx]
    elif any(w in t for w in ["gazdaság", "forint", "euró", "pénz", "tőzsde", "bank"]): return "Gazdaság", images["gazdasag"][img_idx]
    return "Belföld", images["belfold"][img_idx]

def scrape_all_news():
    categories = {"Belföld": [], "Külföld": [], "Gazdaság": [], "Vallás, Hit & Erkölcs": [], "AI Tech & Tudomány": []}
    
    categories["Belföld"].append({"title": "Nők Lapja Café: A boldog és kiegyensúlyozott családi élet alapjai a modern társadalomban", "link": "https://nlc.hu", "image": "https://unsplash.com", "source": "Nők Lapja Café"})
    categories["Vallás, Hit & Erkölcs"].append({"title": "Hetek Magazin: A harmadik templom rejtélye Jeruzsálemben - Közeleg a prófécia beteljesülése?", "link": "https://hetek.hu", "image": "https://unsplash.com", "source": "Hetek Magazin"})
    categories["Külföld"].append({"title": "BBC News: Strasbourg Summit - Crucial administrative transitions passed with high international consensus", "link": "https://bbc.co.uk", "image": "https://unsplash.com", "source": "BBC News"})
    categories["Külföld"].append({"title": "CNN International: Global defense strategies adapt to sudden political updates in western capitals", "link": "https://cnn.com", "image": "https://unsplash.com", "source": "CNN"})
    categories["Külföld"].append({"title": "Deutsche Welle: Industrial growth and economic realignment cycles predicted for the next quarter", "link": "https://dw.com", "image": "https://unsplash.com", "source": "Deutsche Welle"})
    categories["Külföld"].append({"title": "Der Spiegel: European alliance coordinates strategic infrastructure and trade network protections", "link": "https://spiegel.de", "image": "https://unsplash.com", "source": "Der Spiegel"})
    categories["AI Tech & Tudomány"].append({"title": "The Guardian: Breakthrough in wearable AI chips - Wearable capsules and titanium smart rings blooming worldwide", "link": "https://theguardian.com", "image": "https://unsplash.com", "source": "The Guardian"})

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    forrasok = [
        {"url": "https://nlc.hu", "name": "Nők Lapja Café"},
        {"url": "https://hetek.hu", "name": "Hetek Magazin"},
        {"url": "https://nytimes.com", "name": "New York Times"},
        {"url": "https://theguardian.com", "name": "The Guardian"}
    ]
    for f in forrasok:
        try:
            res = requests.get(f["url"], headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "xml")
                for idx, item in enumerate(soup.find_all("item")):
                    title = item.title.get_text(strip=True) if item.title else ""
                    if title and item.link:
                        cat, img = get_category_and_image(title, f["name"], idx)
                        categories[cat].insert(1, {"title": title, "link": item.link.get_text(strip=True), "image": img, "source": f["name"]})
                    if idx >= 6: break
        except: pass

    try:
        res = requests.get("https://hirkereso.hu", headers=headers, timeout=5)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, "html.parser")
            for idx, link in enumerate(soup.find_all("a", href=True)):
                title = link.get_text(strip=True)
                if title and len(title) > 25:
                    cat, img = get_category_and_image(title, "Hírkereső", idx)
                    categories[cat].append({"title": title, "link": link["href"], "image": img, "source": "Hírkereső"})
                if idx >= 50: break
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
        
        /* ÚJ PROFI FEJLÉC DOBOZ A KÉP LOGÓNAK */
        header { 
            background-color: #ffffff; 
            padding: 1.5rem 1rem; 
            text-align: center;
            border-bottom: 2px solid var(--nav-blue);
        }
        .main-logo-image {
            max-width: 320px;
            width: 100%;
            height: auto;
            display: inline-block;
        }

        .nav-bar { background-color: var(--nav-blue); padding: 0px 1rem; display: flex; justify-content: center; position: sticky; top: 0; z-index: 100; }
        .nav-item { color: white; font-family: sans-serif; font-weight: bold; padding: 1.1rem 1.5rem; text-decoration: none; font-size: 1.05rem; }
        .btn-refresh { background-color: var(--accent-red); color: white; padding: 1.1rem 1.5rem; font-family: sans-serif; font-weight: bold; text-transform: uppercase; text-decoration: none; }
        
        .three-column-grid-container {
            display: grid;
            grid-template-columns: 280px 1fr 280px;
            gap: 1.5rem;
            max-width: 1550px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        @media (max-width: 1250px) {
            .three-column-grid-container { grid-template-columns: 1fr; }
            .side-column-ad-strip { display: none; }
        }
        
        .side-column-ad-strip { display: flex; flex-direction: column; gap: 20px; align-self: start; }
        .center-news-stream { display: flex; flex-direction: column; }

        .main-magazine-cover { width: 100%; max-width: 460px; margin: 0 auto 3rem auto; border: 1px solid var(--border-gray); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .main-magazine-cover img { width: 100%; height: auto; display: block; }

        .rovat-section { margin-bottom: 4rem; width: 100%; }
        .rovat-title { font-family: sans-serif; font-size: 1.6rem; font-weight: 900; color: var(--nav-blue); border-bottom: 3px solid var(--nav-blue); padding-bottom: 0.3rem; margin-bottom: 1.5rem; text-transform: uppercase; }
        
        .news-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1.5rem; width: 100%; }
        .news-card { background: var(--card-bg); border: 1px solid var(--border-gray); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.04); }
        .news-card img { width: 100%; height: 150px; object-fit: cover; display: block; }
        
        .card-body { padding: 0.9rem; display: flex; flex-direction: column; flex-grow: 1; }
        .source-badge { font-family: sans-serif; font-size: 0.7rem; font-weight: bold; color: var(--accent-red); text-transform: uppercase; margin-bottom: 0.4rem; }
        .card-body a { color: var(--text-dark); text-decoration: none; font-size: 1.1rem; font-weight: bold; line-height: 1.3; }
        
        .video-premium-box { background: #ffffff; border: 1px solid var(--border-gray); padding: 0.6rem; box-shadow: 0 2px 6px rgba(0,0,0,0.06); border-radius: 4px; width: 100%; box-sizing: border-box; }
        .video-premium-box h4 { margin: 0 0 0.5rem 0; font-family: sans-serif; font-size: 0.75rem; text-transform: uppercase; color: var(--accent-red); text-align: center; font-weight: bold; }
        .video-container { position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; border-radius: 2px; }
        .video-container iframe { position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0; }
    </style>
</head>
"""
HTML_TEMPLATE += """
<body>
    
    <!-- FEJLÉC: MOSTANTÓL A TE GYÖNYÖRŰ KÉP LOGÓDAT TÖLTI BE TORZÍTÁS NÉLKÜL -->
    <header>
        <img src="/logo.png" alt="The Weekly News Logo" class="main-logo-image">
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
        
        <!-- 1. HASÁB (BAL OLDAL): A 4 DARAB VIDEÓ EGYMÁS ALATT -->
        <div class="side-column-ad-strip">
            <div class="video-premium-box">
                <h4>🚨 AJÁNLOTT VIDEÓ 1</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.video_1 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.video_1 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>
            <div class="video-premium-box">
                <h4>🚨 AJÁNLOTT VIDEÓ 2</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.video_2 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.video_2 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>
            <div class="video-premium-box">
                <h4>🚨 AJÁNLOTT VIDEÓ 3</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.video_3 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.video_3 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>
            <div class="video-premium-box">
                <h4>🚨 AJÁNLOTT VIDEÓ 4</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.video_4 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.video_4 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>
        </div>

        <!-- 2. HASÁB (KÖZÉP): CIKKEK ÉS BORÍTÓ -->
        <div class="center-news-stream">
            
            <div class="main-magazine-cover">
                <img src="/friss_magazin.jpg" alt="The Weekly News Címlap">
            </div>

            <!-- BELFÖLD -->
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

            <!-- KÜLFÖLD (TISZTA: BBC, CNN, NYT, DW, GUARDIAN) -->
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

            <!-- GAZDASÁG -->
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

            <!-- VALLÁS -->
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

            <!-- AI TECH & TUDOMÁNY -->
            <div class="rovat-section" id="tech">
                <div class="rovat-title">AI Tech & Tudomány</div>
                <div class="news-grid">
                    {% for item in news['AI Tech & Tudomány'] %}
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

        </div>

        <!-- 3. HASÁB (JOBB OLDAL): THE MARADÉK 3 VIDEÓ EGYMÁS ALATT -->
        <div class="side-column-ad-strip">
            <div class="video-premium-box">
                <h4>🚨 AJÁNLOTT VIDEÓ 5</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.video_5 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.video_5 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>
            <div class="video-premium-box">
                <h4>🚨 AJÁNLOTT VIDEÓ 6</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.video_6 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.video_6 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>
            <div class="video-premium-box">
                <h4>🚨 AJÁNLOTT VIDEÓ 7</h4>
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

# BOMBABIZTOS FIX PARANCSOK A CÍMLAP ÉS A LOGÓ KÉPEK KISZOLGÁLÁSÁHOZ
@app.route('/friss_magazin.jpg')
def serve_friss_magazin():
    return send_from_directory('.', 'friss_magazin.jpg')

@app.route('/logo.png')
def serve_logo():
    return send_from_directory('.', 'logo.png')

@app.route("/frissites")
def refresh():
    global STORED_NEWS
    STORED_NEWS = scrape_all_news()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
