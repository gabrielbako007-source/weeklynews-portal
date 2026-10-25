import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, redirect, url_for

app = Flask(__name__)

STORED_NEWS = []

def scrape_hirkereso():
    url = "https://hirkereso.hu"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            return []
        soup = BeautifulSoup(response.content, "html.parser")
        news_list = []
        links = soup.find_all("a", href=True)
        for link in links:
            title = link.get_text(strip=True)
            href = link["href"]
            if title and len(title) > 20 and (href.startswith("http") or "hirkereso.hu" in href):
                if not any(n['link'] == href for n in news_list):
                    news_list.append({"title": title, "link": href})
            if len(news_list) >= 30:
                break
        return news_list
    except Exception as e:
        print(f"Hiba történt: {e}")
        return []

# A CÍMLAP ALAPJÁN KÉSZÍTETT PRÉMIUM ARCULAT
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>THE WEEKLY TWN NEWS</title>
    <style>
        :root {
            --bg-color: #1a242f;
            --text-main: #ffffff;
            --text-dark: #0f172a;
            --accent-red: #ff2a2a;
            --accent-blue: #3ba2ff;
            --card-bg: rgba(255, 255, 255, 0.07);
            --card-border: rgba(255, 255, 255, 0.12);
        }
        
        body { 
            font-family: 'Times New Roman', Times, 'Georgia', serif; 
            margin: 0; 
            padding: 0; 
            background-color: var(--bg-color); 
            color: var(--text-main);
            background-image: radial-gradient(circle at top, #2c3e50 0%, #121a21 100%);
            min-height: 100vh;
        }

        /* A CÍMLAP LOGÓ PONTOS LEKÉPZÉSE */
        header { 
            background-color: rgba(15, 23, 42, 0.6);
            padding: 3rem 1rem 2rem 1rem; 
            text-align: center;
            border-bottom: 2px solid #ffffff;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }

        .brand-container {
            display: inline-block;
            border-top: 2px solid #ffffff;
            border-bottom: 2px solid #ffffff;
            padding: 1rem 3rem;
            margin-bottom: 1rem;
            background: rgba(0,0,0,0.2);
        }

        .logo-row {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }

        .logo-the {
            font-size: 4rem;
            font-weight: bold;
            font-family: 'Times New Roman', Times, serif;
            line-height: 0.8;
            letter-spacing: -2px;
            border-right: 2px solid #ffffff;
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
            letter-spacing: 4px;
            color: transparent;
            -webkit-text-stroke: 1px #ffffff;
            line-height: 1;
        }

        .logo-bottom-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 2px;
        }

        .logo-twn-badge {
            background-color: var(--accent-blue);
            color: #ffffff;
            font-family: 'Times New Roman', Times, serif;
            font-size: 1rem;
            font-weight: bold;
            font-style: italic;
            padding: 2px 8px;
            border-radius: 4px;
            position: relative;
            box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        }

        /* Kis duma-buborék csőr a TWN alá */
        .logo-twn-badge::after {
            content: '';
            position: absolute;
            bottom: -5px;
            left: 20%;
            border-width: 5px 5px 0;
            border-style: solid;
            border-color: var(--accent-blue) transparent;
            display: block;
            width: 0;
        }

        .logo-news {
            font-size: 2.5rem;
            font-weight: 900;
            font-family: 'Impact', 'Arial Black', sans-serif;
            color: var(--accent-red);
            letter-spacing: 2px;
            line-height: 1;
        }

        .sub-slogan {
            font-size: 1.3rem;
            letter-spacing: 12px;
            text-transform: uppercase;
            font-weight: bold;
            margin-top: 1rem;
            color: #ffffff;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }

        /* TARTALOM */
        .container { 
            max-width: 850px; 
            margin: 3rem auto; 
            padding: 0 1.5rem; 
        }

        .actions {
            text-align: center;
            margin-bottom: 2.5rem;
        }

        .btn-refresh { 
            display: inline-block;
            background-color: var(--accent-red); 
            color: white; 
            padding: 0.8rem 2rem; 
            text-decoration: none; 
            border-radius: 0px; /* Magazinos, szögletes stílus */
            font-family: sans-serif;
            font-weight: bold; 
            font-size: 1rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            transition: all 0.2s ease;
            box-shadow: 0 4px 15px rgba(255, 42, 42, 0.3);
            border: 1px solid #ffffff;
        }

        .btn-refresh:hover { 
            background-color: #d61c1c;
            transform: scale(1.03);
        }

        /* MAGAZIN KÁRTYÁK */
        .news-grid {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }

        .news-card { 
            background: var(--card-bg); 
            padding: 2rem; 
            border: 1px solid var(--card-border);
            border-left: 6px solid var(--accent-blue);
            backdrop-filter: blur(10px);
            transition: all 0.25s ease;
        }

        .news-card:hover { 
            transform: translateX(8px); 
            border-color: rgba(255,255,255,0.3);
            background: rgba(255, 255, 255, 0.12);
            box-shadow: 0 5px 25px rgba(0,0,0,0.2);
        }

        .news-card a { 
            color: var(--text-main); 
            text-decoration: none; 
            font-size: 1.4rem; 
            font-weight: bold; 
            line-height: 1.4;
            display: block;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.3);
        }

        .news-card:hover a { 
            color: #ffffff;
        }

        .empty-state { 
            text-align: center; 
            padding: 4rem 2rem; 
            background: var(--card-bg); 
            border: 1px solid var(--card-border);
            color: #a0aec0; 
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
                        <div class="logo-twn-badge">TWN</div>
                        <div class="logo-news">NEWS</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="sub-slogan">Közéleti Hetilap</div>
    </header>

    <div class="container">
        <div class="actions">
            <a href="/frissites" class="btn-refresh">🔄 Friss hírek beolvasása</a>
        </div>
        
        <div class="news-grid">
            {% if news %}
                {% for item in news %}
                    <div class="news-card">
                        <a href="{{ item.link }}" target="_blank">{{ item.title }}</a>
                    </div>
                {% endfor %}
            {% else %}
                <div class="empty-state">
                    <p>Még nincsenek letöltött hírek. Kattints a frissítés gombra!</p>
                </div>
            {% endif %}
        </div>
    </div>

</body>
</html>
"""

@app.route("/")
def index():
    global STORED_NEWS
    if not STORED_NEWS:
        STORED_NEWS = scrape_hirkereso()
    return render_template_string(HTML_TEMPLATE, news=STORED_NEWS)

@app.route("/frissites")
def refresh():
    global STORED_NEWS
    STORED_NEWS = scrape_hirkereso()
    return redirect(url_for("index"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
