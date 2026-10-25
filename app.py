import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, redirect, url_for

app = Flask(__name__)

# Globális változó a hírek tárolására a memóriában (így nincs szükség adatbázisra a rajthoz)
STORED_NEWS = []

def scrape_hirkereso():
    """Lekéri a legfrissebb híreket a Hírkeresőről"""
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
        
        # Megkeressük a hírblokkokat a Hírkereső oldalán
        # Megjegyzés: A Hírkereső struktúrájától függően ez a rész finomítható
        links = soup.find_all("a", href=True)
        
        for link in links:
            title = link.get_text(strip=True)
            href = link["href"]
            
            # Kiszűrjük a releváns híreket (pl. amelyek külső hivatkozások vagy fix mintát követnek)
            if title and len(title) > 20 and (href.startswith("http") or "hirkereso.hu" in href):
                # Elkerüljük a duplikációkat
                if not any(n['link'] == href for n in news_list):
                    news_list.append({
                        "title": title,
                        "link": href
                    })
            
            # Max 30 hírt gyűjtünk be egyszerre
            if len(news_list) >= 30:
                break
                
        return news_list
    except Exception as e:
        print(f"Hiba a hírgyűjtés során: {e}")
        return []

# Beépített HTML sablon (így nem kell külön templates mappa a kezdeti indításhoz)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WeeklyNews Portal</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; margin: 0; padding: 0; background-color: #f4f6f9; color: #333; }
        header { background-color: #1e293b; color: white; padding: 2rem 1rem; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { margin: 0; font-size: 2.5rem; }
        .container { max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        .btn-refresh { display: inline-block; background-color: #2563eb; color: white; padding: 0.75rem 1.5rem; text-decoration: none; border-radius: 5px; font-weight: bold; margin-bottom: 1.5rem; transition: background 0.2s; }
        .btn-refresh:hover { background-color: #1d4ed8; }
        .news-card { background: white; padding: 1.5rem; margin-bottom: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 5px solid #2563eb; }
        .news-card a { color: #1e293b; text-decoration: none; font-size: 1.2rem; font-weight: 600; }
        .news-card a:hover { color: #2563eb; text-decoration: underline; }
        .empty-state { text-align: center; padding: 3rem; background: white; border-radius: 8px; }
    </style>
</head>
<body>

    <header>
        <h1>📰 WeeklyNews Portal</h1>
        <p>A saját, független hírgyűjtő oldalam</p>
    </header>

    <div class="container">
        <a href="/frissites" class="btn-refresh">🔄 Hírek frissítése most</a>
        
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

</body>
</html>
"""

@app.route("/")
def index():
    # Ha még üres a lista, az első megnyitáskor automatikusan lefut egy gyűjtés
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
    # Render.com környezetben a PORT változót használjuk
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
