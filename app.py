import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
from datetime import datetime
import time
import os
import json
import base64

# ==========================================
# 1. AYARLAR VE VERİTABANI BAĞLANTISI
# ==========================================
st.set_page_config(page_title="Dr. Sait SEVİNÇ - Pro Analiz", layout="wide", page_icon="🧬")

# Grafik Ayarları (Mobilde bozulmayı önler, statik yapar)
PLOTLY_CONFIG = {
    'staticPlot': True,       # Grafiği resim gibi dondurur (Mobilde kaydırmayı düzeltir)
    'displayModeBar': False,  # Menü çubuğunu gizler
    'showTips': False
}

# Veritabanı Kurulumu (SQLite)
def init_db():
    conn = sqlite3.connect('analiz_gecmisi.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sonuclar
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ad TEXT, yas INTEGER, tarih TEXT, 
                  tip TEXT, ozet TEXT, detay_json TEXT)''')
    conn.commit()
    return conn

CONN = init_db()

# --- LOGO VE VERİ YÜKLEME ---
@st.cache_data
def load_resources():
    logo_path = "drsaitlogo.jpeg"
    default_logo = "https://i.ibb.co/xJc52gL/image-0.png"
    # Mizaç Bilgileri (Kütüphane)
    default_json = {
        "Safravi": {"Genel": "Sıcak-Kuru mizaç. Ateş elementi. Lider, hızlı ve öfkelidir.", "Beslenme": "Serinletici ve nemlendirici gıdalar (Salatalık, marul, yoğurt).", "Riskler": ["Migren", "Safra Taşları", "Cilt Kuruluğu", "Uykusuzluk"]},
        "Demevi": {"Genel": "Sıcak-Nemli mizaç. Hava elementi. Sosyal, neşeli ve rahattır.", "Beslenme": "Kuru ve serin gıdalar. Kırmızı eti azaltın.", "Riskler": ["Yüksek Tansiyon", "Kalp Sorunları", "Sivilce/Akne"]},
        "Balgami": {"Genel": "Soğuk-Nemli mizaç. Su elementi. Sakin, uyumlu ve yavaştır.", "Beslenme": "Isıtıcı ve kurutucu baharatlar (Zencefil, kekik, tarçın).", "Riskler": ["Obezite", "Romatizma", "Unutkanlık", "Ödem"]},
        "Sovdavi": {"Genel": "Soğuk-Kuru mizaç. Toprak elementi. Detaycı, planlı ve içe dönük.", "Beslenme": "Isıtıcı ve nemlendirici gıdalar (Et suyu, tereyağı).", "Riskler": ["Depresyon", "Varis", "Kabızlık", "Kuruntu"]}
    }
    return logo_path, default_logo, default_json

LOGO_LOCAL, LOGO_URL, MIZAC_BILGILERI = load_resources()

# ==========================================
# 2. DERİN ANALİZ MOTORU (YENİ 🔥)
# ==========================================
def generate_deep_analysis(mizac, cakra_sonuclar):
    yorumlar = []
    
    # 1. Mizaç Bazlı Derin Yorum
    if mizac == "Safravi":
        yorumlar.append("🔥 **Ateş Elementi Baskın:** Vücudunuzda ısı ve kuruluk hakim. Bu durum öfke kontrol sorunlarına ve inflamasyona (iltihap) yatkınlık oluşturabilir. Serinlemeniz hayati önem taşır.")
    elif mizac == "Balgami":
        yorumlar.append("💧 **Su Elementi Baskın:** Metabolizmanız yavaşlamaya meyilli. Hareketsizlik sizin en büyük düşmanınızdır. Isıtıcı gıdalarla sindirim ateşini yükseltmelisiniz.")
    
    # 2. Çakra & Mizaç Kombinasyonu (Çapraz Analiz)
    if cakra_sonuclar:
        kok = cakra_sonuclar.get("KÖK ÇAKRA (Muladhara)", {}).get("durum")
        if kok and ("Yavaş" in kok or "Blokaj" in kok) and mizac == "Sovdavi":
            yorumlar.append("⚠️ **Kritik Uyarı:** Toprak elementi mizacınız (Sovdavi) ile Kök Çakra blokajınız birleşmiş. Bu, aşırı gelecek kaygısı ve 'köksüzlük' hissi yaratabilir. Doğada yalın ayak yürümek sizin için en iyi ilaçtır.")
        
        solar = cakra_sonuclar.get("SOLAR PLEXUS (Manipura)", {}).get("durum")
        if solar and "Aşırı" in solar and mizac == "Safravi":
            yorumlar.append("⚠️ **Kritik Uyarı:** Ateş mizacınız ile 'Ateş Çakrası' (Solar Plexus) aynı anda yüksek çalışıyor. Mide asidi, ülser ve tükenmişlik sendromuna çok açıksınız. Rekabetten uzak durun.")

    if not yorumlar:
        yorumlar.append("✅ Genel dengeniz makul görünüyor. Mevcut yaşam tarzınızı koruyarak, mevsimsel beslenmeye dikkat ediniz.")
        
    return " ".join(yorumlar)

# ==========================================
# 3. VERİTABANI İŞLEMLERİ
# ==========================================
def save_to_db(user_info, test_type, summary_text, detail_data):
    try:
        c = CONN.cursor()
        tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
        detail_json = json.dumps(detail_data, ensure_ascii=False)
        c.execute("INSERT INTO sonuclar (ad, yas, tarih, tip, ozet, detail_json) VALUES (?, ?, ?, ?, ?, ?)",
                  (user_info['ad'], user_info['yas'], tarih, test_type, summary_text, detail_json))
        CONN.commit()
        st.toast("✅ Sonuçlar Veritabanına Kaydedildi!")
    except Exception as e:
        st.error(f"Kayıt Hatası: {e}")

def get_history():
    c = CONN.cursor()
    c.execute("SELECT id, ad, yas, tarih, tip, ozet FROM sonuclar ORDER BY id DESC")
    return c.fetchall()

# ==========================================
# 4. GRAFİK VE HTML FONKSİYONLARI
# ==========================================
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

def create_html_report(user_info, mizac, detaylar, tarih, fig_cakra_html, cakra_sonuclar, derin_analiz):
    img_data = get_image_base64(LOGO_LOCAL)
    img_src = f"data:image/jpeg;base64,{img_data}" if img_data else LOGO_URL
    
    # Çakra Tablosu
    cakra_rows = ""
    if cakra_sonuclar:
        for cakra, degerler in cakra_sonuclar.items():
            durum = degerler['durum']
            color = "#2ecc71" if "Dengeli" in durum else ("#f39c12" if "Hafif" in durum else "#e74c3c")
            cakra_rows += f"<tr><td><strong>{cakra}</strong></td><td>{degerler['yavas_puan']}</td><td>{degerler['asiri_puan']}</td><td style='color:{color}'><strong>{durum}</strong></td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Analiz Raporu</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: sans-serif; color: #333; padding: 20px; max-width: 800px; margin: auto; }}
            .header {{ text-align: center; border-bottom: 2px solid #333; margin-bottom: 20px; }}
            .logo {{ width: 80px; }}
            .box {{ border: 1px solid #ddd; padding: 15px; border-radius: 8px; margin-bottom: 20px; background: #f9f9f9; }}
            .deep-analysis {{ background-color: #e8f4f8; border-left: 5px solid #3498db; padding: 15px; margin: 20px 0; }}
            table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
            th, td {{ padding: 8px; border-bottom: 1px solid #ddd; text-align: center; }}
            td:first-child {{ text-align: left; }}
        </style>
    </head>
    <body>
        <div class="header">
            <img src="{img_src}" class="logo">
            <h2>BÜTÜNCÜL SAĞLIK RAPORU</h2>
            <p>{user_info.get('ad')} | {user_info.get('yas')} Yaş | {tarih}</p>
        </div>
        
        <div class="deep-analysis">
            <h3>🧠 Uzman Yorumu & Derin Analiz</h3>
            <p>{derin_analiz}</p>
        </div>

        {'<div class="box"><h3>🦁 Baskın Mizaç: ' + mizac + '</h3><p>' + detaylar.get('Genel','') + '</p></div>' if mizac else ''}
        
        {'<div class="box"><h3>🌀 Çakra Analizi</h3>' + fig_cakra_html + '<table><tr><th>Çakra</th><th>Blokaj</th><th>Aşırı</th><th>Durum</th></tr>' + cakra_rows + '</table></div>' if cakra_sonuclar else ''}
        
        <div style="text-align:center; font-size:0.8em; color:#999; margin-top:30px;">Dr. Sait SEVİNÇ Analiz Sistemi</div>
    </body>
    </html>
    """
    return html

# ==========================================
# 5. TEST VERİLERİ (TAM SORU SETİ - RESTORE EDİLDİ)
# ==========================================
SORULAR_ISI = [
    {"text": "Boş vakitlerinizde ne yaparsınız?", "options": [{"text": "Evde zaman geçirmek", "value": 1}, {"text": "Çoğunlukla evde", "value": 2}, {"text": "Bazen evde bezen dışarda", "value": 3}, {"text": "Genellikle dışarda", "value": 4}, {"text": "Evin dışında", "value": 5}]},
    {"text": "Düzene karşı tutumunuz?", "options": [{"text": "Her zaman temiz ve düzenliyim", "value": 1}, {"text": "Çoğunlukla düzenli", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Dağınıklığı sevmem ama yapmam", "value": 4}, {"text": "Dağınık ama bulurum", "value": 5}]},
    {"text": "Paraya karşı tutumunuz?", "options": [{"text": "Genellikle tutumluyum", "value": 1}, {"text": "Gerektiği kadar", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Ailem için", "value": 4}, {"text": "Para harcamayı severim", "value": 5}]},
    {"text": "Genel ruhsal durumunuz?", "options": [{"text": "Keyifsiz", "value": 1}, {"text": "Kaygılı", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Keyifli", "value": 4}, {"text": "Mutlu", "value": 5}]},
    {"text": "Nasıl yürürsünüz?", "options": [{"text": "Çok Yavaş", "value": 1}, {"text": "Yavaş", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Hızlı", "value": 4}, {"text": "Çok Hızlı", "value": 5}]},
    {"text": "Yeni bir ortama girdiğinizde?", "options": [{"text": "Çok az konuşurum", "value": 1}, {"text": "Soru sorulursa", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Konuşkanım", "value": 4}, {"text": "Çok konuşurum", "value": 5}]},
    {"text": "Yeni tanıştığınız insanlara tavrınız?", "options": [{"text": "Çekimser", "value": 1}, {"text": "Mesafeli", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Temkinli ılıman", "value": 4}, {"text": "Samimi", "value": 5}]},
    {"text": "Arkadaş çevreniz nasıl?", "options": [{"text": "Yok denecek kadar az", "value": 1}, {"text": "Çok Az", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Fazla", "value": 4}, {"text": "Geniş çevre", "value": 5}]},
    {"text": "Ses tonunuz nasıl?", "options": [{"text": "Çok sakin/yumuşak", "value": 1}, {"text": "Sakin", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Hızlı / Yüksek", "value": 4}, {"text": "Çok Yüksek", "value": 5}]},
    {"text": "Karar alma süreciniz?", "options": [{"text": "Çok yavaş", "value": 1}, {"text": "Yavaş-Kararsız", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Hızlı", "value": 4}, {"text": "Çok Hızlı", "value": 5}]},
    {"text": "Günlük enerji seviyeniz?", "options": [{"text": "Çok düşük", "value": 1}, {"text": "Düşük", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Yüksek", "value": 4}, {"text": "Çok Yüksek", "value": 5}]},
    {"text": "Konuşma hızınız?", "options": [{"text": "Tane tane", "value": 1}, {"text": "Akıcı", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Hızlı", "value": 4}, {"text": "Çok Hızlı", "value": 5}]},
    {"text": "Cesaret durumunuz?", "options": [{"text": "Hiç", "value": 1}, {"text": "Çok az", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Cesur", "value": 4}, {"text": "Çok Cesur", "value": 5}]},
    {"text": "Gün içindeki düşünceleriniz?", "options": [{"text": "Geçmiş/Negatif", "value": 1}, {"text": "Karamsar", "value": 2}, {"text": "İnişli çıkışlı", "value": 3}, {"text": "İş/Gelecek", "value": 4}, {"text": "Pozitif", "value": 5}]},
    {"text": "Enerjinizin yüksek olduğu saat?", "options": [{"text": "Öğle", "value": 1}, {"text": "Sabah", "value": 2}, {"text": "Belirsiz", "value": 3}, {"text": "Akşam", "value": 4}, {"text": "Gece", "value": 5}]},
    {"text": "Enerjinizin düşük olduğu saat?", "options": [{"text": "Gece", "value": 1}, {"text": "Akşam", "value": 2}, {"text": "Belirsiz", "value": 3}, {"text": "Öğle", "value": 4}, {"text": "Sabah", "value": 5}]},
    {"text": "Kurallara riayet?", "options": [{"text": "Çok fazla", "value": 1}, {"text": "Fazla", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Az", "value": 4}, {"text": "Çok az", "value": 5}]},
    {"text": "İçsel diyalog (Takıntı)?", "options": [{"text": "Çok fazla", "value": 1}, {"text": "Fazla", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Az", "value": 4}, {"text": "Çok az", "value": 5}]},
    {"text": "Sindirim sistemi çalışması?", "options": [{"text": "Çok zayıf", "value": 1}, {"text": "Zayıf", "value": 2}, {"text": "Orta", "value": 3}, {"text": "İyi", "value": 4}, {"text": "Çok iyi", "value": 5}]},
    {"text": "Su tüketimi isteği?", "options": [{"text": "Çok az/aklıma gelmez", "value": 1}, {"text": "Az", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Çok susarım", "value": 4}, {"text": "Sürekli susarım", "value": 5}]}
]

SORULAR_NEM = [
    {"text": "Uyku ile ilişkiniz?", "options": [{"text": "Gözümü açamam", "value": 1}, {"text": "Uykuyu severim", "value": 2}, {"text": "Normal", "value": 3}, {"text": "Az uyurum", "value": 4}, {"text": "Çok az uyurum", "value": 5}]},
    {"text": "Vücut yapınız?", "options": [{"text": "Çok yağlı/kilolu", "value": 1}, {"text": "Yağlı/meyilli", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Zayıf", "value": 4}, {"text": "Çok zayıf", "value": 5}]},
    {"text": "Ten renginiz?", "options": [{"text": "Çok beyaz", "value": 1}, {"text": "Beyaz/Buğday", "value": 2}, {"text": "Normal", "value": 3}, {"text": "Buğday", "value": 4}, {"text": "Koyu", "value": 5}]},
    {"text": "Kilo alma eğilimi?", "options": [{"text": "Çok fazla", "value": 1}, {"text": "Fazla", "value": 2}, {"text": "Normal", "value": 3}, {"text": "Az", "value": 4}, {"text": "Çok az", "value": 5}]},
    {"text": "Saç gürlüğü?", "options": [{"text": "Çok Seyrek", "value": 1}, {"text": "Seyrek", "value": 2}, {"text": "Normal", "value": 3}, {"text": "Gür", "value": 4}, {"text": "Çok Gür/Kıvırcık", "value": 5}]},
    {"text": "Sabah ağız tadı?", "options": [{"text": "Tatlı", "value": 1}, {"text": "Buruk/Tatsız", "value": 2}, {"text": "Normal", "value": 3}, {"text": "Acımtırak", "value": 4}, {"text": "Ekşi/Tuzlu", "value": 5}]},
    {"text": "Salya/Burun akıntısı?", "options": [{"text": "Çok", "value": 1}, {"text": "Nemli", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Az", "value": 4}, {"text": "Kuru", "value": 5}]},
    {"text": "Hafıza?", "options": [{"text": "Unutkanım", "value": 1}, {"text": "Çabuk öğrenir/unuturum", "value": 2}, {"text": "Normal", "value": 3}, {"text": "İyidir", "value": 4}, {"text": "Çok kuvvetli", "value": 5}]},
    {"text": "Cilt yapısı (Dokunuş)?", "options": [{"text": "Çok yumuşak", "value": 1}, {"text": "Yumuşak", "value": 2}, {"text": "Normal", "value": 3}, {"text": "Kuru", "value": 4}, {"text": "Çok kuru/çatlar", "value": 5}]},
    {"text": "Uyum sağlama?", "options": [{"text": "Başkaları uyar", "value": 1}, {"text": "Esnek/Uyumlu", "value": 2}, {"text": "Normal", "value": 3}, {"text": "Uyumsuzum", "value": 4}, {"text": "Çevrem bana uyar", "value": 5}]},
    {"text": "Yüz hatları?", "options": [{"text": "Yuvarlak/Etli", "value": 1}, {"text": "Hafif yuvarlak", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Belirgin kemikli", "value": 4}, {"text": "Çok belirgin kemikli", "value": 5}]},
    {"text": "İştah durumu?", "options": [{"text": "Çok iştahlı", "value": 1}, {"text": "İştahlı", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Az iştahlı", "value": 4}, {"text": "İştahsız", "value": 5}]},
    {"text": "İfrazat/Akciğer doluluğu?", "options": [{"text": "Çok olur", "value": 1}, {"text": "Genelde var", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Az olur", "value": 4}, {"text": "Çok az", "value": 5}]},
    {"text": "Saç uzama/yapı?", "options": [{"text": "Yumuşak/Yavaş uzar", "value": 1}, {"text": "Yumuşak/Hızlı", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Kuru/Yavaş", "value": 4}, {"text": "Kuru/Hızlı/Kıvırcık", "value": 5}]},
    {"text": "Öfke/Reaksiyon süresi?", "options": [{"text": "Yavaş öfkelenirim", "value": 1}, {"text": "Çabuk öfke/Çabuk geçer", "value": 2}, {"text": "Orta", "value": 3}, {"text": "Az öfke/Geçmez", "value": 4}, {"text": "Çok öfke/Kalıcı", "value": 5}]},
    {"text": "Ağız suyu?", "options": [{"text": "Çok olur", "value": 1}, {"text": "Koyu/Kıvamlı", "value": 2}, {"text": "Normal", "value": 3}, {"text": "Az", "value": 4}, {"text": "Kuru", "value": 5}]},
    {"text": "Burun yapısı?", "options": [{"text": "Geniş/Etli", "value": 1}, {"text": "Geniş", "value": 2}, {"text": "Orta", "value": 3}, {"text": "İnce", "value": 4}, {"text": "Çok İnce", "value": 5}]},
    {"text": "Cilt tipi?", "options": [{"text": "Yağlı", "value": 1}, {"text": "Nemli", "value": 2}, {"text": "Karma", "value": 3}, {"text": "Kuru", "value": 4}, {"text": "Çok Kuru", "value": 5}]},
    {"text": "Avuç yapısı?", "options": [{"text": "Geniş/Kısa parmak", "value": 1}, {"text": "İri/Etli", "value": 2}, {"text": "Normal", "value": 3}, {"text": "Dengeli", "value": 4}, {"text": "İnce/Uzun", "value": 5}]},
    {"text": "Kaşıntı/Egzama?", "options": [{"text": "Yoktur", "value": 1}, {"text": "Çok az", "value": 2}, {"text": "Nadiren", "value": 3}, {"text": "Genelde olur", "value": 4}, {"text": "Çok olur", "value": 5}]}
]

SORULAR_GENEL_DETAYLI = {
    "SICAKLIK": {
        "puanlar": {"Hayır": 1, "Orta derece": 2, "Kesinlikle evet": 3},
        "sorular": ["Arkadaş çevrem geniş sosyal biriyim", "Hızlı düşünür çabuk harekete geçerim", "Konuşkan sıcakkanlı bir yapım var", "Soğuk havaları severim", "Soğuk yiyecek içeceklerden hoşlanırım", "Vücudum sıcaktır", "Takıntılı değilim", "Cesur ve atak biriyim", "Çok detaylı düşünmem", "Kabızlık sorunu çok fazla yaşamam", "Rutin / tekdüze sakin yaşamdan pek sevmem", "Pozitifim", "Kuralları çok sevmem", "Sonuç odaklıyım", "Lider bir ruhum var", "Genelde enerjik bir yapım var", "Yapılanı unuturum kin tutamam", "Sır saklamakta zorlanırım anlatma eğilimim vardır"]
    },
    "SOĞUKLUK": {
        "puanlar": {"Hayır": 1, "Orta derece": 2, "Kesinlikle evet": 3},
        "sorular": ["Çok geniş bir çevrem yok", "Temkinli biriyim", "Hemen samimi olmam, seçiciyim", "Sıcak havaları severim", "Sıcak yiyecek ve içeceklerden hoşlanırım", "Vücudum soğuktur üşürüm", "Takıntılıyım", "Hassas ve alıngan biriyim", "Aceleyi sevmem işimi sağlam yavaş yavaş yaparım", "Kabızlık sorunu çok yaşarım", "Sakin yaşam severim", "Karamsarım", "Kurallara uyarım", "Süreç odaklıyım", "İyi bir takım oyuncusuyum", "Genelde enerjim düşüktür (çabuk yorulurum)", "Negatifi unutmam", "Sır saklarım"]
    },
    "KURULUK": {
        "puanlar": {"Hayır": 0, "Orta derece": 2, "Kesinlikle evet": 3},
        "sorular": ["Saçlarım kalın telli", "Zayıf ince yapılıyım", "Cildim genelde kuru", "Cilt lekelerim vardır lekelenmeye müsaittir", "Çok uyuyamam derin değildir uyanırım hemen", "Sıkı ve gergin bir cildim var", "Göz yapım küçüktür", "Belim nispeten incedir", "Hafızam kuvvetlidir", "Duyularım gelişmiştir duyma/ koku alma", "Esnek biri değilim uyum sağlamam zordur", "Eklemlerim çıkıntılı", "Tenim daha sarı ve koyu renkte", "Tırnaklarım serttir", "Çabuk pes etmem ısrarcıyım", "Genelde burun akıntım çok az olur", "Kaşıntı egzemaya yatkınlığım fazladır", "Ağız kuruluğum fazladır"]
    },
    "NEMLİLİK": {
        "puanlar": {"Hayır": 0, "Orta derece": 1, "Kesinlikle evet": 2},
        "sorular": ["Saçlarım ince telli", "Kiloluyum", "Cildim yumuşaktır", "Uykuyu severim derin uyurum", "Çok az cilt lekelerim var", "Cildim yumuşak ve esnektir", "Göz yapım iri ve nemlidir", "Belim nispeten kalındır", "Hafızam kuvvetli değil tekrarlamazsam çabuk unuturum", "Duyularım zayıftır koku alma/işitme", "Esnek biriyim uyum sağlarım", "Eklemlerim, hatlarım belirgin değildir", "Yuvarlak yüzlüyüm", "Tırnak yapım yumuşaktır", "Çabuk pes ederim bıkarım", "Burun akıntım olur", "Egzema ve kaşıntı çok nadir görülür", "Ağız kuruluğum yoktur sulu ve yoğun olabilir"]
    }
}

SORULAR_CAKRA = {
    "KÖK ÇAKRA (Muladhara)": [
        "Kendimi çoğu zaman güvensiz, huzursuz ya da korunmasız hissediyorum.", "Değersiz ya da yetersiz biriymişim gibi hissettiğim anlar sık yaşanıyor.", "Günlük yaşamımda temel ihtiyaçlarımı bile karşılamakta zorlanıyorum.", "Parasal konular beni çok tedirgin ediyor; sürekli bir yokluk kaygısı taşıyorum.",
        "Fiziksel olarak zayıf, halsiz ve enerjisiz hissediyorum.", "Aidiyet hissim zayıf; ne bir yere ne de birilerine gerçekten ait hissedemiyorum.", "Hızlıca odaklanamıyor, başladığım işleri tamamlayamıyorum.", "Bağımlı ilişkiler kurmaya eğilimliyim; tek başıma güvende hissedemiyorum.",
        "Maddi güvence konusunda aşırı takıntılıyım; sahip olduklarımı kaybetme korkusu taşıyorum.", "Fazla inatçı, kontrolcü ve değişime kapalı biri olduğumu düşünüyorum.", "İnsanlara kolay kolay güvenemem, her şeyin altında bir tehdit ararım.", "Fiziksel dünyaya fazlasıyla bağlıyım; maneviyatla ilişkim çok zayıf.",
        "Bırakamama, tutunma, bir şeyi ya da kişiyi bırakınca sanki parçalanacakmışım gibi hissediyorum.", "Kızgınlık, öfke ya da patlayıcı tepkilerle çevreme zarar verebiliyorum.", "Kendi isteklerim doğrultusunda başkalarını yönlendirmeye ya da baskılamaya çalışıyorum.", "Gücü elimde tutma, her şeye hâkim olma arzusu beni yoruyor."
    ],
    "SAKRAL ÇAKRA (Svadhisthana)": [
        "Duygularımı ifade etmekte zorlanıyor, çoğu zaman içime atıyorum.", "Cinselliğe karşı isteksizlik ya da yabancılaşma yaşıyorum.", "Hayattan keyif almakta zorlanıyor, neşesiz hissediyorum.", "Yaratıcılığımı göstermekten çekiniyor ya da ilham bulmakta zorlanıyorum.",
        "Kendime dair tatmin duygum oldukça düşük; hiçbir şeyden tam olarak memnun olmuyorum.", "Başkalarıyla derin bağ kurmakta zorlanıyor, yalnız kalmayı tercih ediyorum.", "Geçmiş duygusal yaralardan kurtulamadığımı hissediyorum.", "Bedenimle olan ilişkim zayıf, çoğu zaman ona yabancı gibiyim.",
        "Sürekli bir haz peşindeyim; duygusal ya da fiziksel tatmin benim için çok önemli.", "Aşırı cinsellik ya da duygusal bağımlılık gibi durumlara eğilimim var.", "Duygularım çok yoğun ve ani; sıklıkla dalgalanma yaşıyorum.", "Tüketim, alışveriş, yemek gibi haz veren şeylere bağımlı hissediyorum.",
        "Duygusal ilişkilerde sınır koymakta zorlanıyor, kendimi kaybediyorum.", "Aşırı hassasım; başkalarının duygusal durumlarından kolay etkileniyorum.", "Sanatsal ya da yaratıcı alanlarda abartıya kaçtığımı düşünüyorum.", "Kontrolsüz duygusal tepkiler veriyor, sonra pişman oluyorum."
    ],
    "SOLAR PLEXUS (Manipura)": [
        "Karar vermekte zorlanıyor ve çoğu zaman başkalarının onayını bekliyorum.", "Hayır demekte zorlanıyorum; sınırlarımı belirleyemiyorum.", "Kendi gücümü ortaya koymakta zorluk yaşıyor, çekingen davranıyorum.", "Sık sık yetersiz ya da başarısız hissediyorum.",
        "Başladığım işleri tamamlamakta zorlanıyor, motivasyon kaybı yaşıyorum.", "Eleştiriler karşısında kolayca kırılıyor, savunmasız hissediyorum.", "Kendime güvenmekte zorlanıyor, içimde sürekli bir eksiklik hissediyorum.", "Başarıya dair arzularım var ama harekete geçecek enerjiyi bulamıyorum.",
        "Kontrolü kaybetmekten korkuyorum; her şeyin benim istediğim gibi olmasını istiyorum.", "Gücümü göstermek için bazen baskıcı ya da manipülatif davranıyorum.", "Başkalarının alanına girmeye eğilimliyim; her şeye müdahil olmak istiyorum.", "Aşırı rekabetçiyim; sürekli üstün gelme ihtiyacı hissediyorum.",
        "Kendimi çok fazla ön plana çıkarıyor, dikkat çekmek istiyorum.", "Başkalarının duygularını görmezden gelerek sadece kendi isteklerime odaklanabiliyorum.", "Öfke patlamaları yaşıyor, küçük konulara aşırı tepki veriyorum.", "Başarıya bağımlıyım; başarısızlık korkusu beni sürekli tedirgin ediyor."
    ],
    "KALP ÇAKRASI (Anahata)": [
        "Başkalarına karşı sevgimi ifade etmekte zorlanıyorum.", "Kırıldığım kişileri affetmek bana çok zor geliyor.", "İnsanlara güvenmekte zorlanıyorum; duygusal olarak geri çekiliyorum.", "Kendimi sevmekte ve kendime değer vermekte zorlanıyorum.",
        "Duygusal ilişkiler beni yıpratıyor; çoğunlukla kaçınmayı tercih ediyorum.", "Kalbimin kapalı olduğunu hissediyorum; kimseye gerçekten açılamıyorum.", "Geçmiş acılar hâlâ içimde yer tutuyor ve içsel huzurumu engelliyor.", "Sevgi vermektense almayı bekliyorum; paylaşmakta zorlanıyorum.",
        "Herkese yardım etmek zorundaymışım gibi hissediyorum; kendimi ihmal ediyorum.", "İnsanların duygularını o kadar çok hissediyorum ki, kendi sınırlarımı kaybediyorum.", "Başkalarının onayına ve sevgisine bağımlı hissediyorum.", "Duygusal ilişkilerde kendimi fazla veriyor, sonra tükeniyorum.",
        "Hayır diyememek beni sürekli zor durumda bırakıyor.", "Kırılganlığım o kadar yoğun ki, başkalarının duygularıyla boğuluyorum.", "Aşırı özverili davranıyor, karşılık beklemesem bile yıpranıyorum.", "Sevgi adına kendi ihtiyaçlarımı ve isteklerimi yok sayıyorum."
    ],
    "BOĞAZ ÇAKRASI (Vishuddha)": [
        "Duygularımı ya da düşüncelerimi açıkça ifade etmekte zorlanıyorum.", "Topluluk önünde konuşmak beni çok geriyor, hatta kaçınmaya çalışıyorum.", "Kendimi bastırılmış ya da sesi kısılmış biri gibi hissediyorum.", "Doğru zamanda, doğru şekilde konuşamadığımı fark ediyorum.",
        "İletişimde sürekli yanlış anlaşıldığımı düşünüyorum.", "Düşüncelerimi toparlamakta ya da kendimi açık ifade etmekte zorlanıyorum.", "Kendimi ifade etme hakkım yokmuş gibi hissediyorum.", "Çoğu zaman sessiz kalmayı tercih ediyorum, içime kapanıyorum.",
        "Sürekli konuşma ihtiyacı hissediyorum, karşımdakini dinlemekte zorlanıyorum.", "İnsanlara düşüncelerimi zorla kabul ettirmeye çalışıyorum.", "Aşırı açıklık ya da fazla detaylı konuşma eğilimim var.", "Başkalarının sözünü sık sık kesiyor ya da üstünlük kurmaya çalışıyorum.",
        "Eleştiriyi kaldıramıyor ve hemen savunmaya geçiyorum.", "Kendimi ifade ederken farkında olmadan kırıcı ya da saldırgan olabiliyorum.", "Ses tonumla veya ifadelerimle dikkat çekmeye çalışıyorum.", "Başkalarını susturup yalnızca kendi düşüncelerime alan açmak istiyorum."
    ],
    "GÖZ ÇAKRASI (Ajna)": [
        "İçgüdülerime güvenmekte zorlanıyor, sürekli dış onay arıyorum.", "Geleceğe dair net bir vizyonum yok; yönümü bulmakta zorlanıyorum.", "Zihnim dağınık, düşüncelerim bulanık ve kararsızlık içinde hissediyorum.", "Meditasyon ya da içsel sessizlik çalışmalarında zorluk yaşıyorum.",
        "Sezgisel sinyalleri algılayamıyor veya yok sayıyorum.", "Mantık ve sezgi arasında sürekli bir çatışma yaşıyorum.", "Hayal kurmakta, yaratıcı düşünmekte zorluk çekiyorum.", "Geçmişte yaşananlara takılı kalıyor, geleceğe dair umut beslemekte zorlanıyorum.",
        "Sürekli zihnimde yaşıyor, gerçeklikten kopuyorum.", "Olaylara aşırı anlamlar yüklüyor, kuruntular içinde kayboluyorum.", "Rüyalar, semboller ya da işaretlerle aşırı meşgul oluyorum.", "Gerçeklikten uzaklaşma ya da spiritüel kaçış hali yaşıyorum.", "İnsanların ne düşündüğünü “hissettiğime” çok fazla inanıyorum.", "Kontrol edilemeyen bir zihinsel aktivite ve içsel konuşma beni yoruyor.",
        "Gelecekle ilgili aşırı hayal kuruyor ama eyleme geçemiyorum.", "Gerçeklikten kopmama neden olan takıntılı düşünce kalıplarım var."
    ],
    "TAÇ ÇAKRASI (Sahasrara)": [
        "Kendimi evrenden veya daha büyük bir bütünün parçası olarak hissetmekte zorlanıyorum.", "Manevi pratiklere veya içsel yolculuğa karşı ilgisiz ya da uzak hissediyorum.", "Anlam ve amaç bulmakta güçlük çekiyorum.", "Ruhsal ya da kişisel gelişimle ilgili deneyimlere kapalıyım.",
        "İçsel huzur ve sükunet duygusundan yoksunum.", "Meditasyon ya da sessizlik içinde olmaktan kaçınıyorum.", "Hayatımda bir boşluk, anlamsızlık ya da kopukluk hissediyorum.", "Ruhsal deneyimlerimde kararsızlık ya da inanç eksikliği yaşıyorum.",
        "Kendimi sürekli evrensel bilinçle bağlantılı hissediyor, gerçeklikten kopuyorum.", "Dünyadan, günlük hayattan ve bedensel deneyimlerden uzaklaşıyorum.", "Spiritüel uygulamalara aşırı odaklanıyor, bazen fanatikleşiyorum.", "Kendi bedenimi ve maddi dünyayı ihmal ediyorum.",
        "Sıklıkla kendimi “aydınlanmış” veya “öteki seviyede” biri olarak görüyorum.", "Günlük sorumluluklarımdan kaçıyor, gerçeklerle yüzleşmekte zorlanıyorum.", "Spiritüel bilgileri abartıyor ya da bu alanda kendimi üstün görüyorum.", "Manevi deneyimlere aşırı bağımlılık hissediyorum."
    ]
}

# ==========================================
# 6. FONKSİYONLAR
# ==========================================
def init_state():
    defaults = {
        "page": "Giriş", "user_info": {}, 
        "results_isi": None, "results_nem": None, "results_genel": None, "results_cakra": None,
        "genel_skorlar": {}, "genel_yuzdeler": {}, "scores": {"isi": 0, "nem": 0},
        "submitted_genel": False, "submitted_isi": False, "submitted_nem": False, "submitted_cakra": False
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

def render_questions_with_validation(soru_listesi, key_prefix, submitted):
    total_score = 0
    missing = False
    for i, soru in enumerate(soru_listesi):
        key = f"{key_prefix}_{i}"
        val = st.session_state.get(key)
        css = "q-box q-default"
        icon = ""
        if val is not None: css = "q-box q-filled"
        elif submitted: css = "q-box q-error"; icon = "🔴 "; missing = True
            
        st.markdown(f"<div class='{css}'><div class='q-text'>{icon}{i+1}. {soru['text']}</div></div>", unsafe_allow_html=True)
        options_text = [opt['text'] for opt in soru['options']]
        choice = st.radio(f"Soru {i+1}", options_text, key=key, index=None, label_visibility="collapsed", horizontal=True)
        if choice:
            for opt in soru['options']:
                if opt['text'] == choice: total_score += opt['value']; break
        else: missing = True
    return total_score, missing

def calculate_cakra_results(answers):
    sonuclar = {}
    for cakra_adi, sorular in SORULAR_CAKRA.items():
        yavas_toplam = 0
        asiri_toplam = 0
        for i in range(16):
            key = f"cakra_{cakra_adi}_{i}"
            val = answers.get(key, 0)
            if i < 8: yavas_toplam += val
            else: asiri_toplam += val
        
        if yavas_toplam >= 30 and asiri_toplam < 30: durum = "Yavaş / Blokaj"
        elif asiri_toplam >= 30 and yavas_toplam < 30: durum = "Aşırı Aktif"
        elif yavas_toplam >= 30 and asiri_toplam >= 30: durum = "Dengesiz (Kaotik)"
        elif 20 <= yavas_toplam <= 25 and 20 <= asiri_toplam <= 25: durum = "Dengeli"
        else: durum = "Hafif Dengesiz"
        
        sonuclar[cakra_adi] = {"yavas_puan": yavas_toplam, "asiri_puan": asiri_toplam, "durum": durum}
    return sonuclar

def calculate_result_isi(score): return "SICAK" if score > 79 else ("MUTEDİL" if score > 70 else "SOĞUK")
def calculate_result_nem(score): return "KURU" if score > 69 else ("MUTEDİL" if score > 60 else "NEMLİ")

def genel_mizac_hesapla(cevaplar):
    skorlar = {}; yuzdeler = {}
    for bolum, veri in SORULAR_GENEL_DETAYLI.items():
        toplam = 0; max_puan = len(veri["sorular"]) * 3
        for i in range(len(veri["sorular"])):
            key = f"genel_{bolum}_{i}"
            secim = cevaplar.get(key)
            if secim: toplam += veri["puanlar"][secim]
        skorlar[bolum] = toplam
        yuzdeler[bolum] = (toplam / max_puan) * 100 if max_puan > 0 else 0
    isi = "SICAK" if yuzdeler["SICAKLIK"] >= yuzdeler["SOĞUKLUK"] else "SOĞUK"
    nem = "KURU" if yuzdeler["KURULUK"] >= yuzdeler["NEMLİLİK"] else "NEMLİ"
    mizac_adi = "Safravi" if "SICAK" in isi and "KURU" in nem else ("Demevi" if "NEMLİ" in nem else ("Balgami" if "SOĞUK" in isi and "NEMLİ" in nem else "Sovdavi"))
    return mizac_adi, skorlar, yuzdeler

def reset_app(): st.session_state.clear(); st.rerun()

# ==========================================
# 7. UYGULAMA AKIŞI
# ==========================================
init_state()

with st.sidebar:
    if os.path.exists(LOGO_LOCAL): st.image(LOGO_LOCAL, width=140)
    else: st.image(LOGO_URL, width=140)
    st.markdown("### Dr. Sait SEVİNÇ")
    if st.session_state.user_info: st.success(f"👤 {st.session_state.user_info.get('ad')}")
    if st.button("🏠 Ana Menü"): st.session_state.page = "Menu"; st.rerun()
    st.divider()
    chk = lambda x: "✅" if x else "⬜"
    st.markdown(f"{chk(st.session_state.results_genel)} Genel Mizaç")
    st.markdown(f"{chk(st.session_state.results_cakra)} Çakra Enerjisi")
    
    st.divider()
    
    # GEÇMİŞ KAYITLARI GÖRÜNTÜLEME
    if st.button("🗄️ Hasta Geçmişi"): st.session_state.page = "History"; st.rerun()

    if st.button("📄 Raporu Görüntüle", type="primary"): 
        if st.session_state.results_genel or st.session_state.results_cakra:
            st.session_state.page = "Rapor"; st.rerun()
        else:
            st.warning("Henüz hiç analiz yapmadınız.")

    if st.button("🔄 Sıfırla", type="secondary"): reset_app()

if st.session_state.page == "Giriş":
    st.markdown("<div style='text-align:center; padding: 20px;'><h1>Bütüncül Analiz Sistemi</h1></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.container(border=True):
            ad = st.text_input("Adınız Soyadınız")
            c1_ic, c2_ic = st.columns(2)
            with c1_ic: cinsiyet = st.selectbox("Cinsiyet", ["Kadın", "Erkek"])
            with c2_ic: yas = st.number_input("Yaşınız", 10, 100, 30)
            if st.button("Analize Başla 🚀", type="primary", use_container_width=True):
                if ad: st.session_state.user_info = {"ad": ad, "cinsiyet": cinsiyet, "yas": yas}; st.session_state.page = "Menu"; st.rerun()
                else: st.warning("İsim giriniz.")

elif st.session_state.page == "History":
    st.title("🗄️ Hasta Geçmişi")
    records = get_history()
    if records:
        for r in records:
            with st.expander(f"{r[2]} yaş | {r[1]} | {r[3]} ({r[4]})"):
                st.write(f"**Özet:** {r[5]}")
    else:
        st.info("Henüz kayıtlı analiz bulunmamaktadır.")
    if st.button("Geri Dön"): st.session_state.page = "Menu"; st.rerun()

elif st.session_state.page == "Menu":
    st.subheader(f"Hoşgeldiniz, {st.session_state.user_info['ad']}")
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    
    def create_card(col, title, icon, desc, key, target, done):
        css = "menu-card card-done" if done else "menu-card"
        badge = "<div class='status-badge'>✅ Tamamlandı</div>" if done else ""
        btn_txt = "Tekrarla" if done else "Başla"
        with col:
            st.markdown(f"""<div class="{css}">{badge}<span class="card-icon">{icon}</span><span class="card-title">{title}</span><span class="card-desc">{desc}</span></div>""", unsafe_allow_html=True)
            if st.button(btn_txt, key=key, use_container_width=True): st.session_state.page = target; st.rerun()

    create_card(c1, "Genel Mizaç", "🦁", "Baskın element tespiti.", "btn_gnl", "Test_Genel", st.session_state.results_genel)
    create_card(c2, "Sıcaklık / Soğukluk", "🔥", "Metabolizma ısısı.", "btn_isi", "Test_Isi", st.session_state.results_isi)
    create_card(c3, "Islaklık / Kuruluk", "💧", "Nem dengesi.", "btn_nem", "Test_Nem", st.session_state.results_nem)
    create_card(c4, "Çakra Enerjisi", "🌀", "Enerji merkezleri.", "btn_cakra", "Test_Cakra", st.session_state.results_cakra)

elif st.session_state.page == "Test_Cakra":
    st.title("🌀 Çakra Enerji Analizi")
    st.info("İfadeleri kendinize göre değerlendiriniz.")
    
    cevaplar_cakra = {}
    missing_count = 0
    labels = ["Hiç Katılmıyorum", "Nadiren", "Bazen", "Sıklıkla", "Tamamen Katılıyorum"]
    
    for cakra, sorular in SORULAR_CAKRA.items():
        st.markdown(f'<div class="section-header">{cakra}</div>', unsafe_allow_html=True)
        for i, soru in enumerate(sorular):
            key = f"cakra_{cakra}_{i}"
            val = st.session_state.get(key)
            css = "q-box q-filled" if val else ("q-box q-error" if st.session_state.submitted_cakra else "q-box q-default")
            icon = "🔴 " if (st.session_state.submitted_cakra and not val) else ""
            st.markdown(f"<div class='{css}'><div class='q-text'>{icon}{i+1}. {soru}</div></div>", unsafe_allow_html=True)
            choice = st.radio(f"{cakra}_{i}", labels, key=key, horizontal=True, index=None, label_visibility="collapsed")
            if choice: cevaplar_cakra[key] = labels.index(choice) + 1
            else: missing_count += 1

    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("Analizi Bitir ve Kaydet", type="primary", use_container_width=True):
            st.session_state.submitted_cakra = True
            if missing_count > 0:
                st.error("Lütfen tüm soruları cevaplayınız.")
                st.rerun()
            else:
                st.session_state.results_cakra = calculate_cakra_results(cevaplar_cakra)
                # VERİTABANI KAYDI
                analiz_ozeti = generate_deep_analysis(st.session_state.results_genel, st.session_state.results_cakra)
                save_to_db(st.session_state.user_info, "Çakra", analiz_ozeti, st.session_state.results_cakra)
                st.success("Çakra analizi tamamlandı ve veritabanına kaydedildi!")
                time.sleep(1)
                st.session_state.page = "Menu"
                st.rerun()
    with c2:
        if st.button("🏠 İptal / Menü", type="secondary", use_container_width=True):
            st.session_state.page = "Menu"; st.rerun()

elif st.session_state.page == "Test_Isi":
    st.title("🔥 Isı Analizi")
    score, missing = render_questions_with_validation(SORULAR_ISI, "isi", st.session_state.submitted_isi)
    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("Kaydet", type="primary", use_container_width=True): 
            st.session_state.submitted_isi = True; st.rerun()
        if st.session_state.submitted_isi and not missing:
            st.session_state.results_isi = calculate_result_isi(score)
            st.session_state.page = "Menu"; st.rerun()
    with c2:
        if st.button("🏠 Menü", type="secondary", use_container_width=True):
            st.session_state.page = "Menu"; st.rerun()

elif st.session_state.page == "Test_Nem":
    st.title("💧 Nem Analizi")
    score, missing = render_questions_with_validation(SORULAR_NEM, "nem", st.session_state.submitted_nem)
    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("Kaydet", type="primary", use_container_width=True): 
            st.session_state.submitted_nem = True; st.rerun()
        if st.session_state.submitted_nem and not missing:
            st.session_state.results_nem = calculate_result_nem(score)
            st.session_state.page = "Menu"; st.rerun()
    with c2:
        if st.button("🏠 Menü", type="secondary", use_container_width=True):
            st.session_state.page = "Menu"; st.rerun()

elif st.session_state.page == "Test_Genel":
    st.title("🦁 Genel Mizaç")
    cevaplar = {}
    for bolum, veri in SORULAR_GENEL_DETAYLI.items():
        st.markdown(f'<div class="section-header">{bolum}</div>', unsafe_allow_html=True)
        secenekler = list(veri["puanlar"].keys()); secenekler.sort(key=lambda x: veri["puanlar"][x])
        for i, soru in enumerate(veri["sorular"]):
            key = f"genel_{bolum}_{i}"
            st.markdown(f"<div class='q-box q-default'><div class='q-text'>{i+1}. {soru}</div></div>", unsafe_allow_html=True)
            choice = st.radio(key, secenekler, key=key, horizontal=True, label_visibility="collapsed")
            if choice: cevaplar[key] = choice

    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("Kaydet ve Bitir", type="primary", use_container_width=True):
            mizac, skorlar, yuzdeler = genel_mizac_hesapla(cevaplar)
            st.session_state.results_genel = mizac
            st.session_state.genel_yuzdeler = yuzdeler
            # VERİTABANI KAYDI
            analiz_ozeti = generate_deep_analysis(mizac, st.session_state.results_cakra)
            save_to_db(st.session_state.user_info, "Mizaç", analiz_ozeti, yuzdeler)
            st.session_state.page = "Menu"; st.rerun()
    with c2:
        if st.button("🏠 Menü", type="secondary", use_container_width=True):
            st.session_state.page = "Menu"; st.rerun()

elif st.session_state.page == "Rapor":
    tarih = datetime.now().strftime("%d.%m.%Y")
    st.markdown(f"## 📄 Analiz Sonuçları: {st.session_state.user_info.get('ad')}")
    
    # Derin Analiz Oluştur
    derin_analiz = generate_deep_analysis(st.session_state.results_genel, st.session_state.results_cakra)
    st.info(f"🧠 **Uzman Yorumu:** {derin_analiz}")

    # ÇAKRA GRAFİĞİ
    fig_cakra_html = ""
    if st.session_state.results_cakra:
        data = st.session_state.results_cakra
        cakra_names = list(data.keys())
        yavas_vals = [d['yavas_puan'] for d in data.values()]
        asiri_vals = [d['asiri_puan'] for d in data.values()]
        
        fig_cakra = go.Figure()
        fig_cakra.add_trace(go.Bar(x=cakra_names, y=yavas_vals, name='Blokaj/Yavaş', marker_color='#5DADE2', text=yavas_vals, textposition='auto'))
        fig_cakra.add_trace(go.Bar(x=cakra_names, y=asiri_vals, name='Aşırı Aktif', marker_color='#EC7063', text=asiri_vals, textposition='auto'))
        
        # YEŞİL BANT & EŞİK
        fig_cakra.add_shape(type="rect", x0=-0.5, x1=len(cakra_names)-0.5, y0=20, y1=25, fillcolor="Green", opacity=0.15, layer="below", line_width=0)
        fig_cakra.add_shape(type="line", x0=-0.5, x1=len(cakra_names)-0.5, y0=30, y1=30, line=dict(color="red", width=2, dash="dot"))
        
        fig_cakra.add_annotation(x=len(cakra_names)-1, y=22.5, text="DENGELİ (20-25)", showarrow=False, font=dict(size=10, color="green"), xanchor="right")
        fig_cakra.add_annotation(x=len(cakra_names)-1, y=31, text="KRİTİK (30+)", showarrow=False, font=dict(size=10, color="red"), xanchor="right")
        
        fig_cakra.update_layout(barmode='group', title="Çakra Enerji Dengesi Analizi", height=450, margin=dict(t=50, b=50, l=40, r=40), plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(showgrid=True, gridcolor='lightgray', range=[0, 45]))
        
        fig_cakra_html = fig_cakra.to_html(full_html=False, include_plotlyjs='cdn', config=PLOTLY_CONFIG)
        st.plotly_chart(fig_cakra, use_container_width=True, config=PLOTLY_CONFIG)
        
        df_cakra = pd.DataFrame.from_dict(data, orient='index')
        st.markdown("### Çakra Durum Tablosu")
        st.dataframe(df_cakra, use_container_width=True)

    # MİZAÇ GRAFİKLERİ
    fig1_html, fig2_html = "", ""
    if st.session_state.results_genel:
        yuzdeler = st.session_state.genel_yuzdeler
        ordered_cats = ["SOĞUKLUK", "NEMLİLİK", "SICAKLIK", "KURULUK"]
        ordered_vals = [yuzdeler.get(k, 0) for k in ordered_cats]
        
        fig1 = go.Figure(go.Bar(x=ordered_cats, y=ordered_vals, marker_color=['#3498DB', '#2ECC71', '#E74C3C', '#F1C40F']))
        fig1.update_layout(height=300, margin=dict(t=10, b=20, l=20, r=20))
        fig1_html = fig1.to_html(full_html=False, include_plotlyjs='cdn', config=PLOTLY_CONFIG)
        st.plotly_chart(fig1, use_container_width=True, config=PLOTLY_CONFIG)
        
        radar_cats = ordered_cats + [ordered_cats[0]]
        radar_vals = ordered_vals + [ordered_vals[0]]
        fig2 = go.Figure(go.Scatterpolar(r=radar_vals, theta=radar_cats, fill='toself', line=dict(color='#8E44AD', width=3)))
        fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=350, margin=dict(t=40, b=40, l=60, r=60))
        fig2_html = fig2.to_html(full_html=False, include_plotlyjs='cdn', config=PLOTLY_CONFIG)
        st.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)
        
        st.info(f"Baskın Mizaç: **{st.session_state.results_genel}**")
        
    # RAPOR İNDİRME
    if st.session_state.results_genel or st.session_state.results_cakra:
        detaylar = MIZAC_BILGILERI.get(st.session_state.results_genel, {}) if st.session_state.results_genel else {}
        mizac_adi = st.session_state.results_genel if st.session_state.results_genel else None
        
        report_html = create_html_report(st.session_state.user_info, mizac_adi, detaylar, tarih, fig1_html, fig2_html, fig_cakra_html, st.session_state.results_cakra, derin_analiz)
        st.download_button("📥 Raporu İndir", data=report_html, file_name="Analiz.html", mime="text/html", type="primary", use_container_width=True)
    
    if st.button("Menüye Dön"): st.session_state.page = "Menu"; st.rerun()
