import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, redirect, url_for, request

app = Flask(__name__)

STORED_NEWS = {
    "Belföld": [],
    "Külföld": [],
    "Gazdaság": [],
    "Vallás, Hit & Erkölcs": [],
    "AI Tech & Tudomány": []
}

STORED_CLASSIFIEDS = [
    {"title": "Prémium családi ház eladó", "price": "45 000 000 Ft", "contact": "06301234567", "source": "Kiemelt Partner"},
    {"title": "Garantáltan bio vitamincsomagok a termelőtől", "price": "8 500 Ft", "contact": "info@biavitamin.hu", "source": "Szponzorált Apró"}
]

SPONSOR_VIDEOS = {
    "Belföld": "https://youtube.com",
    "AI Tech & Tudomány": "https://youtube.com"
}

def translate_text(text, target_lang):
    if target_lang == "en":
        return text
    try:
        url = f"https://googleapis.com{target_lang}&dt=t&q={requests.utils.quote(text)}"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            result = res.json()
            return "".join([sentence for sentence in result if sentence])
    except Exception:
        pass
    return text

def get_category_and_image(title, index):
    t = title.lower()
    images = {
        "vallas": ["https://picsum.photos", "https://picsum.photos"],
        "tech": ["https://picsum.photos", "https://picsum.photos"],
        "gazdasag": ["https://picsum.photos", "https://picsum.photos"],
        "belfold": ["https://picsum.photos", "https://picsum.photos"],
        "kulfold": ["https://picsum.photos", "https://picsum.photos"]
    }
    img_idx = index % 2

    if any(w in t for w in ["templom", "vallás", "hit ", "hitélet", "pápa", "egyház", "isten", "biblia", "izrael", "zsidó", "keresztény", "erkölcs", "morál"]):
        return "Vallás, Hit & Erkölcs", images["vallas"][img_idx]
    elif any(w in t for w in ["család", "gyerek", "iskola", "szülő", "feleség", "férj", "otthon", "egészség", "nevelés", "biztonság", "védelem"]):
        return "Belföld", images["belfold"][img_idx]
    elif any(w in t for w in ["tech", "ai", "mesterséges", "robot", "tudomány", "okostelefon", "drón", "űr", "kütyü", "internet", "google"]):
        return "AI Tech & Tudomány", images["tech"][img_idx]
    elif any(w in t for w in ["gazdaság", "forint", "euró", "pénz", "tőzsde", "részvény", "szankció", "infláció", "hitel", "bank"]):
        return "Gazdaság", images["gazdasag"][img_idx]
    else:
        return "Külföld", images["kulfold"][img_idx]

def scrape_all_news(lang="hu"):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    categories = {"Belföld": [], "Külföld": [], "Gazdaság": [], "Vallás, Hit & Erkölcs": [], "AI Tech & Tudomány": []}
    count = 0

    global_urls = [
        ("https://nytimes.com", "New York Times"),
        ("https://theguardian.com", "The Guardian")
    ]
    for url, source in global_urls:
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "xml")
                for item in soup.find_all("item")[:12]:
                    orig_title = item.title.get_text(strip=True) if item.title else ""
                    link = item.link.get_text(strip=True) if item.link else ""
                    if orig_title and link:
                        translated_title = translate_text(orig_title, lang)
                        cat, img = get_category_and_image(translated_title, count)
                        categories[cat].append({"title": translated_title, "link": link, "image": img, "source": translate_text(source, lang)})
                        count += 1
        except Exception:
            pass

    local_urls = [
        ("https://hetek.hu", "Hetek Magazin"),
        ("https://nlc.hu", "NLC / Nők Lapja")
    ]
    for url, source in local_urls:
        try:
            res = requests.get(url, headers=headers, timeout=5)
            if res.status_code == 200:
                soup = BeautifulSoup(res.content, "xml")
                for item in soup.find_all("item")[:12]:
                    title = item.title.get_text(strip=True) if item.title else ""
                    link = item.link.get_text(strip=True) if item.link else ""
                    if title and link:
                        translated_title = translate_text(title, lang)
                        cat, img = get_category_and_image(translated_title, count)
                        categories[cat].append({"title": translated_title, "link": link, "image": img, "source": translate_text(source, lang)})
                        count += 1
        except Exception:
            pass
    return categories
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>A HETI HÍREK</title>
    <style>
        :root {
            --bg-color: #edeef0;
            --card-bg: #ffffff;
            --text-dark: #111111;
            --accent-red: #ff2a2a;
            --nav-blue: #0c1a2c;
            --border-gray: #d1d5db;
            --ad-gold: #f59e0b;
        }
        
        body { 
            font-family: 'Georgia', serif; 
            margin: 0; 
            padding: 0; 
            background-color: var(--bg-color); 
            color: var(--text-dark);
        }

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
            font-family: 'Arial Black', sans-serif;
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
            font-family: 'Impact', sans-serif;
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
            padding: 0px 0.5rem;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-wrap: wrap;
        }

        .nav-item {
            color: white;
            font-family: sans-serif;
            font-weight: bold;
            padding: 1.1rem 1.2rem;
            text-decoration: none;
            font-size: 0.95rem;
            transition: background 0.2s;
            white-space: nowrap;
        }

        .nav-item:hover {
            background-color: rgba(255,255,255,0.1);
        }

        .btn-refresh {
            background-color: var(--accent-red);
            color: white;
            border: none;
            padding: 1.1rem 1.2rem;
            font-family: sans-serif;
            font-weight: bold;
            cursor: pointer;
            text-transform: uppercase;
            letter-spacing: 1px;
            text-decoration: none;
            white-space: nowrap;
        }

        .container { 
            max-width: 1300px; 
            margin: 3rem auto; 
            padding: 0 1.5rem; 
        }

        .rovat-section {
            margin-bottom: 5rem;
            scroll-margin-top: 20px;
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
            margin-bottom: 1.5rem;
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

        .classifieds-container {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.5rem;
            background: rgba(245, 158, 11, 0.05);
            padding: 1.5rem;
            border: 2px dashed var(--ad-gold);
        }

        .classified-card {
            background: white;
            border: 1px solid var(--ad-gold);
            padding: 1.2rem;
            position: relative;
        }

        .classified-badge {
            background: var(--ad-gold);
            color: white;
            font-size: 0.7rem;
            font-family: sans-serif;
            padding: 2px 6px;
            font-weight: bold;
            position: absolute;
            top: 0;
            right: 0;
            text-transform: uppercase;
        }

        .classified-price {
            color: var(--accent-red);
            font-weight: bold;
            font-size: 1.2rem;
            margin: 0.5rem 0;
        }

        .classified-contact {
            font-family: sans-serif;
            font-size: 0.85rem;
            color: #555555;
            background: #f3f4f6;
            padding: 4px;
            display: inline-block;
        }
    </style>
</head>
<body>

    <header>
        <div class="brand-container">
            <div class="logo-row">
                <div class="logo-the">A</div>
                <div class="logo-right-side">
                    <div class="logo-weekly">HETI</div>
                    <div class="logo-bottom-row">
                        <div class="logo-twn-bubble">
                            <span class="twn-t">T</span>
                            <span class="twn-w">W</span>
                            <span class="twn-n">N</span>
                        </div>
                        <div class="logo-news">HÍREK</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="sub-slogan">HETILAP</div>
    </header>

    <div class="nav-bar">
        <a href="/frissites" class="btn-refresh">🔄 {{ refresh_text }}</a>
        <a href="#belfold" class="nav-item">{{ rovat1 }}</a>
        <a href="#kulfold" class="nav-item">{{ rovat2 }}</a>
        <a href="#gazdasag" class="nav-item">{{ rovat3 }}</a>
        <a href="#vallas" class="nav-item">{{ rovat4 }}</a>
        <a href="#tech" class="nav-item">{{ rovat5 }}</a>
        <a href="#adokveszek" class="nav-item" style="color: var(--ad-gold);">💰 {{ rovat_ad }}</a>
    </div>

    <div class="container">
        <!-- FŐ HÍR SZEKCIÓ -->
        {% for rovat, cikkek in news.items() %}
            {% if cikkek %}
                {% set anchor = "belfold" if rovat == "Belföld" else "kulfold" if rovat == "Külföld" else "gazdasag" if rovat == "Gazdaság" else "vallas" if rovat == "Vallás, Hit & Erkölcs" else "tech" %}
                <div class="rovat-section" id="{{ anchor }}">
                    <div class="rovat-title">
                        {% if rovat == "Belföld" %}{{ rovat1 }}
                        {% elif rovat == "Külföld" %}{{ rovat2 }}
                        {% elif rovat == "Gazdaság" %}{{ rovat3 }}
                        {% elif rovat == "Vallás, Hit & Erkölcs" %}{{ rovat4 }}
                        {% else %}{{ rovat5 }}{% endif %}
                    </div>
                    
                    <div class="magazine-layout">
                        <div class="news-grid">
                            {% for item in cikkek %}
                                <div class="news-card">
                                    <img src="{{ item.image }}" alt="Borítókép">
                                    <div class="card-body">
                                        <div class="source-badge">📰 {{ item.source }}</div>
                                        <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                                    </div>
                                </div>
                            {% endfor %}
                        </div>

                        {% if rovat in sponsor_videos %}
                            <div class="video-ad-box">
                                <h4>📺 {{ video_title }}</h4>
                                <div class="video-container">
                                    <iframe src="{{ sponsor_videos[rovat] }}" allowfullscreen></iframe>
                                </div>
                            </div>
                        {% endif %}
                    </div>

                </div>
            {% endif %}
        {% endfor %}

        <!-- ADOK-VESZEK PIAC ROVAT -->
        <div class="rovat-section" id="adokveszek">
            <div class="rovat-title" style="color: var(--ad-gold); border-bottom-color: var(--ad-gold);">💰 {{ rovat_ad }}</div>
            <div class="classifieds-container">
                {% for ad in classifieds %}
                    <div class="classified-card">
                        <div class="classified-badge">{{ ad.source }}</div>
                        <h3 style="font-size: 1.1rem; margin: 0 0 0.5rem 0; font-family: sans-serif;">{{ ad.title }}</h3>
                        <div class="classified-price">{{ ad.price }}</div>
                        <div class="classified-contact">📞 {{ ad.contact }}</div>
                    </div>
                {% endfor %}
            </div>
        </div>

    </div>

</body>
</html>
"""

@app.route("/")
def index():
    global STORED_NEWS
    accept_lang = request.headers.get('Accept-Language', '')
    if 'de' in accept_lang:
        lang = 'de'
        labels = {"refresh_text": "Aktualisieren", "video_title": "Partner-Video", "rovat1": "Inland", "rovat2": "Ausland", "rovat3": "Wirtschaft", "rovat4": "Religion & Moral", "rovat5": "KI Tech", "rovat_ad": "Kleinanzeigen"}
    elif 'en' in accept_lang:
        lang = 'en'
        labels = {"refresh_text": "Refresh", "video_title": "Partner Video", "rovat1": "National", "rovat2": "International", "rovat3": "Economy", "rovat4": "Religion", "rovat5": "AI Tech", "rovat_ad": "Classifieds"}
    else:
        lang = 'hu'
        labels = {"refresh_text": "FRISSÍTÉS MOST", "video_title": "AJÁNLOTT PARTNER VIDEÓ", "rovat1": "Nemzeti", "rovat2": "Nemzetközi", "rovat3": "Gazdaság", "rovat4": "Vallás és erkölcs", "rovat5": "MI technológia és tudomány", "rovat_ad": "Apróhirdetések (vétel/eladás)"}

    if not any(STORED_NEWS.values()):
        STORED_NEWS = scrape_all_news(lang)
        
    translated_classifieds = []
    for ad in STORED_CLASSIFIEDS:
        translated_classifieds.append({
            "title": translate_text(ad["title"], lang),
            "price": ad["price"],
            "contact": ad["contact"],
            "source": translate_text(ad["source"], lang)
        })

    return render_template_string(HTML_TEMPLATE, news=STORED_NEWS, sponsor_videos=SPONSOR_VIDEOS, classifieds=translated_classifieds, lang=lang, **labels)

@app.route("/frissites")
def refresh():
    global STORED_NEWS
    accept_lang = request.headers.get('Accept-Language', '')
    lang = 'de' if 'de' in accept_lang else 'en' if 'en' in accept_lang else 'hu'
    STORED_NEWS = scrape_all_news(lang)
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
