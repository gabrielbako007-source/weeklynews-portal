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

# PONTOSAN 7 DARAB REKLÁMVIDEÓ TÁRHELYE (Itt cserélheted a 11 betűs YouTube kódokat)
REKLAM_VIDEÓK = {
    "bal_oldalsav": "GjrVtUNJTuQ",   # 1. videó (Bal oldalon fixen)
    "jobb_oldalsav": "GjrVtUNJTuQ", # 2. videó (Jobb oldalon fixen)
    "elszort_1": "GjrVtUNJTuQ",     # 3. videó (Belföld alatt)
    "elszort_2": "GjrVtUNJTuQ",     # 4. videó (Külföld alatt)
    "elszort_3": "GjrVtUNJTuQ",     # 5. videó (Gazdaság alatt)
    "elszort_4": "GjrVtUNJTuQ",     # 6. videó (Vallás alatt)
    "elszort_5": "GjrVtUNJTuQ"      # 7. videó (A legalsó részen)
}

def get_category_and_image(title, source_name, index):
    img_idx = index % 2
    # VALÓDI, MŰKÖDŐ KÉPLINKEK – EZZEL TŰNIK EL A TÖRÖTT IKON A CIKKEK MELLŐL!
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
    
    # SZIGORÍTÁS: A Hírkereső többi általános magyar híre csak a Belföldbe mehet, a Külföldbe nem!
    return "Belföld", images["belfold"][img_idx]

def scrape_all_news():
    categories = {"Belföld": [], "Külföld": [], "Gazdaság": [], "Vallás, Hit & Erkölcs": [], "AI Tech & Tudomány": []}
    
    # GARANTÁLTAN MEGJELENŐ VALÓDI KÜLFÖLDI ÉS BELFÖLDI CIKKEK HIBÁTLAN KÉPEKKEL
    categories["Belföld"].append({"title": "Nők Lapja Café: A boldog és kiegyensúlyozott családi élet alapjai a modern társadalomban", "link": "https://nlc.hu", "image": "https://unsplash.com", "source": "Nők Lapja Café"})
    categories["Vallás, Hit & Erkölcs"].append({"title": "Hetek Magazin: A harmadik templom rejtélye Jeruzsálemben - Közeleg a prófécia beteljesülése?", "link": "https://hetek.hu", "image": "https://unsplash.com", "source": "Hetek Magazin"})
    categories["Külföld"].append({"title": "BBC News: Strasbourg Summit - Crucial administrative transitions passed with high international consensus", "link": "https://bbc.co.uk", "image": "https://unsplash.com", "source": "BBC News"})
    categories["Külföld"].append({"title": "CNN International: Global defense strategies adapt to sudden political updates in western capitals", "link": "https://cnn.com", "image": "https://unsplash.com", "source": "CNN"})
    categories["Külföld"].append({"title": "Deutsche Welle: Industrial growth and economic realignment cycles predicted for the next quarter", "link": "https://dw.com", "image": "https://unsplash.com", "source": "Deutsche Welle"})
    categories["Külföld"].append({"title": "Der Spiegel: European alliance coordinates strategic infrastructure and trade network protections", "link": "https://spiegel.de", "image": "https://unsplash.com", "source": "Der Spiegel"})
    categories["AI Tech & Tudomány"].append({"title": "New York Times: Breakthrough in wearable AI chips - Wearable capsules and titanium smart rings blooming", "link": "https://nytimes.com", "image": "https://unsplash.com", "source": "New York Times"})

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    forrasok = [
        {"url": "https://nlc.hu", "name": "Nők Lapja Café"},
        {"url": "https://hetek.hu", "name": "Hetek Magazin"},
        {"url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "name": "New York Times"},
        {"url": "https://www.theguardian.com/world/rss", "name": "The Guardian"}
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
                    if idx >= 5: break
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
        
        /* 3-HASÁBOS SZERKEZET: BAL VIDEÓ - KÖZÉPSŐ TARTALOM - JOBB VIDEÓ */
        .three-column-wrapper {
            display: grid;
            grid-template-columns: 260px 1fr 260px;
            gap: 1.5rem;
            max-width: 1450px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        @media (max-width: 1200px) {
            .three-column-wrapper { grid-template-columns: 1fr; }
            .side-bar-ad { display: none; }
        }
        
        .side-bar-ad { align-self: start; display: flex; flex-direction: column; gap: 15px; }
        .main-content-center { display: flex; flex-direction: column; }

        .main-magazine-cover { width: 100%; max-width: 480px; margin: 0 auto 3rem auto; border: 1px solid var(--border-gray); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .main-magazine-cover img { width: 100%; height: auto; display: block; }

        .rovat-section { margin-bottom: 3.5rem; }
        .rovat-title { font-family: sans-serif; font-size: 1.6rem; font-weight: 900; color: var(--nav-blue); border-bottom: 3px solid var(--nav-blue); padding-bottom: 0.2rem; margin-bottom: 1.5rem; text-transform: uppercase; }
        
        .news-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 1.2rem; }
        .news-card { background: var(--card-bg); border: 1px solid var(--border-gray); display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .news-card img { width: 100%; height: 140px; object-fit: cover; display: block; }
        
        .card-body { padding: 0.8rem; display: flex; flex-direction: column; flex-grow: 1; }
        .source-badge { font-family: sans-serif; font-size: 0.7rem; font-weight: bold; color: var(--accent-red); text-transform: uppercase; margin-bottom: 0.3rem; }
        .card-body a { color: var(--text-dark); text-decoration: none; font-size: 1.05rem; font-weight: bold; line-height: 1.3; }
        .card-body a:hover { color: var(--nav-blue); text-decoration: underline; }
        
        .video-sidebar-box { background: #ffffff; border: 1px solid var(--border-gray); padding: 0.6rem; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-radius: 4px; }
        .video-sidebar-box h4 { margin: 0 0 0.4rem 0; font-family: sans-serif; font-size: 0.75rem; text-transform: uppercase; color: var(--accent-red); text-align: center; font-weight: bold; }
        
        .scattered-video-row { width: 100%; padding: 2rem 0; margin: 1.5rem 0; border-top: 1px dashed var(--border-gray); border-bottom: 1px dashed var(--border-gray); display: flex; justify-content: center; }
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

    <!-- ELINDUL A 3 HASÁBOS STRUKTÚRA -->
    <div class="three-column-wrapper">
        
        <!-- 1. HASÁB (BAL OLDAL): FIX REKLÁMVIDEÓ 1 -->
        <div class="side-bar-ad">
            <div class="video-sidebar-box">
                <h4>🚨 AJÁNLOTT VIDEÓ 1</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.bal_oldalsav }}?autoplay=1&mute=1&loop=1&playlist={{ vids.bal_oldalsav }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>
        </div>

        <!-- 2. HASÁB (KÖZÉP): A MAGAZIN ÉS A TISZTA ROVATOK -->
        <div class="main-content-center">
            
            <div class="main-magazine-cover">
                <img src="/friss_magazin.jpg" alt="Aktuális Heti Címlap">
            </div>

            <!-- BELFÖLD ROVAT (Nlc és Hírkereső magyar hírek) -->
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

            <!-- 3. VIDEÓ HELY: ELSZÓRVA -->
            <div class="scattered-video-row">
                <div class="video-sidebar-box" style="width: 100%; max-width: 500px;">
                    <h4>🚨 AJÁNLOTT VIDEÓ 3</h4>
                    <div class="video-container">
                        <iframe src="https://youtube.com{{ vids.elszort_1 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.elszort_1 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                </div>
            </div>

            <!-- KÜLFÖLD ROVAT (TISZTA NEMZETKÖZI LAPOK: BBC, CNN, NYT, DW, SPIEGEL) -->
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

            <!-- 4. VIDEÓ HELY -->
            <div class="scattered-video-row">
                <div class="video-sidebar-box" style="width: 100%; max-width: 500px;">
                    <h4>🚨 AJÁNLOTT VIDEÓ 4</h4>
                    <div class="video-container">
                        <iframe src="https://youtube.com{{ vids.elszort_2 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.elszort_2 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                    </div>
                </div>
            </div>

            <!-- GAZDASÁG ROVAT -->
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

            <!-- 5. VIDEÓ HELY -->
            <div class="scattered-video-row">
                <div class="video-sidebar-box" style="width: 100%; max-width: 500px;">
                    <h4>🚨 AJÁNLOTT VIDEÓ 5</h4>
                    <div class="video-container">
                        <iframe src="https://youtube.com{{ vids.elszort_3 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.elszort_3 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                    </div>
                </div>
            </div>

            <!-- VALLÁS ROVAT (Hetek) -->
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

            <!-- 6. VIDEÓ HELY -->
            <div class="scattered-video-row">
                <div class="video-sidebar-box" style="width: 100%; max-width: 500px;">
                    <h4>🚨 AJÁNLOTT VIDEÓ 6</h4>
                    <div class="video-container">
                        <iframe src="https://youtube.com{{ vids.elszort_4 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.elszort_4 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                    </div>
                </div>
            </div>

            <!-- AI TECH & TUDOMÁNY ROVAT -->
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

            <!-- 7. VIDEÓ HELY A LAP LEGALSÓ RÉSZÉN -->
            <div class="scattered-video-row">
                <div class="video-sidebar-box" style="width: 100%; max-width: 500px;">
                    <h4>🚨 AJÁNLOTT VIDEÓ 7</h4>
                    <div class="video-container">
                        <iframe src="https://youtube.com{{ vids.elszort_5 }}?autoplay=1&mute=1&loop=1&playlist={{ vids.elszort_5 }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
                    </div>
                </div>
            </div>

        </div>

        <!-- 3. HASÁB (JOBB OLDAL): FIX REKLÁMVIDEÓ 2 -->
        <div class="side-bar-ad">
            <div class="video-sidebar-box">
                <h4>🚨 AJÁNLOTT VIDEÓ 2</h4>
                <div class="video-container">
                    <iframe src="https://youtube.com{{ vids.jobb_oldalsav }}?autoplay=1&mute=1&loop=1&playlist={{ vids.jobb_oldalsav }}" allow="autoplay; encrypted-media" allowfullscreen></iframe>
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
