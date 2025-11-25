import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import streamlit.components.v1 as components
from datetime import datetime
import time
import random
import os
import json
import base64

# ==========================================
# 1. AYARLAR VE YARDIMCI FONKSİYONLAR
# ==========================================
DEV_MODE = False  # Yayına alırken False

st.set_page_config(page_title="Dr. Sait SEVİNÇ", layout="wide", page_icon="🩺")

# --- LOGO VE JSON YÜKLEME ---
@st.cache_data
def load_resources():
    logo_path = "drsaitlogo.jpeg"
    default_logo = "https://i.ibb.co/xJc52gL/image-0.png"
    
    default_json = {
        "Safravi": {"Genel": "Sıcak-Kuru mizaç. Enerjik ve lider ruhlu.", "Beslenme": "Serinletici gıdalar tüketin (Salatalık, marul).", "Psikoloji": "Hızlı öfkelenen ama çabuk sönen yapı.", "Yasam": "Serin ortamlarda bulunun, yüzme önerilir.", "Riskler": ["Migren", "Safra Kesesi", "Cilt Kuruluğu"]},
        "Demevi": {"Genel": "Sıcak-Nemli mizaç. Sosyal ve neşeli.", "Beslenme": "Az ve sık yiyin, kırmızı eti azaltın.", "Psikoloji": "İyimser, dışa dönük.", "Yasam": "Hacamat yaptırın, hareketsiz kalmayın.", "Riskler": ["Yüksek Tansiyon", "Kalp", "Sivilce"]},
        "Balgami": {"Genel": "Soğuk-Nemli mizaç. Sakin ve uyumlu.", "Beslenme": "Isıtıcı baharatlar (Zencefil, kekik) kullanın.", "Psikoloji": "Sabırlı, bazen tembelliğe meyilli.", "Yasam": "Spor yapın, saunaya gidin.", "Riskler": ["Obezite", "Romatizma", "Unutkanlık"]},
        "Sovdavi": {"Genel": "Soğuk-Kuru mizaç. Detaycı ve planlı.", "Beslenme": "Nemlendirici ve sıcak gıdalar tüketin.", "Psikoloji": "Mükemmeliyetçi, içe dönük.", "Yasam": "Sosyalleşin, cildinizi nemlendirin.", "Riskler": ["Depresyon", "Varis", "Kabızlık"]}
    }
    
    data = default_json
    if os.path.exists("mizac_kutuphanesi.json"):
        try:
            with open("mizac_kutuphanesi.json", "r", encoding="utf-8") as f:
                data = json.load(f)
        except: pass
            
    return logo_path, default_logo, data

LOGO_LOCAL, LOGO_URL, MIZAC_BILGILERI = load_resources()

# --- RESMİ HTML İÇİN BASE64'E ÇEVİRME ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

# --- HTML RAPOR OLUŞTURUCU ---
def create_html_report(user_info, mizac, detaylar, tarih, fig1_html, fig2_html):
    img_data = get_image_base64(LOGO_LOCAL)
    img_src = f"data:image/jpeg;base64,{img_data}" if img_data else LOGO_URL
    
    risk_html = ""
    if "Riskler" in detaylar:
        for r in detaylar["Riskler"]:
            risk_html += f"<li>{r}</li>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Mizaç Analiz Raporu</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: 'Helvetica', sans-serif; color: #333; padding: 40px; max-width: 900px; margin: auto; background-color: white; }}
            .header {{ text-align: center; border-bottom: 2px solid #2c3e50; padding-bottom: 20px; margin-bottom: 30px; }}
            .logo {{ width: 120px; margin-bottom: 10px; }}
            h1 {{ color: #2c3e50; margin: 10px 0; font-size: 24px; }}
            .info {{ font-size: 1.1em; color: #555; margin-bottom: 30px; text-align: center; }}
            .result-box {{ background-color: #f0f8ff; border: 2px solid #3498db; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 30px; }}
            .result-title {{ font-size: 1.8em; color: #e74c3c; font-weight: bold; margin-top: 5px; }}
            .charts-container {{ display: flex; justify-content: space-between; margin-bottom: 30px; page-break-inside: avoid; }}
            .chart-box {{ width: 48%; border: 1px solid #eee; border-radius: 8px; padding: 10px; background: #fff; }}
            .section {{ margin-bottom: 20px; page-break-inside: avoid; }}
            .section h3 {{ border-left: 5px solid #1abc9c; padding-left: 10px; color: #16a085; background: #eefcf9; padding: 8px; margin-bottom: 10px; font-size: 1.2em; }}
            .content {{ padding: 0 10px; line-height: 1.5; font-size: 0.95em; }}
            ul {{ margin-top: 5px; padding-left: 20px; }}
            li {{ margin-bottom: 3px; }}
            .footer {{ margin-top: 40px; text-align: center; font-size: 0.7em; color: #999; border-top: 1px solid #eee; padding-top: 10px; }}
            @media print {{
                body {{ padding: 0; margin: 0; }}
                .charts-container {{ display: block; }}
                .chart-box {{ width: 100%; margin-bottom: 20px; page-break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <img src="{img_src}" class="logo">
            <h1>GELENEKSEL TIP ANALİZ RAPORU</h1>
            <div class="info">
                <strong>Danışan:</strong> {user_info.get('ad')} &nbsp;|&nbsp; 
                <strong>Yaş:</strong> {user_info.get('yas')} &nbsp;|&nbsp; 
                <strong>Tarih:</strong> {tarih}
            </div>
        </div>
        <div class="result-box">
            <div>Baskın Mizaç</div>
            <div class="result-title">{mizac}</div>
        </div>
        <div class="charts-container">
            <div class="chart-box"><div style="text-align:center; font-weight:bold; margin-bottom:5px;">Mizaç Dağılımı</div>{fig1_html}</div>
            <div class="chart-box"><div style="text-align:center; font-weight:bold; margin-bottom:5px;">Mizaç Dengesi</div>{fig2_html}</div>
        </div>
        <div class="section"><h3>💡 Genel Özellikler</h3><div class="content">{detaylar.get('Genel', '-')}</div></div>
        <div class="section"><h3>🥗 Beslenme Tavsiyeleri</h3><div class="content">{detaylar.get('Beslenme', '-')}</div></div>
        <div class="section"><h3>🧠 Psikolojik Durum</h3><div class="content">{detaylar.get('Psikoloji', '-')}</div></div>
        <div class="section"><h3>🏃 Yaşam & Tedavi Önerileri</h3><div class="content">{detaylar.get('Yasam', '-')}</div></div>
        <div class="section"><h3>⚠️ Olası Yatkınlıklar</h3><div class="content"><ul>{risk_html}</ul></div></div>
        <div class="footer">Bu rapor Dr. Sait SEVİNÇ Mizaç Analiz Sistemi tarafından oluşturulmuştur.<br>Tıbbi teşhis yerine geçmez, bilgilendirme amaçlıdır.</div>
    </body>
    </html>
    """
    return html

# ==========================================
# 🎨 CSS (MOBİL UYUMLU VE ŞIK)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }

    /* KART TASARIMI */
    .menu-card {
        background: linear-gradient(145deg, #ffffff, #f0f2f5);
        padding: 20px; border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.05);
        text-align: center; border: 1px solid rgba(255,255,255,0.8);
        height: 220px; display: flex; flex-direction: column;
        justify-content: center; align-items: center;
        transition: all 0.3s ease; position: relative;
    }
    .menu-card:hover { transform: translateY(-5px); box-shadow: 0 8px 25px rgba(52, 152, 219, 0.15); border-color: #3498db; }
    .card-done { border: 2px solid #2ecc71 !important; background: linear-gradient(145deg, #f0fff4, #ffffff) !important; }
    .status-badge { background-color: #2ecc71; color: white; padding: 4px 12px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; margin-bottom: 10px; display: inline-block; box-shadow: 0 2px 5px rgba(46, 204, 113, 0.3); }
    .card-icon { font-size: 42px; margin-bottom: 12px; }
    .card-title { font-size: 1.2rem; font-weight: 700; color: #2c3e50; margin-bottom: 8px; line-height: 1.3; }
    .card-desc { font-size: 0.9rem; color: #7f8c8d; }

    /* SORU KUTULARI (Mobil İçin Özel Ayar) */
    .q-box { 
        padding: 18px; 
        border-radius: 12px; 
        margin-bottom: 15px; 
        transition: border 0.3s; 
    }
    .q-default { background: #f8fbfe; border: 1px solid #dceefb; border-left: 5px solid #bdc3c7; }
    .q-filled { background: #ffffff; border: 1px solid #e0ffe8; border-left: 5px solid #2ecc71; box-shadow: 0 2px 8px rgba(46, 204, 113, 0.1); }
    .q-error { background: #fff5f5; border: 1px solid #ffe0e0; border-left: 5px solid #e74c3c; animation: shake 0.5s; }
    .q-text { font-size: 1.05rem; font-weight: 600; color: #2c3e50; margin-bottom: 10px; line-height: 1.4; }
    
    /* BUTONLAR */
    .stButton button { font-weight: 600; border-radius: 8px; transition: all 0.2s; }
    .stButton button:contains("🛠️") { background-color: #2c3e50 !important; color: white !important; border: 2px dashed #f1c40f !important; }
    
    /* MOBİL İÇİN ÖZEL CSS (EŞSİZ DOKUNUŞ) */
    @media (max-width: 768px) {
        .menu-card { height: auto; min-height: 180px; padding: 15px; }
        .q-box { padding: 12px 15px !important; margin-bottom: 12px !important; }
        .q-text { font-size: 1rem !important; margin-bottom: 8px !important; }
        /* Radio butonlarını sıkılaştır */
        .stRadio > div { gap: 0px !important; }
        .stRadio label { font-size: 0.95rem !important; }
    }
    
    /* DİĞERLERİ */
    .rec-box { background: #eefcf9; border-left: 4px solid #1abc9c; padding: 15px; border-radius: 0 8px 8px 0; margin-top: 10px; line-height: 1.6; }
    .info-list { list-style: none; padding: 0; margin: 0; }
    .info-item { background: white; border-radius: 10px; padding: 12px; margin-bottom: 10px; display: flex; align-items: center; border: 1px solid #eee; }
    .info-icon { font-size: 24px; margin-right: 15px; min-width: 30px; text-align: center; }
    .section-header { background-color: #f1f8ff; padding: 15px; border-radius: 10px; color: #2c3e50; font-weight: 800; font-size: 1.4rem; text-align: center; margin-top: 30px; margin-bottom: 20px; border-bottom: 4px solid #3498db; letter-spacing: 1px; }
    
    @media print {
        .stSidebar, .stButton, button, header, footer, [data-testid="stToolbar"] { display: none !important; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. VERİ SETLERİ (SORULAR) - AYNI
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

# ==========================================
# 5. YARDIMCI FONKSİYONLAR
# ==========================================
def init_state():
    defaults = {
        "page": "Giriş", "user_info": {}, "results_isi": None, "results_nem": None, "results_genel": None,
        "genel_skorlar": {}, "genel_yuzdeler": {}, "scores": {"isi": 0, "nem": 0},
        "submitted_genel": False, "submitted_isi": False, "submitted_nem": False
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

def dev_mode_auto_fill():
    if not st.session_state.user_info: st.session_state.user_info = {"ad": "Test Kullanıcısı", "cinsiyet": "Erkek", "yas": 30}
    
    isi_score = 0
    for i, s in enumerate(SORULAR_ISI):
        opt = random.choice(s['options'])
        st.session_state[f"isi_{i}"] = opt['text']
        isi_score += opt['value']
    st.session_state.results_isi = calculate_result_isi(isi_score)
    st.session_state.submitted_isi = True

    nem_score = 0
    for i, s in enumerate(SORULAR_NEM):
        opt = random.choice(s['options'])
        st.session_state[f"nem_{i}"] = opt['text']
        nem_score += opt['value']
    st.session_state.results_nem = calculate_result_nem(nem_score)
    st.session_state.submitted_nem = True

    genel_cevaplar = {}
    for bolum, veri in SORULAR_GENEL_DETAYLI.items():
        secenekler = list(veri["puanlar"].keys())
        for i in range(len(veri["sorular"])):
            val = random.choice(secenekler)
            key = f"genel_{bolum}_{i}"
            st.session_state[key] = val
            genel_cevaplar[key] = val
    mizac_sonuc, skorlar, yuzdeler = genel_mizac_hesapla(genel_cevaplar)
    st.session_state.results_genel = mizac_sonuc
    st.session_state.genel_skorlar = skorlar
    st.session_state.genel_yuzdeler = yuzdeler
    st.session_state.submitted_genel = True

    st.session_state.page = "Rapor"
    st.toast("✅ Test Verileri Yüklendi ve Rapor Oluşturuldu!")
    time.sleep(0.5)
    st.rerun()

def get_icon_for_disease(disease):
    d = disease.lower()
    icons = {"kalp": "❤️", "tansiyon": "❤️", "mide": "🥣", "safra": "🥣", "hazım": "🥣", "baş": "🧠", "migren": "🧠", 
             "cilt": "🧖", "akne": "🧖", "eklem": "🦴", "romatizma": "🦴", "şeker": "🩸", "diyabet": "🩸", 
             "depresyon": "🌧️", "kaygı": "🌧️", "obezite": "⚖️", "kilo": "⚖️", "uyku": "💤", "bağırsak": "💩", "kabızlık": "💩"}
    for k, v in icons.items():
        if k in d: return v
    return "🔸"

def render_questions_with_validation(soru_listesi, key_prefix, submitted):
    total_score = 0
    missing = False
    for i, soru in enumerate(soru_listesi):
        key = f"{key_prefix}_{i}"
        val = st.session_state.get(key)
        
        # Stil belirleme (Mobil ve Masaüstü Uyumlu)
        css = "q-box q-default"
        icon = ""
        if val is not None: css = "q-box q-filled"
        elif submitted: css = "q-box q-error"; icon = "🔴 "; missing = True
            
        st.markdown(f"<div class='{css}'><div class='q-text'>{icon}{i+1}. {soru['text']}</div></div>", unsafe_allow_html=True)
        options_text = [opt['text'] for opt in soru['options']]
        choice = st.radio(f"Soru {i+1}", options_text, key=key, index=None, label_visibility="collapsed", horizontal=True) # Horizontal eklendi, ama CSS mobilde düzeltecek
        
        if choice:
            for opt in soru['options']:
                if opt['text'] == choice:
                    total_score += opt['value']; break
        else: missing = True
    return total_score, missing

def calculate_result_isi(score):
    if score <= 70: return "SOĞUK"
    elif score <= 79: return "MUTEDİL (Dengeli)"
    else: return "SICAK"

def calculate_result_nem(score):
    if score <= 60: return "NEMLİ"
    elif score <= 69: return "MUTEDİL (Dengeli)"
    else: return "KURU"

def genel_mizac_hesapla(cevaplar):
    skorlar = {}
    yuzdeler = {}
    for bolum, veri in SORULAR_GENEL_DETAYLI.items():
        toplam = 0
        max_puan = len(veri["sorular"]) * max(veri["puanlar"].values())
        for i in range(len(veri["sorular"])):
            key = f"genel_{bolum}_{i}"
            secim = cevaplar.get(key)
            if secim: toplam += veri["puanlar"][secim]
        skorlar[bolum] = toplam
        yuzdeler[bolum] = (toplam / max_puan) * 100 if max_puan > 0 else 0
    isi = "SICAK" if yuzdeler["SICAKLIK"] >= yuzdeler["SOĞUKLUK"] else "SOĞUK"
    nem = "KURU" if yuzdeler["KURULUK"] >= yuzdeler["NEMLİLİK"] else "NEMLİ"
    anahtar = f"{isi} {nem}"
    mizac_adi = "Mutedil"
    if "SICAK" in anahtar and "KURU" in anahtar: mizac_adi = "Safravi"
    elif "SICAK" in anahtar and "NEMLİ" in anahtar: mizac_adi = "Demevi"
    elif "SOĞUK" in anahtar and "NEMLİ" in anahtar: mizac_adi = "Balgami"
    elif "SOĞUK" in anahtar and "KURU" in anahtar: mizac_adi = "Sovdavi"
    return mizac_adi, skorlar, yuzdeler

def reset_app():
    st.session_state.clear()
    st.rerun()

# ==========================================
# 6. UYGULAMA AKIŞI
# ==========================================
init_state()

with st.sidebar:
    if os.path.exists(LOGO_LOCAL): st.image(LOGO_LOCAL, width=140)
    else: st.image(LOGO_URL, width=140)
    st.markdown("### Dr. Sait SEVİNÇ")
    if st.session_state.user_info: st.success(f"👤 {st.session_state.user_info.get('ad')}")
    if st.button("🏠 Ana Menü"): st.session_state.page = "Menu"; st.rerun()
    st.divider()
    st.caption("Tamamlanan Testler")
    if st.session_state.results_genel: st.success("✅ Genel Mizaç")
    else: st.markdown("⬜ Genel Mizaç")
    if st.session_state.results_isi: st.success("✅ Sıcaklık/Soğukluk")
    else: st.markdown("⬜ Sıcaklık/Soğukluk")
    if st.session_state.results_nem: st.success("✅ Islaklık/Kuruluk")
    else: st.markdown("⬜ Islaklık/Kuruluk")
    st.divider()
    if st.button("📄 Analiz Sonuçları", type="primary"): st.session_state.page = "Rapor"; st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Yeni Analiz (Sıfırla)", type="secondary"): reset_app()

    if DEV_MODE:
        st.markdown("---"); st.caption("🛠️ Geliştirici Modu")
        if st.button("⚡ Otomatik Doldur", key="sb_dev"): dev_mode_auto_fill()

if st.session_state.page == "Giriş":
    st.markdown("<div style='text-align:center; padding: 20px;'><h1>Geleneksel Tıp Analiz Sistemi</h1><p style='color:#666;'>Mizacınızı, vücut ısınısı ve nem dengenizi keşfederek daha sağlıklı bir yaşama adım atın.</p></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.container(border=True):
            ad = st.text_input("Adınız Soyadınız")
            c1_ic, c2_ic = st.columns(2)
            with c1_ic: cinsiyet = st.selectbox("Cinsiyet", ["Kadın", "Erkek"])
            with c2_ic: yas = st.number_input("Yaşınız", 10, 100, 30)
            if st.button("Analize Başla 🚀", type="primary", use_container_width=True):
                if ad:
                    st.session_state.user_info = {"ad": ad, "cinsiyet": cinsiyet, "yas": yas}
                    st.session_state.page = "Menu"; st.rerun()
                else: st.warning("Lütfen isminizi giriniz.")
            if DEV_MODE:
                st.markdown("---")
                if st.button("🛠️ Test Modu (Hızlı Giriş)", use_container_width=True, key="main_dev"): dev_mode_auto_fill()

elif st.session_state.page == "Menu":
    st.subheader(f"Hoşgeldiniz, {st.session_state.user_info['ad']}")
    st.write("Lütfen aşağıdaki analizleri sırasıyla tamamlayınız.")
    c1, c2, c3 = st.columns(3)
    
    genel_done = st.session_state.results_genel is not None
    genel_css = "menu-card card-done" if genel_done else "menu-card"
    genel_badge = "<div class='status-badge'>✅ Tamamlandı</div>" if genel_done else ""
    genel_btn = "Tekrarla / Düzenle" if genel_done else "Başla (Genel)"
    
    with c1:
        st.markdown(f"""<div class="{genel_css}">{genel_badge}<span class="card-icon">🦁</span><span class="card-title">Genel Mizaç</span><span class="card-desc">Baskın elementinizi bulun.</span></div>""", unsafe_allow_html=True)
        if st.button(genel_btn, key="btn_genel_menu", use_container_width=True): st.session_state.page = "Test_Genel"; st.rerun()

    isi_done = st.session_state.results_isi is not None
    isi_css = "menu-card card-done" if isi_done else "menu-card"
    isi_badge = "<div class='status-badge'>✅ Tamamlandı</div>" if isi_done else ""
    isi_btn = "Tekrarla / Düzenle" if isi_done else "Başla (Isı)"

    with c2:
        st.markdown(f"""<div class="{isi_css}">{isi_badge}<span class="card-icon">🔥</span><span class="card-title">Sıcaklık / Soğukluk</span><span class="card-desc">Metabolizma ısısı.</span></div>""", unsafe_allow_html=True)
        if st.button(isi_btn, key="btn_isi_menu", use_container_width=True): st.session_state.page = "Test_Isi"; st.rerun()

    nem_done = st.session_state.results_nem is not None
    nem_css = "menu-card card-done" if nem_done else "menu-card"
    nem_badge = "<div class='status-badge'>✅ Tamamlandı</div>" if nem_done else ""
    nem_btn = "Tekrarla / Düzenle" if nem_done else "Başla (Nem)"

    with c3:
        st.markdown(f"""<div class="{nem_css}">{nem_badge}<span class="card-icon">💧</span><span class="card-title">Islaklık / Kuruluk</span><span class="card-desc">Nem dengesi.</span></div>""", unsafe_allow_html=True)
        if st.button(nem_btn, key="btn_nem_menu", use_container_width=True): st.session_state.page = "Test_Nem"; st.rerun()
            
    st.markdown("---")
    if st.button("📊 Analiz Sonuçları", use_container_width=True, type="primary"): st.session_state.page = "Rapor"; st.rerun()

elif st.session_state.page == "Test_Isi":
    st.title("🔥 Sıcaklık ve Soğukluk Analizi")
    score, missing = render_questions_with_validation(SORULAR_ISI, "isi", st.session_state.submitted_isi)
    if st.button("Kaydet ve Bitir", type="primary"):
        st.session_state.submitted_isi = True; st.rerun()
    if st.session_state.submitted_isi:
        if missing: st.error("Lütfen kırmızı ile işaretlenen soruları yanıtlayınız.")
        else:
            st.session_state.results_isi = calculate_result_isi(score)
            st.session_state.scores["isi"] = score
            st.success("✅ Test Tamamlandı!"); time.sleep(1); st.session_state.page = "Menu"; st.rerun()

elif st.session_state.page == "Test_Nem":
    st.title("💧 Islaklık ve Kuruluk Analizi")
    score, missing = render_questions_with_validation(SORULAR_NEM, "nem", st.session_state.submitted_nem)
    if st.button("Kaydet ve Bitir", type="primary"):
        st.session_state.submitted_nem = True; st.rerun()
    if st.session_state.submitted_nem:
        if missing: st.error("Lütfen kırmızı ile işaretlenen soruları yanıtlayınız.")
        else:
            st.session_state.results_nem = calculate_result_nem(score)
            st.session_state.scores["nem"] = score
            st.success("✅ Test Tamamlandı!"); time.sleep(1); st.session_state.page = "Menu"; st.rerun()

elif st.session_state.page == "Test_Genel":
    st.title("🧬 Genel Mizaç Tespiti")
    cevaplar = {}
    missing_any = False
    for bolum, veri in SORULAR_GENEL_DETAYLI.items():
        st.markdown(f'<div class="section-header">📌 {bolum} Bölümü</div>', unsafe_allow_html=True)
        secenekler = list(veri["puanlar"].keys()); secenekler.sort(key=lambda x: veri["puanlar"][x])
        for i, soru in enumerate(veri["sorular"]):
            key = f"genel_{bolum}_{i}"
            val = st.session_state.get(key)
            
            # --- RENK MANTIĞI (MOBİLDE DE ÇALIŞIR) ---
            css = "q-box q-default" # Default
            icon = ""; style = "color: #2c3e50;"
            if val: css = "q-box q-filled"
            elif st.session_state.submitted_genel: css = "q-box q-error"; icon = "🔴 "; style = "color: #e74c3c; font-weight:bold;"
            
            st.markdown(f"<div class='{css}'><div class='q-text' style='{style}'>{icon}{i+1}. {soru}</div></div>", unsafe_allow_html=True)
            
            # Horizontal=True masaüstünde yan yana, mobilde CSS ile sıkışıp alt alta
            choice = st.radio(f"{bolum} {i+1}", secenekler, key=key, index=None, horizontal=True, label_visibility="collapsed")
            if choice: cevaplar[key] = choice
            
    if st.button("Kaydet ve Bitir", type="primary"):
        st.session_state.submitted_genel = True; st.rerun()
    if st.session_state.submitted_genel:
        if len(cevaplar) < sum(len(v["sorular"]) for v in SORULAR_GENEL_DETAYLI.values()):
            st.error("Lütfen eksik soruları tamamlayınız.")
        else:
            mizac, skorlar, yuzdeler = genel_mizac_hesapla(cevaplar)
            st.session_state.results_genel = mizac
            st.session_state.genel_skorlar = skorlar
            st.session_state.genel_yuzdeler = yuzdeler
            st.success("✅ Analiz Tamamlandı!"); time.sleep(1); st.session_state.page = "Menu"; st.rerun()

elif st.session_state.page == "Rapor":
    tarih = datetime.now().strftime("%d.%m.%Y")
    st.markdown(f"""<div class="report-header"><h1>ANALİZ SONUÇLARI</h1><h3>{st.session_state.user_info.get('ad')} | Yaş: {st.session_state.user_info.get('yas')}</h3><p>{tarih}</p></div>""", unsafe_allow_html=True)
    
    # --- GRAFİKLERİ HTML İÇİN HAZIRLAMA ---
    fig1_html = ""
    fig2_html = ""
    
    if st.session_state.results_genel and st.session_state.genel_yuzdeler:
        st.subheader("📊 Analiz Grafiği")
        yuzdeler = st.session_state.genel_yuzdeler
        cats = list(yuzdeler.keys()); vals = list(yuzdeler.values())
        
        # Bar Grafik
        fig1 = go.Figure(go.Bar(x=cats, y=vals, text=[f"%{v:.0f}" for v in vals], textposition='auto', marker_color=['#E74C3C', '#3498DB', '#F1C40F', '#2ECC71']))
        fig1.update_layout(height=300, margin=dict(t=10, b=20, l=20, r=20))
        fig1_html = fig1.to_html(full_html=False, include_plotlyjs='cdn') # HTML için dönüşüm
        
        # Radar Grafik
        vals_c = vals + [vals[0]]; cats_c = cats + [cats[0]]
        fig2 = go.Figure(go.Scatterpolar(r=vals_c, theta=cats_c, fill='toself', line=dict(color='#8E44AD', width=3)))
        fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100]), angularaxis=dict(tickfont=dict(size=12))), height=350, margin=dict(t=40, b=40, l=60, r=60))
        fig2_html = fig2.to_html(full_html=False, include_plotlyjs='cdn') # HTML için dönüşüm

        # Ekrana Basma
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
        with c2: st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
        st.markdown("---")

    # ISI VE NEM SONUÇLARI
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 Isı Dengesi")
        if st.session_state.results_isi:
            res = st.session_state.results_isi
            color = "red" if "SICAK" in res else "blue"
            st.markdown(f"<h2 style='color:{color}'>{res}</h2>", unsafe_allow_html=True)
        else: st.warning("Test yapılmadı.")
    with c2:
        st.subheader("💧 Nem Dengesi")
        if st.session_state.results_nem:
            res = st.session_state.results_nem
            color = "orange" if "KURU" in res else "teal"
            st.markdown(f"<h2 style='color:{color}'>{res}</h2>", unsafe_allow_html=True)
        else: st.warning("Test yapılmadı.")
    st.markdown("---")

    # GENEL MİZAÇ VE TAVSİYELER
    st.subheader("🧬 Genel Mizaç Sonuç")
    if st.session_state.results_genel:
        mizac_adi = st.session_state.results_genel
        detaylar = MIZAC_BILGILERI.get(mizac_adi, {})
        st.info(f"Baskın Mizacınız: **{mizac_adi}**")
        
        # EKRAN İÇİN SEKMELER
        tab1, tab2, tab3, tab4 = st.tabs(["💡 Genel", "🥗 Beslenme", "🧠 Psikoloji", "🏃 Yaşam"])
        with tab1: st.markdown(f"<div class='rec-box'>{detaylar.get('Genel', 'Bilgi yok')}</div>", unsafe_allow_html=True)
        with tab2: st.markdown(f"<div class='rec-box'>{detaylar.get('Beslenme', 'Bilgi yok')}</div>", unsafe_allow_html=True)
        with tab3: st.markdown(f"<div class='rec-box'>{detaylar.get('Psikoloji', 'Bilgi yok')}</div>", unsafe_allow_html=True)
        with tab4: st.markdown(f"<div class='rec-box'>{detaylar.get('Yasam', 'Bilgi yok')}</div>", unsafe_allow_html=True)
        
        if "Riskler" in detaylar:
            st.markdown("#### ⚠️ Olası Rahatsızlıklar")
            html = "<ul class='info-list'>"
            for r in detaylar["Riskler"]:
                icon = get_icon_for_disease(r)
                html += f"<li class='info-item'><span class='info-icon'>{icon}</span>{r}</li>"
            html += "</ul>"
            st.markdown(html, unsafe_allow_html=True)
            
        # --- HTML RAPOR İNDİRME BUTONU ---
        st.markdown("---")
        report_html = create_html_report(st.session_state.user_info, mizac_adi, detaylar, tarih, fig1_html, fig2_html)
        
        col_dl, col_home = st.columns([3, 1])
        with col_dl:
            st.download_button(
                label="📥 Raporu İndir (Yazdırmak İçin)",
                data=report_html,
                file_name=f"Mizac_Raporu_{st.session_state.user_info.get('ad')}.html",
                mime="text/html",
                use_container_width=True
            )
        with col_home: 
            if st.button("🏠 Menüye Dön", use_container_width=True): st.session_state.page = "Menu"; st.rerun()
            
    else: st.warning("Genel mizaç testi yapılmadı.")
    st.markdown("<br><br>", unsafe_allow_html=True)