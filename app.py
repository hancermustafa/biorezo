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

st.set_page_config(page_title="Dr. Sait SEVİNÇ - Bütüncül Analiz", layout="wide", page_icon="🧘")

# --- LOGO VE JSON YÜKLEME ---
@st.cache_data
def load_resources():
    logo_path = "drsaitlogo.jpeg"
    default_logo = "https://i.ibb.co/xJc52gL/image-0.png"
    
    # Varsayılan Mizaç Bilgileri
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

# --- HTML RAPOR OLUŞTURUCU (RENK MANTIĞI DÜZELTİLDİ) ---
def create_html_report(user_info, mizac, detaylar, tarih, fig1_html, fig2_html, fig_cakra_html, cakra_sonuclar):
    img_data = get_image_base64(LOGO_LOCAL)
    img_src = f"data:image/jpeg;base64,{img_data}" if img_data else LOGO_URL
    
    mizac_display = mizac if mizac else "Henüz Belirlenmedi"
    detaylar = detaylar if detaylar else {}
    
    risk_html = ""
    if "Riskler" in detaylar:
        for r in detaylar["Riskler"]:
            risk_html += f"<li>{r}</li>"

    # Çakra Tablosu HTML
    cakra_section_html = ""
    if cakra_sonuclar:
        cakra_rows = ""
        for cakra, degerler in cakra_sonuclar.items():
            durum = degerler['durum']
            
            # --- YENİ RENK MANTIĞI ---
            if durum == "Dengeli":
                status_color = "#2ecc71" # Yeşil (İyi)
            elif "Hafif" in durum:
                status_color = "#f39c12" # Turuncu (Uyarı)
            else:
                status_color = "#e74c3c" # Kırmızı (Sorun: Yavaş, Aşırı veya Kaotik)
            
            cakra_rows += f"""
            <tr>
                <td style="padding:8px; border-bottom:1px solid #eee;"><strong>{cakra}</strong></td>
                <td style="padding:8px; border-bottom:1px solid #eee; text-align:center;">{degerler['yavas_puan']}</td>
                <td style="padding:8px; border-bottom:1px solid #eee; text-align:center;">{degerler['asiri_puan']}</td>
                <td style="padding:8px; border-bottom:1px solid #eee; color:{status_color}; font-weight:bold;">{durum}</td>
            </tr>
            """
        
        cakra_section_html = f"""
        <div class="section" style="page-break-before: always;">
            <h3>🌀 Çakra Enerji Analizi</h3>
            <div class="full-width-chart">
                 {fig_cakra_html}
            </div>
            <div class="content">
                <table style="width:100%; border-collapse:collapse;">
                    <thead>
                        <tr style="background-color:#f8f9fa;">
                            <th style="padding:8px; text-align:left;">Çakra</th>
                            <th style="padding:8px; text-align:center;">Yavaşlık Puanı</th>
                            <th style="padding:8px; text-align:center;">Aşırılık Puanı</th>
                            <th style="padding:8px; text-align:left;">Durum</th>
                        </tr>
                    </thead>
                    <tbody>{cakra_rows}</tbody>
                </table>
            </div>
        </div>
        """

    # Mizaç Bölümü HTML
    mizac_section_html = ""
    if mizac:
        mizac_section_html = f"""
        <div class="result-box">
            <div>Baskın Mizaç</div>
            <div class="result-title">{mizac_display}</div>
        </div>
        <div class="charts-container">
            <div class="chart-box"><div style="text-align:center; font-weight:bold; margin-bottom:5px;">Mizaç Dağılımı</div>{fig1_html}</div>
            <div class="chart-box"><div style="text-align:center; font-weight:bold; margin-bottom:5px;">Mizaç Dengesi</div>{fig2_html}</div>
        </div>
        <div class="section"><h3>💡 Mizaç Özellikleri</h3><div class="content">{detaylar.get('Genel', '-')}</div></div>
        <div class="section"><h3>🥗 Beslenme Tavsiyeleri</h3><div class="content">{detaylar.get('Beslenme', '-')}</div></div>
        <div class="section"><h3>⚠️ Olası Yatkınlıklar</h3><div class="content"><ul>{risk_html}</ul></div></div>
        """
    else:
        mizac_section_html = "<div class='result-box'>Mizaç analizi yapılmadı.</div>"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Bütüncül Analiz Raporu</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: 'Helvetica', sans-serif; color: #333; padding: 40px; max-width: 900px; margin: auto; background-color: white; }}
            .header {{ text-align: center; border-bottom: 2px solid #2c3e50; padding-bottom: 20px; margin-bottom: 30px; }}
            .logo {{ width: 120px; margin-bottom: 10px; }}
            h1 {{ color: #2c3e50; margin: 10px 0; font-size: 24px; }}
            .info {{ font-size: 1.1em; color: #555; margin-bottom: 30px; text-align: center; }}
            .result-box {{ background-color: #f0f8ff; border: 2px solid #3498db; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 30px; }}
            .result-title {{ font-size: 1.8em; color: #e74c3c; font-weight: bold; margin-top: 5px; }}
            .charts-container {{ display: flex; justify-content: space-between; margin-bottom: 30px; }}
            .chart-box {{ width: 48%; border: 1px solid #eee; border-radius: 8px; padding: 10px; background: #fff; }}
            .full-width-chart {{ width: 100%; border: 1px solid #eee; border-radius: 8px; padding: 10px; background: #fff; margin-bottom: 30px; }}
            .section {{ margin-bottom: 20px; }}
            .section h3 {{ border-left: 5px solid #1abc9c; padding-left: 10px; color: #16a085; background: #eefcf9; padding: 8px; margin-bottom: 10px; font-size: 1.2em; }}
            .content {{ padding: 0 10px; line-height: 1.5; font-size: 0.95em; }}
            .footer {{ margin-top: 40px; text-align: center; font-size: 0.7em; color: #999; border-top: 1px solid #eee; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <img src="{img_src}" class="logo">
            <h1>BÜTÜNCÜL SAĞLIK RAPORU</h1>
            <div class="info">
                <strong>Danışan:</strong> {user_info.get('ad')} &nbsp;|&nbsp; 
                <strong>Yaş:</strong> {user_info.get('yas')} &nbsp;|&nbsp; 
                <strong>Tarih:</strong> {tarih}
            </div>
        </div>
        
        {mizac_section_html}
        {cakra_section_html}

        <div class="footer">Bu rapor Dr. Sait SEVİNÇ Analiz Sistemi tarafından oluşturulmuştur.</div>
    </body>
    </html>
    """
    return html

# ==========================================
# 🎨 CSS
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }

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

    .q-box { padding: 18px; border-radius: 12px; margin-bottom: 15px; transition: border 0.3s; }
    .q-default { background: #f8fbfe; border: 1px solid #dceefb; border-left: 5px solid #bdc3c7; }
    .q-filled { background: #ffffff; border: 1px solid #e0ffe8; border-left: 5px solid #2ecc71; box-shadow: 0 2px 8px rgba(46, 204, 113, 0.1); }
    .q-error { background: #fff5f5; border: 1px solid #ffe0e0; border-left: 5px solid #e74c3c; animation: shake 0.5s; }
    .q-text { font-size: 1.05rem; font-weight: 600; color: #2c3e50; margin-bottom: 10px; line-height: 1.4; }
    
    .stButton button { font-weight: 600; border-radius: 8px; transition: all 0.2s; }
    .stRadio > div { gap: 0px !important; }
    .section-header { background-color: #f1f8ff; padding: 15px; border-radius: 10px; color: #2c3e50; font-weight: 800; font-size: 1.4rem; text-align: center; margin-top: 30px; margin-bottom: 20px; border-bottom: 4px solid #3498db; }
    
    @media print { .stSidebar, .stButton, button, header, footer, [data-testid="stToolbar"] { display: none !important; } }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. VERİ SETLERİ
# ==========================================
# (Kod kısalığı için Isı ve Nem sorularını kısa tuttum, gerçek soruları buraya eklemelisin)
SORULAR_ISI = [{"text": "Vücut ısınız?", "options": [{"text": "Çok üşürüm", "value": 1}, {"text": "Çok sıcağım", "value": 5}]}] * 5 
SORULAR_NEM = [{"text": "Cilt yapınız?", "options": [{"text": "Çok nemli", "value": 1}, {"text": "Çok kuru", "value": 5}]}] * 5

SORULAR_GENEL_DETAYLI = {
    "SICAKLIK": {"puanlar": {"Hayır": 1, "Orta": 2, "Evet": 3}, "sorular": ["Hareketli misiniz?", "Öfkeniz hızlı mı?", "Sıcağı sever misiniz?"]},
    "SOĞUKLUK": {"puanlar": {"Hayır": 1, "Orta": 2, "Evet": 3}, "sorular": ["Sakin misiniz?", "Üşümeyi sever misiniz?", "Yavaş hareket eder misiniz?"]},
    "NEMLİLİK": {"puanlar": {"Hayır": 1, "Orta": 2, "Evet": 3}, "sorular": ["Uykuyu sever misiniz?", "Kilo almaya müsait misiniz?", "Cildiniz yumuşak mı?"]},
    "KURULUK":  {"puanlar": {"Hayır": 1, "Orta": 2, "Evet": 3}, "sorular": ["Cildiniz kuru mu?", "Zayıf mısınız?", "Uykunuz hafif mi?"]}
}

SORULAR_CAKRA = {
    "KÖK ÇAKRA (Muladhara)": [
        "Kendimi çoğu zaman güvensiz, huzursuz ya da korunmasız hissediyorum.",
        "Değersiz ya da yetersiz biriymişim gibi hissettiğim anlar sık yaşanıyor.",
        "Günlük yaşamımda temel ihtiyaçlarımı bile karşılamakta zorlanıyorum.",
        "Parasal konular beni çok tedirgin ediyor; sürekli bir yokluk kaygısı taşıyorum.",
        "Fiziksel olarak zayıf, halsiz ve enerjisiz hissediyorum.",
        "Aidiyet hissim zayıf; ne bir yere ne de birilerine gerçekten ait hissedemiyorum.",
        "Hızlıca odaklanamıyor, başladığım işleri tamamlayamıyorum.",
        "Bağımlı ilişkiler kurmaya eğilimliyim; tek başıma güvende hissedemiyorum.",
        "Maddi güvence konusunda aşırı takıntılıyım; sahip olduklarımı kaybetme korkusu taşıyorum.",
        "Fazla inatçı, kontrolcü ve değişime kapalı biri olduğumu düşünüyorum.",
        "İnsanlara kolay kolay güvenemem, her şeyin altında bir tehdit ararım.",
        "Fiziksel dünyaya fazlasıyla bağlıyım; maneviyatla ilişkim çok zayıf.",
        "Bırakamama, tutunma, bir şeyi ya da kişiyi bırakınca sanki parçalanacakmışım gibi hissediyorum.",
        "Kızgınlık, öfke ya da patlayıcı tepkilerle çevreme zarar verebiliyorum.",
        "Kendi isteklerim doğrultusunda başkalarını yönlendirmeye ya da baskılamaya çalışıyorum.",
        "Gücü elimde tutma, her şeye hâkim olma arzusu beni yoruyor."
    ],
    "SAKRAL ÇAKRA (Svadhisthana)": [
        "Duygularımı ifade etmekte zorlanıyor, çoğu zaman içime atıyorum.",
        "Cinselliğe karşı isteksizlik ya da yabancılaşma yaşıyorum.",
        "Hayattan keyif almakta zorlanıyor, neşesiz hissediyorum.",
        "Yaratıcılığımı göstermekten çekiniyor ya da ilham bulmakta zorlanıyorum.",
        "Kendime dair tatmin duygum oldukça düşük; hiçbir şeyden tam olarak memnun olmuyorum.",
        "Başkalarıyla derin bağ kurmakta zorlanıyor, yalnız kalmayı tercih ediyorum.",
        "Geçmiş duygusal yaralardan kurtulamadığımı hissediyorum.",
        "Bedenimle olan ilişkim zayıf, çoğu zaman ona yabancı gibiyim.",
        "Sürekli bir haz peşindeyim; duygusal ya da fiziksel tatmin benim için çok önemli.",
        "Aşırı cinsellik ya da duygusal bağımlılık gibi durumlara eğilimim var.",
        "Duygularım çok yoğun ve ani; sıklıkla dalgalanma yaşıyorum.",
        "Tüketim, alışveriş, yemek gibi haz veren şeylere bağımlı hissediyorum.",
        "Duygusal ilişkilerde sınır koymakta zorlanıyor, kendimi kaybediyorum.",
        "Aşırı hassasım; başkalarının duygusal durumlarından kolay etkileniyorum.",
        "Sanatsal ya da yaratıcı alanlarda abartıya kaçtığımı düşünüyorum.",
        "Kontrolsüz duygusal tepkiler veriyor, sonra pişman oluyorum."
    ],
    "SOLAR PLEXUS (Manipura)": [
        "Karar vermekte zorlanıyor ve çoğu zaman başkalarının onayını bekliyorum.",
        "Hayır demekte zorlanıyorum; sınırlarımı belirleyemiyorum.",
        "Kendi gücümü ortaya koymakta zorluk yaşıyor, çekingen davranıyorum.",
        "Sık sık yetersiz ya da başarısız hissediyorum.",
        "Başladığım işleri tamamlamakta zorlanıyor, motivasyon kaybı yaşıyorum.",
        "Eleştiriler karşısında kolayca kırılıyor, savunmasız hissediyorum.",
        "Kendime güvenmekte zorlanıyor, içimde sürekli bir eksiklik hissediyorum.",
        "Başarıya dair arzularım var ama harekete geçecek enerjiyi bulamıyorum.",
        "Kontrolü kaybetmekten korkuyorum; her şeyin benim istediğim gibi olmasını istiyorum.",
        "Gücümü göstermek için bazen baskıcı ya da manipülatif davranıyorum.",
        "Başkalarının alanına girmeye eğilimliyim; her şeye müdahil olmak istiyorum.",
        "Aşırı rekabetçiyim; sürekli üstün gelme ihtiyacı hissediyorum.",
        "Kendimi çok fazla ön plana çıkarıyor, dikkat çekmek istiyorum.",
        "Başkalarının duygularını görmezden gelerek sadece kendi isteklerime odaklanabiliyorum.",
        "Öfke patlamaları yaşıyor, küçük konulara aşırı tepki veriyorum.",
        "Başarıya bağımlıyım; başarısızlık korkusu beni sürekli tedirgin ediyor."
    ],
    "KALP ÇAKRASI (Anahata)": [
        "Başkalarına karşı sevgimi ifade etmekte zorlanıyorum.",
        "Kırıldığım kişileri affetmek bana çok zor geliyor.",
        "İnsanlara güvenmekte zorlanıyorum; duygusal olarak geri çekiliyorum.",
        "Kendimi sevmekte ve kendime değer vermekte zorlanıyorum.",
        "Duygusal ilişkiler beni yıpratıyor; çoğunlukla kaçınmayı tercih ediyorum.",
        "Kalbimin kapalı olduğunu hissediyorum; kimseye gerçekten açılamıyorum.",
        "Geçmiş acılar hâlâ içimde yer tutuyor ve içsel huzurumu engelliyor.",
        "Sevgi vermektense almayı bekliyorum; paylaşmakta zorlanıyorum.",
        "Herkese yardım etmek zorundaymışım gibi hissediyorum; kendimi ihmal ediyorum.",
        "İnsanların duygularını o kadar çok hissediyorum ki, kendi sınırlarımı kaybediyorum.",
        "Başkalarının onayına ve sevgisine bağımlı hissediyorum.",
        "Duygusal ilişkilerde kendimi fazla veriyor, sonra tükeniyorum.",
        "Hayır diyememek beni sürekli zor durumda bırakıyor.",
        "Kırılganlığım o kadar yoğun ki, başkalarının duygularıyla boğuluyorum.",
        "Aşırı özverili davranıyor, karşılık beklemesem bile yıpranıyorum.",
        "Sevgi adına kendi ihtiyaçlarımı ve isteklerimi yok sayıyorum."
    ],
    "BOĞAZ ÇAKRASI (Vishuddha)": [
        "Duygularımı ya da düşüncelerimi açıkça ifade etmekte zorlanıyorum.",
        "Topluluk önünde konuşmak beni çok geriyor, hatta kaçınmaya çalışıyorum.",
        "Kendimi bastırılmış ya da sesi kısılmış biri gibi hissediyorum.",
        "Doğru zamanda, doğru şekilde konuşamadığımı fark ediyorum.",
        "İletişimde sürekli yanlış anlaşıldığımı düşünüyorum.",
        "Düşüncelerimi toparlamakta ya da kendimi açık ifade etmekte zorlanıyorum.",
        "Kendimi ifade etme hakkım yokmuş gibi hissediyorum.",
        "Çoğu zaman sessiz kalmayı tercih ediyorum, içime kapanıyorum.",
        "Sürekli konuşma ihtiyacı hissediyorum, karşımdakini dinlemekte zorlanıyorum.",
        "İnsanlara düşüncelerimi zorla kabul ettirmeye çalışıyorum.",
        "Aşırı açıklık ya da fazla detaylı konuşma eğilimim var.",
        "Başkalarının sözünü sık sık kesiyor ya da üstünlük kurmaya çalışıyorum.",
        "Eleştiriyi kaldıramıyor ve hemen savunmaya geçiyorum.",
        "Kendimi ifade ederken farkında olmadan kırıcı ya da saldırgan olabiliyorum.",
        "Ses tonumla veya ifadelerimle dikkat çekmeye çalışıyorum.",
        "Başkalarını susturup yalnızca kendi düşüncelerime alan açmak istiyorum."
    ],
    "GÖZ ÇAKRASI (Ajna)": [
        "İçgüdülerime güvenmekte zorlanıyor, sürekli dış onay arıyorum.",
        "Geleceğe dair net bir vizyonum yok; yönümü bulmakta zorlanıyorum.",
        "Zihnim dağınık, düşüncelerim bulanık ve kararsızlık içinde hissediyorum.",
        "Meditasyon ya da içsel sessizlik çalışmalarında zorluk yaşıyorum.",
        "Sezgisel sinyalleri algılayamıyor veya yok sayıyorum.",
        "Mantık ve sezgi arasında sürekli bir çatışma yaşıyorum.",
        "Hayal kurmakta, yaratıcı düşünmekte zorluk çekiyorum.",
        "Geçmişte yaşananlara takılı kalıyor, geleceğe dair umut beslemekte zorlanıyorum.",
        "Sürekli zihnimde yaşıyor, gerçeklikten kopuyorum.",
        "Olaylara aşırı anlamlar yüklüyor, kuruntular içinde kayboluyorum.",
        "Rüyalar, semboller ya da işaretlerle aşırı meşgul oluyorum.",
        "Gerçeklikten uzaklaşma ya da spiritüel kaçış hali yaşıyorum.",
        "İnsanların ne düşündüğünü “hissettiğime” çok fazla inanıyorum.",
        "Kontrol edilemeyen bir zihinsel aktivite ve içsel konuşma beni yoruyor.",
        "Gelecekle ilgili aşırı hayal kuruyor ama eyleme geçemiyorum.",
        "Gerçeklikten kopmama neden olan takıntılı düşünce kalıplarım var."
    ],
    "TAÇ ÇAKRASI (Sahasrara)": [
        "Kendimi evrenden veya daha büyük bir bütünün parçası olarak hissetmekte zorlanıyorum.",
        "Manevi pratiklere veya içsel yolculuğa karşı ilgisiz ya da uzak hissediyorum.",
        "Anlam ve amaç bulmakta güçlük çekiyorum.",
        "Ruhsal ya da kişisel gelişimle ilgili deneyimlere kapalıyım.",
        "İçsel huzur ve sükunet duygusundan yoksunum.",
        "Meditasyon ya da sessizlik içinde olmaktan kaçınıyorum.",
        "Hayatımda bir boşluk, anlamsızlık ya da kopukluk hissediyorum.",
        "Ruhsal deneyimlerimde kararsızlık ya da inanç eksikliği yaşıyorum.",
        "Kendimi sürekli evrensel bilinçle bağlantılı hissediyor, gerçeklikten kopuyorum.",
        "Dünyadan, günlük hayattan ve bedensel deneyimlerden uzaklaşıyorum.",
        "Spiritüel uygulamalara aşırı odaklanıyor, bazen fanatikleşiyorum.",
        "Kendi bedenimi ve maddi dünyayı ihmal ediyorum.",
        "Sıklıkla kendimi “aydınlanmış” veya “öteki seviyede” biri olarak görüyorum.",
        "Günlük sorumluluklarımdan kaçıyor, gerçeklerle yüzleşmekte zorlanıyorum.",
        "Spiritüel bilgileri abartıyor ya da bu alanda kendimi üstün görüyorum.",
        "Manevi deneyimlere aşırı bağımlılık hissediyorum."
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

    if st.button("Analizi Bitir", type="primary", use_container_width=True):
        st.session_state.submitted_cakra = True
        if missing_count > 0:
            st.error("Lütfen tüm soruları cevaplayınız.")
            st.rerun()
        else:
            st.session_state.results_cakra = calculate_cakra_results(cevaplar_cakra)
            st.success("Çakra analizi tamamlandı!")
            time.sleep(1)
            st.session_state.page = "Menu"
            st.rerun()

elif st.session_state.page == "Test_Isi":
    st.title("🔥 Isı Analizi")
    score, missing = render_questions_with_validation(SORULAR_ISI, "isi", st.session_state.submitted_isi)
    if st.button("Kaydet"): st.session_state.submitted_isi = True; st.rerun()
    if st.session_state.submitted_isi and not missing:
        st.session_state.results_isi = calculate_result_isi(score)
        st.session_state.page = "Menu"; st.rerun()

elif st.session_state.page == "Test_Nem":
    st.title("💧 Nem Analizi")
    score, missing = render_questions_with_validation(SORULAR_NEM, "nem", st.session_state.submitted_nem)
    if st.button("Kaydet"): st.session_state.submitted_nem = True; st.rerun()
    if st.session_state.submitted_nem and not missing:
        st.session_state.results_nem = calculate_result_nem(score)
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

    if st.button("Kaydet ve Bitir"):
        mizac, skorlar, yuzdeler = genel_mizac_hesapla(cevaplar)
        st.session_state.results_genel = mizac
        st.session_state.genel_yuzdeler = yuzdeler
        st.session_state.page = "Menu"; st.rerun()

elif st.session_state.page == "Rapor":
    tarih = datetime.now().strftime("%d.%m.%Y")
    st.markdown(f"## 📄 Analiz Sonuçları: {st.session_state.user_info.get('ad')}")
    
    # 1. ÇAKRA GRAFİĞİ (Geliştirilmiş)
    fig_cakra_html = ""
    if st.session_state.results_cakra:
        data = st.session_state.results_cakra
        cakra_names = list(data.keys())
        yavas_vals = [d['yavas_puan'] for d in data.values()]
        asiri_vals = [d['asiri_puan'] for d in data.values()]
        
        fig_cakra = go.Figure()
        
        # Barlar (Soft Renkler)
        fig_cakra.add_trace(go.Bar(x=cakra_names, y=yavas_vals, name='Blokaj/Yavaş', marker_color='#5DADE2', text=yavas_vals, textposition='auto'))
        fig_cakra.add_trace(go.Bar(x=cakra_names, y=asiri_vals, name='Aşırı Aktif', marker_color='#EC7063', text=asiri_vals, textposition='auto'))
        
        # YEŞİL BANT (20-25 Puan)
        fig_cakra.add_shape(type="rect", x0=-0.5, x1=len(cakra_names)-0.5, y0=20, y1=25, fillcolor="Green", opacity=0.15, layer="below", line_width=0)
        
        # KIRMIZI EŞİK (30 Puan)
        fig_cakra.add_shape(type="line", x0=-0.5, x1=len(cakra_names)-0.5, y0=30, y1=30, line=dict(color="red", width=2, dash="dot"))
        
        # Annotations (Açıklamalar)
        fig_cakra.add_annotation(x=len(cakra_names)-1, y=22.5, text="DENGELİ (20-25)", showarrow=False, font=dict(size=10, color="green"), xanchor="right")
        fig_cakra.add_annotation(x=len(cakra_names)-1, y=31, text="KRİTİK (30+)", showarrow=False, font=dict(size=10, color="red"), xanchor="right")
        
        fig_cakra.update_layout(barmode='group', title="Çakra Enerji Dengesi Analizi", height=450, margin=dict(t=50, b=50, l=40, r=40), plot_bgcolor='rgba(0,0,0,0)', yaxis=dict(showgrid=True, gridcolor='lightgray', range=[0, 45]))
        
        fig_cakra_html = fig_cakra.to_html(full_html=False, include_plotlyjs='cdn')
        st.plotly_chart(fig_cakra, use_container_width=True)
        
        # Tablo
        df_cakra = pd.DataFrame.from_dict(data, orient='index')
        st.markdown("### Çakra Durum Tablosu")
        st.dataframe(df_cakra, use_container_width=True)

    # 2. MİZAÇ GRAFİKLERİ
    fig1_html, fig2_html = "", ""
    if st.session_state.results_genel:
        yuzdeler = st.session_state.genel_yuzdeler
        
        # Eksen Sıralaması (NEM=Üst, SOĞUK=Sağ)
        ordered_cats = ["SOĞUKLUK", "NEMLİLİK", "SICAKLIK", "KURULUK"]
        ordered_vals = [yuzdeler.get(k, 0) for k in ordered_cats]
        
        # Bar Grafik
        fig1 = go.Figure(go.Bar(x=ordered_cats, y=ordered_vals, marker_color=['#3498DB', '#2ECC71', '#E74C3C', '#F1C40F']))
        fig1.update_layout(height=300, margin=dict(t=10, b=20, l=20, r=20))
        fig1_html = fig1.to_html(full_html=False, include_plotlyjs='cdn')
        st.plotly_chart(fig1, use_container_width=True)
        
        # Radar Grafik
        radar_cats = ordered_cats + [ordered_cats[0]]
        radar_vals = ordered_vals + [ordered_vals[0]]
        fig2 = go.Figure(go.Scatterpolar(r=radar_vals, theta=radar_cats, fill='toself', line=dict(color='#8E44AD', width=3)))
        fig2.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=350, margin=dict(t=40, b=40, l=60, r=60))
        fig2_html = fig2.to_html(full_html=False, include_plotlyjs='cdn')
        
        st.info(f"Baskın Mizaç: **{st.session_state.results_genel}**")
        
    # RAPOR İNDİRME
    if st.session_state.results_genel or st.session_state.results_cakra:
        detaylar = MIZAC_BILGILERI.get(st.session_state.results_genel, {}) if st.session_state.results_genel else {}
        mizac_adi = st.session_state.results_genel if st.session_state.results_genel else None
        
        report_html = create_html_report(st.session_state.user_info, mizac_adi, detaylar, tarih, fig1_html, fig2_html, fig_cakra_html, st.session_state.results_cakra)
        st.download_button("📥 Raporu İndir", data=report_html, file_name="Analiz.html", mime="text/html", type="primary", use_container_width=True)
    
    if st.button("Menüye Dön"): st.session_state.page = "Menu"; st.rerun()
