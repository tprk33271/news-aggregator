import os
import requests
import feedparser
import google.generativeai as genai
from dotenv import load_dotenv

# Load Environment Variables
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_path, override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not all([GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID]):
    print("⚠️  Please set GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, and TELEGRAM_CHAT_ID in .env file")
    exit(1)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

def fetch_rss_news(url, limit=15):
    try:
        feed = feedparser.parse(url)
        return [entry.title + (" - " + entry.summary[:200] if hasattr(entry, 'summary') else "") for entry in feed.entries[:limit]]
    except Exception as e:
        print(f"Error fetching RSS {url}: {e}")
        return []

def fetch_trending_crypto():
    try:
        url = "https://api.coingecko.com/api/v3/search/trending"
        headers = {"accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        trending_coins = []
        for item in data.get('coins', [])[:10]:
            coin = item['item']
            price = coin.get('data', {}).get('price', 'N/A')
            trending_coins.append(f"• {coin['name']} ({coin['symbol']}) - Price: {price}")
        return trending_coins
    except Exception as e:
        print(f"Error fetching CoinGecko: {e}")
        return []

def gather_raw_data():
    raw_data = ""
    raw_data += "\n--- ข่าวการเมืองโลกและการเงิน (Geopolitics & Macro) ---\n"
    raw_data += "\n".join(fetch_rss_news("http://feeds.bbci.co.uk/news/world/rss.xml")) + "\n"
    raw_data += "\n".join(fetch_rss_news("https://finance.yahoo.com/news/rss")) + "\n"
    
    raw_data += "\n--- ข่าว Crypto, TGE, Airdrops ---\n"
    raw_data += "\n".join(fetch_rss_news("https://cointelegraph.com/rss")) + "\n"
    
    raw_data += "\n--- เหรียญมาแรง (Trending Coins/Memes) ---\n"
    raw_data += "\n".join(fetch_trending_crypto()) + "\n"
    
    return raw_data

def summarize_with_gemini(raw_text):
    prompt = f"""
    คุณคือ AI บรรณาธิการข่าวและนักวิเคราะห์การลงทุนระดับโลก
    หน้าที่ของคุณคืออ่านข้อมูลดิบด้านล่าง และเขียนสรุปเป็น "Daily Briefing" ที่มีความยาว เจาะลึก และเห็นภาพรวมที่ชัดเจน
    
    จัดรูปแบบผลลัพธ์ให้น่าอ่าน แบ่งเป็น 3 หมวดหมู่ชัดเจน:
    
    🌍 1. ข่าวเด่นการเมืองโลก & แมคโคร (Geopolitics & Macro)
    - เลือกข่าวที่สำคัญที่สุด 3-5 ข่าว
    - อธิบายเนื้อหาข่าว พร้อมวิเคราะห์สั้นๆ ว่า "ส่งผลกระทบต่อตลาดหรือโลกอย่างไร" (เขียนเป็นย่อหน้าสั้นๆ ไม่ใช่แค่บรรทัดเดียว)
    
    💎 2. เจาะลึกคริปโต & TGE / Airdrops
    - สรุปสถานการณ์ตลาดคริปโตหลัก
    - **สำคัญมาก:** หากมีข่าวเกี่ยวกับโปรเจกต์ใหม่, TGE, หรือ Airdrop ให้เน้นเป็นพิเศษและอธิบายรายละเอียดโปรเจกต์นั้นๆ
    - เขียนอธิบายแต่ละข่าวความยาว 2-3 บรรทัด
    
    🚀 3. เรดาร์เหรียญกระแสมาแรง (Trending)
    - นำรายชื่อเหรียญมาแสดง พร้อมเขียนวิเคราะห์สั้นๆ ว่า "ทำไมช่วงนี้ถึงมีกระแส" หรือจัดหมวดหมู่ให้ดูง่าย (เช่น หมวด AI, หมวด Meme)
    
    กฎเพิ่มเติม:
    - ห้ามใช้ Markdown (เช่น ** หรือ *) ในคำตอบเด็ดขาด ให้ใช้ข้อความธรรมดาเท่านั้น
    - ความยาวทั้งหมดต้องไม่เกิน 3000 ตัวอักษร เพื่อให้ส่งผ่าน Telegram ได้
    
    ข้อมูลดิบ:
    {raw_text}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ ขัดข้อง: ไม่สามารถสรุปข่าวจาก AI ได้ในขณะนี้ ({e})"

def send_telegram_message(text):
    # Telegram max message length is 4096 characters
    if len(text) > 4000:
        text = text[:4000] + "\n... (ข้อความยาวเกินไป ถูกตัดออก)"
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    response = requests.post(url, json=payload, timeout=10)
    print("Telegram API Response:", response.text)

if __name__ == "__main__":
    print("Fetching data...")
    raw_info = gather_raw_data()
    print("Summarizing with AI...")
    final_news = summarize_with_gemini(raw_info)
    print("Sending to Telegram...")
    send_telegram_message(final_news)
    print("Done!")
