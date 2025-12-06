import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
from datetime import datetime, date
import time
import os
import json
import base64
import io

# ==========================================
# 1. AYARLAR VE STİL YAPILANDIRMASI
# ==========================================
st.set_page_config(page_title="Dr. Sait SEVİNÇ - Pro Asistan", layout="wide", page_icon="🧬")

# Grafik Ayarları
PLOTLY_CONFIG = {
    'staticPlot': True,
    'displayModeBar': False,
    'showTips': False
}

# --- CSS: PRO TASARIM VE TAM GİZLEME ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }

    /* --- TAM GİZLEME KOMUTLARI (Manage App Dahil) --- */
    
    /* 1. Üstteki renkli şerit ve hamburger menü */
    header[data-testid="stHeader"] {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* 2. Sağ üstteki ayarlar (Toolbar) */
    .stAppToolbar {
        display: none !important;
    }

    /* 3. En alttaki 'Made with Streamlit' ve 'Manage app' alanları */
    footer {
        display: none !important;
        visibility: hidden !important;
    }
    
    /* 4. Ekstra Deploy butonları */
    .stDeployButton {
        display: none !important;
    }
    
    /* 5. Görüntüleyici Rozetleri (Viewer Badge) */
    div[data-testid="stStatusWidget"] {
        display: none !important;
    }
    
    /* Ana içerik padding ayarı (Üst boşluğu almak için) */
    .main .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }
    
    /* MENU KARTLARI */
    .menu-card {
        background: linear-gradient(145deg, #ffffff, #f0f2f5);
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        text-align: center; border: 1px solid rgba(255,255,255,0.8);
        height: 200px; display: flex; flex-direction: column;
        justify-content: center; align-items: center;
        transition: all 0.3s ease; position: relative; cursor: pointer;
    }
    .menu-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(52, 152, 219, 0.2); border-color: #3498db; }
    
    .card-done { 
        border: 2px solid #2ecc71 !important; 
        background: linear-gradient(145deg, #f0fff4, #ffffff) !important;
    }
    
    .status-badge { 
        background-color: #2ecc71; color: white; 
        padding: 4px 12px; border-radius: 12px; 
        font-size: 0.8rem; font-weight: bold; margin-bottom: 10px; 
        box-shadow: 0 2px 5px rgba(46,204,113,0.3);
    }
    
    .card-icon { font-size: 40px; margin-bottom: 10px; }
    .card-title { font-size: 1.1rem; font-weight: 700; color: #2c3e50; margin-bottom: 5px; }
    .card-desc { font-size: 0.9rem; color: #7f8c8d; }

    /* SORU KUTULARI */
    .q-box { 
        padding: 15px 20px;
        border-radius: 12px; 
        margin-bottom: 12px; 
        transition: all 0.3s ease;
    }
    
    .q-default { background: #f8fbfe; border: 1px solid #dceefb; border-left: 5px solid #bdc3c7; }
    
    .q-filled { 
        background: #ffffff; 
        border: 1px solid #e0ffe8; border-left: 5px solid #2ecc71; 
        box-shadow: 0 2px 8px rgba(46,204,113,0.1);
    }
    
    .q-error { 
        background: #fff5f5; 
        border: 1px solid #ffcccc; border-left: 5px solid #e74c3c; 
        animation: shake 0.4s;
        box-shadow: 0 2px 8px rgba(231, 76, 60, 0.15);
    }
    
    .q-text { font-size: 1.05rem; font-weight: 500; color: #34495e; margin-bottom: 8px; }
    .section-header { font-size: 1.3rem; font-weight: 700; color: #2c3e50; margin-top: 25px; margin-bottom: 15px; border-bottom: 2px solid #ecf0f1; padding-bottom: 5px; }

    /* WIDGET AYARLARI */
    .stRadio > div { gap: 0px !important; margin-top: -10px; padding-left: 10px; }
    .stButton button { border-radius: 10px; font-weight: 600; transition: 0.3s; width: 100%; height: 50px; }
    
    @keyframes shake {
      0% { transform: translateX(0); } 25% { transform: translateX(-5px); } 
      50% { transform: translateX(5px); } 75% { transform: translateX(-5px); } 
      100% { transform: translateX(0); }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. VERİTABANI VE KAYNAKLAR
# ==========================================
def init_db():
    conn = sqlite3.connect('analiz_gecmisi.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sonuclar
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ad TEXT, yas INTEGER, cinsiyet TEXT, tarih TEXT, 
                  tip TEXT, ozet TEXT, detail_json TEXT)''')
    conn.commit()
    return conn

CONN = init_db()

@st.cache_data
def load_resources():
    logo_path = "drsaitlogo.jpeg"
    default_logo = "https://i.ibb.co/xJc52gL/image-0.png"
    
    mizac_bilgileri = {
        "Safravi": {"Genel": "Sıcak-Kuru mizaç. Ateş elementi.", "Beslenme": "Serinletici gıdalar (Salatalık, marul, yoğurt).", "Riskler": ["Migren", "Safra Taşları", "Uykusuzluk", "Öfke Kontrolü"]},
        "Demevi": {"Genel": "Sıcak-Nemli mizaç. Hava elementi.", "Beslenme": "Az ve sık yiyin. Kırmızı eti azaltın, yeşillik artırın.", "Riskler": ["Yüksek Tansiyon", "Kalp Rahatsızlıkları", "Cilt Sorunları"]},
        "Balgami": {"Genel": "Soğuk-Nemli mizaç. Su elementi.", "Beslenme": "Isıtıcı baharatlar (Zencefil, kekik) tüketin.", "Riskler": ["Obezite", "Romatizma", "Unutkanlık", "Ödem"]},
        "Sovdavi": {"Genel": "Soğuk-Kuru mizaç. Toprak elementi.", "Beslenme": "Nemlendirici ve sıcak gıdalar. Kuru bakliyatı azaltın.", "Riskler": ["Depresyon", "Varis", "Kabızlık", "Kuruntu"]}
    }
    return logo_path, default_logo, mizac_bilgileri

LOGO_LOCAL, LOGO_URL, MIZAC_BILGILERI = load_resources()

def calculate_age(birth_date):
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

# ==========================================
# 3. AKILLI DERİN ANALİZ MOTORU
# ==========================================
def generate_deep_analysis(mizac, cakra_sonuclar, skorlar_isi, skorlar_nem):
    yorumlar = []
    
    # Güvenli Veri Kontrolü
    has_isi = skorlar_isi is not None
    has_nem = skorlar_nem is not None
    has_mizac = mizac is not None
    has_cakra = cakra_sonuclar is not None

    # 1. Isı Dengesi Yorumları
    if has_isi:
        if skorlar_isi > 80: 
            yorumlar.append("🔥 **Metabolik Ateş Yüksek:** Vücut ısınızın yüksekliği inflamasyona zemin hazırlayabilir.")
        elif skorlar_isi < 40:
            yorumlar.append("❄️ **Metabolik Durgunluk:** Enerji üretiminiz düşük, kan dolaşımını hızlandırıcı aktivitelere ihtiyacınız var.")

    # 2. Nem Dengesi Yorumları
    if has_nem:
        if skorlar_nem > 70: 
            yorumlar.append("💧 **Nem Fazlalığı:** Vücutta ödem ve ağırlık birikimi olabilir. Lenfatik drenaj önerilir.")
        elif skorlar_nem < 40: 
            yorumlar.append("🌵 **Kuruluk Hakim:** Cilt ve mukoza kuruluğu artabilir, hidrasyona dikkat ediniz.")

    # 3. Mizaç Yorumu
    if has_mizac:
        if mizac == "Safravi": yorumlar.append("🦁 **Safravi Mizaç:** Lider ruhlu, hızlı karar alan yapı. Karaciğer detoksu şart.")
        elif mizac == "Demevi": yorumlar.append("🌬️ **Demevi Mizaç:** Sosyal, neşeli fakat kan basıncı dalgalanmalarına açık.")
        elif mizac == "Balgami": yorumlar.append("🌊 **Balgami Mizaç:** Sakin, uyumlu fakat harekete geçmekte zorlanan yapı. Metabolizmayı hızlandırmalısınız.")
        elif mizac == "Sovdavi": yorumlar.append("🦅 **Sovdavi Mizaç:** Derin düşünen, hassas yapı. Bağırsak florasını (İkinci beyin) korumalısınız.")

    # 4. Çakra ve Kombinasyon Yorumları
    if has_cakra:
        kok = cakra_sonuclar.get("KÖK ÇAKRA (Muladhara)", {}).get("durum")
        solar = cakra_sonuclar.get("SOLAR PLEXUS (Manipura)", {}).get("durum")
        
        # Sadece Çakra
        if kok and "Yavaş" in kok:
            yorumlar.append("⚠️ **Kök Çakra Blokajı:** Aidiyet ve güven hissinde eksiklik yaşanabilir.")
            
        # Çapraz Analiz (Mizaç + Çakra)
        if has_mizac and mizac == "Sovdavi" and kok and "Yavaş" in kok:
            yorumlar.append("⚠️ **Kritik Kombinasyon:** Toprak mizacı + Kök blokajı = Aşırı kaygı ve güvensizlik yaratabilir.")
        if has_mizac and mizac == "Safravi" and solar and "Aşırı" in solar:
            yorumlar.append("⚠️ **Kritik Kombinasyon:** Safravi mizaç + Aşırı Solar Plexus = Öfke patlamaları ve mide sorunları.")
            
    if not yorumlar: 
        yorumlar.append("✅ Analiz için veri girişi bekleniyor.")
    
    return " ".join(yorumlar)

def save_to_db(user_info, test_type, summary_text, detail_data):
    try:
        c = CONN.cursor()
        tarih = datetime.now().strftime("%d.%m.%Y %H:%M")
        detail_json = json.dumps(detail_data, ensure_ascii=False)
        c.execute("INSERT INTO sonuclar (ad, yas, cinsiyet, tarih, tip, ozet, detail_json) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (user_info['ad'], user_info['yas'], user_info['cinsiyet'], tarih, test_type, summary_text, detail_json))
        CONN.commit()
        st.toast(f"✅ {test_type} Sonucu Veritabanına İşlendi!", icon="💾")
    except Exception as e:
        st.error(f"Kayıt Hatası: {e}")

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# ==========================================
# 4. TEST VERİLERİ (SABİT)
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
    "SICAKLIK": {"puanlar": {"Hayır": 1, "Orta derece": 2, "Kesinlikle evet": 3}, "sorular": ["Arkadaş çevrem geniş sosyal biriyim", "Hızlı düşünür çabuk harekete geçerim", "Konuşkan sıcakkanlı bir yapım var", "Soğuk havaları severim", "Soğuk yiyecek içeceklerden hoşlanırım", "Vücudum sıcaktır", "Takıntılı değilim", "Cesur ve atak biriyim", "Çok detaylı düşünmem", "Kabızlık sorunu çok fazla yaşamam", "Rutin / tekdüze sakin yaşamdan pek sevmem", "Pozitifim", "Kuralları çok sevmem", "Sonuç odaklıyım", "Lider bir ruhum var", "Genelde enerjik bir yapım var", "Yapılanı unuturum kin tutamam", "Sır saklamakta zorlanırım anlatma eğilimim vardır"]},
    "SOĞUKLUK": {"puanlar": {"Hayır": 1, "Orta derece": 2, "Kesinlikle evet": 3}, "sorular": ["Çok geniş bir çevrem yok", "Temkinli biriyim", "Hemen samimi olmam, seçiciyim", "Sıcak havaları severim", "Sıcak yiyecek ve içeceklerden hoşlanırım", "Vücudum soğuktur üşürüm", "Takıntılıyım", "Hassas ve alıngan biriyim", "Aceleyi sevmem işimi sağlam yavaş yavaş yaparım", "Kabızlık sorunu çok yaşarım", "Sakin yaşam severim", "Karamsarım", "Kurallara uyarım", "Süreç odaklıyım", "İyi bir takım oyuncusuyum", "Genelde enerjim düşüktür (çabuk yorulurum)", "Negatifi unutmam", "Sır saklarım"]},
    "KURULUK": {"puanlar": {"Hayır": 0, "Orta derece": 2, "Kesinlikle evet": 3}, "sorular": ["Saçlarım kalın telli", "Zayıf ince yapılıyım", "Cildim genelde kuru", "Cilt lekelerim vardır lekelenmeye müsaittir", "Çok uyuyamam derin değildir uyanırım hemen", "Sıkı ve gergin bir cildim var", "Göz yapım küçüktür", "Belim nispeten incedir", "Hafızam kuvvetlidir", "Duyularım gelişmiştir duyma/ koku alma", "Esnek biri değilim uyum sağlamam zordur", "Eklemlerim çıkıntılı", "Tenim daha sarı ve koyu renkte", "Tırnaklarım serttir", "Çabuk pes etmem ısrarcıyım", "Genelde burun akıntım çok az olur", "Kaşıntı egzemaya yatkınlığım fazladır", "Ağız kuruluğum fazladır"]},
    "NEMLİLİK": {"puanlar": {"Hayır": 0, "Orta derece": 1, "Kesinlikle evet": 2}, "sorular": ["Saçlarım ince telli", "Kiloluyum", "Cildim yumuşaktır", "Uykuyu severim derin uyurum", "Çok az cilt lekelerim var", "Cildim yumuşak ve esnektir", "Göz yapım iri ve nemlidir", "Belim nispeten kalındır", "Hafızam kuvvetli değil tekrarlamazsam çabuk unuturum", "Duyularım zayıftır koku alma/işitme", "Esnek biriyim uyum sağlarım", "Eklemlerim, hatlarım belirgin değildir", "Yuvarlak yüzlüyüm", "Tırnak yapım yumuşaktır", "Çabuk pes ederim bıkarım", "Burun akıntım olur", "Egzema ve kaşıntı çok nadir görülür", "Ağız kuruluğum yoktur sulu ve yoğun olabilir"]}
}

SORULAR_CAKRA = {
    "KÖK ÇAKRA (Muladhara)": ["Kendimi güvensiz hissediyorum", "Değersiz hissediyorum", "Temel ihtiyaçlarımı karşılamakta zorlanıyorum", "Para konularında tedirginim", "Fiziksel olarak zayıfım", "Aidiyet hissim zayıf", "Odaklanamıyorum", "Bağımlı ilişkiler kuruyorum", "Maddi güvence takıntım var", "İnatçıyım", "Güvenemem", "Maneviyatım zayıf", "Bırakamıyorum", "Öfkeliyim", "Baskıcıyım", "Güç tutkum var"],
    "SAKRAL ÇAKRA (Svadhisthana)": ["Duygularımı içime atarım", "Cinselliğe isteksizim", "Hayattan keyif alamıyorum", "Yaratıcılığım tıkalı", "Tatmin olamıyorum", "Yalnızlığı seçerim", "Geçmiş yaralarım var", "Bedenime yabancıyım", "Sürekli haz peşindeyim", "Bağımlılıklara eğilimliyim", "Duygularım dalgalı", "Alışveriş bağımlısıyım", "Sınır koyamam", "Aşırı hassasım", "Abartıya kaçarım", "Pişmanlık duyarım"],
    "SOLAR PLEXUS (Manipura)": ["Onay beklerim", "Hayır diyemem", "Çekingenim", "Yetersiz hissederim", "Motivasyonum düşük", "Eleştiriye kırılırım", "Özgüvenim eksik", "Harekete geçemem", "Kontrol delisiyim", "Manipülatifim", "Müdahaleciyim", "Rekabetçiyim", "Dikkat çekmek isterim", "Bencillik yapabilirim", "Öfke patlamaları yaşarım", "Başarıya bağımlıyım"],
    "KALP ÇAKRASI (Anahata)": ["Sevgimi gösteremem", "Affedemem", "Güvenemem", "Kendimi sevmem", "İlişkilerden kaçarım", "Kalbimi kapatırım", "Geçmiş acıları tutarım", "Paylaşamam", "Kendimi feda ederim", "Sınırlarımı kaybederim", "Onay bağımlısıyım", "Tükenmiş hissederim", "Hayır diyemem", "Başkalarının duygularıyla boğulurum", "Aşırı vericiyim", "Kendi ihtiyaçlarımı yok sayarım"],
    "BOĞAZ ÇAKRASI (Vishuddha)": ["Kendimi ifade edemem", "Toplulukta konuşamam", "Sesim kısılır", "Yanlış anlaşılırım", "Düşüncelerimi toparlayamam", "Kendimi ifade etme hakkım yok gibi", "Sessiz kalırım", "Dinlemem sadece konuşurum", "Düşüncelerimi dayatırım", "Çok detaylı konuşurum", "Söz keserim", "Eleştiriye gelemem", "Kırıcı konuşurum", "Sesimi yükseltirim", "Başkalarını sustururum"],
    "GÖZ ÇAKRASI (Ajna)": ["İçgüdüme güvenmem", "Vizyonum yok", "Zihnim bulanık", "Meditasyon yapamam", "Sezgilerimi yok sayarım", "Mantık-sezgi çatışması yaşarım", "Hayal kuramam", "Umutsuzum", "Sürekli hayal dünyasındayım", "Kuruntuluyum", "Sembollere takıntılıyım", "Gerçeklikten kaçarım", "Başkalarının düşüncelerini okuduğumu sanırım", "Zihnim susmaz", "Eyleme geçemem", "Takıntılı düşüncelerim var"],
    "TAÇ ÇAKRASI (Sahasrara)": ["Bütünden kopuk hissederim", "Maneviyata uzağım", "Amaçsızım", "Gelişime kapalıyım", "Huzursuzum", "Sessizlikten kaçarım", "Boşluktayım", "İnançsızım", "Gerçeklikten kopuğum", "Dünyadan uzaklaştım", "Fanatikleşebilirim", "Bedenimi ihmal ederim", "Kendimi üstün görürüm", "Sorumluluktan kaçarım", "Spiritüel egom var", "Manevi bağımlılığım var"]
}

# ==========================================
# 5. UYGULAMA MANTIĞI VE NAVİGASYON
# ==========================================
def init_state():
    if "user_info" not in st.session_state:
        st.session_state.update({
            "page": "Giriş", "user_info": {}, 
            "results_isi": None, "results_nem": None, "results_genel": None, "results_cakra": None,
            "genel_skorlar": {}, "genel_yuzdeler": {}, "scores": {"isi": None, "nem": None},
            "submitted_genel": False, "submitted_isi": False, "submitted_nem": False, "submitted_cakra": False
        })
    if "page" not in st.session_state:
        st.session_state.page = "Giriş"

# --- SORU RENDER MOTORU ---
def render_questions_pro(soru_listesi, key_prefix, submitted):
    total_score = 0
    missing_count = 0
    
    for i, soru in enumerate(soru_listesi):
        key = f"{key_prefix}_{i}"
        val = st.session_state.get(key)
        
        box_class = "q-default"
        if val is not None: 
            box_class = "q-filled"
        elif submitted: 
            box_class = "q-error"
        
        st.markdown(f"""<div class='q-box {box_class}'><div class='q-text'>{i+1}. {soru['text']}</div></div>""", unsafe_allow_html=True)
        
        options_map = {opt['text']: opt['value'] for opt in soru['options']}
        
        choice = st.radio(
            f"{key}_radio", 
            options=list(options_map.keys()), 
            key=key, 
            index=None, 
            label_visibility="collapsed",
            horizontal=True
        )
        
        if choice: total_score += options_map[choice]
        else: missing_count += 1
            
    return total_score, missing_count

# --- HTML RAPOR ---
def create_html_report(user_info, mizac, detaylar, tarih, fig1_html, fig2_html, fig_cakra_html, cakra_sonuclar, derin_analiz):
    img_data = get_image_base64(LOGO_LOCAL)
    img_src = f"data:image/jpeg;base64,{img_data}" if img_data else LOGO_URL
    
    mizac_display = mizac if mizac else "Belirlenmedi"
    detaylar = detaylar if detaylar else {}
    
    risk_html = ""
    if "Riskler" in detaylar:
        for r in detaylar["Riskler"]: risk_html += f"<li>{r}</li>"

    cakra_rows = ""
    if cakra_sonuclar:
        for cakra, degerler in cakra_sonuclar.items():
            durum = degerler['durum']
            color = "#2ecc71" if "Dengeli" in durum else ("#f39c12" if "Hafif" in durum else "#e74c3c")
            cakra_rows += f"<tr><td data-label='Çakra'><strong>{cakra}</strong></td><td data-label='Yavaş'>{degerler['yavas_puan']}</td><td data-label='Aşırı'>{degerler['asiri_puan']}</td><td data-label='Durum' style='color:{color}'><strong>{durum}</strong></td></tr>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Analiz Raporu</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: 'Helvetica', sans-serif; padding: 20px; max-width: 800px; margin: auto; background: #fff; }}
            .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 20px; }}
            .logo {{ height: 80px; }}
            .box {{ border: 1px solid #eee; padding: 15px; border-radius: 8px; margin-bottom: 20px; background: #fdfdfd; page-break-inside: avoid; }}
            .alert {{ background: #e8f4f8; border-left: 5px solid #3498db; padding: 15px; margin: 20px 0; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ padding: 8px; border-bottom: 1px solid #eee; text-align: center; font-size: 0.9em; }}
            td:first-child {{ text-align: left; }}
        </style>
    </head>
    <body>
        <div class="header">
            <img src="{img_src}" class="logo">
            <h2>BÜTÜNCÜL SAĞLIK RAPORU</h2>
            <p><strong>{user_info.get('ad')}</strong> | {user_info.get('yas')} Yaş | {tarih}</p>
        </div>
        
        <div class="alert">
            <h3>🧠 Uzman Yorumu & Derin Analiz</h3>
            <p>{derin_analiz}</p>
        </div>

        {'<div class="box"><h3>🦁 Mizaç: ' + mizac_display + '</h3>' + fig1_html + fig2_html + '<p><strong>Genel:</strong> ' + detaylar.get('Genel','-') + '</p><p><strong>Beslenme:</strong> ' + detaylar.get('Beslenme','-') + '</p><ul>' + risk_html + '</ul></div>' if mizac else ''}
        
        {'<div class="box"><h3>🌀 Çakra Enerji Durumu</h3>' + fig_cakra_html + '<table><thead><tr><th>Çakra</th><th>Yavaş</th><th>Aşırı</th><th>Durum</th></tr></thead><tbody>' + cakra_rows + '</tbody></table></div>' if cakra_sonuclar else ''}
        
        <div style="text-align:center; font-size:0.8em; color:#999; margin-top:30px;">Dr. Sait SEVİNÇ Analiz Sistemi</div>
    </body>
    </html>
    """
    return html

# ==========================================
# 6. HESAPLAMA MANTIKLARI
# ==========================================
def calculate_result_isi(score): return "SICAK" if score > 79 else ("MUTEDİL" if score > 70 else "SOĞUK")
def calculate_result_nem(score): return "KURU" if score > 69 else ("MUTEDİL" if score > 60 else "NEMLİ")

def genel_mizac_hesapla(cevaplar):
    skorlar = {}; yuzdeler = {}
    for bolum, veri in SORULAR_GENEL_DETAYLI.items():
        toplam = 0; max_puan = len(veri["sorular"]) * 3
        for i in range(len(veri["sorular"])):
            key = f"genel_{bolum}_{i}"
            val_text = cevaplar.get(key)
            if val_text: toplam += veri["puanlar"][val_text]
        skorlar[bolum] = toplam
        yuzdeler[bolum] = (toplam / max_puan) * 100 if max_puan > 0 else 0
    
    isi = "SICAK" if yuzdeler["SICAKLIK"] >= yuzdeler["SOĞUKLUK"] else "SOĞUK"
    nem = "KURU" if yuzdeler["KURULUK"] >= yuzdeler["NEMLİLİK"] else "NEMLİ"
    
    mizac_adi = "Mutedil"
    if "SICAK" in isi and "KURU" in nem: mizac_adi = "Safravi"
    elif "SICAK" in isi and "NEMLİ" in nem: mizac_adi = "Demevi"
    elif "SOĞUK" in isi and "NEMLİ" in nem: mizac_adi = "Balgami"
    elif "SOĞUK" in isi and "KURU" in nem: mizac_adi = "Sovdavi"
    
    return mizac_adi, skorlar, yuzdeler

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

def reset_app(): 
    st.session_state.clear()
    st.rerun()

# ==========================================
# 7. UYGULAMA AKIŞI (MAIN)
# ==========================================
init_state()

with st.sidebar:
    if os.path.exists(LOGO_LOCAL): st.image(LOGO_LOCAL, width=140)
    else: st.image(LOGO_URL, width=140)
    st.markdown("### Dr. Sait SEVİNÇ")
    
    if st.session_state.user_info: 
        st.success(f"👤 {st.session_state.user_info.get('ad')}")
    
    if st.button("🏠 Ana Menü"): 
        st.session_state.page = "Menu"
        st.rerun()
        
    st.divider()
    
    chk = lambda x: "✅" if x else "⬜"
    st.caption("Tamamlanan Analizler")
    st.markdown(f"{chk(st.session_state.results_genel)} Genel Mizaç")
    st.markdown(f"{chk(st.session_state.results_isi)} Isı Dengesi")
    st.markdown(f"{chk(st.session_state.results_nem)} Nem Dengesi")
    st.markdown(f"{chk(st.session_state.results_cakra)} Çakra Enerjisi")
    
    st.divider()
    if st.button("🗄️ Hasta Geçmişi"): 
        st.session_state.page = "History"
        st.rerun()
    
    any_result = any([st.session_state.results_genel, st.session_state.results_isi, st.session_state.results_nem, st.session_state.results_cakra])
    
    if st.button("📄 Sonuç Raporu", type="primary", disabled=not any_result):
        if any_result:
            st.session_state.page = "Rapor"
            st.rerun()
        else: st.warning("En az bir test tamamlanmalı.")
        
    if st.button("🔄 Oturumu Sıfırla", type="secondary"): 
        reset_app()

# --- SAYFALAR ---
if st.session_state.page == "Giriş":
    st.markdown("<div style='text-align:center; padding: 20px;'><h1>Bütüncül Analiz Sistemi</h1></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.container(border=True):
            st.markdown("### Hasta Bilgileri")
            ad = st.text_input("Ad Soyad")
            c1_ic, c2_ic = st.columns(2)
            with c1_ic: cinsiyet = st.selectbox("Cinsiyet", ["Kadın", "Erkek"])
            with c2_ic: 
                dogum_tarihi = st.date_input("Doğum Tarihi", min_value=date(1940, 1, 1), max_value=date.today(), format="DD/MM/YYYY")
            
            yas = calculate_age(dogum_tarihi)
            
            if st.button("Analize Başla 🚀", type="primary", use_container_width=True):
                if ad: 
                    st.session_state.user_info = {"ad": ad, "cinsiyet": cinsiyet, "yas": yas}
                    st.session_state.page = "Menu"
                    st.rerun()
                else: st.warning("Lütfen isim giriniz.")

elif st.session_state.page == "History":
    st.title("🗄️ Hasta Kayıtları")
    c = CONN.cursor()
    c.execute("SELECT * FROM sonuclar ORDER BY id DESC")
    data = c.fetchall()
    
    if data:
        df = pd.DataFrame(data, columns=["ID", "Ad", "Yaş", "Cinsiyet", "Tarih", "Tip", "Özet", "JSON"])
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df.drop(columns=["JSON"]).to_excel(writer, index=False, sheet_name='Hastalar')
        
        st.download_button(
            label="📥 Listeyi Excel Olarak İndir (.xlsx)",
            data=buffer,
            file_name="Hasta_Kayitlari.xlsx",
            mime="application/vnd.ms-excel",
            type="primary"
        )
        st.dataframe(df.drop(columns=["JSON"]), use_container_width=True)
    else:
        st.info("Henüz kayıt bulunmamaktadır.")
    
    if st.button("Geri"): 
        st.session_state.page = "Menu"
        st.rerun()

elif st.session_state.page == "Menu":
    if not st.session_state.user_info:
        st.session_state.page = "Giriş"
        st.rerun()

    st.subheader(f"Hoşgeldiniz, {st.session_state.user_info['ad']} (Yaş: {st.session_state.user_info['yas']})")
    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    
    def create_card(col, title, icon, desc, key, target, done):
        css = "menu-card card-done" if done else "menu-card"
        badge = "<div class='status-badge'>✅ Tamamlandı</div>" if done else ""
        btn_txt = "Sonuçları Gör" if done else "Başla"
        with col:
            st.markdown(f"""<div class="{css}">{badge}<span class="card-icon">{icon}</span><span class="card-title">{title}</span><span class="card-desc">{desc}</span></div>""", unsafe_allow_html=True)
            if st.button(btn_txt, key=key, use_container_width=True): 
                st.session_state.page = target
                st.rerun()

    create_card(c1, "Genel Mizaç", "🦁", "Baskın element tespiti.", "btn_gnl", "Test_Genel", st.session_state.results_genel)
    create_card(c2, "Sıcaklık / Soğukluk", "🔥", "Metabolizma ısısı.", "btn_isi", "Test_Isi", st.session_state.results_isi)
    create_card(c3, "Islaklık / Kuruluk", "💧", "Nem dengesi.", "btn_nem", "Test_Nem", st.session_state.results_nem)
    create_card(c4, "Çakra Enerjisi", "🌀", "Enerji merkezleri.", "btn_cakra", "Test_Cakra", st.session_state.results_cakra)

elif st.session_state.page == "Test_Isi":
    st.title("🔥 Isı Analizi (20 Soru)")
    
    score, missing_count = render_questions_pro(SORULAR_ISI, "isi", st.session_state.submitted_isi)
    
    if st.session_state.submitted_isi and missing_count > 0:
        st.error(f"⚠️ Toplam {missing_count} adet soru boş bırakıldı. Lütfen kırmızı ile işaretlenen alanları doldurunuz.")

    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("Kaydet", type="primary"):
            st.session_state.submitted_isi = True
            if missing_count == 0:
                st.session_state.results_isi = calculate_result_isi(score)
                st.session_state.scores["isi"] = score
                
                analiz_ozeti = generate_deep_analysis(None, None, score, None)
                save_to_db(st.session_state.user_info, "Isı Dengesi", analiz_ozeti, {"Puan": score, "Sonuç": st.session_state.results_isi})
                
                time.sleep(1)
                st.session_state.page = "Menu"
                st.rerun()
            else: st.rerun()
    with c2:
        if st.button("İptal"): 
            st.session_state.page = "Menu"
            st.rerun()

elif st.session_state.page == "Test_Nem":
    st.title("💧 Nem Analizi (20 Soru)")
    
    score, missing_count = render_questions_pro(SORULAR_NEM, "nem", st.session_state.submitted_nem)
    
    if st.session_state.submitted_nem and missing_count > 0:
        st.error(f"⚠️ Toplam {missing_count} adet soru boş bırakıldı. Lütfen kırmızı ile işaretlenen alanları doldurunuz.")
        
    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("Kaydet", type="primary"):
            st.session_state.submitted_nem = True
            if missing_count == 0:
                st.session_state.results_nem = calculate_result_nem(score)
                st.session_state.scores["nem"] = score
                
                analiz_ozeti = generate_deep_analysis(None, None, None, score)
                save_to_db(st.session_state.user_info, "Nem Dengesi", analiz_ozeti, {"Puan": score, "Sonuç": st.session_state.results_nem})
                
                time.sleep(1)
                st.session_state.page = "Menu"
                st.rerun()
            else: st.rerun()
    with c2:
        if st.button("İptal"): 
            st.session_state.page = "Menu"
            st.rerun()

elif st.session_state.page == "Test_Genel":
    st.title("🦁 Genel Mizaç Testi")
    cevaplar = {}
    missing_count = 0
    
    for bolum, veri in SORULAR_GENEL_DETAYLI.items():
        st.markdown(f'<div class="section-header">{bolum}</div>', unsafe_allow_html=True)
        secenekler = list(veri["puanlar"].keys()); secenekler.sort(key=lambda x: veri["puanlar"][x])
        
        for i, soru in enumerate(veri["sorular"]):
            key = f"genel_{bolum}_{i}"
            val = st.session_state.get(key)
            
            box_class = "q-filled" if val else ("q-error" if st.session_state.submitted_genel else "q-default")
            st.markdown(f"""<div class='q-box {box_class}'><div class='q-text'>{i+1}. {soru}</div></div>""", unsafe_allow_html=True)
            
            choice = st.radio(f"{key}_rd", secenekler, key=key, index=None, label_visibility="collapsed", horizontal=True)
            
            if choice: cevaplar[key] = choice
            else: missing_count += 1
            
    if st.session_state.submitted_genel and missing_count > 0:
        st.error(f"⚠️ Toplam {missing_count} adet soru boş bırakıldı. Lütfen kırmızı ile işaretlenen alanları doldurunuz.")

    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("Analizi Bitir", type="primary"):
            st.session_state.submitted_genel = True
            if missing_count == 0:
                mizac, skorlar, yuzdeler = genel_mizac_hesapla(cevaplar)
                st.session_state.results_genel = mizac
                st.session_state.genel_yuzdeler = yuzdeler
                st.session_state.genel_skorlar = skorlar
                
                analiz_ozeti = generate_deep_analysis(mizac, None, None, None)
                save_to_db(st.session_state.user_info, "Mizaç", analiz_ozeti, yuzdeler)
                
                time.sleep(1)
                st.session_state.page = "Menu"
                st.rerun()
            else: st.rerun()
    with c2:
        if st.button("İptal"): 
            st.session_state.page = "Menu"
            st.rerun()

elif st.session_state.page == "Test_Cakra":
    st.title("🌀 Çakra Enerji Analizi")
    st.info("Lütfen aşağıdaki durumları 1 (Hiç) ile 5 (Tamamen) arasında değerlendirin.")
    
    cevaplar_cakra = {}
    missing_count = 0
    labels = ["1-Hiç Katılmıyorum", "2-Nadiren", "3-Bazen", "4-Sıklıkla", "5-Tamamen Katılıyorum"]
    
    for cakra, sorular in SORULAR_CAKRA.items():
        st.markdown(f'<div class="section-header">{cakra}</div>', unsafe_allow_html=True)
        for i, soru in enumerate(sorular):
            key = f"cakra_{cakra}_{i}"
            val = st.session_state.get(key)
            
            box_class = "q-filled" if val else ("q-error" if st.session_state.submitted_cakra else "q-default")
            st.markdown(f"<div class='q-box {box_class}'><div class='q-text'>{i+1}. {soru}</div></div>", unsafe_allow_html=True)
            
            choice = st.radio(f"{key}_rd", labels, key=key, index=None, horizontal=True, label_visibility="collapsed")
            
            if choice: cevaplar_cakra[key] = labels.index(choice) + 1
            else: missing_count += 1
            
    if st.session_state.submitted_cakra and missing_count > 0:
        st.error(f"⚠️ Toplam {missing_count} adet soru boş bırakıldı. Lütfen kırmızı ile işaretlenen alanları doldurunuz.")

    c1, c2 = st.columns([3, 1])
    with c1:
        if st.button("Analizi Bitir", type="primary"):
            st.session_state.submitted_cakra = True
            if missing_count == 0:
                st.session_state.results_cakra = calculate_cakra_results(cevaplar_cakra)
                
                analiz_ozeti = generate_deep_analysis(st.session_state.results_genel, st.session_state.results_cakra, st.session_state.scores.get("isi"), st.session_state.scores.get("nem"))
                save_to_db(st.session_state.user_info, "Çakra", analiz_ozeti, st.session_state.results_cakra)
                
                time.sleep(1)
                st.session_state.page = "Menu"
                st.rerun()
            else: st.rerun()
    with c2:
        if st.button("İptal"): 
            st.session_state.page = "Menu"
            st.rerun()

elif st.session_state.page == "Rapor":
    tarih = datetime.now().strftime("%d.%m.%Y")
    st.markdown(f"## 📄 Analiz Sonuçları: {st.session_state.user_info.get('ad')}")
    
    derin_analiz = generate_deep_analysis(
        st.session_state.results_genel, 
        st.session_state.results_cakra,
        st.session_state.scores.get("isi"), 
        st.session_state.scores.get("nem")
    )
    st.info(f"🧠 **Uzman Yorumu:** {derin_analiz}")

    fig_cakra_html = ""
    if st.session_state.results_cakra:
        data = st.session_state.results_cakra
        cakra_names = list(data.keys())
        yavas_vals = [d['yavas_puan'] for d in data.values()]
        asiri_vals = [d['asiri_puan'] for d in data.values()]
        
        fig_cakra = go.Figure()
        fig_cakra.add_trace(go.Bar(x=cakra_names, y=yavas_vals, name='Blokaj/Yavaş', marker_color='#5DADE2'))
        fig_cakra.add_trace(go.Bar(x=cakra_names, y=asiri_vals, name='Aşırı Aktif', marker_color='#EC7063'))
        
        fig_cakra.add_shape(type="rect", x0=-0.5, x1=len(cakra_names)-0.5, y0=20, y1=25, fillcolor="Green", opacity=0.15, layer="below", line_width=0)
        fig_cakra.add_shape(type="line", x0=-0.5, x1=len(cakra_names)-0.5, y0=30, y1=30, line=dict(color="red", width=2, dash="dot"))
        
        fig_cakra.update_layout(barmode='group', title="Çakra Enerji Dengesi", height=400, margin=dict(t=40, b=40, l=40, r=40), plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(range=[0, 45]))
        fig_cakra_html = fig_cakra.to_html(full_html=False, include_plotlyjs='cdn', config=PLOTLY_CONFIG)
        st.plotly_chart(fig_cakra, use_container_width=True, config=PLOTLY_CONFIG)
        
        df_cakra = pd.DataFrame.from_dict(data, orient='index')
        with st.expander("Detaylı Tabloyu Göster"):
            st.dataframe(df_cakra)

    fig1_html, fig2_html = "", ""
    if st.session_state.results_genel:
        yuzdeler = st.session_state.genel_yuzdeler
        cats = ["SOĞUKLUK", "NEMLİLİK", "SICAKLIK", "KURULUK"]
        vals = [yuzdeler.get(k, 0) for k in cats]
        
        c1, c2 = st.columns(2)
        fig1 = go.Figure(go.Bar(x=cats, y=vals, marker_color=['#3498DB', '#2ECC71', '#E74C3C', '#F1C40F']))
        fig1.update_layout(height=300, margin=dict(t=10,b=10,l=10,r=10))
        fig1_html = fig1.to_html(full_html=False, include_plotlyjs='cdn', config=PLOTLY_CONFIG)
        with c1: st.plotly_chart(fig1, use_container_width=True, config=PLOTLY_CONFIG)
        
        fig2 = go.Figure(go.Scatterpolar(r=vals+[vals[0]], theta=cats+[cats[0]], fill='toself'))
        fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=300, margin=dict(t=20,b=20,l=30,r=30))
        fig2_html = fig2.to_html(full_html=False, include_plotlyjs='cdn', config=PLOTLY_CONFIG)
        with c2: st.plotly_chart(fig2, use_container_width=True, config=PLOTLY_CONFIG)

        st.info(f"Baskın Mizaç: **{st.session_state.results_genel}**")

    any_result = any([st.session_state.results_genel, st.session_state.results_cakra, st.session_state.results_isi, st.session_state.results_nem])
    
    if any_result:
        detaylar = MIZAC_BILGILERI.get(st.session_state.results_genel, {}) if st.session_state.results_genel else {}
        mizac_adi = st.session_state.results_genel if st.session_state.results_genel else None
        
        report_html = create_html_report(st.session_state.user_info, mizac_adi, detaylar, tarih, fig1_html, fig2_html, fig_cakra_html, st.session_state.results_cakra, derin_analiz)
        st.download_button("📥 Tam Raporu İndir (HTML)", data=report_html, file_name=f"Analiz_{st.session_state.user_info.get('ad')}.html", mime="text/html", type="primary", use_container_width=True)
    
    if st.button("Menüye Dön"): 
        st.session_state.page = "Menu"
        st.rerun()
