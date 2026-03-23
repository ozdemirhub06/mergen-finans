import streamlit as st
import psycopg2
from psycopg2 import pool
from psycopg2 import IntegrityError
import pandas as pd
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests 
import datetime
import warnings
import os
import time
import base64
import json


# --- 1. MİMARİ VE PROFESYONEL ARAYÜZ ---
# Logoyu sekme simgesi (favicon) ve uygulama ismi olarak ayarlıyoruz
try:
    st.set_page_config(
        page_title="Mergen Finans",
        page_icon="logo.ico", # KLASÖRDEKİ logo.ico DOSYASINI OKUR
        layout="wide",
        initial_sidebar_state="expanded"
    )
except:
    # Eğer logo.ico dosyası bulunamazsa, sistem hata vermesin diye varsayılan ayar:
    st.set_page_config(
        page_title="Mergen Finans",
        page_icon="M",
        layout="wide",
        initial_sidebar_state="expanded"
    )

st.markdown("""
    <style>
    /* --- 1. BEYAZ ALT ÇUBUĞU VE REKLAMLARI KÖKÜNDEN YOK ETME --- */
    footer, [data-testid="stFooter"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
    }
    .viewerBadge_container__1QSob, .viewerBadge_link__1S137, [class^="viewerBadge"] {
        display: none !important;
        opacity: 0 !important;
    }

    .stAppDeployButton {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    
    [data-testid="stHeader"] {
        background-color: #000000 !important; 
        border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important; 
        box-shadow: none !important;
    }
    
    [data-testid="stMetricValue"] {
        font-family: 'Consolas', 'Courier New', monospace;
        font-weight: 600;
        font-size: 1.8rem !important;
    }
    
    /* --- SİDEBAR MENÜ DÜZENLEMESİ (BUZLU CAM VE SIFIR SCROLL) --- */
    
    /* 1. KUSURSUZ BUZLU CAM (GLASSMORPHISM) SİDEBAR */
    
    /* Streamlit'in dış iskeletini tamamen şeffaf yapıp aradan çekiyoruz */
    [data-testid="stSidebar"] {
        background-color: transparent !important;
        border: none !important;
    }
    
    /* Bütün sihri iç astara uyguluyoruz (Streamlit asıl rengi buraya basar) */
    [data-testid="stSidebar"] > div:first-child {
        background: rgba(10, 10, 10, 0.45) !important; /* Saydam siber siyah */
        backdrop-filter: blur(25px) saturate(150%) !important; /* Yüksek blur ve ışık kırılması */
        -webkit-backdrop-filter: blur(25px) saturate(150%) !important; /* Safari/iOS desteği */
        border-right: 1px solid rgba(0, 255, 0, 0.15) !important;
        box-shadow: inset -2px 0px 15px rgba(0, 255, 0, 0.03) !important; /* Cama hafif siber parlama */
    }

    /* 2. SCROLL ÇUBUĞUNU (KAYDIRMAYI) YOK ET */
    [data-testid="stSidebar"] ::-webkit-scrollbar {
        display: none !important;
        width: 0px !important;
    }
    [data-testid="stSidebar"] * {
        -ms-overflow-style: none !important;
        scrollbar-width: none !important;
    }
    [data-testid="stSidebar"] img {
        border: 2px solid #00ff00 !important;
        padding: 4px !important;
        border-radius: 50% !important; 
        box-shadow: 0 0 15px rgba(0, 255, 0, 0.15) !important;
        aspect-ratio: 1 / 1 !important; /* Fotoğrafı kare formata zorlar */
        object-fit: cover !important; /* Fotoğrafı ezmeden çerçevenin içine oturtur */
    }
    }
    
    /* Sidebar'daki ayırıcı çizgileri (hr) hafif yeşil yapıyoruz */
    [data-testid="stSidebar"] hr {
        border-bottom: 1px solid rgba(0, 255, 0, 0.15) !important;
    }

    /* --- ANA MENÜ TASARIMI (SİBER BLOKLAR) --- */
    
    /* 1. Yuvarlak radio ikonlarını SIFIRLA (Daha keskin ve net seçici) */
    [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {
        display: none !important;
    }
    
    /* 2. Menü kutularının (label) DAHA İNCE tasarımı */
    [data-testid="stSidebar"] div[role="radiogroup"] label {
        background: rgba(20, 20, 20, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 6px !important; /* Köşeleri hafif kıstık */
        padding: 8px 12px !important; /* Yüksekliği daralttık (Eskisi çok genişti) */
        margin-bottom: 6px !important; /* Aralarındaki boşluğu daralttık */
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        display: block !important;
        width: 100% !important;
    }
    
    /* 3. Hover (Fareyle Üzerine Gelince) */
    [data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(0, 255, 0, 0.05) !important;
        border-color: rgba(0, 255, 0, 0.3) !important;
    }
    
    /* 4. SEÇİLİ OLAN MENÜ (Akıllı Seçici) */
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(90deg, rgba(0,255,0,0.15) 0%, rgba(0,0,0,0) 100%) !important;
        border-color: rgba(0, 255, 0, 0.3) !important;
        border-left: 3px solid #00ff00 !important; /* Çizgiyi de incelttik */
        box-shadow: inset 2px 0px 10px rgba(0,255,0,0.05) !important;
    }
    
    /* 5. Yazıların hizası ve rengi (Biraz küçültüldü) */
    [data-testid="stSidebar"] div[role="radiogroup"] label p {
        color: #888888 !important;
        font-size: 0.95rem !important; /* Yazıyı ufalttık ki zarif dursun */
        font-weight: 600 !important;
        margin: 0 !important;
    }
    
    /* 6. Seçili menünün yazısını parlat */
    [data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) p {
        color: #00ff00 !important;
        text-shadow: 0 0 8px rgba(0,255,0,0.4) !important;
    }
            
    /* --- SEKMELERİ (TABS) NEON YEŞİL YAPMA --- */
    .stTabs [data-baseweb="tab-list"] {gap: 24px;}
    .stTabs [data-baseweb="tab"] {padding-top: 10px; padding-bottom: 10px;}
    .stTabs [data-baseweb="tab"] [data-testid="stMarkdownContainer"] p {
        color: gray !important; /* Seçili olmayan sekmeler gri */
    }
    .stTabs div[aria-selected="true"] [data-testid="stMarkdownContainer"] p {
        color: #00ff00 !important; /* Seçili sekme yazısı Neon Yeşil */
        font-weight: bold;
    }
    .stTabs div[aria-selected="true"] {
        border-bottom-color: #00ff00 !important; /* Seçili sekme alt çizgisi Neon Yeşil */
    }
    
    /* --- BİRİNCİL (PRIMARY) BUTONLARI NEON YEŞİL YAPMA --- */
    button[kind="primary"] {
        background-color: #00ff00 !important;
        color: #000000 !important; /* Siyah yazı */
        border: none !important;
        font-weight: bold !important;
    }
    button[kind="primary"]:hover {
        background-color: #00cc00 !important; /* Hover rengi (Koyu Yeşil) */
        color: #000000 !important;
    }
    
    .st-expander {border: 1px solid rgba(255,255,255,0.05) !important; border-radius: 4px !important;}
            /* --- İNATÇI BEYAZ YAZILARI ZORLA SİYAH YAP (FORM BUTONLARI DAHİL) --- */
    button[kind="primary"] p,
    button[kind="primary"] span,
    button[kind="primaryFormSubmit"] p,
    button[kind="primaryFormSubmit"] span,
    [data-testid="baseButton-primary"] p,
    [data-testid="baseButton-primary"] span {
        color: #000000 !important;
        font-weight: 600 !important;
    }

    /* --- BAŞLIKLARIN YANINDAKİ ZİNCİR (LİNK) İKONUNU GİZLE --- */
    h1 a, h2 a, h3 a, h4 a, h5 a, h6 a, a.header-anchor { display: none !important; }
    
    /* --- SİSTEM ASİSTANI (HAREKETLİ LOGO VE PARTİKÜLLER) --- */
    div[data-testid="stElementContainer"]:has(#asistan-marker) { display: none !important; }
    div[data-testid="stElementContainer"]:has(#asistan-marker) + div[data-testid="stElementContainer"] button {
        position: fixed !important; bottom: 30px !important; right: 30px !important;
        width: 70px !important; height: 70px !important; border-radius: 50% !important;
        background: transparent !important; border: none !important; box-shadow: none !important; 
        z-index: 99999 !important; transition: all 0.3s ease !important; 
        animation: float-logo 4s ease-in-out infinite !important;
        display: flex !important; align-items: center !important; justify-content: center !important; padding: 0 !important;
        overflow: visible !important;
    }
    div[data-testid="stElementContainer"]:has(#asistan-marker) + div[data-testid="stElementContainer"] button p { 
        color: transparent !important; position: relative; margin: 0 !important; z-index: -1 !important; 
    }
    div[data-testid="stElementContainer"]:has(#asistan-marker) + div[data-testid="stElementContainer"] button:hover { 
        transform: scale(1.1) translateY(-5px) !important; filter: brightness(1.2);
    }
    
    /* PARTİKÜL EFEKTİ */
    div[data-testid="stElementContainer"]:has(#asistan-marker) + div[data-testid="stElementContainer"] button::after {
        content: ''; position: absolute; top: 50%; left: 50%; width: 10px; height: 10px;
        background: transparent; border-radius: 50%; z-index: -1;
        animation: green-particles 3s ease-out infinite; pointer-events: none;
    }

    @keyframes float-logo { 
        0% { transform: translateY(0px); filter: drop-shadow(0 0 5px rgba(0,255,0,0.3)); } 
        50% { transform: translateY(-10px); filter: drop-shadow(0 0 15px rgba(0,255,0,0.6)); } 
        100% { transform: translateY(0px); filter: drop-shadow(0 0 5px rgba(0,255,0,0.3)); } 
    }
    @keyframes green-particles {
        0% { box-shadow: 0 0 0 transparent, 0 0 0 transparent, 0 0 0 transparent; }
        50% { box-shadow: -20px -30px 4px rgba(0,255,0,0.5), 30px -10px 6px rgba(0,255,0,0.4), -10px 30px 4px rgba(0,255,0,0.6); }
        100% { box-shadow: -40px -60px 0 transparent, 60px -20px 0 transparent, -20px 60px 0 transparent; }
    }
    @keyframes slide-in { from { opacity: 0; transform: translateX(20px); } to { opacity: 1; transform: translateX(0); } }

    /* ==================================================================== */
    /* --- YÜKLEME (SPINNER) EKRANI KESİN VE TEK ÇÖZÜMÜ (TEMİZLENDİ) --- */
    /* ==================================================================== */

    /* 1. Metin İçi Küçük Yükleme Çarkları (Veri Hesaplanıyor vs.) */
    div[data-testid="stSpinner"] div[class*="spinner"] {
        border-width: 4px !important;
        border-color: rgba(0, 255, 0, 0.1) !important;
        border-top-color: #00FF00 !important;
        border-left-color: rgba(0, 255, 0, 0.2) !important;
    }
    div[data-testid="stSpinner"] div[class*="stMarkdown"] p,
    div[data-testid="stSpinner"] span,
    [data-testid="stSpinner"] p {
        color: #00FF00 !important;
        font-family: 'Consolas', monospace !important;
        font-weight: bold !important;
        text-shadow: 0 0 8px rgba(0, 255, 0, 0.5) !important;
    }

    /* 2. Sağ Üstteki Koşan Adamı İptal Edip, Merkeze Dev Neon Halka Ekleme */
    [data-testid="stStatusWidget"] {
        visibility: hidden !important; /* Ekranı bozmaması için sadece gizliyoruz, tamamen yok etmiyoruz ki ::after çalışsın */
    }
    [data-testid="stStatusWidget"]::after {
        content: "";
        visibility: visible !important;
        position: fixed;
        top: 50%;
        left: 50%;
        width: 50px;
        height: 50px;
        border: 4px solid rgba(0, 255, 0, 0.1);
        border-left-color: #00ff00;
        border-radius: 50%;
        animation: siber-spin 0.8s linear infinite;
        z-index: 99999;
        box-shadow: 0 0 15px rgba(0, 255, 0, 0.3);
    }
    @keyframes siber-spin {
        0% { transform: translate(-50%, -50%) rotate(0deg); }
        100% { transform: translate(-50%, -50%) rotate(360deg); }
    }
           /* --- SİDEBAR BUTONU (YALIN VE SIFIR HATA) --- */
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    [data-testid="stHeader"] button {
        background-color: rgba(0, 255, 0, 0.05) !important;
        border: 1px solid rgba(0, 255, 0, 0.3) !important;
        border-radius: 6px !important;
        margin-top: 10px !important;
        margin-left: 10px !important;
    }
    [data-testid="stHeader"] button:hover {
        background-color: rgba(0, 255, 0, 0.2) !important;
    }
    [data-testid="stHeader"] svg {
        fill: #00ff00 !important;
        color: #00ff00 !important;
    }
</style>
               
""", unsafe_allow_html=True)

warnings.filterwarnings("ignore")

# --- STREAMLIT REKLAM VE BUTONLARINI YOK EDEN JS SUİKASTÇISI ---
import streamlit.components.v1 as components
components.html(
    """
    <script>
        const doc = window.parent.document;
        const hideStreamlitJunk = () => {
            // İnatçı butonların ve reklamların tüm kimliklerini hedefliyoruz
            const elements = doc.querySelectorAll('[data-testid="stAppDeployButton"], .stAppDeployButton, [data-testid="manage-app-button"], [data-testid="stToolbar"], a[href*="streamlit.io"], div[class^="viewerBadge"]');
            elements.forEach(el => {
                el.style.display = 'none';
                el.style.visibility = 'hidden';
                el.style.opacity = '0';
            });
        };
        // Sayfa açılır açılmaz vur
        hideStreamlitJunk();
        // Streamlit inat edip sonradan yüklerse diye her yarım saniyede bir kafasına vurmaya devam et
        setInterval(hideStreamlitJunk, 500);
    </script>
    """,
    height=0, width=0
)

# --- 2. VERİTABANI VE YARDIMCI MOTORLAR ---

@st.cache_resource
def init_pool():
    # Yeni Sunucu (Render) Uyumu
    db_url = os.environ.get("DB_URL", "")
    if not db_url:
        try: db_url = st.secrets["DB_URL"]
        except: pass
    return pool.ThreadedConnectionPool(1, 20, db_url)

def get_db():
    try:
        return init_pool().getconn()
    except Exception:
        db_url = os.environ.get("DB_URL", "")
        if not db_url:
            try: db_url = st.secrets["DB_URL"]
            except: pass
        return psycopg2.connect(db_url)

def release_db(conn):
    # Bağlantıyı öldürmüyoruz (close yapmıyoruz), diğer işlemler için havuza geri bırakıyoruz
    try:
        init_pool().putconn(conn)
    except:
        try: conn.close()
        except: pass

@st.dialog("Sistem Onayı")
def islem_onay_dialog(baslik, mesaj, basari_mesaji, sorgular):
    st.markdown(f"#### {baslik}")
    st.info(mesaj)
    st.write("Bu işlemi onaylıyor musunuz?")
    c1, c2 = st.columns(2)
    if c1.button("Onayla", type="primary", use_container_width=True):
        conn = get_db()
        try:
            c = conn.cursor()
            for s, p in sorgular: c.execute(s, p)
            conn.commit()
            if basari_mesaji: st.session_state.islem_bildirimi = {"mesaj": basari_mesaji}
        except Exception as e: st.error(f"Sistem Hatası: {e}")
        finally: release_db(conn)
        st.rerun()
    if c2.button("İptal", use_container_width=True): st.rerun()


# --- KULLANICI BİLGİLERİ PANELİ STİLLERİ ---
# --- KULLANICI BİLGİLERİ PANELİ STİLLERİ ---
def apply_card_style():
    st.markdown("""
        <style>
        .bilgi-karti {
            padding: 15px; 
            border-radius: 6px;
            background: rgba(15, 15, 15, 0.95);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-left: 3px solid #00ff00;
            margin-bottom: 10px; 
        }
        .kart-baslik { color: #00ff00; margin-top: 0; margin-bottom: 10px; font-family: Consolas, monospace; font-size: 0.9em; font-weight: bold; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px; text-transform: uppercase;}
        .kart-veri { color: white; font-weight: bold; font-size: 1.1em; font-family: Consolas, monospace; }
        .kart-etiket { color: gray; font-size: 0.8em; font-family: Consolas, monospace; }
        .analiz-metni { color: #d0d0d0; font-size: 0.85em; line-height: 1.5; font-family: Consolas, monospace; }
        .hedef-bar-bg { width: 100%; background: rgba(255,255,255,0.1); border-radius: 4px; height: 8px; margin-top: 5px; }
        .hedef-bar-fg { background: #00ff00; height: 100%; border-radius: 4px; box-shadow: 0 0 8px rgba(0,255,0,0.5); }
        </style>
    """, unsafe_allow_html=True)

@st.dialog("Kullanıcı Bilgileri", width="large")
def kullanici_bilgileri_sayfasi(k_adi):
    apply_card_style()
    k_bilgi = kullanici_bilgileri_getir(k_adi)
    
    if f'guncelle_mod_{k_adi}' not in st.session_state:
        st.session_state[f'guncelle_mod_{k_adi}'] = False

    # =======================================================
    # GÜNCELLEME MODU
    # =======================================================
    if st.session_state[f'guncelle_mod_{k_adi}']:
        st.markdown("<div class='kart-baslik'>BİLGİLERİ GÜNCELLE</div>", unsafe_allow_html=True)
        yeni_isim = st.text_input("Ad Soyad", value=k_bilgi['isim_soyisim'] if k_bilgi['isim_soyisim'] else "")
        yeni_foto = st.file_uploader("Profil Görseli (Değiştirmeyecekseniz boş bırakın)", type=["png", "jpg", "jpeg"])
        
        c1, c2 = st.columns(2)
        yeni_yas = c1.number_input("Yaşınız", value=st.session_state.get(f'{k_adi}_yas', 30), min_value=18, max_value=100)
        yeni_meslek = c2.text_input("Mesleğiniz", value=st.session_state.get(f'{k_adi}_meslek', "Belirtilmemiş"))
        yeni_gelir = st.number_input("Aylık Gelir (TL)", value=float(st.session_state.get(f'{k_adi}_gelir', 0.0)), step=1000.0)
        
        st.markdown("<div class='kart-baslik' style='margin-top: 10px;'>HEDEF BİLGİLERİ</div>", unsafe_allow_html=True)
        yeni_hedef_adi = st.text_input("Hedefiniz (Örn: Ev Peşinatı)", value=st.session_state.get(f'{k_adi}_hedef_adi', "Belirlenmedi"))
        yeni_hedef_tutar = st.number_input("Hedeflenen Tutar (TL)", value=float(st.session_state.get(f'{k_adi}_hedef_tutar', 100000.0)), step=10000.0)
        
        st.markdown("<div class='kart-baslik' style='margin-top: 10px;'>ŞİFRE DEĞİŞİKLİĞİ</div>", unsafe_allow_html=True)
        y_eski_sifre = st.text_input("Mevcut Şifre", type="password")
        y_yeni_sifre = st.text_input("Yeni Şifre", type="password")
        
        cb1, cb2 = st.columns(2)
        if cb1.button("İptal", use_container_width=True):
            st.session_state[f'guncelle_mod_{k_adi}'] = False
            st.rerun()
            
        if cb2.button("Kaydet", type="primary", use_container_width=True):
            conn = get_db()
            try:
                c = conn.cursor()
                if y_eski_sifre and y_yeni_sifre:
                    c.execute("SELECT sifre FROM kullanicilar WHERE kullanici_adi = %s", (k_adi,))
                    mevcut_sifre = c.fetchone()[0]
                    if y_eski_sifre != mevcut_sifre: st.error("Mevcut şifreniz yanlış."); st.stop()
                    else: c.execute("UPDATE kullanicilar SET sifre = %s WHERE kullanici_adi = %s", (y_yeni_sifre, k_adi))
                
                if yeni_foto is not None:
                    b64 = base64.b64encode(yeni_foto.getvalue()).decode()
                    c.execute("UPDATE kullanicilar SET isim_soyisim = %s, profil_fotosu = %s WHERE kullanici_adi = %s", (yeni_isim, b64, k_adi))
                else:
                    c.execute("UPDATE kullanicilar SET isim_soyisim = %s WHERE kullanici_adi = %s", (yeni_isim, k_adi))
                conn.commit()
                st.session_state[f'{k_adi}_yas'], st.session_state[f'{k_adi}_meslek'], st.session_state[f'{k_adi}_gelir'] = yeni_yas, yeni_meslek, yeni_gelir
                st.session_state[f'{k_adi}_hedef_adi'], st.session_state[f'{k_adi}_hedef_tutar'] = yeni_hedef_adi, yeni_hedef_tutar
                st.session_state[f'guncelle_mod_{k_adi}'] = False
                st.rerun()
            except Exception as e: st.error(f"Hata: {e}")
            finally: release_db(conn)

    # =======================================================
    # BİLGİ VE ANALİZ MODU
    # =======================================================
    else:
        with st.spinner("Verileriniz hesaplanıyor..."):
            conn = get_db()
            try:
                c = conn.cursor()
                # Nakit
                c.execute("SELECT SUM(bakiye) FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (k_adi,))
                nakit_yatirim = c.fetchone()[0] or 0.0
                c.execute("SELECT SUM(bakiye) FROM banka_hesaplari WHERE kullanici_adi = %s AND hesap_turu = 'Vadesiz'", (k_adi,))
                nakit_vadesiz = c.fetchone()[0] or 0.0
                c.execute("SELECT SUM(bakiye) FROM banka_hesaplari WHERE kullanici_adi = %s AND hesap_turu = 'Vadeli'", (k_adi,))
                nakit_vadeli = c.fetchone()[0] or 0.0

                # Varlıklar
                c.execute('SELECT varlik_adi, borsa, SUM(lot), AVG(maliyet) FROM portfoy WHERE kullanici_adi = %s GROUP BY varlik_adi, borsa HAVING SUM(lot) > 0', (k_adi,))
                aktif_portfoy = c.fetchall()
                c.execute("SELECT maden_turu, SUM(miktar), AVG(ortalama_maliyet) FROM emtia_portfoy WHERE kullanici_adi = %s GROUP BY maden_turu HAVING SUM(miktar) > 0", (k_adi,))
                aktif_emtia = c.fetchall()

                # Kar/Zarar Geçmişi
                c.execute("""
                    SELECT SUM(CASE WHEN lot < 0 THEN ABS(lot) * maliyet ELSE 0 END) - SUM(CASE WHEN lot > 0 THEN lot * maliyet ELSE 0 END)
                    FROM portfoy WHERE kullanici_adi = %s GROUP BY varlik_adi, borsa HAVING ABS(SUM(lot)) <= 0.0001 AND COUNT(lot) > 1
                """, (k_adi,))
                kapananlar = c.fetchall()
                realize_kar = sum([x[0] for x in kapananlar]) if kapananlar else 0.0
                c.execute("SELECT SUM(tutar) FROM islem_gecmisi WHERE kullanici_adi = %s AND islem_tipi = 'FAİZ GETİRİSİ (+)'", (k_adi,))
                toplam_faiz = c.fetchone()[0] or 0.0
                c.execute("SELECT SUM(tutar) FROM islem_gecmisi WHERE kullanici_adi = %s AND islem_tipi = 'STOPAJ VERGİSİ (-)'", (k_adi,))
                toplam_stopaj = c.fetchone()[0] or 0.0
                c.execute("SELECT SUM(tutar) FROM islem_gecmisi WHERE kullanici_adi = %s AND islem_tipi = 'KOMİSYON GİDERİ (-)'", (k_adi,))
                toplam_komisyon = c.fetchone()[0] or 0.0
            finally: release_db(conn)

            usd_kur, eur_kur = doviz_kuru_cek("USD"), doviz_kuru_cek("EUR")
            guncel_hisse_degeri, maliyet_hisse = 0.0, 0.0
            hisse_dagilim = {}
            for varlik, borsa, lot, maliyet in aktif_portfoy:
                fiyat = tefas_fiyat_cek(varlik) if borsa == "FON (TEFAS)" else hizli_fiyat_cek(varlik)[0]
                if not fiyat: fiyat = maliyet
                carpan = usd_kur if borsa in ["NASDAQ", "S&P 500", "KRİPTO", "EMTİA", "ETF"] or "-USD" in varlik else 1.0
                carpan = eur_kur if "EUR" in borsa or ".DE" in varlik else carpan
                deger = fiyat * float(lot) * carpan
                guncel_hisse_degeri += deger
                maliyet_hisse += (float(maliyet) * float(lot) * carpan)
                hisse_dagilim[borsa] = hisse_dagilim.get(borsa, 0.0) + deger

            guncel_emtia_degeri, maliyet_emtia = 0.0, 0.0
            for maden, miktar, ort_maliyet in aktif_emtia:
                fiyat = emtia_fiyat_hesapla(maden, usd_kur)
                if not fiyat: fiyat = ort_maliyet
                guncel_emtia_degeri += (float(miktar) * fiyat)
                maliyet_emtia += (float(miktar) * float(ort_maliyet))

            toplam_nakit = nakit_yatirim + nakit_vadesiz + nakit_vadeli
            toplam_varlik = guncel_hisse_degeri + guncel_emtia_degeri + toplam_nakit
            
            unrealize_kar = (guncel_hisse_degeri - maliyet_hisse) + (guncel_emtia_degeri - maliyet_emtia)
            net_kazanc = unrealize_kar + realize_kar + toplam_faiz + toplam_stopaj + toplam_komisyon
            toplam_maliyet_baz = maliyet_hisse + maliyet_emtia
            kazanc_orani = (net_kazanc / toplam_maliyet_baz) * 100 if toplam_maliyet_baz > 0 else 0.0

            oran_hisse = (guncel_hisse_degeri / toplam_varlik * 100) if toplam_varlik > 0 else 0
            oran_emtia = (guncel_emtia_degeri / toplam_varlik * 100) if toplam_varlik > 0 else 0
            oran_vadeli = (nakit_vadeli / toplam_varlik * 100) if toplam_varlik > 0 else 0
            oran_nakit = ((nakit_yatirim + nakit_vadesiz) / toplam_varlik * 100) if toplam_varlik > 0 else 0

        yas = st.session_state.get(f'{k_adi}_yas', 30)
        meslek = st.session_state.get(f'{k_adi}_meslek', 'Belirtilmemiş')
        gelir = st.session_state.get(f'{k_adi}_gelir', 0.0)
        hedef_adi = st.session_state.get(f'{k_adi}_hedef_adi', 'Hedef Belirlenmedi')
        hedef_tutar = st.session_state.get(f'{k_adi}_hedef_tutar', 100000.0)
        
        # HTML Genişlik hatasını önlemek için güvenli oranlama
        oran_ham = (toplam_varlik / hedef_tutar) * 100 if hedef_tutar > 0 else 0
        tamamlanma = min(max(oran_ham, 0), 100)

        # 1. SATIR: PROFİL BİLGİLERİ
        c_profil, c_bilgi = st.columns([1, 4])
        with c_profil:
            bas_harf = k_bilgi['isim_soyisim'][0].upper() if k_bilgi['isim_soyisim'] else "U"
            if k_bilgi['profil_fotosu']:
                try: st.markdown(f"<img src='data:image/png;base64,{k_bilgi['profil_fotosu']}' style='width: 90px; height: 90px; border-radius: 50%; object-fit: cover; border: 2px solid #00ff00; padding: 3px;'>", unsafe_allow_html=True)
                except: st.markdown(f"<div style='width: 90px; height: 90px; border: 2px solid #00ff00; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #00ff00; font-size: 2em; font-family: Consolas;'>{bas_harf}</div>", unsafe_allow_html=True)
            else: st.markdown(f"<div style='width: 90px; height: 90px; border: 2px solid #00ff00; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #00ff00; font-size: 2em; font-family: Consolas;'>{bas_harf}</div>", unsafe_allow_html=True)
        
        with c_bilgi:
            isim = k_bilgi['isim_soyisim'] if k_bilgi['isim_soyisim'] else "Kullanıcı"
            st.markdown(f"<div style='font-size: 1.5em; font-weight: bold; color: white; font-family: Consolas;'>{isim}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='color: gray; font-size: 0.85em; font-family: Consolas; margin-bottom: 5px;'>@{k_adi} | Yaş: {yas} | {meslek}</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='color: #00ff00; font-family: Consolas;'>Aylık Gelir: {gelir:,.0f} TL</div>", unsafe_allow_html=True)

        st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 10px 0;'>", unsafe_allow_html=True)

        # 2. SATIR: HEDEF VE DAVRANIŞ
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown(f"""
            <div class='bilgi-karti'>
                <div class='kart-baslik'>BİRİKİM HEDEFİ: {hedef_adi}</div>
                <div style='display: flex; justify-content: space-between;'>
                    <div><div class='kart-etiket'>Mevcut</div><div class='kart-veri' style='color:#00ff00;'>{toplam_varlik:,.0f} ₺</div></div>
                    <div style='text-align:right;'><div class='kart-etiket'>Hedef</div><div class='kart-veri'>{hedef_tutar:,.0f} ₺</div></div>
                </div>
                <div style='margin-top:10px;'>
                    <div style='display:flex; justify-content:space-between; font-size:0.8em; color:gray;'><span>İlerleme</span><span>%{tamamlanma:.1f}</span></div>
                    <div class='hedef-bar-bg'><div class='hedef-bar-fg' style='width: {int(tamamlanma)}%;'></div></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            profil = "Defansif" if (oran_vadeli + oran_nakit) > 60 else ("Agresif" if oran_hisse > 60 else "Dengeli")
            analiz = f"<span style='color: white; font-weight: bold;'>Profil: {profil} Yatırımcı</span><br>"
            
            if oran_hisse > 0:
                analiz += f"• <span style='color:#00ff00;'>İyi Yapılanlar:</span> Borsa/Fon varlıkları tutuluyor.<br>"
            if oran_emtia < 5:
                analiz += f"• <span style='color:#FF5252;'>Dikkat:</span> Emtia (%{oran_emtia:.1f}) çok düşük, risk dağıtımı yetersiz.<br>"
            if net_kazanc < 0:
                analiz += f"• <span style='color:#00bcd4;'>Tavsiye:</span> Portföy zararda, maliyet düşürme fırsatları değerlendirilebilir."
            else:
                analiz += f"• <span style='color:#00bcd4;'>Tavsiye:</span> Net kazanç pozitif, disiplinli yatırıma devam edin."

            st.markdown(f"""
            <div class='bilgi-karti'>
                <div class='kart-baslik'>YATIRIM DAVRANIŞI</div>
                <div class='analiz-metni'>{analiz}</div>
            </div>
            """, unsafe_allow_html=True)

        # 3. SATIR: GRAFİK VE PERFORMANS
        col3, col4 = st.columns([1.2, 1])
        with col3:
            st.markdown("<div class='bilgi-karti' style='padding-bottom:5px;'><div class='kart-baslik'>VARLIK DAĞILIMI</div>", unsafe_allow_html=True)
            
            c_graf, c_detay = st.columns([1, 1])
            with c_graf:
                dagilim = pd.DataFrame({'Varlık': ['Hisse/Fon', 'Vadeli', 'Emtia', 'Nakit'], 'Oran': [oran_hisse, oran_vadeli, oran_emtia, oran_nakit]})
                dagilim = dagilim[dagilim['Oran'] > 0]
                if not dagilim.empty:
                    import plotly.express as px
                    # Temaya uygun tamamen siber/neon yeşil tonları
                    siber_yesiller = ['#00ff00', '#00cc00', '#009900', '#006600']
                    
                    fig = px.pie(dagilim, values='Oran', names='Varlık', hole=0.6, color_discrete_sequence=siber_yesiller)
                    
                    # Yazılar dışarıda, kutulu ve çizgili
                    fig.update_traces(
                        textposition='outside', 
                        textinfo='label+percent', 
                        textfont=dict(color='white', size=10, family='Consolas'), 
                        marker=dict(line=dict(color='#101010', width=2))
                    )
                    
                    fig.update_layout(
                        height=180, 
                        margin=dict(t=15, b=15, l=15, r=15), 
                        paper_bgcolor="rgba(0,0,0,0)", 
                        plot_bgcolor="rgba(0,0,0,0)", 
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                else: st.info("Veri yok.")
            
            with c_detay:
                st.markdown("<div style='font-family: Consolas; font-size: 0.8em; color: gray; margin-top: 10px;'>Borsa/Fon Detayı:</div>", unsafe_allow_html=True)
                if hisse_dagilim:
                    for borsa, deger in hisse_dagilim.items():
                        oran = (deger / guncel_hisse_degeri) * 100 if guncel_hisse_degeri > 0 else 0
                        st.markdown(f"<div style='font-family: Consolas; font-size: 0.85em; color: white;'>- {borsa}: %{oran:.1f}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='font-family: Consolas; font-size: 0.85em; color: white;'>- Yok</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col4:
            r_renk = "#00ff00" if net_kazanc >= 0 else "#FF5252"
            r_is = "+" if net_kazanc >= 0 else ""
            st.markdown(f"""
            <div class='bilgi-karti' style='height: 195px;'>
                <div class='kart-baslik'>PERFORMANS</div>
                <div style='margin-bottom: 10px;'>
                    <div class='kart-etiket'>Net Kazanç (Kâr + Faiz - Giderler)</div>
                    <div class='kart-veri' style='color: {r_renk}; font-size: 1.4em;'>{r_is}{net_kazanc:,.0f} ₺</div>
                </div>
                <div>
                    <div class='kart-etiket'>Kazanç Oranı (ROI)</div>
                    <div class='kart-veri' style='color: {r_renk}; font-size: 1.2em;'>{r_is}%{kazanc_orani:.1f}</div>
                    <div style='color: gray; font-size: 0.7em; margin-top: 5px; font-family: Consolas;'>* Oran, toplam anapara maliyetine göre hesaplanmıştır.</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("BİLGİLERİ GÜNCELLE", type="primary", use_container_width=True):
            st.session_state[f'guncelle_mod_{k_adi}'] = True
            st.rerun()

def kutuphane_hazirla():
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS kullanicilar (kullanici_adi TEXT PRIMARY KEY, sifre TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS bakiyeler (kullanici_adi TEXT PRIMARY KEY, bakiye REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS portfoy (id SERIAL PRIMARY KEY, kullanici_adi TEXT, varlik_adi TEXT, lot REAL, maliyet REAL, borsa TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS islem_gecmisi (id SERIAL PRIMARY KEY, kullanici_adi TEXT, islem_tipi TEXT, detay TEXT, tutar REAL, tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS banka_hesaplari (id SERIAL PRIMARY KEY, kullanici_adi TEXT, banka_adi TEXT, hesap_adi TEXT, hesap_turu TEXT, bakiye REAL, faiz_orani REAL, stopaj_orani REAL, vade_gun INTEGER, acilis_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS kredi_kartlari (id SERIAL PRIMARY KEY, kullanici_adi TEXT, banka_adi TEXT, kart_adi TEXT, limit_tutari REAL, guncel_borc REAL, hesap_kesim_gunu INTEGER, son_odeme_gunu INTEGER)")
        c.execute("CREATE TABLE IF NOT EXISTS sabit_islemler (id SERIAL PRIMARY KEY, kullanici_adi TEXT, islem_turu TEXT, aciklama TEXT, tutar REAL, islem_gunu INTEGER, bagli_hesap TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS harcama_kategorileri (id SERIAL PRIMARY KEY, kullanici_adi TEXT, kategori_adi TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS harcamalar (id SERIAL PRIMARY KEY, kullanici_adi TEXT, kategori TEXT, aciklama TEXT, tutar REAL, kaynak_hesap TEXT, tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS hesaplar (kullanici_adi TEXT, hesap_adi TEXT, bakiye REAL, PRIMARY KEY(kullanici_adi, hesap_adi))")
        c.execute("CREATE TABLE IF NOT EXISTS emtia_portfoy (id SERIAL PRIMARY KEY, kullanici_adi TEXT, maden_turu TEXT, miktar REAL, ortalama_maliyet REAL, bagli_hesap TEXT, son_guncelleme TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS asistan_bildirimleri (id SERIAL PRIMARY KEY, kullanici_adi TEXT, baslik TEXT, mesaj TEXT, tur TEXT, tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP, okundu BOOLEAN DEFAULT FALSE)")
        c.execute("CREATE TABLE IF NOT EXISTS taksitli_islemler (id SERIAL PRIMARY KEY, kullanici_adi TEXT, kart_adi TEXT, aciklama TEXT, toplam_tutar REAL, aylik_tutar REAL, toplam_taksit INTEGER, odenen_taksit INTEGER DEFAULT 0, tarih TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        c.execute("CREATE TABLE IF NOT EXISTS davetiyeler (kod TEXT PRIMARY KEY, kullanim_hakki INTEGER DEFAULT 2)")
        c.execute("INSERT INTO davetiyeler (kod, kullanim_hakki) VALUES ('MERGEN_VIP_2026', 999) ON CONFLICT DO NOTHING")
        # --- TABLOYU GARANTİYE AL ---
        c.execute("CREATE TABLE IF NOT EXISTS davetiyeler (kod TEXT PRIMARY KEY, kullanim_hakki INTEGER DEFAULT 2)")
        c.execute("INSERT INTO davetiyeler (kod, kullanim_hakki) VALUES ('MERGEN_VIP_2026', 999) ON CONFLICT DO NOTHING")
        conn.commit()

        sorgular = [
            "ALTER TABLE portfoy ALTER COLUMN lot TYPE NUMERIC(20,10)",
            "ALTER TABLE banka_hesaplari ADD COLUMN tahakkuk_saati TEXT DEFAULT '00:00'",
            "ALTER TABLE kredi_kartlari ADD COLUMN kisisel_limit REAL DEFAULT 0.0",
            "ALTER TABLE sabit_islemler ADD COLUMN son_islenme_tarihi TEXT DEFAULT 'Yok'",
            "ALTER TABLE kullanicilar ADD COLUMN isim_soyisim TEXT DEFAULT ''",
            "ALTER TABLE kullanicilar ADD COLUMN profil_fotosu TEXT DEFAULT ''",
            "ALTER TABLE banka_hesaplari ADD COLUMN para_birimi TEXT DEFAULT 'TL'",
            "ALTER TABLE bakiyeler ADD COLUMN bakiye_usd REAL DEFAULT 0.0",
            "ALTER TABLE islem_gecmisi ADD COLUMN para_birimi TEXT DEFAULT 'TL'"
        ]
        for q in sorgular:
            try: c.execute(q); conn.commit()
            except psycopg2.Error: conn.rollback() 
            
        try:
            c.execute("UPDATE kredi_kartlari SET kisisel_limit = limit_tutari WHERE kisisel_limit = 0.0 OR kisisel_limit IS NULL")
            conn.commit()
        except psycopg2.Error: conn.rollback()
    finally: release_db(conn)


def kullanici_bilgileri_getir(k_adi):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT isim_soyisim, profil_fotosu FROM kullanicilar WHERE kullanici_adi = %s", (k_adi,))
        res = c.fetchone()
        return {"isim_soyisim": res[0], "profil_fotosu": res[1]} if res else {"isim_soyisim": "", "profil_fotosu": ""}
    except: return {"isim_soyisim": "", "profil_fotosu": ""}
    finally: release_db(conn)

def bakiye_getir(k_adi):
    conn = get_db()
    try:
        c = conn.cursor()
        
        # 1. MİMARİ DEVRİM: Çöp tabloyu bırak, tek gerçek kasadan nakdi al
        c.execute("SELECT bakiye FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (k_adi,))
        res = c.fetchone()
        nakit = res[0] if res else 0.0
        
        # 2. T+2 Takastaki asılı (avans) parayı hesapla
        c.execute("SELECT COALESCE(SUM(tutar), 0) FROM takas_bekleyen_islemler WHERE kullanici_adi = %s AND durum = 'Bekliyor' AND islem_yonu = 'SATIM'", (k_adi,))
        takas = c.fetchone()[0]
        
        # 3. İkisini toplayarak "Gerçek Alım Gücünü" cüzdana yansıt
        return nakit + takas
    except Exception:
        return 0.0
    finally: 
        release_db(conn)

@st.cache_data(ttl=600) 
def doviz_kuru_cek(birim):
    if birim == "TL": return 1.0
    try:
        if birim == "USD": return yf.Ticker("TRY=X").fast_info['last_price']
        if birim == "EUR": return yf.Ticker("EURTRY=X").fast_info['last_price']
        if birim == "GBP": return yf.Ticker("GBPTRY=X").fast_info['last_price']
    except:
        return {"USD": 33.5, "EUR": 36.5, "GBP": 42.5}.get(birim, 1.0)

@st.cache_data(ttl=60) 
def hizli_fiyat_cek(ticker):
    try:
        tick = yf.Ticker(ticker)
        
        # --- AMERİKAN BORSALARI İÇİN MİDAS USULÜ AFTER-HOURS MOTORU ---
        if ticker and not ticker.endswith(".IS") and not ticker.endswith("=F") and not ticker.endswith("-USD"):
            try:
                info = tick.info
                # Öncelik sırası: Kapanış Sonrası (After-Hours) -> Anlık Fiyat -> Normal Kapanış
                fiyat = info.get('postMarketPrice') or info.get('currentPrice') or info.get('regularMarketPrice')
                onceki_kapanis = info.get('previousClose')
                if fiyat:
                    return float(fiyat), float(onceki_kapanis) if onceki_kapanis else float(fiyat)
            except:
                pass # Yahoo API sapıtırsa alttaki standart motora geçer
        
        # --- BİST, KRİPTO, EMTİA İÇİN STANDART HIZLI MOTOR ---
        inf = tick.fast_info
        return float(inf['last_price']), float(inf['previous_close'])
    except: 
        return None, None
    

@st.cache_data(ttl=86400) 
def tefas_fiyat_cek(fon_kod):
    import urllib3; urllib3.disable_warnings() 
    # Sistemin bot gibi görünmemesi için gerçek tarayıcı kimliği
    basliklar = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    # 1. Deneme: TEFAS Ana Web Sitesi
    try:
        r = requests.get(f"https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fon_kod.upper()}", headers=basliklar, timeout=10, verify=False)
        if 'Son Fiyat (TL)' in r.text:
            fiyat_str = r.text.split('Son Fiyat (TL)')[1].split('<span>')[1].split('</span>')[0].strip()
            return float(fiyat_str.replace('.', '').replace(',', '.'))
    except: pass
    
    # 2. Deneme: Fonbul.com Yedek
    try:
        r = requests.get(f"https://www.fonbul.com/CokluArama/FonDetay?fonKod={fon_kod.upper()}", headers=basliklar, timeout=10, verify=False)
        if 'Son Fiyat' in r.text:
            fiyat_str = r.text.split('Son Fiyat')[1].split('</td>')[1].split('>')[-1].strip()
            return float(fiyat_str.replace('.', '').replace(',', '.'))
    except: pass
    
    # 3. Deneme: TEFAS Gizli API (En sağlamı)
    try:
        api_url = "https://www.tefas.gov.tr/api/DB/BindHistoryInfo"
        data = {
            "fontip": "YAT", "sfontur": "", "fonkod": fon_kod.upper(), "fongrup": "", 
            "bastarih": (datetime.date.today() - datetime.timedelta(days=7)).strftime("%d.%m.%Y"), 
            "bittarih": datetime.date.today().strftime("%d.%m.%Y")
        }
        r = requests.post(api_url, data=data, headers=basliklar, timeout=10, verify=False)
        json_data = r.json()
        if json_data and 'data' in json_data and len(json_data['data']) > 0:
            return float(json_data['data'][-1]['FIYAT'])
    except: pass
    
    return None

def t_arti_2_hesapla():
    bugun = datetime.date.today()
    eklenen_gun, hedef_tarih = 0, bugun
    while eklenen_gun < 2:
        hedef_tarih += datetime.timedelta(days=1)
        if hedef_tarih.weekday() < 5: eklenen_gun += 1
    return bugun, hedef_tarih

def fon_takas_tarihi_hesapla(base_valor):
    # KAYIT DEFTERİ MANTIĞI: Saat kuralı tamamen iptal edildi. Valör neyse o gün geçer!
    bugun = datetime.date.today()
    hedef_tarih = bugun
    # İşlemi hafta sonu giriyorsan otomatik pazartesiye atar
    if hedef_tarih.weekday() >= 5:
        while hedef_tarih.weekday() >= 5: hedef_tarih += datetime.timedelta(days=1)
    
    eklenen = 0
    while eklenen < base_valor:
        hedef_tarih += datetime.timedelta(days=1)
        if hedef_tarih.weekday() < 5: eklenen += 1
    return bugun, hedef_tarih

def asistan_motorunu_calistir(k_adi):
    # Kullanıcının sadece ilk ismini (veya kayıtlı değilse Yönetici adını) çekiyoruz
    k_bilgi = kullanici_bilgileri_getir(k_adi)
    isim = k_bilgi['isim_soyisim'].split()[0] if k_bilgi['isim_soyisim'] else "Yönetici"

    conn = get_db()
    try:
        c = conn.cursor()
        bugun = datetime.date.today()
        
        # 1. Kredi Kartı Ekstre Takibi
        c.execute("SELECT kart_adi, guncel_borc, hesap_kesim_gunu FROM kredi_kartlari WHERE kullanici_adi = %s AND guncel_borc > 0", (k_adi,))
        for k_adi_db, borc, kesim in c.fetchall():
            # Eğer kesim gününe 3 gün veya daha az kalmışsa
            kalan_gun = kesim - bugun.day
            if 0 <= kalan_gun <= 3:
                msg = f"{isim}, {k_adi_db} kredi kartınızın hesap kesim tarihine {kalan_gun} gün kalmıştır. Güncel borcunuz: {borc:,.2f} TL. Lütfen ödeme planınızı kontrol ediniz."
                # Aynı mesajı bugün zaten atmış mı diye kontrol et (Sürekli darlamasın)
                c.execute("SELECT id FROM asistan_bildirimleri WHERE kullanici_adi = %s AND mesaj = %s AND DATE(tarih) = CURRENT_DATE", (k_adi, msg))
                if not c.fetchone():
                    c.execute("INSERT INTO asistan_bildirimleri (kullanici_adi, baslik, mesaj, tur) VALUES (%s, 'Kredi Kartı Ekstre Bildirimi', %s, 'KART')", (k_adi, msg))
        conn.commit()
    except Exception as e: pass
    finally: release_db(conn)

# --- 3. OTOMATİK MOTORLAR ---
def gecmis_harcamalari_dekonta_aktar(k_adi):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT tarih, kategori, aciklama, tutar, kaynak_hesap FROM harcamalar WHERE kullanici_adi = %s", (k_adi,))
        for h_tarih, h_kategori, h_aciklama, h_tutar, h_kaynak in c.fetchall():
            temiz_hesap = h_kaynak.replace("🏦 ", "").replace("💳 ", "").replace("Hesaptan: ", "").replace("Karttan: ", "").replace("Hesap: ", "").replace("Kart: ", "").strip()
            dekont_notu = f"{temiz_hesap} - {h_kategori} Harcaması" + (f" ({h_aciklama})" if h_aciklama else "")
            c.execute("SELECT id FROM islem_gecmisi WHERE kullanici_adi = %s AND islem_tipi = 'HARCAMA (-)' AND tutar = %s AND tarih = %s", (k_adi, -h_tutar, h_tarih))
            if not c.fetchone():
                c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar, tarih) VALUES (%s, 'HARCAMA (-)', %s, %s, %s)", (k_adi, dekont_notu, -h_tutar, h_tarih))
        conn.commit()
    finally: release_db(conn)

def faiz_motorunu_calistir(k_adi):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT id, hesap_adi, bakiye, faiz_orani, stopaj_orani, vade_gun, acilis_tarihi, banka_adi, tahakkuk_saati FROM banka_hesaplari WHERE kullanici_adi = %s AND hesap_turu = 'Vadeli'", (k_adi,))
        for h_id, h_adi, bakiye, faiz, stopaj, vade, son_tarih_str, b_adi, t_saati in c.fetchall():
            try:
                t_saat, t_dakika = map(int, str(t_saati).split(':'))
                son_islem_ani = datetime.datetime.strptime(son_tarih_str.split('.')[0], '%Y-%m-%d %H:%M:%S') if isinstance(son_tarih_str, str) else son_tarih_str
                hedef_tahakkuk_ani = (son_islem_ani + datetime.timedelta(days=vade)).replace(hour=t_saat, minute=t_dakika, second=0, microsecond=0)
                simdi = datetime.datetime.now()
                if simdi >= hedef_tahakkuk_ani and vade > 0:
                    toplam_donem_sayisi = 1 + (simdi - hedef_tahakkuk_ani).days // vade
                    yeni_bakiye, toplam_brut, toplam_stopaj = bakiye, 0.0, 0.0
                    for _ in range(toplam_donem_sayisi):
                        # BANKACILIK KURALI: Her gün 2 haneli kesin yuvarlama yapılır
                        brut = round((yeni_bakiye * faiz / 100) / 365 * vade, 2)
                        kesilen = round(brut * (stopaj / 100), 2)
                        yeni_bakiye = round(yeni_bakiye + (brut - kesilen), 2)
                        toplam_brut += brut
                        toplam_stopaj += kesilen
                    
                    yeni_son_tarih = hedef_tahakkuk_ani + datetime.timedelta(days=(toplam_donem_sayisi - 1) * vade)
                    c.execute("UPDATE banka_hesaplari SET bakiye = %s, acilis_tarihi = %s WHERE id = %s", (yeni_bakiye, yeni_son_tarih.strftime('%Y-%m-%d %H:%M:%S'), h_id))
                    islenen_toplam_gun = toplam_donem_sayisi * vade
                    c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'FAİZ GETİRİSİ (+)', %s, %s)", (k_adi, f"{b_adi} - {h_adi} ({islenen_toplam_gun} Günlük)", toplam_brut))
                    if toplam_stopaj > 0:
                        c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'STOPAJ VERGİSİ (-)', %s, %s)", (k_adi, f"{b_adi} - {h_adi} (%{stopaj} Kesinti)", -toplam_stopaj))
            except: continue
        conn.commit()
    finally: release_db(conn)

def sabit_islemleri_islet(k_adi):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT id, islem_turu, aciklama, tutar, islem_gunu, bagli_hesap, son_islenme_tarihi FROM sabit_islemler WHERE kullanici_adi = %s", (k_adi,))
        bugun = datetime.date.today()
        guncel_damga = f"{bugun.year}-{bugun.month:02d}"
        for s_id, i_turu, aciklama, tutar, i_gunu, b_hesap, son_islem in c.fetchall():
            if bugun.day >= i_gunu and son_islem != guncel_damga:
                hesap_saf = b_hesap.split(" (")[0].replace("🏦 ", "").replace("💳 ", "").replace("💼 ", "").replace("Hesap: ", "").replace("Kart: ", "").replace("Yatırım: ", "")
                if "Gelir" in i_turu:
                    if "Yatırım Hesabı" in hesap_saf:
                        c.execute("UPDATE hesaplar SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (tutar, k_adi))
                        c.execute("UPDATE bakiyeler SET bakiye = bakiye + %s WHERE kullanici_adi = %s", (tutar, k_adi))
                    else:
                        c.execute("UPDATE banka_hesaplari SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = %s", (tutar, k_adi, hesap_saf))
                    c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'OTOMATİK GELİR', %s, %s)", (k_adi, aciklama, tutar))
                else: 
                    if "Kart" in b_hesap or "💳" in b_hesap: 
                        c.execute("UPDATE kredi_kartlari SET guncel_borc = guncel_borc + %s WHERE kullanici_adi = %s AND kart_adi = %s", (tutar, k_adi, hesap_saf))
                    else: 
                        c.execute("UPDATE banka_hesaplari SET bakiye = bakiye - %s WHERE kullanici_adi = %s AND hesap_adi = %s", (tutar, k_adi, hesap_saf))
                    c.execute("INSERT INTO harcamalar (kullanici_adi, kategori, aciklama, tutar, kaynak_hesap) VALUES (%s, 'Otomatik Ödeme', %s, %s, %s)", (k_adi, aciklama, tutar, hesap_saf))
                    c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'OTOMATİK GİDER', %s, %s)", (k_adi, aciklama, -tutar))
                c.execute("UPDATE sabit_islemler SET son_islenme_tarihi = %s WHERE id = %s", (guncel_damga, s_id))
                if 'islem_bildirimi' not in st.session_state:
                    st.session_state.islem_bildirimi = {"mesaj": f"Aylık döngü gerçekleşti: {aciklama} ({tutar} TL)"}
        conn.commit()
    finally: release_db(conn)

def takas_motorunu_calistir(k_adi):
    conn = get_db()
    try:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS takas_bekleyen_islemler 
                     (id SERIAL PRIMARY KEY, kullanici_adi TEXT, varlik TEXT, tutar REAL, 
                     islem_tarihi DATE, takas_tarihi DATE, durum TEXT DEFAULT 'Bekliyor')''')
        
        try: c.execute("ALTER TABLE takas_bekleyen_islemler ADD COLUMN islem_yonu TEXT DEFAULT 'SATIM'")
        except: conn.rollback()
        try: c.execute("ALTER TABLE takas_bekleyen_islemler ADD COLUMN lot REAL DEFAULT 0.0")
        except: conn.rollback()
        try: c.execute("ALTER TABLE takas_bekleyen_islemler ADD COLUMN maliyet REAL DEFAULT 0.0")
        except: conn.rollback()
        try: c.execute("ALTER TABLE takas_bekleyen_islemler ADD COLUMN borsa TEXT DEFAULT 'BİST'")
        except: conn.rollback()
        conn.commit()

        bugun = datetime.date.today()
        c.execute("SELECT id, varlik, tutar, islem_yonu, lot, maliyet, borsa FROM takas_bekleyen_islemler WHERE kullanici_adi = %s AND durum = 'Bekliyor' AND takas_tarihi <= %s", (k_adi, bugun))
        for t_id, t_varlik, t_tutar, t_yon, t_lot, t_maliyet, t_borsa in c.fetchall():
            if t_yon == 'SATIM':
                c.execute("UPDATE bakiyeler SET bakiye = bakiye + %s WHERE kullanici_adi = %s", (t_tutar, k_adi))
                c.execute("UPDATE hesaplar SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (t_tutar, k_adi))
                c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'TAKAS GERÇEKLEŞTİ', %s, %s)", (k_adi, f"{t_varlik} Takas İadesi", t_tutar))
            elif t_yon == 'ALIM':
                c.execute("INSERT INTO portfoy (kullanici_adi, varlik_adi, lot, maliyet, borsa) VALUES (%s,%s,%s,%s,%s)", (k_adi, t_varlik, t_lot, t_maliyet, t_borsa))
                c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'FON TAKASI GERÇEKLEŞTİ', %s, %s)", (k_adi, f"{t_lot} lot {t_varlik} portföye eklendi", 0.0))
            c.execute("UPDATE takas_bekleyen_islemler SET durum = 'Tamamlandi' WHERE id = %s", (t_id,))
        conn.commit()
    finally: release_db(conn)
@st.cache_data(ttl=120) 
def emtia_fiyat_hesapla(maden_turu, anlik_usd_kuru):
    try:
        if "Altın" in maden_turu: ons_usd = yf.Ticker("GC=F").fast_info['last_price']
        elif "Gümüş" in maden_turu: ons_usd = yf.Ticker("SI=F").fast_info['last_price']
        elif "Platin" in maden_turu: ons_usd = yf.Ticker("PL=F").fast_info['last_price']
        elif "Paladyum" in maden_turu: ons_usd = yf.Ticker("PA=F").fast_info['last_price']
        else: ons_usd = 0.0
        if not ons_usd: return 0.0
        if "Gram" in maden_turu: return (ons_usd / 31.1035) * anlik_usd_kuru
        return ons_usd * anlik_usd_kuru
    except: return 0.0

def doviz_islem_modulu(k_adi, sayfa_key):
    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-top: 10px; margin-bottom: 15px;'>", unsafe_allow_html=True)
    st.markdown("<div style='display: flex; align-items: center; margin-bottom: 15px;'><div style='width: 10px; height: 10px; background: #00bcd4; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 8px #00bcd4;'></div><div style='color: #00bcd4; font-size: 1.1em; font-weight: 700; letter-spacing: 1px; font-family: Consolas;'>DÖVİZ İŞLEM TERMİNALİ</div></div>", unsafe_allow_html=True)
    
    conn = get_db()
    try:
        df_tv = pd.read_sql_query("SELECT hesap_adi, bakiye, para_birimi FROM banka_hesaplari WHERE kullanici_adi = %s", conn, params=(k_adi,))
        c = conn.cursor()
        c.execute("SELECT hesap_adi, bakiye FROM hesaplar WHERE kullanici_adi = %s", (k_adi,))
        y_hesaplar = c.fetchall()
    finally: release_db(conn)
    
    hesap_listesi = [f"Hesap: {r['hesap_adi']} ({r['bakiye']:.2f} {r['para_birimi'] if r['para_birimi'] else 'TL'})" for _, r in df_tv.iterrows()]
    for yh in y_hesaplar: hesap_listesi.append(f"Yatırım: {yh[0]} ({yh[1]:.2f} {'USD' if '(USD)' in yh[0] else 'EUR' if '(EUR)' in yh[0] else 'TL'})")
    
    with st.container(border=True):
        st.markdown("<div style='background: rgba(0, 188, 212, 0.05); padding: 10px 15px; border-radius: 6px; border: 1px solid rgba(0, 188, 212, 0.2); margin-bottom: 20px; font-size: 0.85em; color: #e0e0e0;'>Döviz piyasasındaki anlık kur üzerinden alım satım ve arbitraj işlemlerinizi buradan yönetebilirsiniz.</div>", unsafe_allow_html=True)
        
        c_ust1, c_ust2 = st.columns(2)
        with c_ust1:
            st.markdown("<span style='color: gray; font-size: 0.85em;'>İşlem Yönü:</span>", unsafe_allow_html=True)
            d_islem = st.radio("İşlem Yönü", ["Döviz Al", "Döviz Bozdur (Sat)"], horizontal=True, key=f"d_islem_{sayfa_key}", label_visibility="collapsed")
            st.markdown("<span style='color: gray; font-size: 0.85em;'>Hedef Para Birimi:</span>", unsafe_allow_html=True)
            d_para_birimi = st.selectbox("Para Birimi", ["USD", "EUR", "GBP"], key=f"d_pb_{sayfa_key}", label_visibility="collapsed")
            
        canli_kur = doviz_kuru_cek(d_para_birimi)
        
        with c_ust2:
            st.markdown(f"""
            <div style='background: rgba(10,10,10,0.8); border-left: 4px solid #00bcd4; padding: 15px; border-radius: 6px; box-shadow: inset 0 0 15px rgba(0, 188, 212, 0.05); height: 100%; display: flex; flex-direction: column; justify-content: center;'>
                <div style='color: gray; font-size: 0.8em; text-transform: uppercase; margin-bottom: 5px; letter-spacing: 1px;'>CANLI PİYASA KURU</div>
                <div style='color: #00bcd4; font-size: 1.6em; font-weight: bold; font-family: Consolas;'>1 {d_para_birimi} = {canli_kur:,.4f} ₺</div>
            </div>
            """, unsafe_allow_html=True)
            
        with st.form(f"doviz_islem_formu_{sayfa_key}"):
            st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 5px 0 15px 0;'>", unsafe_allow_html=True)
            c_f1, c_f2 = st.columns(2)
            kullanici_kuru = c_f1.number_input("İşlem Kuru (Toleranslı)", value=float(canli_kur), step=0.01, format="%.4f")
            d_tutar = c_f2.number_input(f"İşlem Tutarı ({d_para_birimi})", min_value=1.0, step=100.0)
            
            st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 15px 0 15px 0;'>", unsafe_allow_html=True)
            c_h1, c_h2 = st.columns(2)
            if d_islem == "Döviz Al":
                cikis_hesabi = c_h1.selectbox("Ödeme Kaynağı (- TL)", [h for h in hesap_listesi if "TL" in h])
                giris_hesabi = c_h2.selectbox(f"Hedef Kasa (+ {d_para_birimi})", [h for h in hesap_listesi if d_para_birimi in h])
            else:
                cikis_hesabi = c_h1.selectbox(f"Satış Kaynağı (- {d_para_birimi})", [h for h in hesap_listesi if d_para_birimi in h])
                giris_hesabi = c_h2.selectbox("Hedef Kasa (+ TL)", [h for h in hesap_listesi if "TL" in h])
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("Döviz İşlemini Onayla", type="primary", use_container_width=True):
                if not cikis_hesabi or not giris_hesabi:
                    st.error(f"İşlem için uygun {d_para_birimi} veya TL hesabı bulunamadı. Lütfen 'Yeni Tanımlama' sekmesinden ilgili hesabı ekleyin.")
                else:
                    toplam_tl = d_tutar * kullanici_kuru
                    k_saf_cikis = cikis_hesabi.rsplit(" (", 1)[0].replace("Hesap: ", "").replace("Yatırım: ", "")
                    k_saf_giris = giris_hesabi.rsplit(" (", 1)[0].replace("Hesap: ", "").replace("Yatırım: ", "")
                    bakiye_cikis_str = cikis_hesabi.rsplit("(", 1)[1].replace(")", "").split(" ")[0]
                    bakiye_cikis = float(bakiye_cikis_str.replace(",", ""))
                    
                    if d_islem == "Döviz Al" and bakiye_cikis < toplam_tl:
                        st.error(f"Yetersiz Bakiye! {toplam_tl:,.2f} TL gerekiyor.")
                    elif d_islem == "Döviz Bozdur (Sat)" and bakiye_cikis < d_tutar:
                        st.error(f"Yetersiz Bakiye! {d_tutar:,.2f} {d_para_birimi} gerekiyor.")
                    else:
                        conn = get_db()
                        try:
                            c = conn.cursor()
                            cikis_duser = toplam_tl if d_islem == "Döviz Al" else d_tutar
                            giris_artar = d_tutar if d_islem == "Döviz Al" else toplam_tl
                            
                            # ÇIKIŞ
                            if "Yatırım:" in cikis_hesabi:
                                c.execute("UPDATE hesaplar SET bakiye = bakiye - %s WHERE kullanici_adi = %s AND hesap_adi = %s", (cikis_duser, k_adi, k_saf_cikis))
                                if "TL" in cikis_hesabi: c.execute("UPDATE bakiyeler SET bakiye = bakiye - %s WHERE kullanici_adi = %s", (cikis_duser, k_adi))
                            else:
                                c.execute("UPDATE banka_hesaplari SET bakiye = bakiye - %s WHERE kullanici_adi = %s AND hesap_adi = %s", (cikis_duser, k_adi, k_saf_cikis))
                                
                            # GİRİŞ
                            if "Yatırım:" in giris_hesabi:
                                c.execute("UPDATE hesaplar SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = %s", (giris_artar, k_adi, k_saf_giris))
                                if "TL" in giris_hesabi: c.execute("UPDATE bakiyeler SET bakiye = bakiye + %s WHERE kullanici_adi = %s", (giris_artar, k_adi))
                            else:
                                c.execute("UPDATE banka_hesaplari SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = %s", (giris_artar, k_adi, k_saf_giris))
                            
                            d_not = f"{d_tutar:,.2f} {d_para_birimi} Alındı (Kur: {kullanici_kuru:.4f})" if d_islem == "Döviz Al" else f"{d_tutar:,.2f} {d_para_birimi} Satıldı (Kur: {kullanici_kuru:.4f})"
                            t_etkisi = -toplam_tl if d_islem == "Döviz Al" else toplam_tl
                            c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, %s, %s, %s)", (k_adi, 'DÖVİZ İŞLEMİ', d_not, t_etkisi))
                            
                            conn.commit()
                            st.success("İşlem başarıyla gerçekleşti ve bakiyelere yansıtıldı!")
                            time.sleep(1.5)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Sistem Hatası: {e}")
                        finally:
                            release_db(conn)
# --- 4. GİRİŞ VE SİSTEM DÖNGÜSÜ ---
def akilli_hisse_analiz_motoru(key_prefix):
    with st.container(border=True):
        st.markdown("<div style='display: flex; align-items: center; margin-bottom: 15px;'><div style='width: 10px; height: 10px; background: #00ff00; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 8px #00ff00;'></div><div style='color: #00ff00; font-size: 1.1em; font-weight: 700; letter-spacing: 1px; font-family: Consolas;'>QUANT ANALİZ RADARI</div></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([1, 1.5, 1])
        # WIDGET KEY'LERİ DEĞİŞTİRİLDİ (ÇAKIŞMA HATASI GİDERİLDİ)
        secili_borsa = c1.selectbox("Piyasa", ["BİST", "NASDAQ", "KRİPTO"], key=f"q_ui_borsa_{key_prefix}", label_visibility="collapsed")
        hisse_kodu = c2.text_input("Varlık Kodu", key=f"q_ui_kod_{key_prefix}", placeholder="Örn: THYAO", label_visibility="collapsed").upper()
        
        if c3.button("ANALİZ ET", key=f"q_btn_{key_prefix}", type="primary", use_container_width=True):
            if hisse_kodu:
                # KAYIT KEY'LERİ FARKLI İSİMLENDİRİLDİ
                st.session_state[f'kayitli_hisse_{key_prefix}'] = hisse_kodu.strip()
                st.session_state[f'kayitli_borsa_{key_prefix}'] = secili_borsa
            else: st.warning("Kod giriniz.")

        if st.session_state.get(f'kayitli_hisse_{key_prefix}'):
            t_kod = st.session_state[f'kayitli_hisse_{key_prefix}']
            s_borsa = st.session_state[f'kayitli_borsa_{key_prefix}']
            
            c_kapat, _ = st.columns([1, 4])
            if c_kapat.button("✖ Aramayı Kapat", key=f"q_kapat_{key_prefix}"):
                st.session_state.pop(f'kayitli_hisse_{key_prefix}', None)
                st.rerun()
                
            st.markdown("<hr style='border-color: rgba(0,255,0,0.1); margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
            
            if s_borsa == "BİST" and not t_kod.endswith(".IS"): t_kod += ".IS"
            elif s_borsa == "KRİPTO" and not t_kod.endswith("-USD"): t_kod += "-USD"
            
            with st.spinner("Model işleniyor..."):
                try:
                    df_raw = yf.Ticker(t_kod).history(period="1y", interval="1d").dropna(subset=['Close'])
                    if df_raw.empty: st.error("Veri bulunamadı."); st.stop()
                    
                    son_f = float(df_raw['Close'].iloc[-1])
                    onceki_f = float(df_raw['Close'].iloc[-2]) if len(df_raw) > 1 else son_f
                    deg_yuzde = ((son_f - onceki_f) / onceki_f) * 100 if onceki_f > 0 else 0.0
                    renk_f = "#00ff00" if deg_yuzde >= 0 else "#FF5252"
                    isaret = "+" if deg_yuzde >= 0 else ""
                    hacim = float(df_raw['Volume'].iloc[-1]) if 'Volume' in df_raw.columns else 0.0
                    
                    df_raw['SMA50'] = df_raw['Close'].rolling(50).mean(); df_raw['SMA200'] = df_raw['Close'].rolling(200).mean()
                    sma50 = df_raw['SMA50'].iloc[-1]; sma200 = df_raw['SMA200'].iloc[-1]
                    t_val = 3.0 if (son_f > sma50 and son_f > sma200) else (1.5 if son_f > sma50 else 0.5) if not pd.isna(sma50) else 1.5
                    
                    delta = df_raw['Close'].diff(); gain = delta.clip(lower=0).ewm(alpha=1/14).mean(); loss = (-delta.clip(upper=0)).ewm(alpha=1/14).mean()
                    rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]; rsi = rsi if not pd.isna(rsi) else 50.0
                    ema12 = df_raw['Close'].ewm(span=12).mean(); ema26 = df_raw['Close'].ewm(span=26).mean()
                    macd = (ema12 - ema26).iloc[-1]; sig = (ema12 - ema26).ewm(span=9).mean().iloc[-1]
                    m_val = (2.0 if 45 < rsi < 65 else 0.0) + (2.0 if macd > sig else 0.0)
                    
                    df_raw['STD20'] = df_raw['Close'].rolling(20).std(); df_raw['SMA20'] = df_raw['Close'].rolling(20).mean()
                    std20 = df_raw['STD20'].iloc[-1]; sma20 = df_raw['SMA20'].iloc[-1]
                    v_val = 0.5
                    if not pd.isna(std20): b_alt = sma20 - (std20 * 2); v_val = 3.0 if son_f < b_alt * 1.05 else (1.5 if b_alt < son_f < sma20 else 0.5)
                    
                    puan = t_val + m_val + v_val
                    renk_p = "#00ff00" if puan >= 7.5 else ("#ffb300" if puan >= 5 else "#FF5252")
                    karar = "GÜÇLÜ AL" if puan >= 8.5 else ("AL" if puan >= 7 else ("İZLE" if puan >= 5 else "ZAYIF/SAT"))

                    html_cikti = (
f"<div style='background: rgba(15,15,15,0.6); border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid {renk_p}; border-radius: 8px; padding: 15px; font-family: Consolas, monospace; margin-bottom: 15px;'>"
f"<div style='display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 10px; margin-bottom: 10px;'>"
f"<div><span style='font-size: 1.6em; font-weight: bold; color: white;'>{t_kod.replace('.IS', '').replace('-USD', '')}</span><br>"
f"<span style='font-size: 1.2em; color: {renk_f};'>{son_f:,.2f} ({isaret}{deg_yuzde:.2f}%)</span></div>"
f"<div style='text-align: right;'><span style='font-size: 0.8em; color: gray;'>QUANT SKORU</span><br>"
f"<span style='font-size: 2.2em; font-weight: bold; color: {renk_p};'>{puan:.1f}/10</span></div></div>"
f"<div style='font-size: 0.9em; line-height: 2.0;'>"
f"<div style='display: flex; justify-content: space-between;'><span style='color: gray;'>[KARAR]</span><span style='color: {renk_p}; font-weight: bold;'>{karar}</span></div>"
f"<div style='display: flex; justify-content: space-between;'><span style='color: gray;'>[HACİM]</span><span style='color: white;'>{hacim:,.0f} Lot</span></div>"
f"<div style='display: flex; justify-content: space-between;'><span style='color: gray;'>[TREND / MOMENTUM]</span><span style='color: white;'>{(t_val+m_val):.1f}/7.0</span></div>"
f"</div></div>"
                    )
                    st.markdown(html_cikti, unsafe_allow_html=True)
                    
                    cg1, cg2 = st.columns(2)
                    g_ara = cg1.selectbox("Aralık", ["1 Gün", "1 Hafta", "1 Ay", "3 Ay", "6 Ay", "1 Yıl"], index=2, key=f"qa_{key_prefix}", label_visibility="collapsed")
                    g_tur = cg2.selectbox("Tür", ["Mum Grafik", "Çizgi Grafik"], key=f"qt_{key_prefix}", label_visibility="collapsed")
                    
                    if g_ara == "1 Gün": p_val, i_val = "1d", "5m"
                    elif g_ara == "1 Hafta": p_val, i_val = "5d", "1h"
                    elif g_ara == "1 Ay": p_val, i_val = "1mo", "1d"
                    elif g_ara == "3 Ay": p_val, i_val = "3mo", "1d"
                    elif g_ara == "6 Ay": p_val, i_val = "6mo", "1d"
                    else: p_val, i_val = "1y", "1d"
                    
                    df_chart = yf.Ticker(t_kod).history(period=p_val, interval=i_val).dropna(subset=['Close'])
                    
                    if not df_chart.empty:
                        if i_val == '5m': x_vals = df_chart.index.strftime('%H:%M')
                        elif i_val == '1h': x_vals = df_chart.index.strftime('%d %b %H:%M')
                        else: x_vals = df_chart.index.strftime('%d %b %Y')
                        
                        from plotly.subplots import make_subplots
                        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.75, 0.25])
                        
                        if g_tur == "Mum Grafik":
                            fig.add_trace(go.Candlestick(x=x_vals, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], 
                                                         increasing_line_color='#00ff00', decreasing_line_color='#FF5252', increasing_fillcolor='#00ff00', decreasing_fillcolor='#FF5252',
                                                         line=dict(width=1), name='Fiyat'), row=1, col=1)
                        else:
                            fig.add_trace(go.Scatter(x=x_vals, y=df_chart['Close'], mode='lines', line=dict(color=renk_f, width=2), name='Fiyat'), row=1, col=1)

                        colors = ['rgba(0, 255, 0, 0.4)' if row['Close'] >= row['Open'] else 'rgba(255, 82, 82, 0.4)' for _, row in df_chart.iterrows()]
                        fig.add_trace(go.Bar(x=x_vals, y=df_chart['Volume'], marker_color=colors, name='Hacim'), row=2, col=1)

                        fig.update_layout(height=320, margin=dict(t=5,b=0,l=0,r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_rangeslider_visible=False, showlegend=False, font=dict(family="Consolas", color="gray", size=10))
                        fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', type='category', nticks=6, row=2, col=1)
                        fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', side='right', tickformat=".2f", row=1, col=1)
                        fig.update_yaxes(showgrid=False, side='right', showticklabels=False, row=2, col=1)
                        
                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                except Exception as e: st.error(f"İşlem hatası: {e}")

    
    # --- SİSTEM HAFIZASI KONTROLÜ ---
if 'iceride_mi' not in st.session_state:
    st.session_state.iceride_mi = False
    st.session_state.aktif_kullanici = None
    # SİBER HAFIZA: Çerez dosyasını okur ve otomatik içeri alır
    if os.path.exists("beni_hatirla.json"):
        try:
            with open("beni_hatirla.json", "r") as f:
                data = json.load(f)
                st.session_state.aktif_kullanici = data["kullanici_adi"]
                st.session_state.iceride_mi = True
        except: pass

if not st.session_state.iceride_mi:
    
    # --- GİRİŞ EKRANI SÜZÜLEN LOGO VE 360 DERECE PARTİKÜL EFEKTİ ---
    logo_b64, logo_mime = "", "png"
    for img_file in ["logo.png", "logo.jpg", "logo.ico"]:
        if os.path.exists(img_file):
            try:
                with open(img_file, "rb") as f:
                    logo_b64 = base64.b64encode(f.read()).decode()
                    if img_file.endswith(".ico"): logo_mime = "x-icon"
                    elif img_file.endswith(".jpg"): logo_mime = "jpeg"
                break
            except: pass

    if logo_b64:
        st.markdown(f"""
        <style>
        .giris-logo-anim {{
            position: fixed; bottom: 80px; right: 80px; width: 150px; height: 150px;
            background-image: url('data:image/{logo_mime};base64,{logo_b64}');
            background-size: contain; background-repeat: no-repeat; background-position: center;
            z-index: 9999; pointer-events: none;
            /* Logo hem aşağı yukarı süzülür hem de 4 saniyede bir parlar ve büyür */
            animation: logo-pulse-float 4s ease-in-out infinite;
        }}
        @keyframes logo-pulse-float {{
            0% {{ transform: translateY(0px) scale(1); filter: drop-shadow(0 0 10px rgba(0,255,0,0.2)); }}
            50% {{ transform: translateY(-20px) scale(1.1); filter: drop-shadow(0 0 35px rgba(0,255,0,0.9)); }}
            100% {{ transform: translateY(0px) scale(1); filter: drop-shadow(0 0 10px rgba(0,255,0,0.2)); }}
        }}

        /* 360 Derece Her Yöne Saçılan Partiküller */
        .giris-logo-anim::before, .giris-logo-anim::after {{
            content: ''; position: absolute; top: 50%; left: 50%;
            width: 5px; height: 5px; background: transparent; border-radius: 50%;
            z-index: -1; pointer-events: none;
            /* Partikül patlaması logonun parlamasıyla aynı sürede (4s) sekronize çalışır */
            animation: burst 4s ease-out infinite;
        }}
        
        .giris-logo-anim::after {{
            width: 3px; height: 3px;
            animation-delay: 0.3s;
        }}

        @keyframes burst {{
            0% {{ 
                box-shadow: 0 0 0 transparent; 
                opacity: 1; 
                transform: translate(-50%, -50%) scale(0.1); 
            }}
            40% {{ 
                /* Logo parlamaya başladığında partiküller her köşeye (+ ve - X/Y yönlerine) saçılır */
                box-shadow: 
                    -100px -100px 4px #00ff00, 100px 100px 6px rgba(0,255,0,0.8),
                    100px -100px 4px rgba(0,255,0,0.6), -100px 100px 5px rgba(0,255,0,0.9),
                    0px -140px 4px #00ff00, 0px 140px 6px rgba(0,255,0,0.7),
                    -140px 0px 5px rgba(0,255,0,0.8), 140px 0px 4px rgba(0,255,0,0.9),
                    -70px -150px 3px #00ff00, 150px 70px 4px rgba(0,255,0,0.7);
                opacity: 0.9;
            }}
            100% {{ 
                /* Partiküller tamamen uzaklaşıp yok olur */
                box-shadow: 
                    -250px -250px 0 transparent, 250px 250px 0 transparent,
                    250px -250px 0 transparent, -250px 250px 0 transparent,
                    0px -300px 0 transparent, 0px 300px 0 transparent,
                    -300px 0px 0 transparent, 300px 0px 0 transparent,
                    -150px -350px 0 transparent, 350px 150px 0 transparent;
                opacity: 0; 
                transform: translate(-50%, -50%) scale(1.5); 
            }}
        }}
        </style>
        <div class="giris-logo-anim"></div>
        """, unsafe_allow_html=True)

    # Giriş formunu ortalamak için ekranı 3 parçaya bölüyoruz
    bosluk_sol, merkez_kolon, bosluk_sag = st.columns([1, 2, 1])
    
    with merkez_kolon:
        st.markdown("<h1 style='text-align: center; margin-bottom: 0px;'>Mergen Finans</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray; margin-top: 0px;'>Sistem Girişi</p>", unsafe_allow_html=True)
        st.markdown("<hr style='border: 1px solid rgba(0,255,0,0.2); margin-bottom: 30px;'>", unsafe_allow_html=True)
        
        k_adi_input = st.text_input("Kullanıcı Kodu")
        sifre_input = st.text_input("Parola", type="password")
        
        c_alt1, c_alt2 = st.columns(2)
        beni_hatirla = c_alt1.checkbox("Oturumu Açık Tut")
        davetiye_input = c_alt2.text_input("Davetiye Kodu (Kayıt İçin)", type="password", placeholder="Sadece yeni kayıtlar için")
        
        # --- ANTI-SPAM: GENEL İŞLEM SOĞUMA (COOLDOWN) SÜRESİ ---
        if 'son_islem_zamani' not in st.session_state:
            st.session_state.son_islem_zamani = 0

        col1, col2 = st.columns(2)
        
        if col1.button("Sisteme Bağlan", type="primary", use_container_width=True):
            simdi = time.time()
            if simdi - st.session_state.son_islem_zamani < 2.0:
                st.warning("Anti-Spam: Lütfen saniyede bir tıklama yapın.")
            else:
                st.session_state.son_islem_zamani = simdi
                conn = get_db()
                try:
                    c = conn.cursor()
                    c.execute("SELECT * FROM kullanicilar WHERE kullanici_adi = %s AND sifre = %s", (k_adi_input, sifre_input))
                    if c.fetchone():
                        st.session_state.aktif_kullanici = k_adi_input
                        st.session_state.iceride_mi = True
                        
                        # Eğer kutucuk işaretlendiyse kimliği diske yazar
                        if beni_hatirla:
                            with open("beni_hatirla.json", "w") as f:
                                json.dump({"kullanici_adi": k_adi_input}, f)
                                
                        st.rerun()
                    else: 
                        st.error("Yetkilendirme Hatası: Kimlik bilgileri geçersiz.")
                finally: release_db(conn)
        
        if col2.button("Yeni Kayıt Oluştur", use_container_width=True):
            simdi = time.time()
            if simdi - st.session_state.son_islem_zamani < 3.0:
                st.warning("Anti-Spam: Lütfen art arda işlem yapmayın.")
            else:
                st.session_state.son_islem_zamani = simdi
                if k_adi_input and sifre_input and davetiye_input:
                    conn = get_db()
                    try:
                        c = conn.cursor()
                        # --- DAVETİYE KONTROLÜ ---
                        c.execute("SELECT kullanim_hakki FROM davetiyeler WHERE kod = %s", (davetiye_input,))
                        davetiye_res = c.fetchone()
                        
                        if not davetiye_res:
                            st.error("Geçersiz Davetiye Kodu! Lütfen geliştiriciden kod talep edin.")
                        elif davetiye_res[0] <= 0:
                            st.error("Bu davetiye kodunun kullanım limiti (Max 2 kişi) dolmuştur!")
                        else:
                            # Kayıt Başarılıysa
                            c.execute("INSERT INTO kullanicilar (kullanici_adi, sifre) VALUES (%s,%s)", (k_adi_input, sifre_input))
                            c.execute("INSERT INTO bakiyeler VALUES (%s, 0.0)", (k_adi_input,))
                            # Davetiye hakkını düşür
                            c.execute("UPDATE davetiyeler SET kullanim_hakki = kullanim_hakki - 1 WHERE kod = %s", (davetiye_input,))
                            
                            conn.commit()
                            st.success("Kayıt oluşturuldu. Sisteme bağlanabilirsiniz.")
                    except IntegrityError: 
                        st.error("Bu Kullanıcı Kodu daha önce alınmış.")
                    except Exception as e:
                        st.error(f"Kayıt Hatası: {e}")
                    finally: 
                        release_db(conn)
                else:
                    st.warning("Yeni kayıt için Kullanıcı Kodu, Parola ve geçerli bir Davetiye Kodu girmek zorunludur.")

else:
    k_adi = st.session_state.aktif_kullanici
    mevcut_bakiye = bakiye_getir(k_adi)
    
    
    
    
    if 'motorlar_calisti' not in st.session_state:
        # SİBER MAYMUNCUK: Takasta hapis kalan PPF paralarını anında serbest bırakır
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute("UPDATE takas_bekleyen_islemler SET takas_tarihi = CURRENT_DATE - INTERVAL '1 day' WHERE durum = 'Bekliyor' AND varlik = 'TP2'")
            conn.commit()
        except: pass
        finally: release_db(conn)

        takas_motorunu_calistir(k_adi)
        faiz_motorunu_calistir(k_adi)
        gecmis_harcamalari_dekonta_aktar(k_adi)
        sabit_islemleri_islet(k_adi)
        asistan_motorunu_calistir(k_adi)
        
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute("INSERT INTO hesaplar (kullanici_adi, hesap_adi, bakiye) VALUES (%s, 'Vadesiz TL', 50000.0) ON CONFLICT (kullanici_adi, hesap_adi) DO NOTHING", (k_adi,))
            c.execute("INSERT INTO hesaplar (kullanici_adi, hesap_adi, bakiye) VALUES (%s, 'Yatırım Hesabı', %s) ON CONFLICT (kullanici_adi, hesap_adi) DO NOTHING", (k_adi, mevcut_bakiye))
            c.execute("INSERT INTO hesaplar (kullanici_adi, hesap_adi, bakiye) VALUES (%s, 'Yatırım Hesabı (USD)', 0.0) ON CONFLICT (kullanici_adi, hesap_adi) DO NOTHING", (k_adi,))
            conn.commit()
        finally: release_db(conn)
        st.session_state.motorlar_calisti = True
        
        # --- MERGEN ASİSTAN ARAYÜZÜ VE BUTONU ---
    @st.dialog("Sistem Bildirim Merkezi")
    def asistan_paneli_ac(k_adi):
        st.markdown("<span style='color: #00ff00; font-weight: bold; font-size: 1.1em;'>Sistem Analizleri ve Bildirimler</span>", unsafe_allow_html=True)
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute("SELECT baslik, mesaj, tarih FROM asistan_bildirimleri WHERE kullanici_adi = %s ORDER BY tarih DESC LIMIT 10", (k_adi,))
            bildirimler = c.fetchall()
            c.execute("UPDATE asistan_bildirimleri SET okundu = TRUE WHERE kullanici_adi = %s", (k_adi,))
            conn.commit()
        finally: release_db(conn)
        
        if bildirimler:
            for b in bildirimler:
                tarih_str = b[2].strftime("%d.%m.%Y %H:%M")
                st.markdown(f"""
                <div style='border-left: 3px solid #00ff00; background: rgba(0,255,0,0.05); padding: 12px; margin-bottom: 12px; border-radius: 0 5px 5px 0;'>
                    <div style='font-size: 0.8em; color: gray; margin-bottom: 2px;'>{tarih_str}</div>
                    <div style='font-weight: bold; color: white; margin-bottom: 4px;'>{b[0]}</div>
                    <div style='font-size: 0.95em; color: #d0d0d0; line-height: 1.4;'>{b[1]}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Sistemde okunmamış yeni bir analiz veya bildirim bulunmamaktadır.")

    conn = get_db()
    try:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM asistan_bildirimleri WHERE kullanici_adi = %s AND okundu = FALSE", (k_adi,))
        okunmamis = c.fetchone()[0]
        son_mesaj = ""
        if okunmamis > 0:
            c.execute("SELECT mesaj FROM asistan_bildirimleri WHERE kullanici_adi = %s AND okundu = FALSE ORDER BY tarih DESC LIMIT 1", (k_adi,))
            son_mesaj_db = c.fetchone()
            if son_mesaj_db: son_mesaj = son_mesaj_db[0]
    finally: release_db(conn)

    logo_b64, logo_mime = "", "png"
    for img_file in ["logo.png", "logo.jpg", "logo.ico"]:
        if os.path.exists(img_file):
            try:
                with open(img_file, "rb") as f:
                    logo_b64 = base64.b64encode(f.read()).decode()
                    if img_file.endswith(".ico"): logo_mime = "x-icon"
                    elif img_file.endswith(".jpg"): logo_mime = "jpeg"
                break
            except: pass

    if logo_b64:
        st.markdown(f"<style>div[data-testid='stElementContainer']:has(#asistan-marker) + div[data-testid='stElementContainer'] button::before {{ content: '' !important; background-image: url('data:image/{logo_mime};base64,{logo_b64}'); background-size: contain; background-repeat: no-repeat; background-position: center; width: 100%; height: 100%; position: absolute; z-index: 1; }}</style>", unsafe_allow_html=True)
    else:
        st.markdown("<style>div[data-testid='stElementContainer']:has(#asistan-marker) + div[data-testid='stElementContainer'] button::before { content: 'M' !important; position: absolute; color: #00ff00; font-family: Consolas, monospace; font-size: 26px; font-weight: bold; text-shadow: 0 0 10px rgba(0, 255, 0, 0.8); z-index: 1; display: flex; align-items: center; justify-content: center; width: 100%; height: 100%; top: 0; left: 0; }</style>", unsafe_allow_html=True)

    # Bildirim varsa Konuşma Balonunu (Speech Bubble) ekrana basıyoruz
    if okunmamis > 0 and son_mesaj:
        bubble_html = f"""
        <div id="asistan-bubble" style="position: fixed; bottom: 45px; right: 110px; width: 300px; background: rgba(12,12,12,0.95); border: 1px solid rgba(0,255,0,0.3); border-radius: 8px; padding: 15px; box-shadow: 0 5px 15px rgba(0,255,0,0.1); z-index: 99998; animation: slide-in 0.3s ease-out; transition: opacity 0.5s ease;">
            <div id="asistan-close-btn" style="position: absolute; top: 5px; right: 12px; color: #888; font-size: 18px; font-weight: bold; cursor: pointer; transition: color 0.3s ease;">×</div>
            <div style="color: #00ff00; font-size: 0.75em; font-weight: bold; letter-spacing: 1px; margin-bottom: 8px; border-bottom: 1px solid rgba(0,255,0,0.1); padding-bottom: 4px; padding-right: 15px;">SİSTEM BİLDİRİMİ ({okunmamis})</div>
            <div style="color: #e0e0e0; font-size: 0.9em; line-height: 1.4; font-family: 'system-ui', sans-serif;">{son_mesaj}</div>
            <div style="position: absolute; right: -6px; bottom: 15px; width: 10px; height: 10px; background: rgba(12,12,12,0.95); border-right: 1px solid rgba(0,255,0,0.3); border-bottom: 1px solid rgba(0,255,0,0.3); transform: rotate(-45deg);"></div>
        </div>
        """
        st.markdown(bubble_html, unsafe_allow_html=True)
        
        # Balonu kontrol eden görünmez Javascript motoru
        import streamlit.components.v1 as components
        js_kodu = """
        <script>
            const doc = window.parent.document;
            setTimeout(() => {
                const bubble = doc.getElementById('asistan-bubble');
                const closeBtn = doc.getElementById('asistan-close-btn');
                
                if (bubble && closeBtn) {
                    // Çarpının üzerine gelince neon yeşil yap
                    closeBtn.onmouseover = () => { closeBtn.style.color = '#00ff00'; };
                    closeBtn.onmouseout = () => { closeBtn.style.color = '#888'; };
                    
                    // Çarpıya tıklanınca anında kapat
                    closeBtn.onclick = () => { 
                        bubble.style.display = 'none'; 
                    };
                    
                    // Tam 5 saniye (5000 ms) sonra yavaşça kaybolarak kapan
                    setTimeout(() => {
                        if (bubble.style.display !== 'none') {
                            bubble.style.opacity = '0';
                            setTimeout(() => { bubble.style.display = 'none'; }, 500); // 0.5sn fade-out sonrası DOM'dan gizle
                        }
                    }, 5000);
                }
            }, 100);
        </script>
        """
        components.html(js_kodu, height=0, width=0)

    st.markdown('<div id="asistan-marker"></div>', unsafe_allow_html=True)
    if st.button("ASISTAN_LOGO"):
        asistan_paneli_ac(k_adi)

    with st.sidebar:
        # --- 1. TARİH VE GÜN MODÜLÜ ---
        aylar = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
        gunler = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        simdi = datetime.datetime.now()
        st.markdown(f"<div style='text-align: center; color: #00ff00; font-family: monospace; font-size: 1.1rem; padding-bottom: 5px; border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 10px;'><b>{simdi.day} {aylar[simdi.month]} {simdi.year}</b><br><span style='font-size: 0.9rem; color: gray;'>{gunler[simdi.weekday()]}</span></div>", unsafe_allow_html=True)

        # --- 2. PROFİL KISMI ---
        k_bilgi = kullanici_bilgileri_getir(k_adi)
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            if k_bilgi['profil_fotosu']:
                try:
                    g_data = base64.b64decode(k_bilgi['profil_fotosu'])
                    st.image(g_data, use_container_width=True)
                except:
                    st.markdown("<div style='width: 100%; aspect-ratio: 1/1; border: 2px solid #00ff00; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #00ff00; font-size: 2em; background: rgba(0,255,0,0.05);'>U</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='width: 100%; aspect-ratio: 1/1; border: 2px solid #00ff00; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #00ff00; font-size: 2em; background: rgba(0,255,0,0.05);'>U</div>", unsafe_allow_html=True)
        
        isim_yazi = k_bilgi['isim_soyisim'] if k_bilgi['isim_soyisim'] else "Bilinmeyen Kullanıcı"
        st.markdown(f"<div style='text-align: center; margin-top: 5px;'><h4 style='margin-bottom: 0px;'>{isim_yazi}</h4><span style='color: gray; font-size: 12px;'>Kod: {k_adi}</span></div>", unsafe_allow_html=True)
        
        # ... profil fotosu kodları ...
        st.markdown("<br>", unsafe_allow_html=True)
        # --- BU SATIRI YENİSİYLE DEĞİŞTİRİYORSUN ---
        if st.button("Kullanıcı Bilgileri", use_container_width=True):
            kullanici_bilgileri_sayfasi(k_adi)
        # ------------------------------------------
        st.markdown("<hr style='margin-top: 10px; margin-bottom: 10px; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        # ... menü devamı ...
        st.markdown("<span style='color: gray; font-size: 12px; font-weight: bold;'>ANA TERMİNAL</span>", unsafe_allow_html=True)
        
        # --- GİZLİ YÖNETİCİ MENÜSÜ KONTROLÜ ---
        ADMIN_KULLANICILAR = ["oguzhan", "admin", "mergen"] # Sisteme kayıt olurken bu isimlerden birini kullan ki admin olasın
        
        menu_secenekleri = ["Portföy Yönetimi", "Banka ve Bütçe", "Piyasa Analiz"]
        if k_adi in ADMIN_KULLANICILAR:
            menu_secenekleri.append("Yönetici Paneli")
            
        # Seçim Menüsü
        secilen_sayfa = st.radio("Menü", menu_secenekleri, label_visibility="collapsed")
        
        st.markdown("<hr style='margin-top: 10px; margin-bottom: 10px; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
        st.markdown("<span style='color: gray; font-size: 12px; font-weight: bold;'>SİSTEM</span>", unsafe_allow_html=True)
        
        if st.button("Yenile", use_container_width=True): 
            st.rerun()
            
        if st.button("Güvenli Çıkış", type="primary", use_container_width=True):
            st.session_state.clear()
            if os.path.exists("beni_hatirla.json"): 
                os.remove("beni_hatirla.json")
            st.rerun()
        st.markdown("<br><br>", unsafe_allow_html=True)
            
    # --- ANA YATIRIM SAYFASI ---
    if secilen_sayfa == "Portföy Yönetimi":
        st.title("Portföy Yönetim Terminali")
        
        with st.expander("Portföy Raporlarını Dışa Aktar (.md)"):
            st.info("İhtiyacınız olan rapor türünü seçerek Markdown (.md) formatında indirebilirsiniz.")
            
            conn = get_db()
            try:
                # 1. Güncel Portföy Verisi
                df_guncel = pd.read_sql_query('SELECT varlik_adi as "VARLIK", borsa as "BORSA", SUM(lot) as "LOT", AVG(maliyet) as "ORT_MALIYET" FROM portfoy WHERE kullanici_adi = %s GROUP BY varlik_adi, borsa HAVING SUM(lot) > 0.0001', conn, params=(k_adi,))
                
                # 2. Kapanan Pozisyonlar Verisi
                sorgu_kapanan = """
                SELECT 
                    varlik_adi as "VARLIK", 
                    borsa as "BORSA",
                    SUM(CASE WHEN lot > 0 THEN lot ELSE 0 END) as "ALINAN_LOT",
                    SUM(CASE WHEN lot > 0 THEN lot * maliyet ELSE 0 END) / NULLIF(SUM(CASE WHEN lot > 0 THEN lot ELSE 0 END), 0) as "ORT_ALIS",
                    SUM(CASE WHEN lot > 0 THEN lot * maliyet ELSE 0 END) as "TOPLAM_MALIYET",
                    SUM(CASE WHEN lot < 0 THEN ABS(lot) * maliyet ELSE 0 END) / NULLIF(SUM(CASE WHEN lot < 0 THEN ABS(lot) ELSE 0 END), 0) as "ORT_SATIS",
                    SUM(CASE WHEN lot < 0 THEN ABS(lot) * maliyet ELSE 0 END) as "TOPLAM_GELIR"
                FROM portfoy 
                WHERE kullanici_adi = %s 
                GROUP BY varlik_adi, borsa 
                HAVING ABS(SUM(lot)) <= 0.0001 AND COUNT(lot) > 1
                """
                df_kapanan = pd.read_sql_query(sorgu_kapanan, conn, params=(k_adi,))
                
                # 3. Tüm İşlem Geçmişi (Sadece Yatırımlar)
                df_gecmis = pd.read_sql_query("SELECT tarih, islem_tipi, detay, tutar FROM islem_gecmisi WHERE kullanici_adi = %s AND (islem_tipi LIKE 'BORSA%%' OR islem_tipi LIKE 'MADEN%%' OR islem_tipi LIKE 'FON%%' OR islem_tipi LIKE 'TAKAS%%') ORDER BY tarih DESC", conn, params=(k_adi,))
                
                # 4. Nakit Durumu
                c = conn.cursor()
                c.execute("SELECT bakiye FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (k_adi,))
                yt_bak = c.fetchone()
                yatirim_nakit = yt_bak[0] if yt_bak else 0.0
            finally: release_db(conn)

            usd_kuru = doviz_kuru_cek("USD")
            eur_kuru = doviz_kuru_cek("EUR")

            # ==========================================
            # RAPOR 1: GÜNCEL PORTFÖY RAPORU
            # ==========================================
            rapor_guncel = f"# MERGEN FİNANS - GÜNCEL PORTFÖY RAPORU\n**Tarih:** {datetime.date.today().strftime('%d.%m.%Y')}\n\n## 1. YÖNETİCİ ÖZETİ\n- **Boşta Bekleyen Nakit (Yatırım Hesabı):** {yatirim_nakit:,.2f} TL\n"
            toplam_maliyet, toplam_guncel, varlik_satirlari = 0.0, 0.0, ""
            
            if not df_guncel.empty:
                varlik_satirlari += "| Varlık Kodu | Piyasa | Miktar (Lot/Pay) | Birim Maliyet | Güncel Fiyat | Toplam Değer (TL) | Kâr/Zarar (%) |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
                for _, r in df_guncel.iterrows():
                    v_kod, v_borsa, v_lot, v_maliyet = r['VARLIK'], r['BORSA'], r['LOT'], r['ORT_MALIYET']
                    v_fiyat = tefas_fiyat_cek(v_kod) if v_borsa == "FON (TEFAS)" else hizli_fiyat_cek(v_kod)[0]
                    if not v_fiyat: v_fiyat = v_maliyet
                    
                    # BURA DEĞİŞTİ: "ETF" EKLENDİ
                    if v_borsa in ["NASDAQ", "S&P 500", "KRİPTO", "EMTİA", "ETF"] or "-USD" in v_kod: carpan, pb = usd_kuru, "$"
                    elif "EUR" in v_borsa or ".DE" in v_kod or ".PA" in v_kod or ".AS" in v_kod: carpan, pb = eur_kuru, "€"
                    else: carpan, pb = 1.0, "TL"
                    
                    satir_maliyet_tl, satir_guncel_tl = v_maliyet * v_lot * carpan, v_fiyat * v_lot * carpan
                    kz_yuzde = ((v_fiyat - v_maliyet) / v_maliyet) * 100 if v_maliyet > 0 else 0
                    
                    toplam_maliyet += satir_maliyet_tl
                    toplam_guncel += satir_guncel_tl
                    varlik_satirlari += f"| **{v_kod}** | {v_borsa} | {v_lot:.6f} | {v_maliyet:.6f} {pb} | {v_fiyat:.6f} {pb} | {satir_guncel_tl:,.2f} TL | %{kz_yuzde:.2f} |\n"
            
            if toplam_maliyet > 0:
                genel_kz_tl = toplam_guncel - toplam_maliyet
                genel_kz_oran = (genel_kz_tl / toplam_maliyet) * 100
                rapor_guncel += f"- **Portföye Yatırılan Toplam Ana Para:** {toplam_maliyet:,.2f} TL\n- **Portföyün Güncel Toplam Değeri:** {toplam_guncel:,.2f} TL\n- **Net Portföy Kâr/Zarar Durumu:** {genel_kz_tl:,.2f} TL (%{genel_kz_oran:.2f})\n\n"
            else: rapor_guncel += "- *Aktif bir yatırım bulunmuyor.*\n\n"
            rapor_guncel += "## 2. GÜNCEL VARLIK DETAYLARI VE DAĞILIM\n" + (varlik_satirlari + "\n" if varlik_satirlari else "*Portföyde henüz aktif bir varlık bulunmuyor.*\n\n")

            # ==========================================
            # RAPOR 2: TÜM ZAMANLAR PORTFÖY RAPORU
            # ==========================================
            rapor_tumu = f"# MERGEN FİNANS - TÜM ZAMANLAR PORTFÖY ANALİZİ\n**Oluşturulma Tarihi:** {datetime.date.today().strftime('%d.%m.%Y')}\n\n"
            rapor_tumu += "## 1. KAPANAN POZİSYONLAR (TAMAMI SATILAN VARLIKLAR)\n"
            
            if not df_kapanan.empty:
                rapor_tumu += "| Varlık Kodu | Piyasa | İşlem Hacmi (Lot/Pay) | Ort. Alış Maliyeti | Ort. Satış Fiyatı | Toplam Yatırım | Ele Geçen Nakit | Net Kâr/Zarar | K/Z Oranı |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
                for _, r in df_kapanan.iterrows():
                    varlik, borsa = r['VARLIK'], r['BORSA']
                    alinan_lot = r['ALINAN_LOT']
                    ort_alis = float(r['ORT_ALIS']) if pd.notnull(r['ORT_ALIS']) else 0.0
                    ort_satis = float(r['ORT_SATIS']) if pd.notnull(r['ORT_SATIS']) else 0.0
                    top_mal = float(r['TOPLAM_MALIYET']) if pd.notnull(r['TOPLAM_MALIYET']) else 0.0
                    top_gel = float(r['TOPLAM_GELIR']) if pd.notnull(r['TOPLAM_GELIR']) else 0.0
                    
                    pb = "$" if borsa in ["NASDAQ", "S&P 500", "KRİPTO", "EMTİA"] else "TL"
                    kar_zarar_net = top_gel - top_mal
                    kz_yuzde = (kar_zarar_net / top_mal) * 100 if top_mal > 0 else 0.0
                    
                    rapor_tumu += f"| **{varlik}** | {borsa} | {alinan_lot:.6f} | {ort_alis:,.4f} {pb} | {ort_satis:,.4f} {pb} | {top_mal:,.2f} {pb} | {top_gel:,.2f} {pb} | {kar_zarar_net:,.2f} {pb} | %{kz_yuzde:.2f} |\n"
                rapor_tumu += "\n"
            else:
                rapor_tumu += "*Henüz tamamen kapatılmış bir pozisyon bulunmuyor.*\n\n"
                
            rapor_tumu += "## 2. DETAYLI İŞLEM GEÇMİŞİ (KRONOLOJİK)\n| Tarih | İşlem Tipi | İşlem Detayı | Tutar Etkisi (TL) |\n| :--- | :--- | :--- | :--- |\n"
            if not df_gecmis.empty:
                for _, r in df_gecmis.iterrows():
                    tarih_str = pd.to_datetime(r['tarih']).strftime('%d.%m.%Y %H:%M')
                    rapor_tumu += f"| {tarih_str} | {r['islem_tipi']} | {r['detay']} | {r['tutar']:,.2f} TL |\n"
            else:
                rapor_tumu += "| - | Veri Yok | Sistemde yatırım işlemi bulunamadı. | - |\n"

            # İki Butonu Yan Yana Ekleme
            c_btn1, c_btn2 = st.columns(2)
            c_btn1.download_button("Güncel Portföy Raporunu İndir (.md)", data=rapor_guncel, file_name=f"Mergen_Guncel_Portfoy_{datetime.date.today().strftime('%d_%m_%Y')}.md", mime="text/markdown", use_container_width=True)
            c_btn2.download_button("Tüm Zamanlar Analizini İndir (.md)", data=rapor_tumu, file_name=f"Mergen_TumZamanlar_Portfoy_{datetime.date.today().strftime('%d_%m_%Y')}.md", mime="text/markdown", use_container_width=True)

        if 'islem_bildirimi' in st.session_state:
            st.toast(st.session_state.islem_bildirimi['mesaj'])
            del st.session_state.islem_bildirimi 

        tab1, tab2, tab3, tab4 = st.tabs(["Cari Portföy", "İşlem Terminali", "Virman Yönetimi", "İşlem Dökümü"])

        with tab1: 
            conn = get_db()
            try:
                c = conn.cursor()
                c.execute("SELECT bakiye FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (k_adi,))
                yt_tl = c.fetchone()
                nakit_tl = yt_tl[0] if yt_tl else 0.0
                
                c.execute("SELECT bakiye FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı (USD)'", (k_adi,))
                yt_usd = c.fetchone()
                nakit_usd = yt_usd[0] if yt_usd else 0.0
                
                # --- MİDAS YAMASI: TAKASTA BEKLEYEN PARAYI ÇEK ---
                c.execute("SELECT COALESCE(SUM(tutar), 0) FROM takas_bekleyen_islemler WHERE kullanici_adi = %s AND durum = 'Bekliyor' AND islem_yonu = 'SATIM'", (k_adi,))
                brut_takas_tl = c.fetchone()[0]
            finally: release_db(conn)
                
            anlik_dolar = doviz_kuru_cek("USD")
            
            # --- AKILLI MAHSUPLAŞMA (NETTING) MANTIĞI ---
            # Eğer eksi bakiyeye düştüysek, bunu takastaki parandan kullanılmış avans olarak sayarız.
            kullanilan_avans = 0.0
            if nakit_tl < 0:
                kullanilan_avans = abs(nakit_tl)
                net_takas_tl = brut_takas_tl + nakit_tl # nakit eksi olduğu için takastan düşer
                nakit_tl = 0.0 # Kasada eksi para görünmez, sıfırlanır
            else:
                net_takas_tl = brut_takas_tl
                
            alim_gucu_tl = nakit_tl + net_takas_tl
            toplam_nakit_tl = alim_gucu_tl + (nakit_usd * anlik_dolar)

            st.markdown("##### Nakit Bakiye ve Alım Gücü")
            
            # --- 1. NAKİT BAKİYE KARTLARI (EMOJİSİZ SİBER TASARIM) ---
            nakit_kartlari = [
                {"isim": "TL Alım Gücü" if net_takas_tl > 0 else "TL Kasası", "alt": "Türk Lirası", "deger": f"{alim_gucu_tl:,.2f} TL", "renk": "#4CAF50", "detay": f"Nakit: {nakit_tl:,.2f} | Net Takas: {net_takas_tl:,.2f}" if net_takas_tl > 0 else "Kullanılabilir Nakit", "ikon": "TL"},
                {"isim": "USD Kasası", "alt": "Amerikan Doları", "deger": f"{nakit_usd:,.2f} $", "renk": "#4CAF50", "detay": f"Anlık Kur: {anlik_dolar:.2f} TL", "ikon": "USD"},
                {"isim": "Toplam TL Karşılığı", "alt": "Tüm Varlıklar", "deger": f"{toplam_nakit_tl:,.2f} TL", "renk": "#00ff00", "detay": "T+2 ve Döviz Dahil", "ikon": "TOPLAM"}
            ]
            
            cols_n = st.columns(3)
            for idx, kart in enumerate(nakit_kartlari):
                with cols_n[idx]:
                    bas_harf = kart['ikon'][0]
                    img_html = f"<div style='width: 38px; height: 38px; border-radius: 50%; border: 1px solid rgba(0,255,0,0.4); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #00ff00; background: rgba(0,255,0,0.05); font-size: 16px;'>{bas_harf}</div>"
                    
                    for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
                        p = f"Banka Logoları/{kart['ikon']}{ext}"
                        if os.path.exists(p):
                            with open(p, "rb") as f:
                                b64 = base64.b64encode(f.read()).decode()
                                img_html = f"<img src='data:image/png;base64,{b64}' style='width: 38px; height: 38px; border-radius: 50%; border: 1px solid rgba(0,255,0,0.4); padding: 3px; object-fit: contain; background: #ffffff;'>"
                            break
                            
                    kart_html = f"""
                    <div style='border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 15px; background: rgba(10,10,10,0.5); margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: all 0.3s ease;'>
                        <div style='display: flex; align-items: center; margin-bottom: 15px;'>
                            <div>{img_html}</div>
                            <div style='margin-left: 12px; line-height: 1.2;'>
                                <div style='font-size: 0.70em; color: gray; text-transform: uppercase; letter-spacing: 0.5px;'>{kart['alt']}</div>
                                <div style='font-size: 0.95em; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{kart['isim']}</div>
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 1.35em; font-weight: bold; color: {kart['renk']};'>{kart['deger']}</div>
                            <div style='font-size: 0.8em; color: gray; margin-top: 4px; font-family: monospace;'>{kart['detay']}</div>
                        </div>
                    </div>
                    """
                    st.markdown(kart_html, unsafe_allow_html=True)

            # --- YENİ: TAKAS DETAY MODÜLÜ ---
            if brut_takas_tl > 0:
                with st.expander("Takasta Bekleyen Bakiye Detayları"):
                    conn = get_db()
                    try:
                        df_takas_detay = pd.read_sql_query("SELECT varlik, tutar, islem_tarihi, takas_tarihi FROM takas_bekleyen_islemler WHERE kullanici_adi = %s AND durum = 'Bekliyor' AND islem_yonu = 'SATIM' ORDER BY takas_tarihi ASC", conn, params=(k_adi,))
                    finally: release_db(conn)
                        
                    if not df_takas_detay.empty:
                        for _, r_t in df_takas_detay.iterrows():
                            t_tarih = pd.to_datetime(r_t['takas_tarihi']).strftime('%d.%m.%Y')
                            i_tarih = pd.to_datetime(r_t['islem_tarihi']).strftime('%d.%m.%Y')
                            
                            st.markdown(f"""
                            <div style='display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 8px 0; align-items: center;'>
                                <div><b style='color: #00ff00;'>{r_t['varlik']}</b> <span style='color: gray; font-size: 0.85em;'>(Satış: {i_tarih})</span></div>
                                <div style='color: gray; font-size: 0.85em; font-family: monospace;'>Hesaba Geçiş: {t_tarih}</div>
                                <div><b style='color: #4CAF50; font-size: 1.05em;'>+ {r_t['tutar']:,.2f} TL</b></div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        if kullanilan_avans > 0:
                            st.markdown(f"""
                            <div style='display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 8px 0; align-items: center; background-color: rgba(255, 82, 82, 0.05);'>
                                <div><b style='color: #FF5252;'>Yeni Alımlarda Kullanılan (Avans)</b></div>
                                <div style='color: gray; font-size: 0.85em; font-family: monospace;'>Anında Düşüldü</div>
                                <div><b style='color: #FF5252; font-size: 1.05em;'>- {kullanilan_avans:,.2f} TL</b></div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                        st.markdown(f"""
                        <div style='text-align: right; padding-top: 10px;'>
                            <span style='color: gray; font-size: 0.9em;'>Net Bekleyen Takas Bakiyesi:</span> <b style='color: #00ff00; font-size: 1.2em;'>{net_takas_tl:,.2f} TL</b>
                        </div>
                        """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("##### Piyasa Endeksleri")
            idx_map = {"BİST": "XU100.IS", "NASDAQ": "^IXIC", "S&P 500": "^GSPC", "KRİPTO": "BTC-USD", "EMTİA": "GC=F"}
            
            conn = get_db()
            df_b = pd.read_sql_query("SELECT DISTINCT borsa FROM portfoy WHERE kullanici_adi = %s", conn, params=(k_adi,))
            release_db(conn)
            
            aktif_borsalar = [b for b in df_b['borsa'].tolist() if b in idx_map] if not df_b.empty else []
            if not aktif_borsalar: aktif_borsalar = ["BİST"]
            
            # --- 2. PİYASA ENDEKS KARTLARI (EMOJİSİZ SİBER TASARIM) ---
            cols_e = st.columns(len(aktif_borsalar))
            for i, b in enumerate(aktif_borsalar):
                fiyat, okapanis = hizli_fiyat_cek(idx_map[b])
                if fiyat and okapanis:
                    degisim = ((fiyat - okapanis) / okapanis) * 100
                    renk = "#4CAF50" if degisim >= 0 else "#FF5252"
                    isaret = "+" if degisim >= 0 else ""
                    
                    # Emoji yerine şık baş harf (Avatar) tasarımı
                    bas_harf = b[0].upper()
                    img_html = f"<div style='width: 38px; height: 38px; border-radius: 50%; border: 1px solid rgba(0,255,0,0.4); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #00ff00; background: rgba(0,255,0,0.05); font-size: 16px;'>{bas_harf}</div>"
                    
                    for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
                        p = f"Banka Logoları/{b}{ext}"
                        if os.path.exists(p):
                            with open(p, "rb") as f:
                                b64 = base64.b64encode(f.read()).decode()
                                img_html = f"<img src='data:image/png;base64,{b64}' style='width: 38px; height: 38px; border-radius: 50%; border: 1px solid rgba(0,255,0,0.4); padding: 3px; object-fit: contain; background: #ffffff;'>"
                            break
                            
                    endeks_html = f"""
                    <div style='border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 15px; background: rgba(10,10,10,0.5); margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: all 0.3s ease;'>
                        <div style='display: flex; align-items: center; margin-bottom: 15px;'>
                            <div>{img_html}</div>
                            <div style='margin-left: 12px; line-height: 1.2;'>
                                <div style='font-size: 0.70em; color: gray; text-transform: uppercase; letter-spacing: 0.5px;'>Piyasa</div>
                                <div style='font-size: 0.95em; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{b}</div>
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 1.35em; font-weight: bold; color: white;'>{fiyat:,.2f}</div>
                            <div style='font-size: 0.85em; color: {renk}; margin-top: 4px; font-weight: bold;'>{isaret}{degisim:.2f}%</div>
                        </div>
                    </div>
                    """
                    with cols_e[i]:
                        st.markdown(endeks_html, unsafe_allow_html=True)
            
            st.markdown("---")
            
            conn = get_db()
            df_p = pd.read_sql_query('SELECT varlik_adi as "VARLIK", borsa as "BORSA", SUM(lot) as "LOT", AVG(maliyet) as "ORT_MALIYET" FROM portfoy WHERE kullanici_adi = %s GROUP BY varlik_adi, borsa HAVING SUM(lot) > 0.0001', conn, params=(k_adi,))
            df_emtia = pd.read_sql_query("SELECT maden_turu, SUM(miktar) as miktar, SUM(miktar * ortalama_maliyet) as toplam_maliyet FROM emtia_portfoy WHERE kullanici_adi = %s GROUP BY maden_turu HAVING SUM(miktar) > 0.001", conn, params=(k_adi,))
            release_db(conn)
            
            genel_maliyet_toplami, genel_guncel_toplam = 0.0, 0.0
            dagilim_data = []
            
        # --- 1. BORSA VE FON VARLIKLARI ---
            if 'p_card_currency_toggles' not in st.session_state:
                st.session_state['p_card_currency_toggles'] = {}

            if not df_p.empty:
                st.markdown("##### Borsa ve Fon Varlıkları")
                
                # --- MİLYON DOLARLIK CSS HACK'İ (Sıfır Kayma, Sıfır Genişleme) ---
                st.markdown("""
                <style>
                div[data-testid="stVerticalBlock"] > div {
                    gap: 0rem !important;
                }
                
                /* Streamlit'in buton etrafındaki görünmez yükseklik fazlalıklarını yokediyoruz */
                div.stButton {
                    margin: 0px !important;
                    padding: 0px !important;
                    line-height: 1 !important;
                    height: 28px !important; /* Kartın şişmesini engeller */
                }

                button[kind="tertiary"] {
                    background: transparent !important;
                    border: none !important;
                    box-shadow: none !important;
                    padding: 0px !important;
                    margin: 0px !important;
                    width: 100% !important;
                    min-height: 0px !important;
                    height: 28px !important;
                    display: block !important; 
                    text-align: right !important; 
                }

                button[kind="tertiary"] > div, button[kind="tertiary"] > span {
                    display: block !important;
                    text-align: right !important;
                    width: 100% !important;
                }

                button[kind="tertiary"] p {
                    font-size: 1.15em !important;
                    font-weight: bold !important;
                    color: white !important;
                    font-family: inherit !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    text-align: right !important;
                    transition: color 0.2s ease !important;
                }

                button[kind="tertiary"]:hover p {
                    color: #00ff00 !important;
                }
                button[kind="tertiary"]:active p {
                    color: #ffffff !important;
                }
                </style>
                """, unsafe_allow_html=True)

                for _, row in df_p.iterrows():
                    ticker, borsa, lot, maliyet = row['VARLIK'], row['BORSA'], row['LOT'], row['ORT_MALIYET']
                    fiyat = tefas_fiyat_cek(ticker) if borsa == "FON (TEFAS)" else hizli_fiyat_cek(ticker)[0]
                    if not fiyat: fiyat = maliyet
                    
                    is_foreign = borsa in ["NASDAQ", "S&P 500", "KRİPTO", "EMTİA", "ETF"]
                    carpan = anlik_dolar if is_foreign else 1.0
                    
                    varlik_maliyet_tl = maliyet * lot * carpan
                    varlik_guncel_tl = fiyat * lot * carpan
                    kar_zarar_tl = varlik_guncel_tl - varlik_maliyet_tl
                    kar_zarar_yuzde = ((fiyat - maliyet) / maliyet) * 100 if maliyet > 0 else 0
                    
                    genel_maliyet_toplami += varlik_maliyet_tl
                    genel_guncel_toplam += varlik_guncel_tl
                    dagilim_data.append({"Varlık": ticker, "Değer": varlik_guncel_tl})
                    
                    bas_harf = ticker[0].upper()
                    
                    doviz_goster = st.session_state['p_card_currency_toggles'].get(ticker, False)
                    
                    if doviz_goster and is_foreign:
                        pb_gosterim = "$"
                        maliyet_gosterim = maliyet
                        fiyat_gosterim = fiyat
                        toplam_gosterim = fiyat * lot
                        kz_gosterim = (fiyat - maliyet) * lot
                    else:
                        pb_gosterim = "₺"
                        maliyet_gosterim = (varlik_maliyet_tl / lot) if lot > 0 else 0.0
                        fiyat_gosterim = (varlik_guncel_tl / lot) if lot > 0 else 0.0
                        toplam_gosterim = varlik_guncel_tl
                        kz_gosterim = kar_zarar_tl
                        
                    renk, isaret = ("#4CAF50", "+") if kz_gosterim >= 0 else ("#FF5252", "")
                    lot_gosterim = f"{lot:,.6f}" if is_foreign else f"{lot:,.0f}"

                    with st.container(border=True):
                        c1, c2 = st.columns([6.5, 3.5])
                        
                        with c1:
                            st.markdown(f"""
                            <div style='display: flex; align-items: center; margin-top: 5px; margin-bottom: 5px;'>
                                <div style='min-width: 42px; height: 42px; border-radius: 50%; border: 1px solid rgba(0,255,0,0.4); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #00ff00; background: rgba(0,255,0,0.05); font-size: 18px;'>
                                    {bas_harf}
                                </div>
                                <div style='margin-left: 15px; line-height: 1.3;'>
                                    <div style='font-size: 0.70em; color: gray; text-transform: uppercase; letter-spacing: 0.5px;'>{borsa}</div>
                                    <div style='font-size: 1.05em; font-weight: bold; color: white;'>{ticker}</div> <div style='font-size: 0.8em; color: gray;'>Lot: {lot_gosterim} | Maliyet: {maliyet_gosterim:,.2f} {pb_gosterim}</div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"<div style='text-align: right; font-size: 0.8em; color: gray; margin-top: 5px; margin-bottom: 2px;'>Güncel: {fiyat_gosterim:,.2f} {pb_gosterim}</div>", unsafe_allow_html=True)
                            
                            if is_foreign:
                                if st.button(f"{toplam_gosterim:,.2f} {pb_gosterim}", key=f"btn_{ticker}", use_container_width=True, type="tertiary"):
                                    st.session_state['p_card_currency_toggles'][ticker] = not doviz_goster
                                    st.rerun()
                                # SİHİRLİ DOKUNUŞ: Butonun yarattığı boşluğu negatif marjinle emiyoruz
                                m_top = "-5px"
                            else:
                                st.markdown(f"<div style='text-align: right; font-size: 1.15em; font-weight: bold; color: white; padding: 0; margin: 0;'>{toplam_gosterim:,.2f} {pb_gosterim}</div>", unsafe_allow_html=True)
                                m_top = "2px"
                                
                            st.markdown(f"<div style='text-align: right; font-size: 0.85em; font-weight: bold; color: {renk}; margin-top: {m_top}; margin-bottom: 5px;'>{isaret}{kz_gosterim:,.2f} {pb_gosterim} ({isaret}%{kar_zarar_yuzde:.2f})</div>", unsafe_allow_html=True)

            # --- 2. KIYMETLİ MADEN (EMTİA) VARLIKLARI ---
            if not df_emtia.empty:
                st.markdown("##### Kıymetli Madenler (Fiziki & Banka)")
                for _, r in df_emtia.iterrows():
                    e_maden, e_mik = r['maden_turu'], r['miktar']
                    e_mal = r['toplam_maliyet'] / e_mik if e_mik > 0 else 0
                    
                    e_fiyat = emtia_fiyat_hesapla(e_maden, anlik_dolar)
                    if not e_fiyat: e_fiyat = e_mal 
                    
                    guncel_tl = e_mik * e_fiyat
                    maliyet_tl = e_mik * e_mal
                    kz_tl = guncel_tl - maliyet_tl
                    kz_yuzde = (kz_tl / maliyet_tl) * 100 if maliyet_tl > 0 else 0
                    
                    genel_maliyet_toplami += maliyet_tl
                    genel_guncel_toplam += guncel_tl
                    dagilim_data.append({"Varlık": e_maden, "Değer": guncel_tl})
                    
                    renk, isaret = ("#4CAF50", "+") if kz_tl >= 0 else ("#FF5252", "")
                    bas_harf = e_maden[0].upper()
                    
                    # Siber Tasarımlı Maden Kartı
                    kart_html = f"""
                    <div style='border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 15px; background: rgba(10,10,10,0.5); margin-bottom: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: all 0.3s ease; display: flex; justify-content: space-between; align-items: center;'>
                        <div style='display: flex; align-items: center;'>
                            <div style='min-width: 42px; height: 42px; border-radius: 50%; border: 1px solid rgba(0,255,0,0.4); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #00ff00; background: rgba(0,255,0,0.05); font-size: 18px;'>
                                {bas_harf}
                            </div>
                            <div style='margin-left: 15px; line-height: 1.3;'>
                                <div style='font-size: 0.70em; color: gray; text-transform: uppercase; letter-spacing: 0.5px;'>Fiziki & Banka</div>
                                <div style='font-size: 1.05em; font-weight: bold; color: white;'>{e_maden}</div>
                                <div style='font-size: 0.8em; color: gray;'>Miktar: {e_mik:,.2f} | Ort. Maliyet: {e_mal:,.2f} TL</div>
                            </div>
                        </div>
                        <div style='text-align: right; line-height: 1.3;'>
                            <div style='font-size: 0.8em; color: gray;'>Güncel: {e_fiyat:,.2f} TL</div>
                            <div style='font-size: 1.15em; font-weight: bold; color: white;'>{guncel_tl:,.2f} TL</div>
                            <div style='font-size: 0.85em; font-weight: bold; color: {renk};'>{isaret}{kz_tl:,.2f} TL ({isaret}%{kz_yuzde:.2f})</div>
                        </div>
                    </div>
                    """
                    st.markdown(kart_html, unsafe_allow_html=True)

            # --- 3. ANA ÖZET VE DAĞILIM GRAFİĞİ ---
            st.markdown("---")
            if genel_maliyet_toplami > 0:
                st.markdown("##### Portföy Dağılımı ve Genel Özet")
                c_grafik, c_ozet = st.columns([1.2, 1])
                
                with c_grafik:
                    if dagilim_data:
                        with st.container(border=True):
                            df_dagilim = pd.DataFrame(dagilim_data)
                            
                            # Sadece Bizim Neon Yeşilimiz ve Diğer Yeşil Tonları
                            siber_renkler = ['#00ff00', '#00cc00', '#009900', '#006600', '#4d4d4d', '#808080', '#cccccc']
                            
                            # hole=0.75 ile daha şık, ince bir siber-halka (donut) yapısına dönüştü
                            fig = px.pie(df_dagilim, values='Değer', names='Varlık', hole=0.75, color_discrete_sequence=siber_renkler)
                            fig.update_traces(
                                textposition='outside', # Yazıları dışarı aldık ki birbirine girmesin
                                textinfo='percent+label', 
                                textfont=dict(size=12, color='white', family='Consolas'), 
                                marker=dict(line=dict(color='#0A0A0A', width=3)),
                                pull=[0.02] * len(df_dagilim) # Dilimleri birbirinden milimetrik ayırarak 3D hissi verdik
                            )
                            fig.update_layout(
                                height=320, 
                                margin=dict(t=20, b=20, l=20, r=20), 
                                paper_bgcolor="rgba(0,0,0,0)", 
                                plot_bgcolor="rgba(0,0,0,0)", 
                                showlegend=False, # Lejantı tamamen gizleyip yazıları grafiğin dışına yazdık
                                annotations=[dict(text='PORTFÖY', x=0.5, y=0.5, font_size=16, font_color='gray', showarrow=False)]
                            )
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                        
                with c_ozet:
                    genel_kz_tl = genel_guncel_toplam - genel_maliyet_toplami
                    genel_kz_yuzde = (genel_kz_tl / genel_maliyet_toplami) * 100 if genel_maliyet_toplami > 0 else 0
                    
                    renk_ana = "#4CAF50" if genel_kz_tl >= 0 else "#FF5252"
                    isaret_ana = "+" if genel_kz_tl >= 0 else ""
                    
                    # HTML'in bozulmaması için baştaki girintileri (boşlukları) temizledik
                    ozet_html = f"""
<div style='display: flex; flex-direction: column; gap: 15px; height: 100%; justify-content: center;'>
    <div style='border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid gray; border-radius: 8px; padding: 15px; background: rgba(10,10,10,0.6); box-shadow: 0 4px 6px rgba(0,0,0,0.2);'>
        <div style='font-size: 0.85em; color: gray; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;'>Toplam Maliyet (Yatırılan)</div>
        <div style='font-size: 1.6em; font-weight: bold; color: white; font-family: Consolas, monospace;'>{genel_maliyet_toplami:,.2f} TL</div>
    </div>
    <div style='border: 1px solid rgba(0,255,0,0.15); border-left: 4px solid #00ff00; border-radius: 8px; padding: 15px; background: rgba(0,255,0,0.02); box-shadow: 0 4px 6px rgba(0,0,0,0.2);'>
        <div style='font-size: 0.85em; color: gray; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;'>Güncel Portföy Büyüklüğü</div>
        <div style='font-size: 1.8em; font-weight: bold; color: #00ff00; font-family: Consolas, monospace;'>{genel_guncel_toplam:,.2f} TL</div>
    </div>
    <div style='border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid {renk_ana}; border-radius: 8px; padding: 15px; background: rgba(10,10,10,0.6); box-shadow: 0 4px 6px rgba(0,0,0,0.2);'>
        <div style='font-size: 0.85em; color: gray; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;'>Net Kâr / Zarar Durumu</div>
        <div style='display: flex; align-items: baseline; gap: 10px;'>
            <div style='font-size: 1.6em; font-weight: bold; color: {renk_ana}; font-family: Consolas, monospace;'>{isaret_ana}{genel_kz_tl:,.2f} TL</div>
            <div style='font-size: 1.1em; font-weight: bold; color: {renk_ana}; background: rgba({255 if genel_kz_tl < 0 else 0},{255 if genel_kz_tl >= 0 else 0},0,0.1); padding: 2px 8px; border-radius: 4px;'>{isaret_ana}%{genel_kz_yuzde:.2f}</div>
        </div>
    </div>
</div>
"""
                    st.markdown(ozet_html, unsafe_allow_html=True)

            # --- 4. AKILLI KÂR/ZARAR OPTİMİZASYON MOTORU ---
            st.markdown("---")
            with st.expander(" Kâr-Zarar Optimizasyonu"):
                    st.info("Ekranda görünen kâr veya zarar rakamında hata varsa, buraya olması gereken GERÇEK kâr/zarar miktarınızı yazın. Sistem tersine mühendislik yaparak doğru alış maliyetinizi hesaplayıp veritabanını güncelleyecektir.")
                    if not df_p.empty:
                        c_opt1, c_opt2 = st.columns(2)
                        opt_secim = c_opt1.selectbox("Düzeltilecek Varlık:", df_p['VARLIK'].tolist())
                        
                        # Seçilen varlığın verilerini çek
                        secilen_r = df_p[df_p['VARLIK'] == opt_secim].iloc[0]
                        opt_lot = secilen_r['LOT']
                        opt_borsa = secilen_r['BORSA']
                        
                        # Anlık Fiyatı ve Çarpanı Bul
                        opt_fiyat = tefas_fiyat_cek(opt_secim) if opt_borsa == "FON (TEFAS)" else hizli_fiyat_cek(opt_secim)[0]
                        if not opt_fiyat: opt_fiyat = secilen_r['ORT_MALIYET']
                        opt_carpan = anlik_dolar if opt_borsa in ["NASDAQ", "S&P 500", "KRİPTO", "EMTİA"] else 1.0
                        
                        hedef_kar_tl = c_opt2.number_input("Gerçek Kâr / Zarar Tutarı (TL)", value=0.0, step=10.0, format="%.2f")
                        st.caption("Uyarı: Eğer varlıktan zarardaysanız tutarın başına eksi (-) koyarak yazın. Örn: -450")
                        
                        if st.button("Optimizasyonu Başlat", type="primary", use_container_width=True):
                            # --- TERSİNE MÜHENDİSLİK MATEMATİĞİ ---
                            guncel_deger_tl = float(opt_lot * opt_fiyat * opt_carpan)
                            hedef_toplam_maliyet_tl = float(guncel_deger_tl - hedef_kar_tl)
                            yeni_birim_maliyet = float(hedef_toplam_maliyet_tl / (opt_lot * opt_carpan))
                            
                            conn = get_db()
                            try:
                                c = conn.cursor()
                                c.execute("UPDATE portfoy SET maliyet = %s WHERE kullanici_adi = %s AND varlik_adi = %s AND lot > 0", (yeni_birim_maliyet, k_adi, opt_secim))
                                conn.commit()
                                st.success(f"Düzeltme Başarılı! Yeni Birim Maliyet: {yeni_birim_maliyet:,.4f} olarak ayarlandı.")
                                time.sleep(1.5)
                                st.rerun()
                            except Exception as e:
                                st.error(f"Optimizasyon Hatası: {e}")
                            finally: release_db(conn)

        with tab2:
            c_borsa, c_maden = st.columns(2)
            
            # ==========================================
            # 1. SOL BLOK: BORSA VE FON İŞLEMLERİ
            # ==========================================
            with c_borsa:
                st.markdown("<div style='display: flex; align-items: center; margin-bottom: 15px;'><div style='width: 10px; height: 10px; background: #00ff00; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 8px #00ff00;'></div><div style='color: #00ff00; font-size: 1.1em; font-weight: 700; letter-spacing: 1px; font-family: Consolas;'>BORSA VE FON İŞLEMLERİ</div></div>", unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown("<span style='color: gray; font-size: 0.85em;'>İşlem Yönü:</span>", unsafe_allow_html=True)
                    tip = st.radio("İşlem Yönü (Borsa):", ["ALIM", "SATIM"], horizontal=True, label_visibility="collapsed")
                    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 5px 0 15px 0;'>", unsafe_allow_html=True)
                    
                    conn = get_db()
                    df_eldeki = pd.read_sql_query("SELECT varlik_adi, borsa, SUM(lot) as toplam_lot FROM portfoy WHERE kullanici_adi = %s GROUP BY varlik_adi, borsa HAVING SUM(lot) > 0", conn, params=(k_adi,))
                    release_db(conn)
                    eldeki_list = df_eldeki['varlik_adi'].tolist() if not df_eldeki.empty else []

                    st.markdown("<span style='color: gray; font-size: 0.85em;'>Piyasa / Varlık Seçimi:</span>", unsafe_allow_html=True)
                    if tip == "ALIM":
                        brsa = st.selectbox("Piyasa Seçimi:", ["BİST", "KRİPTO", "FON (TEFAS)", "NASDAQ", "ETF", "EMTİA", "S&P 500"], label_visibility="collapsed")
                        v_kod_sat = None
                    else:
                        v_kod_sat = st.selectbox("Satılacak Varlık:", eldeki_list if eldeki_list else ["Elde Varlık Yok"], label_visibility="collapsed")
                        brsa = df_eldeki[df_eldeki['varlik_adi'] == v_kod_sat]['borsa'].values[0] if v_kod_sat != "Elde Varlık Yok" else "BİST"
                    
                    with st.form("borsa_form"):
                        st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 5px 0 15px 0;'>", unsafe_allow_html=True)
                        c1, c2 = st.columns(2)
                        if tip == "ALIM":
                            v_kod = c1.text_input("Varlık Kodu (Örn: MAC, VOO, SQQQ)")
                            max_eldeki = 0.0
                        else:
                            v_kod = v_kod_sat
                            c1.text_input("Varlık Kodu", value=v_kod, disabled=True)
                            max_eldeki = df_eldeki[df_eldeki['varlik_adi'] == v_kod]['toplam_lot'].values[0] if v_kod in eldeki_list else 0.0

                        tumu = st.checkbox(f"Tümünü İşleme Al (Mevcut: {max_eldeki})") if tip == "SATIM" else False
                        
                        cx1, cx2 = st.columns(2)
                        v_lot = cx1.number_input("Miktar (Lot / Pay)", min_value=0.0, value=float(max_eldeki) if tumu and tip == "SATIM" else 0.0, step=0.00000001, format="%.8f")
                        v_fiyat = cx2.number_input("Birim Fiyat (USD/TL)", min_value=0.0, step=0.000001, format="%.6f")
                        
                        fon_valoru = 0
                        if brsa == "FON (TEFAS)":
                            fon_valoru = st.number_input("İzahname Valörü (İş Günü):", min_value=0, max_value=7, step=1, value=0)
                        
                        cekim_tipi = "Standart"
                        if tip == "SATIM" and brsa in ["BİST", "NASDAQ", "S&P 500", "ETF"]:
                            st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 10px 0 10px 0;'>", unsafe_allow_html=True)
                            st.markdown("<span style='color: gray; font-size: 0.85em;'>Takas ve Nakit Yöntemi:</span>", unsafe_allow_html=True)
                            cekim_tipi = st.radio("Nakit Geçiş Yöntemi", ["T+2 Bekle (Ücretsiz)", "Anında Çek (%0.6 Komisyon)"], label_visibility="collapsed")

                        st.markdown("<br>", unsafe_allow_html=True)
                        if st.form_submit_button("Borsa Emrini İlet", type="primary", use_container_width=True):
                            if v_kod and v_lot > 0 and v_fiyat > 0:
                                if brsa == "BİST" and not float(v_lot).is_integer():
                                    st.error("Hata: BİST piyasasında hisseler parçalı (küsuratlı) alınamaz."); st.stop()
                                    
                                t_kod = v_kod.upper()
                                if brsa == "BİST" and ".IS" not in t_kod: ticker = t_kod + ".IS"
                                elif brsa == "KRİPTO" and "-USD" not in t_kod: ticker = t_kod + "-USD"
                                elif brsa == "EMTİA" and "=F" not in t_kod: ticker = t_kod + "=F"
                                else: ticker = t_kod 

                                is_usd_market = brsa in ["NASDAQ", "S&P 500", "KRİPTO", "EMTİA", "ETF"]
                                is_midas_us = brsa in ["NASDAQ", "S&P 500", "ETF"]
                                komisyon_usd = 1.50 if is_midas_us else 0.0
                                
                                usd_kur = doviz_kuru_cek("USD")
                                carpan = usd_kur if is_usd_market else 1.0
                                islem_tutari_baz = v_lot * v_fiyat
                                islem_tutari_tl = islem_tutari_baz * carpan
                                komisyon_tl = komisyon_usd * usd_kur
                                
                                conn = get_db()
                                try:
                                    c = conn.cursor()
                                    c.execute("SELECT bakiye FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (k_adi,))
                                    m_tl = c.fetchone()[0] if c.rowcount > 0 else 0.0
                                    c.execute("SELECT bakiye FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı (USD)'", (k_adi,))
                                    m_usd = c.fetchone()[0] if c.rowcount > 0 else 0.0

                                    c.execute("SELECT COALESCE(SUM(tutar), 0) FROM takas_bekleyen_islemler WHERE kullanici_adi = %s AND durum = 'Bekliyor' AND islem_yonu = 'SATIM'", (k_adi,))
                                    takastaki_para_tl = c.fetchone()[0]
                                    alim_gucu_tl = m_tl + takastaki_para_tl

                                    if tip == "ALIM":
                                        if is_usd_market:
                                            toplam_gerekli_usd = islem_tutari_baz + komisyon_usd
                                            
                                            # --- MİDAS KÜSURAT VE YUVARLAMA TOLERANSI ---
                                            if 0 < (toplam_gerekli_usd - m_usd) <= 0.15:
                                                toplam_gerekli_usd = m_usd
                                                islem_tutari_baz = m_usd - komisyon_usd
                                                islem_tutari_tl = islem_tutari_baz * carpan

                                            if toplam_gerekli_usd > m_usd: 
                                                st.error(f"Yetersiz Bakiye. (İşlem: {islem_tutari_baz:,.2f} USD + Komisyon: {komisyon_usd} USD = Gereken: {toplam_gerekli_usd:,.2f} USD)"); st.stop()
                                            else: 
                                                c.execute("UPDATE hesaplar SET bakiye = bakiye - %s WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı (USD)'", (toplam_gerekli_usd, k_adi))
                                        else:
                                            if 0 < (islem_tutari_baz - alim_gucu_tl) <= 2.0:
                                                islem_tutari_baz = alim_gucu_tl
                                                islem_tutari_tl = alim_gucu_tl

                                            if islem_tutari_baz > alim_gucu_tl: 
                                                st.error(f"Yetersiz Bakiye! Alım Gücünüz: {alim_gucu_tl:,.2f} TL, Gereken: {islem_tutari_baz:,.2f} TL"); st.stop()
                                            else:
                                                c.execute("UPDATE bakiyeler SET bakiye = bakiye - %s WHERE kullanici_adi = %s", (islem_tutari_baz, k_adi))
                                                c.execute("UPDATE hesaplar SET bakiye = bakiye - %s WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (islem_tutari_baz, k_adi))
                                        
                                        c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'BORSA ALIM', %s, %s)", (k_adi, f"{v_lot:.8f} lot {ticker} ({islem_tutari_baz:,.2f} {'USD' if is_usd_market else 'TL'})", -islem_tutari_tl))
                                        
                                        if komisyon_usd > 0:
                                            c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'KOMİSYON GİDERİ (-)', %s, %s)", (k_adi, f"{ticker} ABD Borsa Alım Komisyonu ({komisyon_usd} USD)", -komisyon_tl))
                                            c.execute("INSERT INTO harcamalar (kullanici_adi, kategori, aciklama, tutar, kaynak_hesap) VALUES (%s, 'Banka Kesintisi', %s, %s, 'Yatırım Hesabı (USD)')", (k_adi, f"{ticker} Alım Komisyonu", komisyon_tl))

                                        if brsa == "FON (TEFAS)":
                                            bugun_tarih, takas_tarihi = fon_takas_tarihi_hesapla(fon_valoru)
                                            if takas_tarihi == datetime.date.today():
                                                c.execute("INSERT INTO portfoy (kullanici_adi, varlik_adi, lot, maliyet, borsa) VALUES (%s,%s,%s,%s,%s)", (k_adi, ticker, v_lot, v_fiyat, brsa))
                                                st.session_state.islem_bildirimi = {"mesaj": f"{ticker} fonu portföyünüze eklendi."}
                                            else:
                                                c.execute("INSERT INTO takas_bekleyen_islemler (kullanici_adi, varlik, tutar, islem_tarihi, takas_tarihi, islem_yonu, lot, maliyet, borsa) VALUES (%s,%s,%s,%s,%s,'ALIM',%s,%s,%s)", (k_adi, ticker, islem_tutari_baz, bugun_tarih, takas_tarihi, v_lot, v_fiyat, brsa))
                                                st.session_state.islem_bildirimi = {"mesaj": f"Fon alım emri verildi. Takas: {takas_tarihi.strftime('%d.%m.%Y')}"}
                                        else:
                                            c.execute("INSERT INTO portfoy (kullanici_adi, varlik_adi, lot, maliyet, borsa) VALUES (%s,%s,%s,%s,%s)", (k_adi, ticker, v_lot, v_fiyat, brsa))
                                            if komisyon_usd > 0:
                                                st.session_state.islem_bildirimi = {"mesaj": f"{ticker} başarıyla alındı. {islem_tutari_baz:,.2f} USD işlem ve {komisyon_usd}$ komisyon USD bakiyeden düşüldü."}
                                            else:
                                                st.session_state.islem_bildirimi = {"mesaj": f"{ticker} başarıyla alındı."}
                                        conn.commit(); st.rerun()

                                    else: # SATIM
                                        if max_eldeki < v_lot: st.error("Yetersiz Lot."); st.stop()
                                        
                                        c.execute("SELECT SUM(lot * maliyet) / NULLIF(SUM(lot), 0) FROM portfoy WHERE kullanici_adi = %s AND varlik_adi = %s AND lot > 0", (k_adi, ticker))
                                        ort_maliyet_res = c.fetchone()
                                        ort_maliyet = float(ort_maliyet_res[0]) if ort_maliyet_res and ort_maliyet_res[0] else float(v_fiyat)
                                        kar_zarar_miktari_tl = (float(v_fiyat) - ort_maliyet) * float(v_lot) * carpan
                                        
                                        if kar_zarar_miktari_tl > 0:
                                            a_msg = f"{ticker} pozisyonunuzdan {kar_zarar_miktari_tl:,.2f} TL kâr realize edilmiştir."
                                            c.execute("INSERT INTO asistan_bildirimleri (kullanici_adi, baslik, mesaj, tur) VALUES (%s, 'Kâr Realizasyonu Bildirimi', %s, 'SATIM')", (k_adi, a_msg))
                                        elif kar_zarar_miktari_tl < 0:
                                            a_msg = f"{ticker} varlığında {abs(kar_zarar_miktari_tl):,.2f} TL zarar kesim (stop-loss) işlemi gerçekleştirilmiştir."
                                            c.execute("INSERT INTO asistan_bildirimleri (kullanici_adi, baslik, mesaj, tur) VALUES (%s, 'Zarar Kesim Bildirimi', %s, 'SATIM')", (k_adi, a_msg))

                                        c.execute("INSERT INTO portfoy (kullanici_adi, varlik_adi, lot, maliyet, borsa) VALUES (%s,%s,%s,%s,%s)", (k_adi, ticker, -v_lot, v_fiyat, brsa))
                                        
                                        if is_usd_market:
                                            ele_gecen_usd = islem_tutari_baz - komisyon_usd
                                            if ele_gecen_usd < 0:
                                                st.error("Hata: İşlem tutarı, 1.50$ komisyonu karşılamaya yetmiyor."); st.stop()
                                                
                                            c.execute("UPDATE hesaplar SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı (USD)'", (ele_gecen_usd, k_adi))
                                            c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'BORSA SATIM (USD)', %s, %s)", (k_adi, f"{v_lot:.8f} lot {ticker} ({islem_tutari_baz:,.2f} USD)", islem_tutari_tl))
                                            
                                            if komisyon_usd > 0:
                                                c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'KOMİSYON GİDERİ (-)', %s, %s)", (k_adi, f"{ticker} ABD Borsa Satım Komisyonu ({komisyon_usd} USD)", -komisyon_tl))
                                                c.execute("INSERT INTO harcamalar (kullanici_adi, kategori, aciklama, tutar, kaynak_hesap) VALUES (%s, 'Banka Kesintisi', %s, %s, 'Yatırım Hesabı (USD)')", (k_adi, f"{ticker} Satım Komisyonu", komisyon_tl))
                                                st.session_state.islem_bildirimi = {"mesaj": f"Satış başarılı. 1.50$ komisyon düşülerek {ele_gecen_usd:,.2f} USD nakit bakiyenize eklendi."}
                                            else:
                                                st.session_state.islem_bildirimi = {"mesaj": f"Satış başarılı. {ele_gecen_usd:,.2f} USD nakit bakiyenize eklendi."}
                                        
                                        elif brsa == "FON (TEFAS)":
                                            bugun_tarih, takas_tarihi = fon_takas_tarihi_hesapla(fon_valoru)
                                            if takas_tarihi == datetime.date.today():
                                                c.execute("UPDATE bakiyeler SET bakiye = bakiye + %s WHERE kullanici_adi = %s", (islem_tutari_baz, k_adi))
                                                c.execute("UPDATE hesaplar SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (islem_tutari_baz, k_adi))
                                                c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'BORSA SATIM', %s, %s)", (k_adi, f"{v_lot:.8f} lot {ticker}", islem_tutari_baz))
                                                st.session_state.islem_bildirimi = {"mesaj": f"{ticker} satıldı, tutar bakiyenize eklendi."}
                                            else:
                                                c.execute("INSERT INTO takas_bekleyen_islemler (kullanici_adi, varlik, tutar, islem_tarihi, takas_tarihi, islem_yonu) VALUES (%s,%s,%s,%s,%s,'SATIM')", (k_adi, ticker, islem_tutari_baz, bugun_tarih, takas_tarihi))
                                                c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'BORSA SATIM (Takas Bekliyor)', %s, %s)", (k_adi, f"{v_lot:.8f} lot {ticker}", islem_tutari_baz))
                                                st.session_state.islem_bildirimi = {"mesaj": f"Fon satıldı. Takas: {takas_tarihi.strftime('%d.%m.%Y')}"}
                                        
                                        else: # BİST
                                            if "T+2" in cekim_tipi:
                                                bugun_tarih, takas_tarihi = t_arti_2_hesapla()
                                                c.execute("INSERT INTO takas_bekleyen_islemler (kullanici_adi, varlik, tutar, islem_tarihi, takas_tarihi, islem_yonu) VALUES (%s,%s,%s,%s,%s,'SATIM')", (k_adi, ticker, islem_tutari_baz, bugun_tarih, takas_tarihi))
                                                c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'BORSA SATIM (T+2 Bekliyor)', %s, %s)", (k_adi, f"{v_lot:.8f} lot {ticker}", islem_tutari_baz))
                                                st.session_state.islem_bildirimi = {"mesaj": f"Satış başarılı. Tutar {takas_tarihi.strftime('%d.%m.%Y')} tarihinde bakiyenize geçecek."}
                                            else:
                                                net_ele_gecen = islem_tutari_baz - (islem_tutari_baz * 0.006 * 1.05)
                                                c.execute("UPDATE bakiyeler SET bakiye = bakiye + %s WHERE kullanici_adi = %s", (net_ele_gecen, k_adi))
                                                c.execute("UPDATE hesaplar SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (net_ele_gecen, k_adi))
                                                c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'BORSA SATIM (Anında Nakit)', %s, %s)", (k_adi, f"{v_lot:.8f} lot {ticker}", net_ele_gecen))
                                                st.session_state.islem_bildirimi = {"mesaj": f"Satış yapıldı. Vergi/Komisyon sonrası {net_ele_gecen:,.2f} TL hesabınıza yattı."}
                                        conn.commit(); st.rerun()
                                finally: release_db(conn)

            # ==========================================
            # 2. SAĞ BLOK: KIYMETLİ MADEN İŞLEMLERİ
            # ==========================================
            with c_maden:
                st.markdown("<div style='display: flex; align-items: center; margin-bottom: 15px;'><div style='width: 10px; height: 10px; background: #FFD700; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 8px #FFD700;'></div><div style='color: #FFD700; font-size: 1.1em; font-weight: 700; letter-spacing: 1px; font-family: Consolas;'>KIYMETLİ MADEN İŞLEMLERİ</div></div>", unsafe_allow_html=True)
                with st.container(border=True):
                    st.markdown("<span style='color: gray; font-size: 0.85em;'>İşlem Yönü:</span>", unsafe_allow_html=True)
                    e_islem_tipi = st.radio("İşlem Yönü (Maden):", ["ALIM", "SATIM"], horizontal=True, key="emtia_islem_tipi", label_visibility="collapsed")
                    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 5px 0 15px 0;'>", unsafe_allow_html=True)
                    
                    conn = get_db()
                    try:
                        df_e_hesaplar = pd.read_sql_query("SELECT hesap_adi, bakiye FROM banka_hesaplari WHERE kullanici_adi = %s AND hesap_turu = 'Vadesiz'", conn, params=(k_adi,))
                        df_e_portfoy = pd.read_sql_query("SELECT maden_turu, bagli_hesap, miktar, ortalama_maliyet FROM emtia_portfoy WHERE kullanici_adi = %s AND miktar > 0", conn, params=(k_adi,))
                    except:
                        df_e_hesaplar, df_e_portfoy = pd.DataFrame(), pd.DataFrame()
                    finally: release_db(conn)

                    e_hesap_listesi = [f"{r['hesap_adi']} (Bakiye: {r['bakiye']:,.2f} TL)" for _, r in df_e_hesaplar.iterrows()] if not df_e_hesaplar.empty else []

                    with st.form("emtia_islem_formu"):
                        st.markdown("<span style='color: gray; font-size: 0.85em;'>Maden Türü ve Hesap Seçimi:</span>", unsafe_allow_html=True)
                        if e_islem_tipi == "ALIM":
                            e_maden = st.selectbox("Maden Türü", ["Gram Altın (XAU/TRY)", "Gram Gümüş (XAG/TRY)", "Ons Altın (XAU/USD)", "Platin", "Paladyum"], label_visibility="collapsed")
                            e_hesap = st.selectbox("İşlemin Çıkacağı Hesap (-)", e_hesap_listesi if e_hesap_listesi else ["Hesap Bulunamadı"])
                            max_e = 0.0
                        else:
                            if not df_e_portfoy.empty:
                                e_sat_liste = [f"{r['maden_turu']} | Hesap: {r['bagli_hesap']} (Mevcut: {r['miktar']:,.2f})" for _, r in df_e_portfoy.iterrows()]
                            else:
                                e_sat_liste = ["Elde Maden Yok"]
                            e_secilen_sat = st.selectbox("Satılacak Maden ve Kasa", e_sat_liste, label_visibility="collapsed")
                            
                            if e_secilen_sat != "Elde Maden Yok":
                                e_maden = e_secilen_sat.split(" | ")[0]
                                e_hesap_saf = e_secilen_sat.split("Hesap: ")[1].split(" (")[0]
                                max_e = df_e_portfoy[(df_e_portfoy['maden_turu'] == e_maden) & (df_e_portfoy['bagli_hesap'] == e_hesap_saf)]['miktar'].values[0]
                            else:
                                e_maden, e_hesap_saf, max_e = None, None, 0.0
                            e_hesap = None
                            
                        st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 5px 0 15px 0;'>", unsafe_allow_html=True)
                        ce1, ce2 = st.columns(2)
                        e_miktar = ce1.number_input("Miktar (Gr/Adet)", min_value=0.0, step=1.0, value=float(max_e) if e_islem_tipi=="SATIM" else 0.0)
                        e_fiyat = ce2.number_input("Birim Fiyat (TL)", min_value=0.0, step=10.0)
                        
                        st.markdown("<br>", unsafe_allow_html=True)
                        submit_emtia = st.form_submit_button(f"Maden {e_islem_tipi} Emrini İlet", type="primary", use_container_width=True)

                        if submit_emtia:
                            if e_miktar > 0 and e_fiyat > 0:
                                conn = get_db()
                                try:
                                    c = conn.cursor()
                                    islem_tutari = e_miktar * e_fiyat
                                    
                                    if e_islem_tipi == "ALIM":
                                        if e_hesap == "Hesap Bulunamadı": st.error("Lütfen Vadesiz Hesap ekleyin."); st.stop()
                                        h_saf = e_hesap.split(" (")[0]
                                        bakiye_kontrol = df_e_hesaplar[df_e_hesaplar['hesap_adi'] == h_saf]['bakiye'].values[0]
                                        
                                        if islem_tutari > bakiye_kontrol:
                                            st.error("İşlem Reddedildi: Banka hesabınızda yeterli bakiye yok.")
                                        else:
                                            c.execute("UPDATE banka_hesaplari SET bakiye = bakiye - %s WHERE kullanici_adi = %s AND hesap_adi = %s", (islem_tutari, k_adi, h_saf))
                                            c.execute("SELECT id, miktar, ortalama_maliyet FROM emtia_portfoy WHERE kullanici_adi = %s AND maden_turu = %s AND bagli_hesap = %s", (k_adi, e_maden, h_saf))
                                            kayit = c.fetchone()
                                            if kayit:
                                                eski_mik, eski_mal = kayit[1], kayit[2]
                                                yeni_maliyet = ((eski_mik * eski_mal) + islem_tutari) / (eski_mik + e_miktar)
                                                c.execute("UPDATE emtia_portfoy SET miktar = miktar + %s, ortalama_maliyet = %s WHERE id = %s", (e_miktar, yeni_maliyet, kayit[0]))
                                            else:
                                                c.execute("INSERT INTO emtia_portfoy (kullanici_adi, maden_turu, miktar, ortalama_maliyet, bagli_hesap) VALUES (%s,%s,%s,%s,%s)", (k_adi, e_maden, e_miktar, e_fiyat, h_saf))
                                            
                                            c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'MADEN ALIM (-)', %s, %s)", (k_adi, f"{e_miktar:,.2f} gr/adet {e_maden} ({h_saf})", -islem_tutari))
                                            conn.commit()
                                            st.session_state.islem_bildirimi = {"mesaj": f"Alım başarılı. {islem_tutari:,.2f} TL bankanızdan tahsil edildi."}
                                            st.rerun()
                                            
                                    else: # SATIM
                                        if e_secilen_sat == "Elde Maden Yok": st.stop()
                                        if e_miktar > max_e: st.error("Elinizdeki miktardan fazlasını satamazsınız."); st.stop()
                                        
                                        c.execute("UPDATE banka_hesaplari SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = %s", (islem_tutari, k_adi, e_hesap_saf))
                                        c.execute("UPDATE emtia_portfoy SET miktar = miktar - %s WHERE kullanici_adi = %s AND maden_turu = %s AND bagli_hesap = %s", (e_miktar, k_adi, e_maden, e_hesap_saf))
                                        c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'MADEN SATIM (+)', %s, %s)", (k_adi, f"{e_miktar:,.2f} gr/adet {e_maden} satıldı ({e_hesap_saf})", islem_tutari))
                                        conn.commit()
                                        st.session_state.islem_bildirimi = {"mesaj": f"Satış başarılı. {islem_tutari:,.2f} TL {e_hesap_saf} hesabınıza yattı."}
                                        st.rerun()
                                finally: release_db(conn)

            # ==========================================
            # 3. ALT BLOK: DÖVİZ İŞLEMLERİ (TAM GENİŞLİK)
            # ==========================================
            doviz_islem_modulu(k_adi, "portfoy_tab2")   

        with tab3: 
            st.markdown("<div style='display: flex; align-items: center; margin-bottom: 15px;'><div style='width: 10px; height: 10px; background: #bb86fc; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 8px #bb86fc;'></div><div style='color: #bb86fc; font-size: 1.1em; font-weight: 700; letter-spacing: 1px; font-family: Consolas;'>KURUM İÇİ TRANSFER (VİRMAN)</div></div>", unsafe_allow_html=True)
            
            conn = get_db()
            try:
                df_tum_vad = pd.read_sql_query("SELECT hesap_adi, bakiye, para_birimi FROM banka_hesaplari WHERE kullanici_adi = %s", conn, params=(k_adi,))
                c = conn.cursor()
                c.execute("SELECT hesap_adi, bakiye FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi LIKE '%%Yatırım Hesabı%%'", (k_adi,))
                y_hesaplar = c.fetchall()
            finally: release_db(conn)
            
            transfer_hesaplari = [f"Hesap: {r['hesap_adi']} ({r['bakiye']:.2f} {r['para_birimi'] if r['para_birimi'] else 'TL'})" for _, r in df_tum_vad.iterrows()]
            for yh in y_hesaplar: transfer_hesaplari.append(f"Yatırım: {yh[0]} ({yh[1]:.2f} {'USD' if '(USD)' in yh[0] else 'EUR' if '(EUR)' in yh[0] else 'TL'})")

            with st.container(border=True):
                st.markdown("<div style='background: rgba(187, 134, 252, 0.05); padding: 10px 15px; border-radius: 6px; border: 1px solid rgba(187, 134, 252, 0.2); margin-bottom: 20px; font-size: 0.85em; color: #e0e0e0;'>Kendi hesaplarınız ve portföy kasalarınız arasında komisyonsuz veya düşük masraflı fon aktarımı yapabilirsiniz.</div>", unsafe_allow_html=True)
                
                st.markdown("<span style='color: gray; font-size: 0.85em;'>Çıkış Yapılacak Kaynak:</span>", unsafe_allow_html=True)
                gonderen = st.selectbox("Çıkış Yapılacak Kaynak", transfer_hesaplari, label_visibility="collapsed", key="v_kaynak_portfoy")
                kalan_hesaplar = [h for h in transfer_hesaplari if h != gonderen]
                
                k_bak_p = float(gonderen.rsplit("(", 1)[1].replace(")", "").split(" ")[0])
                k_pb_p = gonderen.rsplit("(", 1)[1].replace(")", "").split(" ")[1]

                with st.form("yatirim_virman_form"):
                    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 5px 0 15px 0;'>", unsafe_allow_html=True)
                    st.markdown("<span style='color: gray; font-size: 0.85em;'>Giriş Yapılacak Hedef:</span>", unsafe_allow_html=True)
                    alan = st.selectbox("Giriş Yapılacak Hedef:", kalan_hesaplar, label_visibility="collapsed")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    tumu_p = st.checkbox(f"Tüm Bakiyeyi Transfer Et (Mevcut: {k_bak_p:,.2f} {k_pb_p})")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    c_tut, c_kom = st.columns(2)
                    tutar = c_tut.number_input("Transfer Tutarı", min_value=0.0, value=0.0, step=100.0, disabled=tumu_p)
                    komisyon = c_kom.number_input("Komisyon / Masraf", min_value=0.0, step=5.0, value=0.0)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.form_submit_button("Transferi Başlat", type="primary", use_container_width=True):
                        k_saf = gonderen.rsplit(" (", 1)[0].replace("Hesap: ", "").replace("Yatırım: ", "")
                        h_saf = alan.rsplit(" (", 1)[0].replace("Hesap: ", "").replace("Yatırım: ", "")
                        k_pb = gonderen.rsplit("(", 1)[1].replace(")", "").split(" ")[1]
                        h_pb = alan.rsplit("(", 1)[1].replace(")", "").split(" ")[1]
                        k_bak = float(gonderen.rsplit("(", 1)[1].replace(")", "").split(" ")[0])
                        
                        islem_tutari = (k_bak - komisyon) if tumu_p else tutar
                        if islem_tutari <= 0: st.error("Hata: Transfer tutarı 0'dan büyük olmalıdır (Komisyon bakiyeyi aşıyor olabilir)."); st.stop()
                        
                        toplam_cikis = islem_tutari + komisyon
                        if toplam_cikis > k_bak: st.error("Yetersiz Bakiye (Tutar + Komisyon)."); st.stop()
                        
                        kur_k, kur_h = doviz_kuru_cek(k_pb), doviz_kuru_cek(h_pb)
                        tutar_tl, hedef_tutar = islem_tutari * kur_k, (islem_tutari * kur_k) / kur_h
                        komisyon_tl = komisyon * kur_k
                        
                        conn = get_db()
                        try:
                            c = conn.cursor()
                            if "Yatırım:" in gonderen:
                                c.execute("UPDATE hesaplar SET bakiye = bakiye - %s WHERE kullanici_adi = %s AND hesap_adi = %s", (toplam_cikis, k_adi, k_saf))
                                if k_pb == "TL": c.execute("UPDATE bakiyeler SET bakiye = bakiye - %s WHERE kullanici_adi = %s", (toplam_cikis, k_adi))
                            else: c.execute("UPDATE banka_hesaplari SET bakiye = bakiye - %s WHERE kullanici_adi = %s AND hesap_adi = %s", (toplam_cikis, k_adi, k_saf))
                                
                            if "Yatırım:" in alan:
                                c.execute("UPDATE hesaplar SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = %s", (hedef_tutar, k_adi, h_saf))
                                if h_pb == "TL": c.execute("UPDATE bakiyeler SET bakiye = bakiye + %s WHERE kullanici_adi = %s", (hedef_tutar, k_adi))
                            else: c.execute("UPDATE banka_hesaplari SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = %s", (hedef_tutar, k_adi, h_saf))
                                
                            c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'VİRMAN', %s, %s)", (k_adi, f"{k_saf} ({islem_tutari:.2f} {k_pb}) -> {h_saf} ({hedef_tutar:.2f} {h_pb})", tutar_tl))
                            if komisyon > 0:
                                c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'KOMİSYON GİDERİ (-)', %s, %s)", (k_adi, f"{k_saf} Transfer Ücreti", -komisyon_tl))
                                c.execute("INSERT INTO harcamalar (kullanici_adi, kategori, aciklama, tutar, kaynak_hesap) VALUES (%s, 'Banka Kesintisi', 'Transfer Komisyonu', %s, %s)", (k_adi, komisyon_tl, k_saf))

                            conn.commit()
                            st.success(f"İşlem Tamamlandı: {islem_tutari:.2f} {k_pb} -> {hedef_tutar:.2f} {h_pb} aktarıldı. (Kesinti: {komisyon:.2f} {k_pb})"); st.rerun()
                        finally: release_db(conn)
            
        with tab4: 
            st.markdown("<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;'><div style='display: flex; align-items: center;'><div style='width: 10px; height: 10px; background: #ffb300; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 8px #ffb300;'></div><div style='color: #ffb300; font-size: 1.1em; font-weight: 700; letter-spacing: 1px; font-family: Consolas;'>PORTFÖY İŞLEM LOGLARI</div></div></div>", unsafe_allow_html=True)
            
            zaman_filtresi_yat = st.selectbox("Zaman Aralığı:", ["Bugün", "Son 24 Saat", "Son 7 Gün", "Son 15 Gün", "Son 1 Ay", "Tümü"], index=2)
            st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
            
            conn = get_db()
            try:
                df_b_gecmis = pd.read_sql_query("SELECT tarih, islem_tipi, detay, tutar FROM islem_gecmisi WHERE kullanici_adi = %s AND islem_tipi LIKE 'BORSA%%' ORDER BY tarih DESC", conn, params=(k_adi,))
                df_n_gecmis = pd.read_sql_query("SELECT tarih, islem_tipi, detay, tutar FROM islem_gecmisi WHERE kullanici_adi = %s AND (islem_tipi = 'VİRMAN' OR detay LIKE '%%Yatırım Hesabı%%') ORDER BY tarih DESC", conn, params=(k_adi,))
            finally: release_db(conn)

            bugun_t = pd.Timestamp.today()
            def filtrele(df, filtre_tipi):
                if df.empty: return df
                df['t_dt'] = pd.to_datetime(df['tarih'])
                if filtre_tipi == "Bugün": return df[df['t_dt'].dt.date == bugun_t.date()]
                elif filtre_tipi == "Son 24 Saat": return df[df['t_dt'] >= bugun_t - pd.Timedelta(hours=24)]
                elif filtre_tipi == "Son 7 Gün": return df[df['t_dt'] >= bugun_t - pd.Timedelta(days=7)]
                elif filtre_tipi == "Son 15 Gün": return df[df['t_dt'] >= bugun_t - pd.Timedelta(days=15)]
                elif filtre_tipi == "Son 1 Ay": return df[df['t_dt'] >= bugun_t - pd.DateOffset(months=1)]
                return df

            df_b_gecmis, df_n_gecmis = filtrele(df_b_gecmis, zaman_filtresi_yat), filtrele(df_n_gecmis, zaman_filtresi_yat)

            # İşlem listelerini yan yana koyup ekranı şıklaştırıyoruz
            c_log1, c_log2 = st.columns(2)
            
            with c_log1:
                st.markdown("<div style='color: gray; font-size: 0.9em; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 1px;'>Borsa İşlem Dökümü</div>", unsafe_allow_html=True)
                with st.container(height=400, border=True):
                    if not df_b_gecmis.empty:
                        for _, r in df_b_gecmis.iterrows():
                            renk = "#00ff00" if r['tutar'] > 0 else "#FF5252"
                            isaret = "+" if r['tutar'] > 0 else "-"
                            st.markdown(f"""
                            <div style='background: rgba(10,10,10,0.5); border-left: 3px solid {renk}; padding: 12px; border-radius: 4px; margin-bottom: 8px; border-top: 1px solid rgba(255,255,255,0.02); border-right: 1px solid rgba(255,255,255,0.02); border-bottom: 1px solid rgba(255,255,255,0.02);'>
                                <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                                    <div>
                                        <div style='color: white; font-weight: bold; font-size: 0.95em;'>{r['islem_tipi']}</div>
                                        <div style='color: gray; font-size: 0.8em; margin-top: 4px;'>{r['detay']}</div>
                                    </div>
                                    <div style='text-align: right;'>
                                        <div style='color: {renk}; font-weight: bold; font-family: Consolas; font-size: 1.1em;'>{isaret}{abs(r['tutar']):,.2f} ₺</div>
                                        <div style='color: #666; font-size: 0.75em; margin-top: 4px;'>{r['t_dt'].strftime('%d.%m.%Y %H:%M')}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else: st.info("Bu aralıkta borsa kaydı bulunmuyor.")
            
            with c_log2:
                st.markdown("<div style='color: gray; font-size: 0.9em; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 1px;'>Nakit Transfer Dökümü</div>", unsafe_allow_html=True)
                with st.container(height=400, border=True):
                    if not df_n_gecmis.empty:
                        for _, r in df_n_gecmis.iterrows():
                            renk = "#00ff00" if r['tutar'] > 0 else "#FF5252"
                            isaret = "+" if r['tutar'] > 0 else "-"
                            st.markdown(f"""
                            <div style='background: rgba(10,10,10,0.5); border-left: 3px solid {renk}; padding: 12px; border-radius: 4px; margin-bottom: 8px; border-top: 1px solid rgba(255,255,255,0.02); border-right: 1px solid rgba(255,255,255,0.02); border-bottom: 1px solid rgba(255,255,255,0.02);'>
                                <div style='display: flex; justify-content: space-between; align-items: flex-start;'>
                                    <div>
                                        <div style='color: white; font-weight: bold; font-size: 0.95em;'>{r['islem_tipi']}</div>
                                        <div style='color: gray; font-size: 0.8em; margin-top: 4px;'>{r['detay']}</div>
                                    </div>
                                    <div style='text-align: right;'>
                                        <div style='color: {renk}; font-weight: bold; font-family: Consolas; font-size: 1.1em;'>{isaret}{abs(r['tutar']):,.2f} ₺</div>
                                        <div style='color: #666; font-size: 0.75em; margin-top: 4px;'>{r['t_dt'].strftime('%d.%m.%Y %H:%M')}</div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else: st.info("Bu aralıkta transfer kaydı bulunmuyor.")

    # --- ANA BANKA VE BÜTÇE SAYFASI ---
    elif secilen_sayfa == "Banka ve Bütçe":
        st.title("Banka ve Finans Merkezi")
        # --- KESİN SENKRONİZASYON VE TEMİZLİK ---
        conn = get_db()
        try:
            c = conn.cursor()
            # 1. Asıl portföy kasasındaki (Yatırım Hesabı) doğru bakiyeyi çek
            c.execute("SELECT bakiye FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (k_adi,))
            gercek_kasa = c.fetchone()
            
            # 2. Banka tablosundaki Yatırım Hesabını eşitle (kurum sütunu kullanmadan)
            if gercek_kasa is not None:
                c.execute("UPDATE banka_hesaplari SET bakiye = %s WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (float(gercek_kasa[0]), k_adi))
            
            # 3. Virman listesindeki hayalet 50.000 TL hesabını kalıcı olarak sil
            c.execute("DELETE FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi = 'Vadesiz TL'", (k_adi,))
            
            conn.commit()
        except Exception as e:
            st.error(f"Veritabanı Eşitleme Hatası: {e}")
        finally: 
            release_db(conn)
        # --- YAPIŞTIRILACAK KOD BAŞLANGICI ---
        conn = get_db()
        try:
            c = conn.cursor()
            # 1. Kök Çözüm: Hayalet hesabı veritabanından kalıcı olarak siler
            c.execute("DELETE FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi = 'Vadesiz TL'", (k_adi,))
            
            # 2. Kök Çözüm: Midas banka bakiyesini asıl portföy kasası ile kalıcı olarak eşitler
            c.execute("SELECT bakiye FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (k_adi,))
            gercek_bakiye = c.fetchone()
            if gercek_bakiye:
                c.execute("UPDATE banka_hesaplari SET bakiye = %s WHERE kullanici_adi = %s AND (hesap_adi = 'Yatırım Hesabı' OR kurum = 'Midas')", (gercek_bakiye[0], k_adi))
            conn.commit()
        except: pass
        finally: release_db(conn)
        # --- YAPIŞTIRILACAK KOD BİTİŞİ ---
        # Arka plan senkronizasyonu (Portföy kasası ile Banka kasasını eşitler)
        conn = get_db()
        try:
            c = conn.cursor()
            c.execute("SELECT bakiye FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (k_adi,))
            gercek_bakiye = c.fetchone()
            if gercek_bakiye:
                c.execute("UPDATE banka_hesaplari SET bakiye = %s WHERE kullanici_adi = %s AND hesap_adi = 'Yatırım Hesabı'", (gercek_bakiye[0], k_adi))
                conn.commit()
        except: pass
        finally: release_db(conn)
        t_harcama, t_liste, t_transfer, t_ekle = st.tabs(["Harcama Yönetimi", "Cüzdan ve Bankalar", "Transfer İşlemleri", "Yeni Tanımlama"])
        
        with t_harcama:
            conn = get_db()
            try:
                # SQL GÜNCELLEMESİ: Logoları çekebilmek için banka_adi sütununu da ekledik
                df_vad = pd.read_sql_query("SELECT banka_adi, hesap_adi, bakiye FROM banka_hesaplari WHERE kullanici_adi = %s AND hesap_turu = 'Vadesiz'", conn, params=(k_adi,))
                df_kar = pd.read_sql_query("SELECT banka_adi, kart_adi, limit_tutari, guncel_borc, kisisel_limit FROM kredi_kartlari WHERE kullanici_adi = %s", conn, params=(k_adi,))
            finally: release_db(conn)

            st.markdown("##### Cari Cüzdan Özeti")
            
            # 1. Cüzdan Verilerini Tek Bir Havuzda Topluyoruz
            cuzdan_listesi = [{"banka": "Midas", "isim": "Yatırım Hesabı", "bakiye": mevcut_bakiye, "tur": "Yatirim"}]
            for _, r in df_vad.iterrows(): cuzdan_listesi.append({"banka": r['banka_adi'], "isim": r['hesap_adi'], "bakiye": r['bakiye'], "tur": "Vadesiz"})
            for _, r in df_kar.iterrows(): cuzdan_listesi.append({"banka": r['banka_adi'], "isim": r['kart_adi'], "bakiye": r['kisisel_limit'] - r['guncel_borc'], "borc": r['guncel_borc'], "tur": "Kart"})
            
            # 2. Şık Tasarım İçin Verileri 4'lü Satırlara Bölüyoruz
            satirlar = [cuzdan_listesi[i:i+4] for i in range(0, len(cuzdan_listesi), 4)]
            
            for satir in satirlar:
                cols = st.columns(4)
                for idx, item in enumerate(satir):
                    with cols[idx]:
                        b_adi = item['banka']
                        
                        # Emoji yerine profesyonel baş harf logosu (Avatar)
                        bas_harf = b_adi[0].upper() if b_adi else "B"
                        img_html = f"<div style='width: 38px; height: 38px; border-radius: 50%; border: 1px solid rgba(0,255,0,0.4); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #00ff00; background: rgba(0,255,0,0.05); font-size: 16px;'>{bas_harf}</div>"
                        
                        # Eğer logo klasörde varsa onu Base64 formatına çevirip HTML içine gömüyoruz
                        for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
                            p = f"Banka Logoları/{b_adi}{ext}"
                            if os.path.exists(p):
                                with open(p, "rb") as f:
                                    b64 = base64.b64encode(f.read()).decode()
                                    img_html = f"<img src='data:image/png;base64,{b64}' style='width: 38px; height: 38px; border-radius: 50%; border: 1px solid rgba(0,255,0,0.4); padding: 3px; object-fit: contain; background: #ffffff;'>"
                                break
                        
                        # Kartın altındaki ufak yazı (Borç veya Nakit durumu)
                        alt_yazi = "Nakit Kasa"
                        alt_renk = "gray"
                        bakiye_renk = "#4CAF50" # Neon Yeşil
                        if item['tur'] == "Kart":
                            alt_yazi = f"Güncel Borç: -{item['borc']:,.2f} TL"
                            alt_renk = "#FF5252" # Kırmızı
                        if item['bakiye'] < 0:
                            bakiye_renk = "#FF5252" # Eksi bakiyeyse kırmızı

                        # Profesyonel HTML Kart Tasarımı
                        kart_html = f"""
                        <div style='border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 15px; background: rgba(10,10,10,0.5); margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); transition: all 0.3s ease;'>
                            <div style='display: flex; align-items: center; margin-bottom: 15px;'>
                                <div>{img_html}</div>
                                <div style='margin-left: 12px; line-height: 1.2;'>
                                    <div style='font-size: 0.70em; color: gray; text-transform: uppercase; letter-spacing: 0.5px;'>{item['banka']}</div>
                                    <div style='font-size: 0.95em; font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 140px;'>{item['isim']}</div>
                                </div>
                            </div>
                            <div style='text-align: right;'>
                                <div style='font-size: 1.35em; font-weight: bold; color: {bakiye_renk};'>{item['bakiye']:,.2f} TL</div>
                                <div style='font-size: 0.8em; color: {alt_renk}; margin-top: 4px; font-family: monospace;'>{alt_yazi}</div>
                            </div>
                        </div>
                        """
                        st.markdown(kart_html, unsafe_allow_html=True)
            
            st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px;'>", unsafe_allow_html=True)
            
            kaynaklar = []
            for _, r in df_vad.iterrows(): 
                kaynaklar.append(f"Hesap: {r['hesap_adi']} (Bakiye: {r['bakiye']:,.2f} TL)")
                
            for _, r in df_kar.iterrows(): 
                kalan_limit = float(r['kisisel_limit']) - float(r['guncel_borc'])
                kaynaklar.append(f"Kart: {r['kart_adi']} (Kalan Limit: {kalan_limit:,.2f} TL)")
            
            if not kaynaklar: st.warning("Sistem Uyarısı: Harcama girebilmek için önce bir Vadesiz Hesap veya Kredi Kartı eklemelisiniz.")
            else:
                conn = get_db()
                try:
                    c = conn.cursor()
                    c.execute("SELECT kategori_adi FROM harcama_kategorileri WHERE kullanici_adi = %s", (k_adi,))
                    oz_kat = [row[0] for row in c.fetchall()]
                finally: release_db(conn)
                
                tum_kategoriler = sorted(list(set(["Yemek", "Market", "Sigara", "Yurt Gideri", "Atıştırmalık", "Zaruri İhtiyaç", "Kişisel Bakım", "Telefon Faturası", "Ulaşım", "Eğitim", "Giyim", "Kahve", "Diğer"] + oz_kat)))

                # --- HARCAMA TERMİNALİ TASARIMI ---
                st.markdown("<div style='display: flex; align-items: center; margin-bottom: 15px;'><div style='width: 10px; height: 10px; background: #00ff00; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 8px #00ff00;'></div><div style='color: #00ff00; font-size: 1.1em; font-weight: 700; letter-spacing: 1px; font-family: Consolas;'>HARCAMA İŞLEME TERMİNALİ</div></div>", unsafe_allow_html=True)

                with st.container(border=True):
                    st.markdown("<div style='background: rgba(255, 82, 82, 0.05); padding: 10px 15px; border-radius: 6px; border: 1px solid rgba(255, 82, 82, 0.2); margin-bottom: 20px; font-size: 0.85em; color: #e0e0e0;'>Günlük harcamalarınızı ve kart işlemlerinizi buradan sisteme kaydedin. Çıkışlar doğrudan seçtiğiniz kaynaktan düşülecektir.</div>", unsafe_allow_html=True)
                    
                    st.markdown("<span style='color: gray; font-size: 0.85em;'>Ödeme Kaynağı & Kategori:</span>", unsafe_allow_html=True)
                    c1, c2 = st.columns(2)
                    h_kaynak = c1.selectbox("Ödeme Kaynağı", kaynaklar, label_visibility="collapsed")
                    h_kategori = c2.selectbox("Kategori", tum_kategoriler, label_visibility="collapsed")
                    
                    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 15px 0;'>", unsafe_allow_html=True)
                    
                    st.markdown("<span style='color: gray; font-size: 0.85em;'>Tutar (TL) & Açıklama:</span>", unsafe_allow_html=True)
                    c3, c4 = st.columns(2)
                    h_tutar_saf = c3.number_input("Tutar (TL)", min_value=1.0, step=10.0, label_visibility="collapsed")
                    h_detay_orj = c4.text_input("Açıklama (Opsiyonel)", placeholder="Örn: Market alışverişi, Fatura...", label_visibility="collapsed")
                    
                    h_taksit = 1
                    h_faiz = 0.0
                    
                    if "Kart:" in h_kaynak:
                        st.markdown("<hr style='margin: 15px 0px 5px 0px; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
                        taksit_secimi = st.checkbox(" Taksitli veya Vadeli İşlem Ekle")
                        
                        if taksit_secimi:
                            st.markdown("<div style='margin-bottom: 10px; margin-top: 5px; color: #ffb300; font-size: 0.85em; font-weight: bold;'>Taksit ve Vade Ayarları</div>", unsafe_allow_html=True)
                            c5, c6 = st.columns(2)
                            h_taksit = c5.number_input("Taksit Sayısı (Peşin için 1)", min_value=1, max_value=36, value=1, step=1)
                            h_faiz = c6.number_input("Vade Farkı Oranı (%)", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("Harcamayı İşle (-)", type="primary", use_container_width=True):
                        salt_kaynak, gecerli_mi, sorgular = h_kaynak.split(" (")[0], False, []
                        
                        h_tutar = h_tutar_saf * (1 + (h_faiz / 100))
                        h_detay = h_detay_orj
                        
                        if h_taksit > 1:
                            aylik_tutar = h_tutar / h_taksit
                            secilen_k = h_kaynak.split(": ")[1].split(" (")[0]
                            ek_not = f"({h_taksit} Taksit | Aylık: {aylik_tutar:,.2f} TL | %{h_faiz} Vade Farkı)"
                            h_detay = f"{h_detay_orj} {ek_not}".strip() if h_detay_orj else f"{h_kategori} {ek_not}"
                            
                            sorgular.append(("INSERT INTO taksitli_islemler (kullanici_adi, kart_adi, aciklama, toplam_tutar, aylik_tutar, toplam_taksit, odenen_taksit) VALUES (%s, %s, %s, %s, %s, %s, 0)", (k_adi, secilen_k, h_detay_orj if h_detay_orj else h_kategori, h_tutar, aylik_tutar, h_taksit)))
                        elif h_faiz > 0:
                            ek_not = f"(%{h_faiz} Vade Farkı)"
                            h_detay = f"{h_detay_orj} {ek_not}".strip() if h_detay_orj else f"{h_kategori} {ek_not}"

                        if "Hesap:" in h_kaynak:
                            secilen_h = h_kaynak.split(": ")[1].split(" (")[0]
                            mevcut_bak = df_vad[df_vad['hesap_adi'] == secilen_h]['bakiye'].values[0]
                            if h_tutar > mevcut_bak: st.error("İşlem Reddedildi: Yetersiz Bakiye.")
                            else:
                                sorgular.append(("UPDATE banka_hesaplari SET bakiye = bakiye - %s WHERE kullanici_adi = %s AND hesap_adi = %s", (h_tutar, k_adi, secilen_h)))
                                gecerli_mi = True
                        elif "Kart:" in h_kaynak:
                            secilen_k = h_kaynak.split(": ")[1].split(" (")[0]
                            k_kisisel_limit, k_borc = df_kar[df_kar['kart_adi'] == secilen_k]['kisisel_limit'].values[0], df_kar[df_kar['kart_adi'] == secilen_k]['guncel_borc'].values[0]
                            if (k_borc + h_tutar) > k_kisisel_limit: st.error(f"İşlem Reddedildi: Kişisel Bütçe Sınırı Aşıldı.")
                            else:
                                sorgular.append(("UPDATE kredi_kartlari SET guncel_borc = guncel_borc + %s WHERE kullanici_adi = %s AND kart_adi = %s", (h_tutar, k_adi, secilen_k)))
                                gecerli_mi = True

                        if gecerli_mi:
                            sorgular.append(("INSERT INTO harcamalar (kullanici_adi, kategori, aciklama, tutar, kaynak_hesap) VALUES (%s,%s,%s,%s,%s)", (k_adi, h_kategori, h_detay, h_tutar, salt_kaynak)))
                            dekont = f"{salt_kaynak.replace('Hesap: ', '').replace('Kart: ', '')} - {h_kategori} Harcaması" + (f" ({h_detay})" if h_detay else "")
                            sorgular.append(("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'HARCAMA (-)', %s, %s)", (k_adi, dekont, -h_tutar)))
                            
                            if h_tutar >= 3000:
                                asistan_mesaji = f"{h_kategori} kategorisinde tek seferde {h_tutar:,.2f} TL tutarında yüksek bir harcama tespit edilmiştir. Bütçe limitlerinizi gözden geçirmeniz tavsiye olunur."
                                sorgular.append(("INSERT INTO asistan_bildirimleri (kullanici_adi, baslik, mesaj, tur) VALUES (%s, 'Yüksek Tutarlı Harcama Tespiti', %s, 'GIDER')", (k_adi, asistan_mesaji)))
                            
                            # --- ONAY BEKLEMEDEN DİREKT İŞLEME MOTORU ---
                            conn = get_db()
                            try:
                                c = conn.cursor()
                                for s, p in sorgular: c.execute(s, p)
                                conn.commit()
                                st.session_state.islem_bildirimi = {"mesaj": "Harcama başarıyla kaydedildi!"}
                            except Exception as e:
                                st.error(f"Sistem Hatası: {e}")
                            finally:
                                release_db(conn)
                            st.rerun()
                            
                            islem_onay_dialog("Harcama Onayı", f"Kategori: {h_kategori}\nToplam Tutar: {h_tutar:,.2f} TL\nKaynak: {salt_kaynak}", "Harcama başarıyla işlendi.", sorgular)
                with st.expander("Kategori Yönetimi"):
                    c_ekle, c_sil = st.columns(2)
                    with c_ekle:
                        yeni_kat = st.text_input("Yeni Kategori Ekle")
                        if st.button("Sisteme Ekle", use_container_width=True):
                            if yeni_kat and yeni_kat not in tum_kategoriler:
                                conn = get_db()
                                c = conn.cursor()
                                c.execute("INSERT INTO harcama_kategorileri (kullanici_adi, kategori_adi) VALUES (%s, %s)", (k_adi, yeni_kat))
                                conn.commit(); release_db(conn); st.rerun()
                    with c_sil:
                        if oz_kat:
                            silinecek_kat = st.selectbox("Kategori Sil", oz_kat)
                            if st.button("Sistemden Çıkar", use_container_width=True):
                                conn = get_db()
                                c = conn.cursor()
                                c.execute("DELETE FROM harcama_kategorileri WHERE kullanici_adi = %s AND kategori_adi = %s", (k_adi, silinecek_kat))
                                conn.commit(); release_db(conn); st.rerun()
                
            st.markdown("---")
            st.markdown("##### Harcama Analizi ve Dağılım Raporu")
            conn = get_db()
            df_harcama = pd.read_sql_query("SELECT id, tarih, kategori, tutar, kaynak_hesap, aciklama FROM harcamalar WHERE kullanici_adi = %s ORDER BY tarih DESC", conn, params=(k_adi,))
            release_db(conn)
            
            if not df_harcama.empty:
                df_harcama['GercekTarih'] = pd.to_datetime(df_harcama['tarih'])
                
                # Filtre ve Toplam Tutarı aynı hizaya, şık bir şekilde diziyoruz
                c_analiz1, c_analiz2 = st.columns([1, 1])
                st.caption("Analiz Aralığı:")
                filtre = c_analiz1.selectbox("Analiz Aralığı:", ["Bugün", "Son 24 Saat", "Son 7 Gün", "Son 15 Gün", "Son 1 Ay", "Tümü"], index=2, label_visibility="collapsed")
                
                bugun = pd.Timestamp.today()
                
                if filtre == "Bugün": df_filtreli = df_harcama[df_harcama['GercekTarih'].dt.date == bugun.date()]
                elif filtre == "Son 24 Saat": df_filtreli = df_harcama[df_harcama['GercekTarih'] >= bugun - pd.Timedelta(hours=24)]
                elif filtre == "Son 7 Gün": df_filtreli = df_harcama[df_harcama['GercekTarih'] >= bugun - pd.Timedelta(days=7)]
                elif filtre == "Son 15 Gün": df_filtreli = df_harcama[df_harcama['GercekTarih'] >= bugun - pd.Timedelta(days=15)]
                elif filtre == "Son 1 Ay": df_filtreli = df_harcama[df_harcama['GercekTarih'] >= bugun - pd.DateOffset(months=1)]
                else: df_filtreli = df_harcama
                    
                if df_filtreli.empty: st.info("Bu zaman aralığında harcama kaydı bulunamadı.")
                else:
                    c_analiz2.markdown(f"<div style='text-align: right; margin-top: -15px;'><span style='color: gray; font-size: 0.9em;'>Toplam Gider ({filtre})</span><br><b style='color: #FF5252; font-size: 1.4em;'>-{df_filtreli['tutar'].sum():,.2f} TL</b></div>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # NİZAMİ EŞİT KUTULAR
                    # NİZAMİ EŞİT KUTULAR
                    c_grafik, c_liste = st.columns([1, 1])
                    
                    with c_grafik:
                        # Yükseklik tam 420px olarak betonlandı
                        with st.container(border=True, height=420):
                            st.markdown("<span style='color: #00ff00; font-weight: bold;'>Kategori Dağılımı</span>", unsafe_allow_html=True)
                            df_grup = df_filtreli.groupby('kategori')['tutar'].sum().reset_index()
                            
                            siber_renkler = ['#00ff00', '#00cc00', '#009900', '#4d4d4d', '#262626', '#808080', '#006600', '#1a1a1a']
                            
                            fig = px.pie(df_grup, values='tutar', names='kategori', hole=0.6, color_discrete_sequence=siber_renkler)
                            fig.update_traces(
                                textposition='inside', 
                                textinfo='percent+label', 
                                textfont=dict(size=12, color='white', family='Consolas'), 
                                marker=dict(line=dict(color='#050505', width=3))
                            )
                            fig.update_layout(
                                height=330, # Kutunun içine tam sığar
                                margin=dict(t=10, b=10, l=0, r=0), 
                                paper_bgcolor="rgba(0,0,0,0)", 
                                plot_bgcolor="rgba(0,0,0,0)", 
                                showlegend=False
                            )
                            # KAMERA VE ZOOM İKONLARINI YOK ETTİK (config ayarı)
                            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                            
                    with c_liste:
                        # Kaybolan liste geri geldi ve yüksekliği 420px olarak betonlandı
                        with st.container(border=True, height=420):
                            st.markdown("<span style='color: #00ff00; font-weight: bold;'>İşlem Dökümü</span>", unsafe_allow_html=True)
                            for _, r in df_filtreli.iterrows():
                                with st.container(border=True):
                                    c_d1, c_d2 = st.columns([3, 2])
                                    acik_txt = f" <span style='color: gray; font-size: 0.85em;'>({r['aciklama']})</span>" if r['aciklama'] else ""
                                    c_d1.markdown(f"**{r['kategori']}**{acik_txt}<br><span style='font-size: 0.8em; color: gray;'>{r['GercekTarih'].strftime('%d.%m.%Y %H:%M')} | {r['kaynak_hesap']}</span>", unsafe_allow_html=True)
                                    c_d2.markdown(f"<div style='text-align: right; padding-top: 10px;'><b style='color: #FF5252;'>-{r['tutar']:,.2f} TL</b></div>", unsafe_allow_html=True)
                
                st.markdown("---")
            # --- İKİYE BÖLÜNMÜŞ, DAR SÜTUNLU ŞIK GRAFİK MODÜLÜ VE RAPORLAMA ---
                st.markdown("##### Harcama Trendi ve Raporlama")
                
                # Rapor indirme butonu ve trend aralığı seçimi yan yana
                c_filtre, c_rapor = st.columns([2, 1])
                with c_filtre:
                    trend_filtre = st.radio("Trend Aralığı:", ["1 Hafta", "1 Ay", "6 Ay", "1 Yıl"], horizontal=True, label_visibility="collapsed")
                
                # Veriyi zaman aralığına göre hazırlıyoruz
                df_t = pd.DataFrame()
                if not df_harcama.empty:
                    bugun_t = pd.Timestamp.today()
                    
                    # 1. Filtreleme ve Akıllı Etiketleme (Haftalık/Aylık Düzeltmesi)
                    if trend_filtre == "1 Hafta": 
                        baslangic = bugun_t - pd.Timedelta(days=7)
                        df_t = df_harcama[pd.to_datetime(df_harcama['tarih']) >= baslangic].copy()
                        df_t['GercekTarih'] = pd.to_datetime(df_t['tarih'])
                        df_t['GosterimTarihi'] = df_t['GercekTarih'].dt.strftime('%d %b')
                    elif trend_filtre == "1 Ay": 
                        baslangic = bugun_t - pd.DateOffset(months=1)
                        df_t = df_harcama[pd.to_datetime(df_harcama['tarih']) >= baslangic].copy()
                        df_t['GercekTarih'] = pd.to_datetime(df_t['tarih'])
                        # Haftanın Pazartesi gününü bulup etiket yapıyoruz (Örn: 04 Mar Hft.)
                        df_t['GosterimTarihi'] = (df_t['GercekTarih'] - pd.to_timedelta(df_t['GercekTarih'].dt.dayofweek, unit='D')).dt.strftime('%d %b') + " (Hft)"
                    elif trend_filtre == "6 Ay": 
                        baslangic = bugun_t - pd.DateOffset(months=6)
                        df_t = df_harcama[pd.to_datetime(df_harcama['tarih']) >= baslangic].copy()
                        df_t['GercekTarih'] = pd.to_datetime(df_t['tarih'])
                        df_t['GosterimTarihi'] = df_t['GercekTarih'].dt.strftime('%b %Y')
                    else: 
                        baslangic = bugun_t - pd.DateOffset(years=1)
                        df_t = df_harcama[pd.to_datetime(df_harcama['tarih']) >= baslangic].copy()
                        df_t['GercekTarih'] = pd.to_datetime(df_t['tarih'])
                        df_t['GosterimTarihi'] = df_t['GercekTarih'].dt.strftime('%b %Y')
                        
                    # Kronolojik sıraya diz (Grafikte soldan sağa doğru zaman aksın diye)
                    df_t = df_t.sort_values('GercekTarih', ascending=True)

                with c_rapor:
                    if not df_t.empty:
                        # Markdown Formatında VIP Harcama Raporu
                        rapor_metni = f"# MERGEN FİNANS - HARCAMA RAPORU\n**Analiz Aralığı:** {trend_filtre}\n**Oluşturulma Tarihi:** {datetime.date.today().strftime('%d.%m.%Y')}\n\n"
                        rapor_metni += f"## 1. DÖNEM ÖZETİ\n- **Toplam Gider:** {df_t['tutar'].sum():,.2f} TL\n\n"
                        rapor_metni += "## 2. KATEGORİ BAZLI DAĞILIM\n| Kategori | Toplam Harcama | Oran |\n| :--- | :--- | :--- |\n"
                        cat_grup = df_t.groupby('kategori')['tutar'].sum()
                        toplam_tutar = df_t['tutar'].sum()
                        for cat, val in cat_grup.items():
                            rapor_metni += f"| **{cat}** | {val:,.2f} TL | %{(val/toplam_tutar)*100:.2f} |\n"
                        rapor_metni += "\n## 3. İŞLEM DÖKÜMÜ\n"
                        # İşlem dökümünü yeni tarihten eskiye göstermek için tersten dön
                        for _, r in df_t.sort_values('GercekTarih', ascending=False).iterrows():
                            rapor_metni += f"- **[{r['GercekTarih'].strftime('%d.%m.%Y %H:%M')}] {r['kategori']}:** {r['tutar']:,.2f} TL (Kaynak: {r['kaynak_hesap']}) - {r['aciklama']}\n"
                        
                        # BUTONU TASARIM DİLİNE UYDURDUK VE EMOJİYİ SİLDİK
                        st.download_button("Dönem Raporunu İndir (.md)", data=rapor_metni, file_name=f"Mergen_Harcama_Raporu_{trend_filtre.replace(' ', '_')}.md", mime="text/markdown", use_container_width=True, type="primary")

                c_trend, c_yan = st.columns([1.3, 0.7]) 
                
                with c_trend:
                    # YÜKSEKLİK SABİTLENDİ (height=400)
                    with st.container(border=True, height=400):
                        st.markdown("<span style='color: #00ff00; font-weight: bold;'>Trend Grafiği</span>", unsafe_allow_html=True)
                        if not df_t.empty:
                            df_grup = df_t.groupby('GosterimTarihi', sort=False)['tutar'].sum().reset_index()

                            fig_bar = px.bar(df_grup, x='GosterimTarihi', y='tutar', text='tutar')
                            fig_bar.update_traces(
                                texttemplate='%{text:,.0f} ₺',
                                textposition='outside',
                                textfont=dict(color='#00ff00', size=11),
                                marker_color='rgba(0, 255, 0, 0.10)',
                                marker_line_color='#00ff00',
                                marker_line_width=1.5,
                                width=0.35,
                                hoverinfo="x+y"
                            )
                            fig_bar.update_layout(
                                height=280,
                                paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)",
                                margin=dict(t=30, b=10, l=0, r=0),
                                xaxis=dict(showgrid=False, showline=True, linecolor='rgba(255, 255, 255, 0.2)', color='gray', title='', tickangle=0),
                                yaxis=dict(showgrid=True, visible=True, showline=True, gridcolor='rgba(255, 255, 255, 0.05)', linecolor='rgba(255, 255, 255, 0.2)', color='gray', title=''), 
                                hovermode="x unified",
                                font=dict(family="Consolas")
                            )
                            
                            max_y = df_grup['tutar'].max()
                            fig_bar.update_yaxes(range=[0, max_y * 1.25]) 
                            
                            st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})
                        else: st.info("Harcama dökümü boş.")

                with c_yan:
                    # YÜKSEKLİK SABİTLENDİ (height=400) -> Eşit nizami duruş
                    with st.container(border=True, height=400):
                        st.markdown("<span style='color: #00ff00; font-weight: bold;'>Gün / Dönem Analizi</span>", unsafe_allow_html=True)
                        if not df_t.empty:
                            secenekler = df_grup[df_grup['tutar'] > 0]['GosterimTarihi'].tolist()
                            if not secenekler: secenekler = ["Veri Yok"]
                            
                            st.caption("Detayını görmek istediğiniz sütunu seçin:")
                            secilen_tarih = st.selectbox("İncele:", secenekler, index=len(secenekler)-1 if secenekler[0] != "Veri Yok" else 0, label_visibility="collapsed")
                            
                            if secilen_tarih != "Veri Yok":
                                df_sec = df_t[df_t['GosterimTarihi'] == secilen_tarih]
                                st.markdown(f"**{secilen_tarih} Dağılımı**")
                                if not df_sec.empty:
                                    cat_g = df_sec.groupby('kategori')['tutar'].sum().reset_index()
                                    cat_g = cat_g.sort_values(by='tutar', ascending=False)
                                    for _, r in cat_g.iterrows():
                                        st.markdown(f"<div style='display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 4px 0;'><span style='color: gray; font-size: 0.9em;'>{r['kategori']}</span> <b style='color: #FF5252; font-size: 0.9em;'>{r['tutar']:,.2f} ₺</b></div>", unsafe_allow_html=True)
                                    st.markdown(f"<div style='text-align: right; margin-top: 10px; font-weight: bold;'>Toplam: <span style='color: #00ff00;'>{df_sec['tutar'].sum():,.2f} ₺</span></div>", unsafe_allow_html=True)
                                else:
                                    st.caption("Bu tarihte işlem yok.")
                        else:
                            st.caption("Veri bulunmuyor.")
                
                st.markdown("---")
                # --- SİBER GRAFİK BİTİŞİ ---
                with st.expander("Hatalı İşlemi İptal Et"):
                    islem_sozluk = {f"{pd.to_datetime(r['tarih']).strftime('%d.%m.%Y %H:%M')} | {r['kategori']} | {r['tutar']} TL | {r['kaynak_hesap']}": r['id'] for _, r in df_filtreli.iterrows()}
                    if islem_sozluk:
                        sil_sec = st.selectbox("İptal Edilecek İşlem:", list(islem_sozluk.keys()))
                        if st.button("İşlemi İade Al", type="primary"):
                            sil_id = int(islem_sozluk[sil_sec])
                            conn = get_db()
                            try:
                                c = conn.cursor()
                                c.execute("SELECT tutar, kaynak_hesap FROM harcamalar WHERE id = %s", (sil_id,))
                                isl = c.fetchone()
                                if isl:
                                    i_tut, i_kay = isl[0], isl[1]
                                    g_hes = i_kay.split(": ")[1] if ": " in i_kay else i_kay.replace("Hesap: ", "").replace("Kart: ", "").replace("🏦 ", "").replace("💳 ", "")
                                    if "Hesap" in i_kay or "🏦" in i_kay: c.execute("UPDATE banka_hesaplari SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = %s", (i_tut, k_adi, g_hes))
                                    elif "Kart" in i_kay or "💳" in i_kay: c.execute("UPDATE kredi_kartlari SET guncel_borc = guncel_borc - %s WHERE kullanici_adi = %s AND kart_adi = %s", (i_tut, k_adi, g_hes))
                                    c.execute("DELETE FROM harcamalar WHERE id = %s", (sil_id,))
                                    c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'İADE/İPTAL (+)', %s, %s)", (k_adi, f"{g_hes} - İptal", i_tut))
                                    conn.commit()
                                    st.success("İşlem başarıyla iptal edildi."); st.rerun()
                            finally: release_db(conn)
            else: st.info("Veri yok.")
        
        with t_liste:
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT DISTINCT banka_adi FROM banka_hesaplari WHERE kullanici_adi = %s UNION SELECT DISTINCT banka_adi FROM kredi_kartlari WHERE kullanici_adi = %s", (k_adi, k_adi))
            k_bankalar = ["Midas"] + [row[0] for row in c.fetchall()]
            release_db(conn)
            
            st.markdown("##### Kurum Filtresi")
            if 'aktif_banka' not in st.session_state or st.session_state.aktif_banka not in k_bankalar: st.session_state.aktif_banka = k_bankalar[0]
            
            # Sütun sayısını banka sayısına göre dinamik ayarla (en fazla 5)
            sutun_sayisi = len(k_bankalar) if len(k_bankalar) > 0 else 1
            cols = st.columns(min(sutun_sayisi, 5))
            
            for idx, b_adi in enumerate(k_bankalar):
                with cols[idx % 5]:
                    is_active = (st.session_state.aktif_banka == b_adi)
                    
                    # Kartı bir bütün olarak sarmalayacak çerçeve (Container)
                    with st.container(border=True):
                        # Logoyu alıp HTML ile tam ortaya hizalıyoruz
                        ly = next((f"Banka Logoları/{b_adi}{ext}" for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG'] if os.path.exists(f"Banka Logoları/{b_adi}{ext}")), None)
                        
                        if ly: 
                            with open(ly, "rb") as f: b64 = base64.b64encode(f.read()).decode()
                            img_html = f"<div style='display: flex; justify-content: center; margin-bottom: 10px;'><img src='data:image/png;base64,{b64}' style='width: 45px; height: 45px; border-radius: 8px; object-fit: contain; background: white; padding: 2px;'></div>"
                        else:
                            bas_harf = b_adi[0].upper()
                            img_html = f"<div style='display: flex; justify-content: center; margin-bottom: 10px;'><div style='width: 45px; height: 45px; border-radius: 8px; border: 1px solid rgba(0,255,0,0.4); display: flex; align-items: center; justify-content: center; font-weight: bold; color: #00ff00; background: rgba(0,255,0,0.05); font-size: 18px;'>{bas_harf}</div></div>"
                        
                        st.markdown(img_html, unsafe_allow_html=True)
                        
                        # Buton hemen logonun altında, sınırları dolduracak şekilde konumlanıyor
                        if st.button(b_adi, key=f"btn_{b_adi}", use_container_width=True, type="primary" if is_active else "secondary"):
                            st.session_state.aktif_banka = b_adi
                            st.rerun()
            
            sb = st.session_state.aktif_banka
            st.markdown("---")
            st.markdown(f"##### {sb} Üzerindeki Varlıklar")
            
            conn = get_db()
            conn = get_db()
            if sb == "Midas":
                df_bh = pd.DataFrame([{"id": 0, "hesap_adi": "Yatırım Hesabı", "hesap_turu": "Vadesiz", "bakiye": mevcut_bakiye, "faiz_orani": 0.0}])
                df_bk = pd.DataFrame()
            else:
                df_bh = pd.read_sql_query("SELECT id, hesap_adi, hesap_turu, bakiye, faiz_orani, stopaj_orani, acilis_tarihi, vade_gun FROM banka_hesaplari WHERE kullanici_adi = %s AND banka_adi = %s", conn, params=(k_adi, sb))
                df_bk = pd.read_sql_query("SELECT id, banka_adi, kart_adi, limit_tutari, guncel_borc, kisisel_limit, hesap_kesim_gunu, son_odeme_gunu FROM kredi_kartlari WHERE kullanici_adi = %s AND banka_adi = %s", conn, params=(k_adi, sb))
            t_vd, t_vl, t_kr, t_gh = st.tabs(["Vadesiz Hesaplar", "Vadeli Mevduat", "Kredi Kartları", "Hesap Dökümü"])
            
            with t_vd:
                vd_ler = df_bh[df_bh['hesap_turu'] == 'Vadesiz']
                if not vd_ler.empty:
                    for _, r in vd_ler.iterrows():
                        with st.container(border=True):
                            c1, c2 = st.columns([3, 1])
                            c1.markdown(f"**{r['hesap_adi']}**<br><span style='font-size:0.85em;color:gray;'>Vadesiz TL</span>", unsafe_allow_html=True)
                            c2.markdown(f"<div style='text-align:right; color:#4CAF50; font-size:1.3em; font-weight:bold;'>{r['bakiye']:,.2f} TL</div>", unsafe_allow_html=True)
                    if sb != "Midas":
                        with st.expander("Hesap Kaydını Sil"):
                            sv = st.selectbox("Hesap Seçimi:", vd_ler['hesap_adi'].tolist(), key=f"sv_{sb}")
                            if st.button("Kalıcı Olarak Sil", key=f"bsv_{sb}"):
                                conn = get_db()
                                c = conn.cursor()
                                c.execute("DELETE FROM islem_gecmisi WHERE kullanici_adi = %s AND detay LIKE %s", (k_adi, f"%{sv}%"))
                                c.execute("DELETE FROM harcamalar WHERE kullanici_adi = %s AND kaynak_hesap LIKE %s", (k_adi, f"%{sv}%"))
                                c.execute("DELETE FROM sabit_islemler WHERE kullanici_adi = %s AND bagli_hesap LIKE %s", (k_adi, f"%{sv}%"))
                                c.execute("DELETE FROM banka_hesaplari WHERE kullanici_adi = %s AND hesap_adi = %s", (k_adi, sv))
                                conn.commit(); release_db(conn); st.rerun()
                else: st.info("Kayıt yok.")
                    
            with t_vl:
                if 'acilis_tarihi' in df_bh.columns and 'vade_gun' in df_bh.columns:
                    vl_ler = df_bh[df_bh['hesap_turu'] == 'Vadeli']
                    if not vl_ler.empty:
                        for _, r in vl_ler.iterrows():
                            bakiye = r['bakiye']
                            faiz = r['faiz_orani']
                            stopaj = r['stopaj_orani'] if pd.notna(r['stopaj_orani']) else 0.0
                            vade = r['vade_gun'] if pd.notna(r['vade_gun']) and r['vade_gun'] > 0 else 1
                            
                            # --- GERİYE DÖNÜK "SON YATAN FAİZ" HESAPLAMASI ---
                            # Bakiye = Önceki Anapara + (Önceki Anapara * Net Oran)
                            # Önceki Anapara = Bakiye / (1 + Net Oran)
                            net_oran = ((faiz / 100) / 365 * vade) * (1 - (stopaj / 100))
                            onceki_anapara = bakiye / (1 + net_oran)
                            son_yatan_net = bakiye - onceki_anapara
                            
                            with st.container(border=True):
                                c1, c2, c3 = st.columns([2, 1.5, 1])
                                c1.markdown(f"**{r['hesap_adi']}**<br><span style='font-size:0.85em;color:gray;'>Vadeli Hesap</span>", unsafe_allow_html=True)
                                
                                if son_yatan_net > 0:
                                    bakiye_html = f"<span style='font-size:0.8em;color:gray;'>Güncel Bakiye</span><br><span style='color:#4CAF50; font-weight:bold; font-size:1.2em;'>{bakiye:,.2f} TL</span><br><span style='font-size:0.75em;color:#FFD700;'>+ {son_yatan_net:,.2f} TL Son Yatan Faiz</span>"
                                else:
                                    bakiye_html = f"<span style='font-size:0.8em;color:gray;'>Bakiye</span><br><span style='color:#4CAF50; font-weight:bold; font-size:1.2em;'>{bakiye:,.2f} TL</span>"
                                    
                                c2.markdown(f"<div style='text-align:right;'>{bakiye_html}</div>", unsafe_allow_html=True)
                                c3.markdown(f"<div style='text-align:right;'><span style='font-size:0.8em;color:gray;'>Faiz</span><br><span style='font-weight:bold; font-size:1.2em;'>%{faiz}</span></div>", unsafe_allow_html=True)
                        # --- VADELİ HESAP SİLME OPERASYONU ---
                        st.markdown("---")
                        with st.expander("Vadeli Hesap Kaydını Sil"):
                            svl = st.selectbox("Silinecek Hesap Seçimi:", vl_ler['hesap_adi'].tolist(), key=f"svl_delete_{sb}")
                            if st.button("Kalıcı Olarak Sil", key=f"bsvl_final_{sb}", type="primary", use_container_width=True):
                                conn = get_db()
                                try:
                                    c = conn.cursor()
                                    c.execute("DELETE FROM islem_gecmisi WHERE kullanici_adi = %s AND detay LIKE %s", (k_adi, f"%{svl}%"))
                                    c.execute("DELETE FROM banka_hesaplari WHERE kullanici_adi = %s AND hesap_adi = %s", (k_adi, svl))
                                    conn.commit()
                                    st.success(f"{svl} hesabı temizlendi.")
                                    time.sleep(1)
                                    st.rerun()
                                finally: release_db(conn)
                    else: st.info("Kayıt yok.")
                else: st.info("Sistem verisi güncelleniyor, lütfen sayfayı yenileyin.")
            
            with t_kr:
                def is_gunune_yuvarla(hedef_tarih):
                    if hedef_tarih.weekday() == 5: return hedef_tarih + datetime.timedelta(days=2)
                    elif hedef_tarih.weekday() == 6: return hedef_tarih + datetime.timedelta(days=1)
                    return hedef_tarih

                conn = get_db()
                try:
                    df_taksitler = pd.read_sql_query("SELECT kart_adi, aciklama, aylik_tutar, toplam_taksit, odenen_taksit FROM taksitli_islemler WHERE kullanici_adi = %s AND odenen_taksit < toplam_taksit", conn, params=(k_adi,))
                    df_harcamalar = pd.read_sql_query("SELECT id, tarih, kategori, aciklama, tutar, kaynak_hesap FROM harcamalar WHERE kullanici_adi = %s AND kaynak_hesap LIKE 'Kart:%%' ORDER BY tarih DESC", conn, params=(k_adi,))
                    df_gecmis_ekstreler = pd.read_sql_query("SELECT id, kart_adi, donem_adi, toplam_borc, kesim_tarihi, son_odeme_tarihi, durum FROM gecmis_ekstreler WHERE kullanici_adi = %s ORDER BY kesim_tarihi DESC", conn, params=(k_adi,))
                except:
                    df_taksitler, df_harcamalar, df_gecmis_ekstreler = pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
                finally: release_db(conn)

                if not df_bk.empty:
                    bugun = datetime.date.today()
                    aylar_tr = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
                    
                    for _, r in df_bk.iterrows():
                        kart_adi, banka_adi = r['kart_adi'], r['banka_adi']
                        limit, borc = r['limit_tutari'], r['guncel_borc']
                        kisisel_limit = r['kisisel_limit'] if r['kisisel_limit'] > 0 else limit
                        k_bilgi = kullanici_bilgileri_getir(k_adi)
                        k_isim = k_bilgi['isim_soyisim'].upper() if k_bilgi['isim_soyisim'] else k_adi.upper()
                        kesim_gunu, odeme_gunu = int(r['hesap_kesim_gunu']), int(r['son_odeme_gunu'])
                        
                        # --- AKILLI TAKVİM VE DÖNEM GEÇİŞ MOTORU ---
                        import calendar
                        son_gun = calendar.monthrange(bugun.year, bugun.month)[1]
                        h_kesim = datetime.date(bugun.year, bugun.month, min(kesim_gunu, son_gun))
                        
                        if bugun > h_kesim:
                            y_ay = bugun.month + 1 if bugun.month < 12 else 1
                            y_yil = bugun.year if bugun.month < 12 else bugun.year + 1
                            son_gun = calendar.monthrange(y_yil, y_ay)[1]
                            h_kesim = datetime.date(y_yil, y_ay, min(kesim_gunu, son_gun))

                        o_ay = h_kesim.month + 1 if odeme_gunu < kesim_gunu else h_kesim.month
                        o_yil = h_kesim.year + 1 if (odeme_gunu < kesim_gunu and h_kesim.month == 12) else h_kesim.year
                        o_son_gun = calendar.monthrange(o_yil, o_ay)[1]
                        h_odeme = datetime.date(o_yil, o_ay, min(odeme_gunu, o_son_gun))

                        gercek_kesim = is_gunune_yuvarla(h_kesim)
                        gercek_odeme = is_gunune_yuvarla(h_odeme)
                        kalan_gun = (gercek_kesim - bugun).days
                        donem_yazisi = f"{aylar_tr[bugun.month - 1]} {bugun.year}"

                        # --- OTOMATİK EKSTRE KESİM TETİKLEYİCİ ---
                        if kalan_gun < 0:
                            gecmis_ay = bugun.month - 2 if bugun.month > 1 else 11
                            gecmis_yil = bugun.year if bugun.month > 1 else bugun.year - 1
                            gecmis_donem_adi = f"{aylar_tr[gecmis_ay]} {gecmis_yil}"
                            
                            conn = get_db()
                            try:
                                c = conn.cursor()
                                c.execute("INSERT INTO gecmis_ekstreler (kullanici_adi, kart_adi, donem_adi, toplam_borc, kesim_tarihi, son_odeme_tarihi) VALUES (%s,%s,%s,%s,%s,%s)", (k_adi, kart_adi, gecmis_donem_adi, borc, gercek_kesim, gercek_odeme))
                                c.execute("UPDATE taksitli_islemler SET odenen_taksit = odenen_taksit + 1 WHERE kullanici_adi = %s AND kart_adi = %s AND odenen_taksit < toplam_taksit", (k_adi, kart_adi))
                                c.execute("UPDATE harcamalar SET kaynak_hesap = %s WHERE kullanici_adi = %s AND kaynak_hesap = %s", (f"[Geçmiş] Kart: {kart_adi}", k_adi, f"Kart: {kart_adi}"))
                                conn.commit()
                                st.session_state.islem_bildirimi = {"mesaj": f"{kart_adi} ekstreniz kesildi. Yeni döneme geçildi."}
                                time.sleep(1)
                                st.rerun()
                            except: pass
                            finally: release_db(conn)

                        # --- GÖRSEL TASARIM ---
                        with st.container(border=True):
                            c_kart, c_grafik = st.columns([1, 1.5])
                            # --- GÖRSEL TASARIM ---
                        with st.container(border=True):
                            c_kart, c_grafik = st.columns([1, 1.5])
                            with c_kart:
                                # Logo bul
                                kart_logo = ""
                                for ext in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']:
                                    p = f"Banka Logoları/{banka_adi}{ext}"
                                    if os.path.exists(p):
                                        with open(p, "rb") as f:
                                            b64 = base64.b64encode(f.read()).decode()
                                            kart_logo = f"<img src='data:image/png;base64,{b64}' style='height: 25px; border-radius: 4px; background: white; padding: 2px;'>"
                                        break
                                
                                st.markdown(f"""
                                <div style='background: linear-gradient(135deg, rgba(20,20,20,0.95) 0%, rgba(5,5,5,0.98) 100%); border: 1px solid rgba(0,255,0,0.3); border-radius: 12px; padding: 20px; box-shadow: 0 8px 16px rgba(0,0,0,0.5), inset 0 0 15px rgba(0,255,0,0.05); position: relative; height: 210px; display: flex; flex-direction: column; justify-content: space-between;'>
                                    <div style='width: 35px; height: 25px; background: linear-gradient(135deg, #FFD700 0%, #B8860B 100%); border-radius: 4px; position: absolute; top: 20px; left: 20px; box-shadow: inset 1px 1px 3px rgba(255,255,255,0.5);'></div>
                                    <div style='text-align: right; position: absolute; top: 15px; right: 20px;'>{kart_logo}</div>
                                    <div style='margin-top: 45px;'>
                                        <div style='color: gray; font-size: 0.7em; letter-spacing: 2px;'>KART TANIMI</div>
                                        <div style='color: white; font-size: 1.1em; font-weight: bold; letter-spacing: 1px; font-family: monospace;'>{kart_adi.upper()}</div>
                                    </div>
                                    <div style='display: flex; justify-content: space-between; align-items: flex-end;'>
                                        <div>
                                            <div style='color: gray; font-size: 0.6em; letter-spacing: 1px;'>KULLANICI</div>
                                            <div style='color: #00ff00; font-size: 0.85em; font-weight: bold;'>{k_isim}</div>
                                        </div>
                                        <div style='text-align: right;'>
                                            <div style='color: gray; font-size: 0.6em; letter-spacing: 1px;'>TOPLAM LİMİT</div>
                                            <div style='color: white; font-size: 1.1em; font-weight: bold; font-family: monospace;'>{limit:,.0f} ₺</div>
                                        </div>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # Tarihler şimdi tek satırda ve tam olarak yazacak
                                st.markdown(f"""
                                <div style='text-align: center; margin-top: 12px; font-size: 0.85em; color: gray;'>
                                    Dönem: <b style='color: white;'>{donem_yazisi}</b> | 
                                    Kesim: <b style='color: white;'>{gercek_kesim.strftime('%d.%m.%Y')}</b> 
                                    (<b style='color: {'#FF5252' if kalan_gun <= 3 else '#00ff00'};'>{kalan_gun} Gün</b>) | 
                                    Ödeme: <b style='color: white;'>{gercek_odeme.strftime('%d.%m.%Y')}</b>
                                </div>
                                """, unsafe_allow_html=True)

                            with c_grafik:
                                cg1, cg2 = st.columns(2)
                                with cg1:
                                    oran1 = (borc / limit) * 100 if limit > 0 else 0
                                    r1 = "#00ff00" if oran1 < 50 else ("#ffb300" if oran1 < 80 else "#FF5252")
                                    fig1 = go.Figure(go.Indicator(mode="gauge+number", value=borc, title={'text': "Banka Limiti", 'font': {'size': 13, 'color': 'gray'}},
                                        number={'valueformat': ",.0f", 'suffix': " ₺", 'font': {'size': 20, 'color': 'white'}},
                                        gauge={'axis': {'range': [None, limit], 'tickcolor': "rgba(255,255,255,0.1)"}, 'bar': {'color': r1},
                                        'bgcolor': "rgba(255,255,255,0.05)", 'borderwidth': 0,
                                        'steps': [{'range': [0, limit*0.5], 'color': "rgba(0,255,0,0.05)"}, {'range': [limit*0.5, limit*0.8], 'color': "rgba(255,179,0,0.05)"}, {'range': [limit*0.8, limit], 'color': "rgba(255,82,82,0.05)"}]}))
                                    
                                    # Yükseklik ve tepe boşluğu artırıldı ki kafası kesilmesin
                                    fig1.update_layout(height=210, margin=dict(t=45, b=0, l=15, r=15), paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Consolas"))
                                    st.plotly_chart(fig1, use_container_width=True, config={'displayModeBar': False})
                                    st.markdown(f"<div style='text-align: center; color: gray; font-size: 0.85em; margin-top: -20px;'>Kalan: <b style='color: {r1};'>{(limit-borc):,.2f} ₺</b></div>", unsafe_allow_html=True)
                                
                                with cg2:
                                    oran2 = (borc / kisisel_limit) * 100 if kisisel_limit > 0 else 0
                                    r2 = "#00bcd4" if oran2 < 75 else "#FF5252"
                                    fig2 = go.Figure(go.Indicator(mode="gauge+number", value=borc, title={'text': "Kişisel Bütçe Sınırı", 'font': {'size': 13, 'color': 'gray'}},
                                        number={'valueformat': ",.0f", 'suffix': " ₺", 'font': {'size': 20, 'color': 'white'}},
                                        gauge={'axis': {'range': [None, kisisel_limit], 'tickcolor': "rgba(255,255,255,0.1)"}, 'bar': {'color': r2},
                                        'bgcolor': "rgba(255,255,255,0.05)", 'borderwidth': 0}))
                                    
                                    # Yükseklik ve tepe boşluğu artırıldı
                                    fig2.update_layout(height=210, margin=dict(t=45, b=0, l=15, r=15), paper_bgcolor="rgba(0,0,0,0)", font=dict(family="Consolas"))
                                    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
                                    st.markdown(f"<div style='text-align: center; color: gray; font-size: 0.85em; margin-top: -20px;'>Kalan Bütçe: <b style='color: {r2};'>{(kisisel_limit-borc):,.2f} ₺</b></div>", unsafe_allow_html=True)

                        # --- SEKME İÇİ SİBER LİSTELER ---
                        st.markdown("<br>", unsafe_allow_html=True)
                        t_aktif, t_taksit, t_gecmis = st.tabs(["Dönemiçi Harcamalar", "Aktif Taksitler", "Geçmiş Ekstreler"])
                        
                        with t_aktif:
                            with st.container(height=350, border=True):
                                kart_harcamalari = df_harcamalar[df_harcamalar['kaynak_hesap'] == f"Kart: {kart_adi}"] if not df_harcamalar.empty else pd.DataFrame()
                                if not kart_harcamalari.empty:
                                    st.markdown(f"<div style='color: #00ff00; font-size: 0.9em; font-weight: bold; margin-bottom: 10px;'>{donem_yazisi} Dönemi İçi Aktif Hareketler</div>", unsafe_allow_html=True)
                                    for _, h in kart_harcamalari.iterrows():
                                        st.markdown(f"<div style='display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 8px 0;'><div><div style='font-weight: bold; color: #e0e0e0; font-size: 0.95em;'>{h['kategori']}</div><div style='color: gray; font-size: 0.75em;'>{pd.to_datetime(h['tarih']).strftime('%d.%m.%Y %H:%M')} | {h['aciklama']}</div></div><div style='color: #FF5252; font-weight: bold; font-family: Consolas;'>-{h['tutar']:,.2f} ₺</div></div>", unsafe_allow_html=True)
                                else: st.info("Bu dönem için karta ait harcama kaydı bulunmuyor.")

                        with t_taksit:
                            with st.container(height=350, border=True):
                                kartin_taksitleri = df_taksitler[df_taksitler['kart_adi'] == kart_adi] if not df_taksitler.empty else pd.DataFrame()
                                if not kartin_taksitleri.empty:
                                    st.markdown(f"<div style='color: #00ff00; font-size: 0.9em; font-weight: bold; margin-bottom: 10px;'>Bu Ay Ekstreye Yansıyacak Toplam Taksit: {kartin_taksitleri['aylik_tutar'].sum():,.2f} ₺</div>", unsafe_allow_html=True)
                                    for _, taksit in kartin_taksitleri.iterrows():
                                        st.markdown(f"<div style='display: flex; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.05); padding: 8px 0;'><div><div style='font-weight: bold; color: #e0e0e0; font-size: 0.9em;'>{taksit['aciklama']}</div><div style='color: gray; font-size: 0.75em;'>Kalan: {taksit['toplam_taksit'] - taksit['odenen_taksit']} Ay</div></div><div style='text-align: right;'><div style='color: #FF5252; font-weight: bold; font-size: 1.1em;'>{taksit['aylik_tutar']:,.2f} ₺</div><div style='background: rgba(255,255,255,0.1); padding: 2px 6px; border-radius: 4px; font-size: 0.75em; color: gray;'>Taksit: {taksit['odenen_taksit'] + 1} / {taksit['toplam_taksit']}</div></div></div>", unsafe_allow_html=True)
                                else: st.info("Bu karta ait devam eden taksitli işlem bulunmuyor.")

                        with t_gecmis:
                            with st.container(height=350, border=True):
                                kartin_gecmisi = df_gecmis_ekstreler[df_gecmis_ekstreler['kart_adi'] == kart_adi] if not df_gecmis_ekstreler.empty else pd.DataFrame()
                                if not kartin_gecmisi.empty:
                                    for _, ekstre in kartin_gecmisi.iterrows():
                                        e_durum = ekstre['durum']
                                        d_renk = "#00ff00" if e_durum == "Ödendi" else "#FF5252"
                                        with st.container(border=True):
                                            st.markdown(f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'><div><div style='font-weight: bold; color: white; font-size: 1.1em;'>{ekstre['donem_adi']} Ekstresi</div><div style='color: gray; font-size: 0.8em;'>Son Ödeme: {pd.to_datetime(ekstre['son_odeme_tarihi']).strftime('%d.%m.%Y')}</div></div><div style='text-align: right;'><div style='color: {d_renk}; font-weight: bold; font-size: 1.2em;'>{ekstre['toplam_borc']:,.2f} ₺</div><div style='color: {d_renk}; font-size: 0.75em; border: 1px solid {d_renk}; border-radius: 4px; padding: 2px 5px;'>{e_durum.upper()}</div></div></div>", unsafe_allow_html=True)
                                            c_ode, c_indir = st.columns(2)
                                            if e_durum == "Ödenmedi":
                                                if c_ode.button(f"Ekstreyi Öde", key=f"ode_{ekstre['id']}", use_container_width=True):
                                                    conn = get_db()
                                                    try:
                                                        c = conn.cursor()
                                                        c.execute("UPDATE gecmis_ekstreler SET durum = 'Ödendi' WHERE id = %s", (ekstre['id'],))
                                                        c.execute("UPDATE kredi_kartlari SET guncel_borc = GREATEST(0, guncel_borc - %s) WHERE kullanici_adi = %s AND kart_adi = %s", (ekstre['toplam_borc'], k_adi, kart_adi))
                                                        conn.commit()
                                                    finally: release_db(conn)
                                                    st.success("Ödendi işaretlendi!"); time.sleep(1); st.rerun()
                                            dekont_metni = f"# EKSTRE DEKONTU\nKart: {kart_adi}\nDönem: {ekstre['donem_adi']}\nToplam Borç: {ekstre['toplam_borc']:,.2f} TL\nKesim Tarihi: {pd.to_datetime(ekstre['kesim_tarihi']).strftime('%d.%m.%Y')}\n"
                                            c_indir.download_button("Dekont İndir", dekont_metni, file_name=f"Dekont_{ekstre['donem_adi']}.md", key=f"dl_{ekstre['id']}", use_container_width=True)
                                else: st.info("Geçmiş ekstre bulunmuyor.")
                                st.markdown("---")
                        c_lim, c_sil = st.columns(2)
                        with c_lim:
                            with st.expander("Bütçe Sınırını Güncelle"):
                                yeni_lim = st.number_input("Yeni Sınır (TL)", value=float(kisisel_limit), step=500.0, key=f"ylim_{kart_adi}")
                                if st.button("Güncelle", key=f"ubtn_{kart_adi}", type="primary"):
                                    conn = get_db(); c = conn.cursor(); c.execute("UPDATE kredi_kartlari SET kisisel_limit = %s WHERE kullanici_adi = %s AND kart_adi = %s", (yeni_lim, k_adi, kart_adi)); conn.commit(); release_db(conn); st.rerun()
                        with c_sil:
                            with st.expander("Kartı Sil"):
                                if st.button("Kalıcı Sil", key=f"del_{kart_adi}"):
                                    conn = get_db(); c = conn.cursor(); c.execute("DELETE FROM kredi_kartlari WHERE kullanici_adi = %s AND kart_adi = %s", (k_adi, kart_adi)); conn.commit(); release_db(conn); st.rerun()
                else: st.info("Kayıtlı kredi kartı bulunamadı.")
            
            with t_gh:
                h_sec = ["Tümü"] + (["Yatırım Hesabı"] if sb == "Midas" else df_bh['hesap_adi'].tolist() + df_bk['kart_adi'].tolist())
                cf1, cf2 = st.columns(2)
                hf = cf1.selectbox("Hesap Filtresi:", h_sec)
                zf = cf2.selectbox("Zaman Aralığı:", ["Bugün", "Son 24 Saat", "Son 7 Gün", "Son 1 Ay", "Tümü"], index=2, key=f"z_{sb}")
                
                conn = get_db()
                try:
                    if sb == "Midas":
                        k = "(islem_tipi LIKE 'BORSA%%' OR detay LIKE '%%Yatırım Hesabı%%')" if hf == "Tümü" else "detay LIKE '%%Yatırım Hesabı%%'"
                        df_h = pd.read_sql_query(f"SELECT tarih, islem_tipi, detay, tutar FROM islem_gecmisi WHERE kullanici_adi = %s AND {k} ORDER BY tarih DESC", conn, params=(k_adi,))
                    else:
                        ara = df_bh['hesap_adi'].tolist() + df_bk['kart_adi'].tolist() if hf == "Tümü" else [hf]
                        if ara:
                            sq = " OR ".join(["detay LIKE %s" for _ in ara])
                            df_h = pd.read_sql_query(f"SELECT tarih, islem_tipi, detay, tutar FROM islem_gecmisi WHERE kullanici_adi = %s AND ({sq}) ORDER BY tarih DESC", conn, params=[k_adi] + [f"%{x}%" for x in ara])
                        else: df_h = pd.DataFrame()
                finally: release_db(conn)
                
                if not df_h.empty:
                    df_h['t_dt'] = pd.to_datetime(df_h['tarih'])
                    bt = pd.Timestamp.today()
                    if zf == "Bugün": df_h = df_h[df_h['t_dt'].dt.date == bt.date()]
                    elif zf == "Son 24 Saat": df_h = df_h[df_h['t_dt'] >= bt - pd.Timedelta(hours=24)]
                    elif zf == "Son 7 Gün": df_h = df_h[df_h['t_dt'] >= bt - pd.Timedelta(days=7)]
                    elif zf == "Son 1 Ay": df_h = df_h[df_h['t_dt'] >= bt - pd.DateOffset(months=1)]
                    
                    with st.container(height=350):
                        if df_h.empty: st.info("Kayıt yok.")
                        else:
                            for _, r in df_h.iterrows():
                                rr = "#4CAF50" if r['tutar'] > 0 else "#FF5252"
                                ri = "+" if r['tutar'] > 0 else "-"
                                with st.container(border=True):
                                    c1, c2 = st.columns([4, 2])
                                    c1.markdown(f"**{r['islem_tipi']}**<br><span style='font-size:0.85em;color:gray;'>{r['detay']} | {r['t_dt'].strftime('%d.%m.%Y %H:%M')}</span>", unsafe_allow_html=True)
                                    c2.markdown(f"<div style='text-align:right; color:{rr}; padding-top:10px;'><b>{ri}{abs(r['tutar']):,.2f} TL</b></div>", unsafe_allow_html=True)
                else: st.info("Kayıt yok.")

        with t_transfer:
            conn = get_db()
            df_tv = pd.read_sql_query("SELECT hesap_adi, bakiye, para_birimi FROM banka_hesaplari WHERE kullanici_adi = %s", conn, params=(k_adi,))
            c = conn.cursor()
            c.execute("SELECT hesap_adi, bakiye FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi LIKE '%%Yatırım Hesabı%%'", (k_adi,))
            y_hesaplar = c.fetchall()
            release_db(conn)
            
            th = [f"Hesap: {r['hesap_adi']} ({r['bakiye']:.2f} {r['para_birimi'] if r['para_birimi'] else 'TL'})" for _, r in df_tv.iterrows()]
            for yh in y_hesaplar: th.append(f"Yatırım: {yh[0]} ({yh[1]:.2f} {'USD' if '(USD)' in yh[0] else 'EUR' if '(EUR)' in yh[0] else 'TL'})")
            
            # EKRANI İKİYE BÖLÜYORUZ
            c_ic, c_dis = st.columns(2)
            
            with c_ic:
                st.markdown("##### Kurumlar Arası Virman")
                
                st.markdown("<span style='font-size:0.9em; color:gray;'>Çıkış Yapılacak Kaynak:</span>", unsafe_allow_html=True)
                v_k = st.selectbox("Çıkış Yapılacak Kaynak", th, label_visibility="collapsed", key="v_kaynak_banka")
                kalan_th = [h for h in th if h != v_k]
                
                kbak_b = float(v_k.rsplit("(", 1)[1].split(" ")[0])
                k_pb_b = v_k.rsplit("(", 1)[1].split(" ")[1].replace(")", "")

                with st.form("virman_form"):
                    v_h = st.selectbox("Giriş Yapılacak Hedef", kalan_th)
                    
                    tumu_v = st.checkbox(f"Tüm Bakiyeyi Transfer Et (Mevcut: {kbak_b:,.2f} {k_pb_b})")
                    
                    cv1, cv2 = st.columns(2)
                    v_t = cv1.number_input("Transfer Tutarı", min_value=0.0, value=0.0, step=100.0, disabled=tumu_v)
                    v_kom = cv2.number_input("Komisyon / Masraf", min_value=0.0, step=5.0, value=0.0)
                    
                    if st.form_submit_button("Transferi Başlat", type="primary"):
                        ks = v_k.rsplit(" (", 1)[0].replace("Hesap: ", "").replace("Yatırım: ", "").replace("🏦 ", "").replace("💼 ", "")
                        hs = v_h.rsplit(" (", 1)[0].replace("Hesap: ", "").replace("Yatırım: ", "").replace("🏦 ", "").replace("💼 ", "")
                        k_pb = v_k.rsplit("(", 1)[1].split(" ")[1].replace(")", "")
                        h_pb = v_h.rsplit("(", 1)[1].split(" ")[1].replace(")", "")
                        kbak = float(v_k.rsplit("(", 1)[1].split(" ")[0])
                        
                        islem_tutari = (kbak - v_kom) if tumu_v else v_t
                        if islem_tutari <= 0: st.error("Hata: Transfer tutarı 0'dan büyük olmalıdır (Komisyon bakiyeyi aşıyor olabilir)."); st.stop()
                        
                        toplam_cikis = islem_tutari + v_kom
                        if toplam_cikis > kbak: st.error("Yetersiz Bakiye (Tutar + Komisyon)."); st.stop()
                        
                        k1, k2 = doviz_kuru_cek(k_pb), doviz_kuru_cek(h_pb)
                        ttl, ht, kom_tl = islem_tutari * k1, (islem_tutari * k1) / k2, v_kom * k1
                        
                        conn = get_db()
                        try:
                            c = conn.cursor()
                            if "Yatırım:" in v_k or "💼" in v_k:
                                c.execute("UPDATE hesaplar SET bakiye = bakiye - %s WHERE kullanici_adi = %s AND hesap_adi = %s", (toplam_cikis, k_adi, ks))
                                if k_pb == "TL": c.execute("UPDATE bakiyeler SET bakiye = bakiye - %s WHERE kullanici_adi = %s", (toplam_cikis, k_adi))
                            else: c.execute("UPDATE banka_hesaplari SET bakiye = bakiye - %s WHERE kullanici_adi = %s AND hesap_adi = %s", (toplam_cikis, k_adi, ks))
                                
                            if "Yatırım:" in v_h or "💼" in v_h:
                                c.execute("UPDATE hesaplar SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = %s", (ht, k_adi, hs))
                                if h_pb == "TL": c.execute("UPDATE bakiyeler SET bakiye = bakiye + %s WHERE kullanici_adi = %s", (ht, k_adi))
                            else: c.execute("UPDATE banka_hesaplari SET bakiye = bakiye + %s WHERE kullanici_adi = %s AND hesap_adi = %s", (ht, k_adi, hs))
                                
                            c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'VİRMAN', %s, %s)", (k_adi, f"{ks} ({islem_tutari:.2f} {k_pb}) -> {hs} ({ht:.2f} {h_pb})", ttl))
                            if v_kom > 0:
                                c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'KOMİSYON GİDERİ (-)', %s, %s)", (k_adi, f"{ks} Transfer Ücreti", -kom_tl))
                                c.execute("INSERT INTO harcamalar (kullanici_adi, kategori, aciklama, tutar, kaynak_hesap) VALUES (%s, 'Banka Kesintisi', 'Kurumlar Arası Virman Komisyonu', %s, %s)", (k_adi, kom_tl, ks))

                            conn.commit()
                            st.success(f"Transfer İşlendi: {islem_tutari:.2f} {k_pb} -> {ht:.2f} {h_pb} (Kesinti: {v_kom:.2f} {k_pb})"); st.rerun()
                        finally: release_db(conn)

            with c_dis:
                st.markdown("##### Dış İşlemler (EFT / Havale / SWIFT)")
                st.caption("Sistem Notu: Kurum dışı hesaplardan gelen veya kuruma gönderilen transferler (TL/Döviz).")
                
                islem_yonu = st.radio("İşlem Yönü", ["Giden Transfer (EFT/SWIFT Gönder)", "Gelen Transfer (Hesaba Para Girişi)"])
                st.markdown("<span style='font-size:0.9em; color:gray;'>İşlem Yapılacak Kendi Hesabınız:</span>", unsafe_allow_html=True)
                d_kaynak = st.selectbox("İşlem Yapılacak Kendi Hesabınız", th, label_visibility="collapsed", key="d_kaynak_dis")
                
                kbak_d = float(d_kaynak.rsplit("(", 1)[1].split(" ")[0])
                pb_d = d_kaynak.rsplit("(", 1)[1].split(" ")[1].replace(")", "")
                
                with st.form("dis_islem_form"):
                    d_karsi = st.text_input("Karşı Taraf (Gönderen / Alıcı Adı veya IBAN)")
                    
                    tumu_d = False
                    if "Giden" in islem_yonu:
                        tumu_d = st.checkbox(f"Tüm Bakiyeyi Gönder (Mevcut: {kbak_d:,.2f} {pb_d})")
                        
                    cd1, cd2 = st.columns(2)
                    d_tutar = cd1.number_input("Transfer Tutarı", min_value=0.0, value=0.0, step=100.0, disabled=tumu_d)
                    d_kom = cd2.number_input("Komisyon / Masraf", min_value=0.0, step=5.0, value=0.0)
                    
                    if st.form_submit_button("İşlemi Onayla", type="primary"):
                        if not d_karsi: st.error("İşlem Reddedildi: Lütfen karşı taraf bilgilerini girin."); st.stop()
                        
                        k_saf = d_kaynak.rsplit(" (", 1)[0].replace("Hesap: ", "").replace("Yatırım: ", "").replace("🏦 ", "").replace("💼 ", "")
                        kbak = float(d_kaynak.rsplit("(", 1)[1].split(" ")[0])
                        pb = d_kaynak.rsplit("(", 1)[1].split(" ")[1].replace(")", "")
                        kom_tl = d_kom * doviz_kuru_cek(pb)
                        
                        islem_tutari = (kbak - d_kom) if tumu_d else d_tutar
                        if islem_tutari <= 0: st.error("Hata: Transfer tutarı 0'dan büyük olmalıdır."); st.stop()
                        
                        conn = get_db()
                        try:
                            c = conn.cursor()
                            if "Giden" in islem_yonu:
                                toplam_cikis = islem_tutari + d_kom
                                if toplam_cikis > kbak: st.error("İşlem Reddedildi: Yetersiz Bakiye (Tutar + Komisyon)."); st.stop()
                                
                                if "Yatırım:" in d_kaynak or "💼" in d_kaynak:
                                    c.execute("UPDATE hesaplar SET bakiye = bakiye - %s WHERE kullanici_adi = %s AND hesap_adi = %s", (toplam_cikis, k_adi, k_saf))
                                    if pb == "TL": c.execute("UPDATE bakiyeler SET bakiye = bakiye - %s WHERE kullanici_adi = %s", (toplam_cikis, k_adi))
                                else:
                                    c.execute("UPDATE banka_hesaplari SET bakiye = bakiye - %s WHERE kullanici_adi = %s AND hesap_adi = %s", (toplam_cikis, k_adi, k_saf))
                                
                                detay_notu = f"{k_saf} -> {d_karsi} (Giden)"
                                tl_karsiligi = islem_tutari * doviz_kuru_cek(pb)
                                c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'DIŞ TRANSFER (-)', %s, %s)", (k_adi, detay_notu, -tl_karsiligi))
                                
                                if d_kom > 0:
                                    c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'KOMİSYON GİDERİ (-)', %s, %s)", (k_adi, f"{k_saf} Giden Transfer Ücreti", -kom_tl))
                                    c.execute("INSERT INTO harcamalar (kullanici_adi, kategori, aciklama, tutar, kaynak_hesap) VALUES (%s, 'Banka Kesintisi', 'Giden Transfer Komisyonu', %s, %s)", (k_adi, kom_tl, k_saf))
                                
                                conn.commit()
                                st.success(f"İşlem Başarılı: {islem_tutari:,.2f} {pb}, {d_karsi} tarafına gönderildi. (Masraf: {d_kom:.2f} {pb})")
                            else:
                                if "Yatırım:" in d_kaynak or "💼" in d_kaynak:
                                    c.execute("UPDATE hesaplar SET bakiye = bakiye + %s - %s WHERE kullanici_adi = %s AND hesap_adi = %s", (islem_tutari, d_kom, k_adi, k_saf))
                                    if pb == "TL": c.execute("UPDATE bakiyeler SET bakiye = bakiye + %s - %s WHERE kullanici_adi = %s", (islem_tutari, d_kom, k_adi))
                                else:
                                    c.execute("UPDATE banka_hesaplari SET bakiye = bakiye + %s - %s WHERE kullanici_adi = %s AND hesap_adi = %s", (islem_tutari, d_kom, k_adi, k_saf))
                                    
                                detay_notu = f"{d_karsi} -> {k_saf} (Gelen)"
                                tl_karsiligi = islem_tutari * doviz_kuru_cek(pb)
                                c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'DIŞ TRANSFER (+)', %s, %s)", (k_adi, detay_notu, tl_karsiligi))
                                
                                if d_kom > 0:
                                    c.execute("INSERT INTO islem_gecmisi (kullanici_adi, islem_tipi, detay, tutar) VALUES (%s, 'KOMİSYON GİDERİ (-)', %s, %s)", (k_adi, f"{k_saf} Gelen Transfer Kesintisi", -kom_tl))
                                    c.execute("INSERT INTO harcamalar (kullanici_adi, kategori, aciklama, tutar, kaynak_hesap) VALUES (%s, 'Banka Kesintisi', 'Gelen Transfer Masrafı', %s, %s)", (k_adi, kom_tl, k_saf))
                                    
                                conn.commit()
                                st.success(f"İşlem Başarılı: {islem_tutari:,.2f} {pb}, {k_saf} hesabınıza yatırıldı. (Masraf: {d_kom:.2f} {pb})")
                            
                            time.sleep(1.5)
                            st.rerun()
                        finally:
                            release_db(conn)

        with t_ekle:
            st.markdown("##### Sistem Kaydı Oluştur")
            tur = st.radio("Kayıt Tipi", ["Banka Hesabı", "Kredi Kartı", "Düzenli Gelir / Gider"], horizontal=True, label_visibility="collapsed")
            bankalar = ["Vakıfbank", "Ziraat Bankası", "Garanti BBVA", "İş Bankası", "Yapı Kredi", "Akbank", "QNB Finansbank", "Enpara", "Diğer"]
            
            if tur == "Banka Hesabı":
                c_s, c_t, c_p = st.columns([3, 2, 2])
                s_b = c_s.selectbox("Finansal Kurum", bankalar)
                h_t = c_t.selectbox("Hesap Türü", ["Vadesiz", "Vadeli"])
                p_b = c_p.selectbox("Para Birimi", ["TL", "USD", "EUR", "GBP"])
                
                with st.form("y_hesap"):
                    h_a = st.text_input("Hesap Tanımı (Örn: Maaş Hesabı)")
                    if h_t == "Vadeli":
                        st.caption("Sistem Notu: Vadeli hesaplar için faiz ve vade detaylarını girin. Sistem zamanı geldiğinde bileşik faizi otomatik işleyecektir.")
                        c3, c4, c5 = st.columns(3)
                        bak = c3.number_input(f"Başlangıç Bakiyesi ({p_b})", min_value=0.0)
                        faiz = c4.number_input("Brüt Faiz Oranı (%)", min_value=0.0, step=0.1)
                        stopaj = c5.number_input("Stopaj Oranı (%)", min_value=0.0, step=0.1, value=5.0)
                        c6, c7 = st.columns(2)
                        vade = c6.number_input("Vade (Gün)", min_value=1, step=1)
                        saat = c7.time_input("Tahakkuk Saati", value=datetime.time(0,0))
                    else:
                        bak = st.number_input(f"Mevcut Bakiye ({p_b})", min_value=0.0)
                        faiz, stopaj, vade, saat = 0.0, 0.0, 0, "00:00"
                        
                    if st.form_submit_button("Hesabı Sisteme Ekle", type="primary"):
                        if h_a:
                            s_str = saat.strftime("%H:%M") if h_t == "Vadeli" else "00:00"
                            saat_tam = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            conn = get_db()
                            try:
                                c = conn.cursor()
                                c.execute("INSERT INTO banka_hesaplari (kullanici_adi, banka_adi, hesap_adi, hesap_turu, bakiye, faiz_orani, stopaj_orani, vade_gun, tahakkuk_saati, acilis_tarihi, para_birimi) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", (k_adi, s_b, h_a, h_t, bak, faiz, stopaj, vade, s_str, saat_tam, p_b))
                                conn.commit()
                            finally: release_db(conn)
                            st.success("Hesap kaydı tamamlandı."); st.rerun()
                            
            elif tur == "Kredi Kartı":
                s_b = st.selectbox("Finansal Kurum", bankalar)
                with st.form("y_kart"):
                    c1, c2, c3 = st.columns([2,1,1])
                    k_a = c1.text_input("Kart Tanımı")
                    b_lim = c2.number_input("Banka Limiti (TL)", min_value=0.0)
                    k_lim = c3.number_input("Kişisel Bütçe Sınırı (TL)", min_value=0.0)
                    st.caption("Sistem Notu: Ekstre döngülerini girin ki sistem yaklaştığında sizi uyarsın.")
                    cx1, cx2 = st.columns(2)
                    kesim = cx1.number_input("Hesap Kesim Günü", min_value=1, max_value=31)
                    odeme = cx2.number_input("Son Ödeme Günü", min_value=1, max_value=31)
                    
                    if st.form_submit_button("Kartı Sisteme Ekle", type="primary"):
                        if k_a and b_lim > 0:
                            conn = get_db()
                            try:
                                c = conn.cursor()
                                c.execute("INSERT INTO kredi_kartlari (kullanici_adi, banka_adi, kart_adi, limit_tutari, guncel_borc, hesap_kesim_gunu, son_odeme_gunu, kisisel_limit) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (k_adi, s_b, k_a, b_lim, 0.0, kesim, odeme, k_lim if k_lim > 0 else b_lim))
                                conn.commit()
                            finally: release_db(conn)
                            st.success("Kart kaydı tamamlandı."); st.rerun()
                        else:
                            st.error("Lütfen geçerli bir kart adı ve limit girin.")
                            
            else: 
                conn = get_db()
                try:
                    df_vad = pd.read_sql_query("SELECT hesap_adi FROM banka_hesaplari WHERE kullanici_adi = %s AND hesap_turu = 'Vadesiz'", conn, params=(k_adi,))
                    df_kar = pd.read_sql_query("SELECT kart_adi FROM kredi_kartlari WHERE kullanici_adi = %s", conn, params=(k_adi,))
                    c = conn.cursor()
                    c.execute("SELECT hesap_adi FROM hesaplar WHERE kullanici_adi = %s AND hesap_adi LIKE '%%Yatırım Hesabı%%'", (k_adi,))
                    y_hesaplar = c.fetchall()
                finally: release_db(conn)
                
                s_kaynaklar = [f"Hesap: {r['hesap_adi']}" for _, r in df_vad.iterrows()]
                for yh in y_hesaplar: s_kaynaklar.append(f"Yatırım: {yh[0]}")
                s_kartlar = [f"Kart: {r['kart_adi']}" for _, r in df_kar.iterrows()]

                with st.form("y_sabit"):
                    st.caption("Her ay otomatik işlenecek maaş, kira, fatura gibi düzenli döngülerinizi tanımlayın.")
                    s_tip = st.selectbox("İşlem Tipi", ["Düzenli Gelir (+)", "Düzenli Gider (-)"])
                    
                    if "Gider" in s_tip:
                        s_hesap = st.selectbox("Çekileceği Kaynak", s_kaynaklar + s_kartlar)
                    else:
                        s_hesap = st.selectbox("Yatırılacağı Kaynak", s_kaynaklar)
                        
                    s_isim = st.text_input("Açıklama (Örn: Maaş, Kira, Netflix)")
                    
                    c1, c2 = st.columns(2)
                    s_tutar = c1.number_input("Aylık Tutar (TL)", min_value=1.0, step=100.0)
                    s_gun = c2.number_input("Her Ayın Kaçıncı Günü?", min_value=1, max_value=31, step=1)
                    
                    if st.form_submit_button("Otomatik Talimatı Başlat", type="primary"):
                        if s_isim and s_tutar > 0:
                            bugun = datetime.date.today()
                            
                            # Akıllı Mühür (Eski ayları veya geçilmiş günleri yatırmaz)
                            if bugun.day >= s_gun:
                                ilk_damga = f"{bugun.year}-{bugun.month:02d}"
                            else:
                                ilk_damga = "Yok"
                                
                            conn = get_db()
                            try:
                                c = conn.cursor()
                                c.execute("INSERT INTO sabit_islemler (kullanici_adi, islem_turu, aciklama, tutar, islem_gunu, bagli_hesap, son_islenme_tarihi) VALUES (%s,%s,%s,%s,%s,%s,%s)", 
                                          (k_adi, "Gelir" if "Gelir" in s_tip else "Gider", s_isim, s_tutar, s_gun, s_hesap, ilk_damga))
                                conn.commit()
                            finally: release_db(conn)
                            st.success(f"Talimat kaydedildi. Sistem bu işlemi her ayın {s_gun}. günü otomatik uygulayacak."); st.rerun()
                        else:
                            st.error("Lütfen geçerli bir isim ve tutar girin.")
                            
    
   # --- ANA PİYASA VE HABER TERMİNALİ ---
    elif secilen_sayfa == "Piyasa Analiz":
        st.title("Piyasa ve Ekonomi Terminali")
        
        t_grafik, t_gosterge, t_haber, t_makro = st.tabs(["Piyasa Grafikleri", "Teknik Göstergeler", "KAP ve Şirket Haberleri", "Makro Ekonomi"])

        with t_grafik:
            conn = get_db()
            try:
                df_p = pd.read_sql_query('SELECT varlik_adi as "VARLIK", borsa as "BORSA" FROM portfoy WHERE kullanici_adi = %s GROUP BY varlik_adi, borsa HAVING SUM(lot) > 0.01', conn, params=(k_adi,))
                df_e = pd.read_sql_query("SELECT maden_turu FROM emtia_portfoy WHERE kullanici_adi = %s GROUP BY maden_turu HAVING SUM(miktar) > 0.01", conn, params=(k_adi,))
            finally: release_db(conn)

            def periyot_ayarla(p_str):
                if p_str == "1 Gün": return "1d", "5m"
                elif p_str == "1 Hafta": return "5d", "1h"
                elif p_str == "1 Ay": return "1mo", "1d"
                elif p_str == "3 Ay": return "3mo", "1d"
                elif p_str == "6 Ay": return "6mo", "1d"
                elif p_str == "1 Yıl": return "1y", "1d"
                elif p_str == "Maks.": return "max", "1wk"
                else: return "1mo", "1d"

            @st.cache_data(ttl=3600)
            def tefas_gecmis_veri_cek(fon_kod, periyot_str):
                import urllib3; urllib3.disable_warnings()
                # --- TEFAS GÜVENLİK DUVARI AŞICI (Tarayıcı Kimliği) ---
                basliklar = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Origin': 'https://www.tefas.gov.tr',
                    'Referer': f'https://www.tefas.gov.tr/FonAnaliz.aspx?FonKod={fon_kod.upper()}'
                }
                bugun = datetime.date.today()
                
                # Grafiğin düzgün çizilmesi için başlangıç tarihlerini genişlettik
                if periyot_str in ["Bugün", "1 Gün", "1 Hafta"]: bas_tarih = bugun - datetime.timedelta(days=10)
                elif periyot_str == "1 Ay": bas_tarih = bugun - datetime.timedelta(days=35)
                elif periyot_str == "3 Ay": bas_tarih = bugun - datetime.timedelta(days=95)
                elif periyot_str == "6 Ay": bas_tarih = bugun - datetime.timedelta(days=185)
                elif periyot_str == "1 Yıl": bas_tarih = bugun - datetime.timedelta(days=370)
                else: bas_tarih = bugun - datetime.timedelta(days=1825)
                
                api_url = "https://www.tefas.gov.tr/api/DB/BindHistoryInfo"
                data = {"fontip": "YAT", "sfontur": "", "fonkod": fon_kod.upper(), "fongrup": "", "bastarih": bas_tarih.strftime("%d.%m.%Y"), "bittarih": bugun.strftime("%d.%m.%Y")}
                try:
                    r = requests.post(api_url, data=data, headers=basliklar, timeout=10, verify=False)
                    if r.status_code == 200 and 'data' in r.json() and len(r.json()['data']) > 0:
                        df = pd.DataFrame(r.json()['data'])
                        try: df['TARIH'] = pd.to_datetime(df['TARIH'], unit='ms')
                        except: df['TARIH'] = pd.to_datetime(df['TARIH'])
                        df['FIYAT'] = df['FIYAT'].astype(float)
                        df = df.sort_values('TARIH').set_index('TARIH')
                        return df[['FIYAT']]
                except: pass
                return pd.DataFrame()

            def cizgi_grafik_ciz(isim, kod, borsa_turu, periyot_str, ana_grafik=False):
                try:
                    is_tefas = (borsa_turu == "FON (TEFAS)")
                    if is_tefas:
                        data = tefas_gecmis_veri_cek(kod, periyot_str)
                        if data.empty: st.caption(f"{isim} için TEFAS sunucusundan veri çekilemedi."); return
                        fiyat_sutunu = 'FIYAT'
                        x_ekseni = data.index.strftime('%d %b %Y')
                    else:
                        p_val, i_val = periyot_ayarla(periyot_str)
                        is_us = borsa_turu in ["NASDAQ", "S&P 500", "ETF"]
                        data = yf.Ticker(kod).history(period=p_val, interval=i_val, prepost=is_us).dropna(subset=['Close'])
                        if data.empty: st.caption(f"{isim} için Yahoo Finance verisi yok."); return
                        fiyat_sutunu = 'Close'
                        if i_val == '5m': x_ekseni = data.index.strftime('%H:%M')
                        elif i_val == '1h': x_ekseni = data.index.strftime('%d %b %H:%M')
                        else: x_ekseni = data.index.strftime('%d %b %Y')
                    
                    guncel_f = tefas_fiyat_cek(kod) if is_tefas else hizli_fiyat_cek(kod)[0]
                    ilk_f = data[fiyat_sutunu].iloc[0]
                    
                    if guncel_f:
                        son_f = guncel_f
                        data.iloc[-1, data.columns.get_loc(fiyat_sutunu)] = guncel_f
                    else:
                        son_f = data[fiyat_sutunu].iloc[-1]

                    degisim = ((son_f - ilk_f) / ilk_f) * 100
                    
                    # --- DİNAMİK RENK AYARI ---
                    # Grafik çizgisi ve metinler için ana renk
                    t_renk = '#00ff00' if degisim >= 0 else '#FF5252' 
                    # Grafik arka plan gradyanı için şeffaf renk (Yeşil veya Kırmızı)
                    b_renk = 'rgba(0,255,0,0.05)' if degisim >= 0 else 'rgba(255,82,82,0.05)'
                    
                    isaret = "+" if degisim >= 0 else ""
                    f_metin = f"{son_f:,.4f}" if is_tefas else f"{son_f:,.2f}"
                    
                    # HTML Kartını Dinamik Renkle Çiz
                    st.markdown(f"""
                        <div style='background: linear-gradient(90deg, {b_renk} 0%, rgba(0,0,0,0) 100%); border-left: 3px solid {t_renk}; padding: 10px 15px; border-radius: 4px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;'>
                            <div style='line-height: 1.2;'>
                                <div style='font-size: 1.1em; font-weight: bold; color: white;'>{isim}</div>
                                <div style='color: gray; font-size: 0.8em; font-family: Consolas;'>{kod}</div>
                            </div>
                            <div style='text-align: right; line-height: 1.2;'>
                                <div style='font-size: 1.2em; font-weight: bold; color: white; font-family: Consolas;'>{f_metin}</div>
                                <div style='color: {t_renk}; font-size: 0.9em; font-weight: bold; font-family: Consolas;'>{isaret}{degisim:.2f}%</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Plotly Grafiğini Dinamik Renkle Çiz
                    fig = go.Figure(go.Scatter(x=x_ekseni, y=data[fiyat_sutunu], mode='lines', line=dict(color=t_renk, width=2)))
                    min_v = data[fiyat_sutunu].min() * 0.99
                    max_v = data[fiyat_sutunu].max() * 1.01
                    h = 320 if ana_grafik else 240
                    
                    fig.update_layout(
                        height=h, margin=dict(t=5, b=5, l=0, r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", 
                        yaxis=dict(gridcolor='rgba(255, 255, 255, 0.05)', tickformat=".4f" if is_tefas else ".2f", range=[min_v, max_v]), 
                        xaxis=dict(gridcolor='rgba(255, 255, 255, 0.0)', showline=False, type='category', nticks=5), 
                        hovermode="x unified", font=dict(family="Consolas", color="gray", size=10), showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                except Exception: st.caption(f"{isim} grafiği şu an yüklenemiyor.")

            # --- EKRANI İKİYE BÖLÜYORUZ (PORTFÖY GRAFİKLERİ KORUNARAK) ---
            # --- 2. EKRANI İKİYE BÖLME VE ANA TASARIM ---
            # --- 2. EKRANI İKİYE BÖLME VE ANA TASARIM ---
            ana_sol, ana_sag = st.columns(2)
            
            # ================= SOL KARE: QUANT ANALİZ =================
            with ana_sol:
                with st.container(border=True):
                    st.markdown("<div style='display: flex; align-items: center; margin-bottom: 15px;'><div style='width: 10px; height: 10px; background: #00ff00; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 8px #00ff00;'></div><div style='color: #00ff00; font-size: 1.1em; font-weight: 700; letter-spacing: 1px; font-family: Consolas;'>QUANT ANALİZ RADARI</div></div>", unsafe_allow_html=True)
                    
                    c1, c2, c3 = st.columns([1.2, 1.5, 1.3])
                    secili_borsa = c1.selectbox("Piyasa", ["BİST", "NASDAQ", "KRİPTO"], key="q_borsa", label_visibility="collapsed")
                    hisse_kodu = c2.text_input("Varlık Kodu", key="q_kod", placeholder="Örn: THYAO", label_visibility="collapsed").upper()
                    
                    if c3.button("ANALİZ ET", key="q_btn", type="primary", use_container_width=True):
                        if hisse_kodu:
                            st.session_state['q_aktif_hisse'] = hisse_kodu.strip()
                            st.session_state['q_aktif_borsa'] = secili_borsa
                        else: st.warning("Kod giriniz.")

                    # ARAMA YAPILDIYSA
                    if st.session_state.get('q_aktif_hisse'):
                        t_kod = st.session_state['q_aktif_hisse']
                        s_borsa = st.session_state['q_aktif_borsa']
                        
                        st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-top: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)
                        c_baslik, c_kapat = st.columns([3, 1])
                        c_baslik.markdown(f"<div style='color: gray; font-size: 0.85em; padding-top: 5px;'>Aktif Analiz: <b style='color: #00ff00;'>{t_kod}</b></div>", unsafe_allow_html=True)
                        if c_kapat.button("✖ Kapat", key="q_kapat_btn", use_container_width=True):
                            st.session_state.pop('q_aktif_hisse', None)
                            st.rerun()
                            
                        if s_borsa == "BİST" and not t_kod.endswith(".IS"): t_kod += ".IS"
                        elif s_borsa == "KRİPTO" and not t_kod.endswith("-USD"): t_kod += "-USD"
                        elif s_borsa == "EMTİA" and "=F" not in t_kod: t_kod += "=F"
                        
                        with st.spinner("Model işleniyor..."):
                            try:
                                df_raw = yf.Ticker(t_kod).history(period="1y", interval="1d").dropna(subset=['Close'])
                                if df_raw.empty: st.error("Veri bulunamadı."); st.stop()
                                
                                son_f = float(df_raw['Close'].iloc[-1])
                                onceki_f = float(df_raw['Close'].iloc[-2]) if len(df_raw) > 1 else son_f
                                deg_yuzde = ((son_f - onceki_f) / onceki_f) * 100 if onceki_f > 0 else 0.0
                                renk_f = "#00ff00" if deg_yuzde >= 0 else "#FF5252"
                                isaret = "+" if deg_yuzde >= 0 else ""
                                hacim = float(df_raw['Volume'].iloc[-1]) if 'Volume' in df_raw.columns else 0.0
                                
                                df_raw['SMA50'] = df_raw['Close'].rolling(50).mean(); df_raw['SMA200'] = df_raw['Close'].rolling(200).mean()
                                sma50 = df_raw['SMA50'].iloc[-1]; sma200 = df_raw['SMA200'].iloc[-1]
                                t_val = 3.0 if (son_f > sma50 and son_f > sma200) else (1.5 if son_f > sma50 else 0.5) if not pd.isna(sma50) else 1.5
                                
                                delta = df_raw['Close'].diff(); gain = delta.clip(lower=0).ewm(alpha=1/14).mean(); loss = (-delta.clip(upper=0)).ewm(alpha=1/14).mean()
                                rsi = 100 - (100 / (1 + (gain / loss))).iloc[-1]; rsi = rsi if not pd.isna(rsi) else 50.0
                                ema12 = df_raw['Close'].ewm(span=12).mean(); ema26 = df_raw['Close'].ewm(span=26).mean()
                                macd = (ema12 - ema26).iloc[-1]; sig = (ema12 - ema26).ewm(span=9).mean().iloc[-1]
                                m_val = (2.0 if 45 < rsi < 65 else 0.0) + (2.0 if macd > sig else 0.0)
                                
                                df_raw['STD20'] = df_raw['Close'].rolling(20).std(); df_raw['SMA20'] = df_raw['Close'].rolling(20).mean()
                                std20 = df_raw['STD20'].iloc[-1]; sma20 = df_raw['SMA20'].iloc[-1]
                                v_val = 0.5
                                if not pd.isna(std20): b_alt = sma20 - (std20 * 2); v_val = 3.0 if son_f < b_alt * 1.05 else (1.5 if b_alt < son_f < sma20 else 0.5)
                                
                                puan = t_val + m_val + v_val
                                renk_p = "#00ff00" if puan >= 7.5 else ("#ffb300" if puan >= 5 else "#FF5252")
                                karar = "GÜÇLÜ AL" if puan >= 8.5 else ("AL" if puan >= 7 else ("İZLE" if puan >= 5 else "ZAYIF/SAT"))

                                html_cikti = (
    f"<div style='background: rgba(15,15,15,0.6); border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid {renk_p}; border-radius: 6px; padding: 10px; font-family: Consolas, monospace; margin-bottom: 10px;'>"
    f"<div style='display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 5px; margin-bottom: 5px;'>"
    f"<div><span style='font-size: 1.3em; font-weight: bold; color: white;'>{t_kod.replace('.IS', '').replace('-USD', '')}</span><br>"
    f"<span style='font-size: 1.0em; color: {renk_f};'>{son_f:,.2f} ({isaret}{deg_yuzde:.2f}%)</span></div>"
    f"<div style='text-align: right;'><span style='font-size: 0.7em; color: gray;'>QUANT SKORU</span><br>"
    f"<span style='font-size: 1.6em; font-weight: bold; color: {renk_p};'>{puan:.1f}/10</span></div></div>"
    f"<div style='font-size: 0.85em; line-height: 1.6;'>"
    f"<div style='display: flex; justify-content: space-between;'><span style='color: gray;'>[KARAR]</span><span style='color: {renk_p}; font-weight: bold;'>{karar}</span></div>"
    f"<div style='display: flex; justify-content: space-between;'><span style='color: gray;'>[HACİM]</span><span style='color: white;'>{hacim:,.0f} Lot</span></div>"
    f"<div style='display: flex; justify-content: space-between;'><span style='color: gray;'>[MOMENTUM]</span><span style='color: white;'>{(t_val+m_val):.1f}/7.0</span></div>"
    f"</div></div>"
                                )
                                st.markdown(html_cikti, unsafe_allow_html=True)
                                
                                cg1, cg2 = st.columns(2)
                                g_ara = cg1.selectbox("Aralık", ["1 Gün", "1 Hafta", "1 Ay", "3 Ay", "6 Ay", "1 Yıl"], index=2, key="qa", label_visibility="collapsed")
                                g_tur = cg2.selectbox("Tür", ["Mum Grafik", "Çizgi Grafik"], key="qt", label_visibility="collapsed")
                                
                                p_val, i_val = periyot_ayarla(g_ara)
                                df_chart = yf.Ticker(t_kod).history(period=p_val, interval=i_val).dropna(subset=['Close'])
                                
                                if not df_chart.empty:
                                    if i_val == '5m': x_vals = df_chart.index.strftime('%H:%M')
                                    elif i_val == '1h': x_vals = df_chart.index.strftime('%d %b %H:%M')
                                    else: x_vals = df_chart.index.strftime('%d %b %Y')
                                    
                                    from plotly.subplots import make_subplots
                                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.8, 0.2])
                                    
                                    if g_tur == "Mum Grafik":
                                        fig.add_trace(go.Candlestick(x=x_vals, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], 
                                                                     increasing_line_color='#00ff00', decreasing_line_color='#FF5252', increasing_fillcolor='#00ff00', decreasing_fillcolor='#FF5252',
                                                                     line=dict(width=1), name='Fiyat'), row=1, col=1)
                                    else:
                                        fig.add_trace(go.Scatter(x=x_vals, y=df_chart['Close'], mode='lines', line=dict(color=renk_f, width=1.5), name='Fiyat'), row=1, col=1)

                                    colors = ['rgba(0, 255, 0, 0.4)' if row['Close'] >= row['Open'] else 'rgba(255, 82, 82, 0.4)' for _, row in df_chart.iterrows()]
                                    fig.add_trace(go.Bar(x=x_vals, y=df_chart['Volume'], marker_color=colors, name='Hacim'), row=2, col=1)

                                    fig.update_layout(height=230, margin=dict(t=5,b=0,l=0,r=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_rangeslider_visible=False, showlegend=False, font=dict(family="Consolas", color="gray", size=9))
                                    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', type='category', nticks=4, row=2, col=1)
                                    fig.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', side='right', tickformat=".2f", row=1, col=1)
                                    fig.update_yaxes(showgrid=False, side='right', showticklabels=False, row=2, col=1)
                                    
                                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                            except Exception as e: st.error(f"İşlem hatası: {e}")

            # ================= SAĞ KARE: PİYASA ENDEKSLERİ =================
            with ana_sag:
                with st.container(border=True):
                    st.markdown("<div style='display: flex; align-items: center; margin-bottom: 15px;'><div style='width: 10px; height: 10px; background: #00ff00; border-radius: 50%; margin-right: 10px; box-shadow: 0 0 8px #00ff00;'></div><div style='color: #00ff00; font-size: 1.1em; font-weight: 700; letter-spacing: 1px; font-family: Consolas;'>PİYASA ENDEKSLERİ</div></div>", unsafe_allow_html=True)
                    
                    if 'e_sec_state' not in st.session_state: st.session_state['e_sec_state'] = "Seçiniz..."
                    
                    endeksler = {"Seçiniz...": None, "BİST 100": "XU100.IS", "NASDAQ": "^IXIC", "S&P 500": "^GSPC", "Bitcoin (BTC)": "BTC-USD", "Ons Altın": "GC=F"}
                    ce1, ce2 = st.columns([1.5, 1])
                    
                    def endeks_degisti(): st.session_state['e_sec_state'] = st.session_state['e_sec_widget']
                        
                    secilen_endeks = ce1.selectbox("Endeks", list(endeksler.keys()), key="e_sec_widget", label_visibility="collapsed", on_change=endeks_degisti)
                    end_per = ce2.selectbox("Zaman", ["1 Gün", "1 Hafta", "1 Ay", "3 Ay", "6 Ay", "1 Yıl", "Maks."], index=2, key="e_per", label_visibility="collapsed")
                    
                    if st.session_state['e_sec_state'] != "Seçiniz...":
                        st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-top: 10px; margin-bottom: 10px;'>", unsafe_allow_html=True)
                        c_ebaslik, c_ekapat = st.columns([3, 1])
                        c_ebaslik.markdown(f"<div style='color: gray; font-size: 0.85em; padding-top: 5px;'>Aktif Endeks: <b style='color: #00ff00;'>{st.session_state['e_sec_state']}</b></div>", unsafe_allow_html=True)
                        
                        if c_ekapat.button("✖ Kapat", key="e_kapat_btn", use_container_width=True):
                            st.session_state['e_sec_state'] = "Seçiniz..."
                            st.rerun()
                            
                        cizgi_grafik_ciz(st.session_state['e_sec_state'], endeksler[st.session_state['e_sec_state']], "ENDEKS", end_per)

            # --- BÖLÜM 2: AKTİF PORTFÖY GRAFİKLERİ ---
            st.markdown("<hr style='border-color: rgba(255,255,255,0.1); margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)
            st.markdown("##### Aktif Portföy Grafikleri")

            
            portfoy_listesi = []
            for _, r in df_p.iterrows():
                v = r['VARLIK']
                borsa = r['BORSA']
                t_kod = v
                if borsa == "BİST" and ".IS" not in t_kod: t_kod += ".IS"
                elif borsa == "KRİPTO" and "-USD" not in t_kod: t_kod += "-USD"
                elif borsa == "EMTİA" and "=F" not in t_kod: t_kod += "=F"
                portfoy_listesi.append((v, t_kod, borsa))
            
            for _, r in df_e.iterrows():
                maden = r['maden_turu']
                if "Altın" in maden: t_kod = "GC=F"
                elif "Gümüş" in maden: t_kod = "SI=F"
                elif "Platin" in maden: t_kod = "PL=F"
                elif "Paladyum" in maden: t_kod = "PA=F"
                else: continue
                if not any(item[0] == maden for item in portfoy_listesi):
                    portfoy_listesi.append((maden, t_kod, "EMTİA"))
            
            if portfoy_listesi:
                cols = st.columns(2)
                for idx, (isim, kod, borsa_turu) in enumerate(portfoy_listesi):
                    with cols[idx % 2]:
                        with st.container(border=True):
                            c_bos, c_per = st.columns([1.5, 1])
                            varlik_periyot = c_per.selectbox("Periyot", ["Bugün", "1 Hafta", "1 Ay", "3 Ay", "6 Ay", "1 Yıl", "Maks."], index=1, key=f"g_varlik_{idx}", label_visibility="collapsed")
                            cizgi_grafik_ciz(isim, kod, borsa_turu, varlik_periyot, ana_grafik=False)
            else:
                st.info("Portföyünüzde şu an aktif (lotu sıfırdan büyük) bir borsa varlığı veya emtia bulunmuyor.")
                
        with t_gosterge:
            st.markdown("##### Teknik Göstergeler ve Analiz Raporu")
            st.caption("Seçilen zaman aralığına göre aktif varlıkların grafiklerini ve sistemin ürettiği otomatik teknik analiz raporlarını inceleyin.")
            
            conn = get_db()
            try:
                df_ta = pd.read_sql_query("SELECT varlik_adi, borsa FROM portfoy WHERE kullanici_adi = %s AND borsa != 'FON (TEFAS)' GROUP BY varlik_adi, borsa HAVING SUM(lot) > 0.01", conn, params=(k_adi,))
                df_ea = pd.read_sql_query("SELECT maden_turu FROM emtia_portfoy WHERE kullanici_adi = %s GROUP BY maden_turu HAVING SUM(miktar) > 0.01", conn, params=(k_adi,))
            finally:
                release_db(conn)
            
            ta_listesi = []
            for _, r in df_ta.iterrows():
                v, borsa = r['varlik_adi'], r['borsa']
                t_kod = v
                if borsa == "BİST" and ".IS" not in t_kod: t_kod += ".IS"
                elif borsa == "KRİPTO" and "-USD" not in t_kod: t_kod += "-USD"
                elif borsa == "EMTİA" and "=F" not in t_kod: t_kod += "=F"
                ta_listesi.append((v, t_kod))
                
            for _, r in df_ea.iterrows():
                maden = r['maden_turu']
                if "Altın" in maden: ta_listesi.append((maden, "GC=F"))
                elif "Gümüş" in maden: ta_listesi.append((maden, "SI=F"))
                
            ta_listesi = list(dict.fromkeys(ta_listesi))
                
            if not ta_listesi:
                st.info("Teknik analiz yapılabilecek aktif bir borsa varlığınız bulunmuyor.")
            else:
                for varlik_grup in [ta_listesi[i:i+2] for i in range(0, len(ta_listesi), 2)]:
                    c1, c2 = st.columns(2)
                    
                    for idx, v_data in enumerate(varlik_grup):
                        varlik_adi, varlik_kod = v_data
                        current_col = c1 if idx == 0 else c2
                        b_key = f"b_{varlik_kod}_{k_adi}".replace(".", "").replace("=", "").replace("-", "").replace(" ", "")
                        
                        with current_col.container(border=True):
                            # SİHİRLİ DOKUNUŞ: Başlığı grafikten sonra, veriye göre renklendirmek için boş alan açıyoruz
                            baslik_alani = st.empty()
                            
                            c_zaman, c_g1, c_g2, c_g3, c_g4 = st.columns([1.8, 1, 1, 1, 1])
                            zaman_secim = c_zaman.selectbox("Periyot", ["1 Günlük", "1 Haftalık", "1 Aylık", "3 Aylık", "1 Yıllık", "5 Yıllık"], index=4, key=f"zaman_{b_key}", label_visibility="collapsed")
                            
                            ops_h_ort = c_g1.checkbox("H.ORT", key=f"sma_{b_key}", value=False)
                            ops_rsi = c_g2.checkbox("RSI", key=f"rsi_{b_key}", value=False)
                            ops_macd = c_g3.checkbox("MACD", key=f"macd_{b_key}", value=False)
                            ops_boll = c_g4.checkbox("BOLL", key=f"boll_{b_key}", value=False)
                            
                            periyot_ayarlari = {
                                "1 Günlük": ("5d", "5m", 1),
                                "1 Haftalık": ("1mo", "15m", 7),
                                "1 Aylık": ("2y", "1d", 30),
                                "3 Aylık": ("2y", "1d", 90),
                                "1 Yıllık": ("3y", "1d", 365),
                                "5 Yıllık": ("10y", "1wk", 1825)
                            }
                            f_per, i_val, gun_kesim = periyot_ayarlari[zaman_secim]
                            
                            with st.spinner(f"Analiz İşleniyor..."):
                                try:
                                    import numpy as np
                                    import pandas as pd
                                    from plotly.subplots import make_subplots
                                    
                                    df_grafik = yf.Ticker(varlik_kod).history(period=f_per, interval=i_val)
                                    
                                    if df_grafik.empty:
                                        st.warning(f"Bu periyot için piyasa verisi bulunamadı.")
                                        # Veri yoksa gri renkte başlık basar, yanındaki küçük yeşil kodu sildik
                                        baslik_alani.markdown(f"<div style='background: linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(0,0,0,0) 100%); border-left: 4px solid gray; padding: 10px 15px; border-radius: 4px; margin-bottom: 15px;'><span style='font-size: 1.15em; font-weight: bold; color: white;'>{varlik_adi}</span></div>", unsafe_allow_html=True)
                                    else:
                                        # DİNAMİK RENK HESAPLAMASI VE BAŞLIK ÇİZİMİ
                                        ilk_fiyat = df_grafik['Close'].iloc[0]
                                        son_fiyat_grafik = df_grafik['Close'].iloc[-1]
                                        trend_renk = "#00ff00" if son_fiyat_grafik >= ilk_fiyat else "#FF5252"
                                        bg_renk = "rgba(0,255,0,0.1)" if trend_renk == "#00ff00" else "rgba(255,82,82,0.1)"
                                        
                                        # Gereksiz küçük yeşil kod BURADAN SİLİNDİ, kutu dinamik renge boyandı
                                        baslik_alani.markdown(f"""
                                            <div style='background: linear-gradient(90deg, {bg_renk} 0%, rgba(0,0,0,0) 100%); border-left: 4px solid {trend_renk}; padding: 10px 15px; border-radius: 4px; margin-bottom: 15px;'>
                                                <span style='font-size: 1.15em; font-weight: bold; color: white;'>{varlik_adi}</span> 
                                            </div>
                                        """, unsafe_allow_html=True)

                                        # Temel Gösterge Hesaplamaları
                                        df_grafik['SMA20'] = df_grafik['Close'].rolling(window=20).mean()
                                        df_grafik['SMA50'] = df_grafik['Close'].rolling(window=50).mean()
                                        df_grafik['SMA200'] = df_grafik['Close'].rolling(window=200).mean()
                                        
                                        df_grafik['STD20'] = df_grafik['Close'].rolling(window=20).std()
                                        df_grafik['BOLL_UP'] = df_grafik['SMA20'] + (df_grafik['STD20'] * 2)
                                        df_grafik['BOLL_DOWN'] = df_grafik['SMA20'] - (df_grafik['STD20'] * 2)
                                        
                                        df_grafik['EMA12'] = df_grafik['Close'].ewm(span=12, adjust=False).mean()
                                        df_grafik['EMA26'] = df_grafik['Close'].ewm(span=26, adjust=False).mean()
                                        df_grafik['MACD'] = df_grafik['EMA12'] - df_grafik['EMA26']
                                        df_grafik['MACD_SIGNAL'] = df_grafik['MACD'].ewm(span=9, adjust=False).mean()
                                        df_grafik['MACD_HIST'] = df_grafik['MACD'] - df_grafik['MACD_SIGNAL']
                                        
                                        delta = df_grafik['Close'].diff()
                                        gain = delta.clip(lower=0).ewm(alpha=1/14, adjust=False).mean()
                                        loss = (-delta.clip(upper=0)).ewm(alpha=1/14, adjust=False).mean()
                                        rs = gain / loss
                                        df_grafik['RSI'] = 100 - (100 / (1 + rs))

                                        # Analiz Raporu İçin Güncel Değerleri Al
                                        son_fiyat = df_grafik['Close'].iloc[-1]
                                        son_sma20 = df_grafik['SMA20'].iloc[-1]
                                        son_sma50 = df_grafik['SMA50'].iloc[-1]
                                        son_sma200 = df_grafik['SMA200'].iloc[-1]
                                        son_rsi = df_grafik['RSI'].iloc[-1]
                                        son_macd = df_grafik['MACD'].iloc[-1]
                                        son_macd_signal = df_grafik['MACD_SIGNAL'].iloc[-1]
                                        son_boll_up = df_grafik['BOLL_UP'].iloc[-1]
                                        son_boll_down = df_grafik['BOLL_DOWN'].iloc[-1]

                                        analiz_metni = ""
                                        
                                        if ops_h_ort:
                                            metin = ""
                                            if son_fiyat > son_sma20 and son_fiyat > son_sma50:
                                                metin = f"Fiyat, kısa (SMA20: {son_sma20:.2f}) ve orta (SMA50: {son_sma50:.2f}) vadeli ortalamaların üzerinde seyrediyor. Mevcut periyot için <span style='color: #00ff00; font-weight: 500;'>pozitif trend</span> hakim."
                                            elif son_fiyat < son_sma20 and son_fiyat < son_sma50:
                                                metin = f"Fiyat, hareketli ortalamaların (SMA20: {son_sma20:.2f}, SMA50: {son_sma50:.2f}) altında. Sistem <span style='color: #FF5252; font-weight: 500;'>düşüş trendi</span> sinyali veriyor."
                                            else:
                                                metin = f"Fiyat ({son_fiyat:.2f}), hareketli ortalamalar arasına sıkışmış durumda. Yön arayışı devam ediyor."
                                                
                                            analiz_metni += f"""
                                            <div style='margin-bottom: 16px;'>
                                                <div style='color: #00bcd4; font-weight: 600; font-size: 0.85em; margin-bottom: 4px; letter-spacing: 0.5px;'>■ HAREKETLİ ORTALAMALAR (SMA)</div>
                                                <div style='color: #e0e0e0; font-size: 0.95em; line-height: 1.5;'>{metin}</div>
                                            </div>
                                            """

                                        if ops_rsi:
                                            metin = ""
                                            if son_rsi >= 70:
                                                metin = f"Güncel RSI değeri {son_rsi:.2f}. Varlık <span style='color: #FF5252; font-weight: 500;'>aşırı alım bölgesinde</span> bulunuyor, olası bir düzeltme/kâr satışı riski değerlendirilmelidir."
                                            elif son_rsi <= 30:
                                                metin = f"Güncel RSI değeri {son_rsi:.2f}. Varlık <span style='color: #00ff00; font-weight: 500;'>aşırı satım bölgesinde</span>. Olası bir tepki alımı veya dip oluşumu takip edilebilir."
                                            else:
                                                metin = f"Güncel RSI değeri {son_rsi:.2f} ile nötr bölgede (30-70 arası). Momentuma dair belirgin bir aşırılık gözlenmiyor."
                                                
                                            analiz_metni += f"""
                                            <div style='margin-bottom: 16px;'>
                                                <div style='color: #00bcd4; font-weight: 600; font-size: 0.85em; margin-bottom: 4px; letter-spacing: 0.5px;'>■ GÖRECİLİ GÜÇ ENDEKSİ (RSI)</div>
                                                <div style='color: #e0e0e0; font-size: 0.95em; line-height: 1.5;'>{metin}</div>
                                            </div>
                                            """

                                        if ops_macd:
                                            metin = ""
                                            if son_macd > son_macd_signal:
                                                if son_macd > 0:
                                                    metin = f"MACD çizgisi ({son_macd:.3f}), Sinyal çizgisini ({son_macd_signal:.3f}) yukarı kesmiş ve sıfırın üzerinde. <span style='color: #00ff00; font-weight: 500;'>Güçlü alım sinyali</span> teyit ediliyor."
                                                else:
                                                    metin = f"MACD çizgisi Sinyal'in üzerinde ancak henüz sıfır hattının altında. Bu bir <span style='color: #00ff00; font-weight: 500;'>toparlanma sinyali</span> olabilir."
                                            else:
                                                if son_macd < 0:
                                                    metin = f"MACD çizgisi ({son_macd:.3f}), Sinyal çizgisinin ({son_macd_signal:.3f}) altında ve negatif bölgede. <span style='color: #FF5252; font-weight: 500;'>Güçlü satış baskısı</span> devam ediyor."
                                                else:
                                                    metin = f"MACD sıfır hattının üzerinde olmasına rağmen Sinyal çizgisini aşağı kesmiş. Bu bir <span style='color: #FF5252; font-weight: 500;'>zayıflama sinyali</span> olarak yorumlanabilir."
                                                    
                                            analiz_metni += f"""
                                            <div style='margin-bottom: 16px;'>
                                                <div style='color: #bb86fc; font-weight: 600; font-size: 0.85em; margin-bottom: 4px; letter-spacing: 0.5px;'>■ MACD İNDİKATÖRÜ</div>
                                                <div style='color: #e0e0e0; font-size: 0.95em; line-height: 1.5;'>{metin}</div>
                                            </div>
                                            """

                                        if ops_boll:
                                            metin = ""
                                            bant_genisligi = ((son_boll_up - son_boll_down) / son_boll_down) * 100
                                            if son_fiyat >= son_boll_up:
                                                metin += f"Fiyat ({son_fiyat:.2f}), üst bandı ({son_boll_up:.2f}) test ediyor veya aşmış. <span style='color: #FF5252; font-weight: 500;'>Aşırı iyimserlik veya olası direnç seviyesi.</span> "
                                            elif son_fiyat <= son_boll_down:
                                                metin += f"Fiyat ({son_fiyat:.2f}), alt banda ({son_boll_down:.2f}) değmiş veya altına inmiş. <span style='color: #00ff00; font-weight: 500;'>Aşırı karamsarlık veya olası destek seviyesi.</span> "
                                            else:
                                                metin += f"Fiyat bant sınırları içerisinde seyrediyor. "
                                            
                                            if bant_genisligi < 5: 
                                                metin += f"Bantlar oldukça daralmış durumda (%{bant_genisligi:.1f}). Yakın vadede <span style='color: #ffffff; font-weight: 500;'>sert bir yön kırılımı (volatilite artışı)</span> beklenebilir."
                                                
                                            analiz_metni += f"""
                                            <div style='margin-bottom: 16px;'>
                                                <div style='color: #ffb300; font-weight: 600; font-size: 0.85em; margin-bottom: 4px; letter-spacing: 0.5px;'>■ BOLLINGER BANTLARI</div>
                                                <div style='color: #e0e0e0; font-size: 0.95em; line-height: 1.5;'>{metin}</div>
                                            </div>
                                            """

                                        # --- MAKASLAMA İŞLEMİ ---
                                        if zaman_secim == "1 Günlük":
                                            son_gun = df_grafik.index[-1].date()
                                            df_grafik = df_grafik[df_grafik.index.date == son_gun]
                                        else:
                                            sinir_tarih = df_grafik.index[-1] - pd.Timedelta(days=gun_kesim)
                                            df_grafik = df_grafik[df_grafik.index >= sinir_tarih]
                                        
                                        if i_val in ['5m', '15m']: df_grafik['Tarih_Str'] = df_grafik.index.strftime('%d %b %H:%M')
                                        else: df_grafik['Tarih_Str'] = df_grafik.index.strftime('%Y-%m-%d')
                                        
                                        ops_toplami = sum([ops_rsi, ops_macd])
                                        toplam_satir = 1 + ops_toplami
                                        row_heights = [0.6] + [0.2 for _ in range(ops_toplami)]
                                        
                                        fig = make_subplots(rows=toplam_satir, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=row_heights)
                                        
                                        # ÇİZGİ RENGİ BURADA BELİRLENİYOR (Zaten yukarıda hesapladık)
                                        fig.add_trace(go.Scatter(x=df_grafik['Tarih_Str'], y=df_grafik['Close'], mode='lines', line=dict(color=trend_renk, width=2.5), name='Fiyat'), row=1, col=1)
                                        
                                        if ops_h_ort:
                                            fig.add_trace(go.Scatter(x=df_grafik['Tarih_Str'], y=df_grafik['SMA20'], line=dict(color='#00bcd4', width=1.5), name='SMA 20'), row=1, col=1)
                                            fig.add_trace(go.Scatter(x=df_grafik['Tarih_Str'], y=df_grafik['SMA50'], line=dict(color='#ffb300', width=1.5), name='SMA 50'), row=1, col=1)
                                            fig.add_trace(go.Scatter(x=df_grafik['Tarih_Str'], y=df_grafik['SMA200'], line=dict(color='#ffffff', width=1.5), name='SMA 200'), row=1, col=1)
                                        
                                        if ops_boll:
                                            fig.add_trace(go.Scatter(x=df_grafik['Tarih_Str'], y=df_grafik['BOLL_UP'], line=dict(color='rgba(255, 255, 255, 0.3)', width=1, dash='dash'), name='BOLL Üst'), row=1, col=1)
                                            fig.add_trace(go.Scatter(x=df_grafik['Tarih_Str'], y=df_grafik['BOLL_DOWN'], line=dict(color='rgba(255, 255, 255, 0.3)', width=1, dash='dash'), name='BOLL Alt', fill='tonexty', fillcolor='rgba(255, 255, 255, 0.05)'), row=1, col=1)

                                        g_satir = 2
                                        if ops_rsi:
                                            fig.add_trace(go.Scatter(x=df_grafik['Tarih_Str'], y=df_grafik['RSI'], line=dict(color='#00bcd4', width=1.5), name='RSI'), row=g_satir, col=1)
                                            fig.add_hline(y=70, line_dash="dot", line_color="rgba(255, 82, 82, 0.5)", row=g_satir, col=1)
                                            fig.add_hline(y=30, line_dash="dot", line_color="rgba(0, 255, 0, 0.5)", row=g_satir, col=1)
                                            g_satir += 1

                                        if ops_macd:
                                            fig.add_trace(go.Scatter(x=df_grafik['Tarih_Str'], y=df_grafik['MACD'], line=dict(color='#bb86fc', width=1.5), name='MACD'), row=g_satir, col=1)
                                            fig.add_trace(go.Scatter(x=df_grafik['Tarih_Str'], y=df_grafik['MACD_SIGNAL'], line=dict(color='#ffb300', width=1), name='Sinyal'), row=g_satir, col=1)
                                            hist_colors = ['#00ff00' if val >= 0 else '#FF5252' for val in df_grafik['MACD_HIST']]
                                            fig.add_trace(go.Bar(x=df_grafik['Tarih_Str'], y=df_grafik['MACD_HIST'], marker_color=hist_colors, name='Hist'), row=g_satir, col=1)

                                        fig.update_layout(
                                            height=550 if toplam_satir > 1 else 320, 
                                            margin=dict(t=30, b=5, l=0, r=0),
                                            paper_bgcolor="rgba(0,0,0,0)", 
                                            plot_bgcolor="rgba(0,0,0,0)",
                                            font=dict(family="system-ui, -apple-system, sans-serif", color="gray", size=10),
                                            showlegend=True, 
                                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                                            xaxis=dict(rangeslider=dict(visible=False))
                                        )
                                        
                                        fig.update_xaxes(showgrid=True, gridcolor='rgba(255, 255, 255, 0.05)', type='category', nticks=5, showline=False)
                                        fig.update_yaxes(showgrid=True, gridcolor='rgba(255, 255, 255, 0.05)', showline=False)
                                        
                                        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                                        # Analiz Metnini Ekrana Bas
                                        if analiz_metni:
                                            st.markdown(f"""
                                            <div style='border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 20px; background: rgba(18,18,18,0.95); margin-top: 15px; font-family: system-ui, -apple-system, sans-serif;'>
                                                <div style='display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(0,255,0,0.2); padding-bottom: 10px; margin-bottom: 15px;'>
                                                    <span style='color: #00ff00; font-weight: 700; font-size: 1.05em; letter-spacing: 0.5px;'>SİSTEM ANALİZ RAPORU</span>
                                                    <span style='color: #888888; font-size: 0.85em;'>Periyot: {zaman_secim}</span>
                                                </div>
                                                {analiz_metni}
                                            </div>
                                            """, unsafe_allow_html=True)

                                except Exception as e:
                                    st.error(f"Sistem Hatası: Grafik çizilirken veya analiz edilirken bir sorun oluştu. {e}")
        with t_haber:
            st.markdown("##### KAP ve Şirket Haberleri")
            st.caption("Resmi KAP bildirimleri doğrudan Kamuyu Aydınlatma Platformu'ndan, piyasa haberleri ise Yahoo Finance altyapısından çekilmektedir.")

            conn = get_db()
            try:
                df_h = pd.read_sql_query("SELECT varlik_adi, borsa FROM portfoy WHERE kullanici_adi = %s AND borsa != 'FON (TEFAS)' GROUP BY varlik_adi, borsa HAVING SUM(lot) > 0.01", conn, params=(k_adi,))
            finally: 
                release_db(conn)

            if df_h.empty:
                st.info("Haber akışını görmek için portföyünüzde aktif hisse senedi veya kripto bulunmalıdır.")
            else:
                kap_haberleri = []
                piyasa_haberleri = []

                with st.spinner("Resmi KAP veritabanı ve piyasa bülteni taranıyor..."):
                    import requests
                    import math

                    # --- 1. DOĞRUDAN KAP VERİTABANI SORGUSU ---
                    bist_varliklar = df_h[df_h['borsa'] == 'BİST']['varlik_adi'].tolist()
                    if bist_varliklar:
                        temiz_kodlar = [k.replace('.IS', '') for k in bist_varliklar]
                        try:
                            # KAP API'sine doğrudan son 15 günün sorgusunu atıyoruz
                            kap_url = "https://www.kap.org.tr/tr/api/memberDisclosureQuery"
                            bugun_tarih = datetime.datetime.now()
                            gecmis_tarih = bugun_tarih - datetime.timedelta(days=15)
                            payload = {
                                "fromDate": gecmis_tarih.strftime("%Y-%m-%d"),
                                "toDate": bugun_tarih.strftime("%Y-%m-%d"),
                                "stockList": temiz_kodlar
                            }
                            headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                            
                            r = requests.post(kap_url, json=payload, headers=headers, timeout=10)
                            
                            if r.status_code == 200:
                                kap_data = r.json()
                                for d in kap_data:
                                    b_id = d.get('disclosureIndex', '')
                                    b_baslik = d.get('title', 'Başlıksız Bildirim')
                                    b_sirket = d.get('companyName', '')
                                    b_kod = d.get('stockCodes', '')
                                    tarih_str = d.get('publishDate', '')
                                    
                                    # Tarih formatı genelde "19.03.2026 14:30" şeklindedir
                                    try:
                                        tarih_dt = pd.to_datetime(tarih_str, format="%d.%m.%Y %H:%M")
                                        zaman_ts = tarih_dt.timestamp()
                                        zaman_st = tarih_dt.strftime('%d.%m.%Y %H:%M')
                                    except:
                                        zaman_ts = 0
                                        zaman_st = tarih_str
                                        
                                    # Hangi varlığa ait olduğunu bul
                                    ilgili_varlik = next((k for k in temiz_kodlar if k in b_kod), "BİST")
                                    
                                    kap_haberleri.append({
                                        'varlik': ilgili_varlik,
                                        'baslik': b_baslik,
                                        'kaynak': 'KAP (Resmi Bildirim)',
                                        'link': f"https://www.kap.org.tr/tr/Bildirim/{b_id}",
                                        'zaman_str': zaman_st,
                                        'zaman_sort': zaman_ts,
                                        'renk': '#00ff00' # Senin neon yeşil
                                    })
                        except Exception:
                            pass # KAP POST başarısız olursa sistem çökmesin diye sessizce atla

                    # --- 2. TEK VE GÜVENİLİR KAYNAK: YAHOO FINANCE (PİYASA HABERLERİ) ---
                    for _, r in df_h.iterrows():
                        v, borsa = r['varlik_adi'], r['borsa']
                        t_kod = v
                        if borsa == "BİST" and ".IS" not in t_kod: t_kod += ".IS"
                        elif borsa == "KRİPTO" and "-USD" not in t_kod: t_kod += "-USD"
                        elif borsa == "EMTİA" and "=F" not in t_kod: t_kod += "=F"
                        
                        try:
                            haberler = yf.Ticker(t_kod).news
                            if haberler:
                                for h in haberler[:8]: # Varlık başı 8 haber
                                    title = h.get('title', 'Başlıksız Haber')
                                    link = h.get('link', '#')
                                    source = h.get('publisher', 'Yahoo Finance')
                                    zaman_ts = h.get('providerPublishTime', 0)
                                    
                                    zaman_st = datetime.datetime.fromtimestamp(zaman_ts).strftime('%d.%m.%Y %H:%M') if zaman_ts else "Tarih Yok"
                                    
                                    piyasa_haberleri.append({
                                        'varlik': v.replace('.IS', ''),
                                        'baslik': title,
                                        'kaynak': source,
                                        'link': link,
                                        'zaman_str': zaman_st,
                                        'zaman_sort': zaman_ts,
                                        'renk': '#00ff00' # Senin neon yeşil
                                    })
                        except: pass

                # Tarihe göre en yeniden eskiye sıralama
                kap_haberleri = sorted(kap_haberleri, key=lambda x: x['zaman_sort'], reverse=True)
                piyasa_haberleri = sorted(piyasa_haberleri, key=lambda x: x['zaman_sort'], reverse=True)

                # --- ARAYÜZ VE KATEGORİ SEÇİMİ ---
                kategori = st.radio("Kategori Seçimi", ["Resmi KAP Bildirimleri", "Piyasa Haberleri"], horizontal=True, label_visibility="collapsed")
                st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

                aktif_liste = kap_haberleri if kategori == "Resmi KAP Bildirimleri" else piyasa_haberleri
                state_key = "sayfa_kap" if kategori == "Resmi KAP Bildirimleri" else "sayfa_piyasa"

                if not aktif_liste:
                    st.warning(f"Bu kategori için sistemde güncel veri bulunamadı.")
                else:
                    sayfa_basina = 5
                    toplam_sayfa = math.ceil(len(aktif_liste) / sayfa_basina)

                    if state_key not in st.session_state:
                        st.session_state[state_key] = 1

                    if st.session_state[state_key] > toplam_sayfa:
                        st.session_state[state_key] = toplam_sayfa
                    if st.session_state[state_key] < 1:
                        st.session_state[state_key] = 1

                    baslangic_idx = (st.session_state[state_key] - 1) * sayfa_basina
                    bitis_idx = baslangic_idx + sayfa_basina
                    gosterilecek_haberler = aktif_liste[baslangic_idx:bitis_idx]

                    for h in gosterilecek_haberler:
                        kart_html = f"""
                        <div style='border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid {h['renk']}; border-radius: 8px; padding: 15px; background: rgba(10,10,10,0.6); margin-bottom: 12px; transition: transform 0.2s ease; box-shadow: 0 4px 6px rgba(0,0,0,0.2);'>
                            <div style='display: flex; justify-content: space-between; margin-bottom: 8px; align-items: center;'>
                                <div style='background: rgba(0, 255, 0, 0.05); padding: 4px 10px; border-radius: 4px; border: 1px solid rgba(0, 255, 0, 0.2);'>
                                    <span style='color: {h['renk']}; font-weight: bold; font-family: Consolas; font-size: 0.9em;'>{h['varlik']}</span>
                                </div>
                                <span style='color: gray; font-size: 0.85em; font-family: Consolas;'>{h['zaman_str']}</span>
                            </div>
                            <div style='font-size: 1.1em; color: white; font-weight: 500; margin-bottom: 12px; line-height: 1.4; font-family: system-ui, -apple-system, sans-serif;'>{h['baslik']}</div>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <span style='color: gray; font-size: 0.85em;'>Kaynak: <span style='color:{h['renk']}; font-weight: bold;'>{h['kaynak']}</span></span>
                                <a href='{h['link']}' target='_blank' style='text-decoration: none; color: black; background: {h['renk']}; padding: 5px 12px; border-radius: 4px; font-size: 0.85em; font-weight: bold; transition: all 0.3s ease;'>{'Bildirime Git' if kategori == 'Resmi KAP Bildirimleri' else 'Habere Git'}</a>
                            </div>
                        </div>
                        """
                        st.markdown(kart_html, unsafe_allow_html=True)

                    # SAYFALAMA KONTROL PANELİ
                    st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin-top: 15px; margin-bottom: 15px;'>", unsafe_allow_html=True)
                    c_bos1, c_prev, c_page, c_next, c_bos2 = st.columns([2, 1.5, 2, 1.5, 2])
                    
                    with c_prev:
                        if st.button("Önceki Sayfa", key=f"prev_{state_key}", use_container_width=True, disabled=(st.session_state[state_key] <= 1)):
                            st.session_state[state_key] -= 1
                            st.rerun()
                            
                    with c_page:
                        st.markdown(f"""
                        <div style='text-align: center; padding: 6px; border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; background: rgba(20,20,20,0.5);'>
                            <span style='color: gray; font-family: Consolas; font-size: 0.9em;'>SAYFA</span> 
                            <span style='color: #00ff00; font-weight: bold; font-family: Consolas; font-size: 1.1em;'>{st.session_state[state_key]}</span> 
                            <span style='color: gray; font-family: Consolas; font-size: 0.9em;'>/ {toplam_sayfa}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with c_next:
                        if st.button("Sonraki Sayfa", key=f"next_{state_key}", use_container_width=True, disabled=(st.session_state[state_key] >= toplam_sayfa)):
                            st.session_state[state_key] += 1
                            st.rerun() 
        with t_makro:
            st.info("Türkiye ve Dünya ekonomisi sıcak gelişme akışı, jeopolitik risk haritası bağlanıyor... (Kervan yolda düzülüyor)")
            # --- GİZLİ YÖNETİCİ PANELİ ---
    elif secilen_sayfa == "Yönetici Paneli" and k_adi in ADMIN_KULLANICILAR:
        st.title("Sistem Yönetim ve Güvenlik Terminali")
        st.markdown("<div style='background: rgba(255, 82, 82, 0.05); padding: 10px 15px; border-radius: 6px; border: 1px solid rgba(255, 82, 82, 0.2); margin-bottom: 20px; font-size: 0.85em; color: #e0e0e0;'>Bu alan sadece yöneticilere özeldir. Sistemdeki davetiye kodlarını ve kullanıcıları buradan yönetebilirsiniz.</div>", unsafe_allow_html=True)
        
        t_davet, t_kullanici = st.tabs(["Davetiye Yönetimi", "Kayıtlı Kullanıcılar"])
        
        with t_davet:
            with st.container(border=True):
                st.markdown("<span style='color: #00ff00; font-weight: bold;'>Yeni Davetiye Kodu Üret (Max 2 Kişilik)</span>", unsafe_allow_html=True)
                import random
                import string
                
                c1, c2 = st.columns([3, 1])
                yeni_kod = c1.text_input("Özel bir kod belirle (Boş bırakırsan sistem rastgele üretir)", placeholder="Örn: KANKALAR2026")
                if c2.button("Kod Üret / Sisteme Ekle", type="primary", use_container_width=True):
                    # Eğer boş bıraktıysan rastgele 6 haneli siber bir kod üretir
                    if not yeni_kod:
                        yeni_kod = "MRGN-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    
                    conn = get_db()
                    try:
                        c = conn.cursor()
                        # Her üretilen koda 2 kullanım hakkı tanımlanır
                        c.execute("INSERT INTO davetiyeler (kod, kullanim_hakki) VALUES (%s, 2)", (yeni_kod.upper(),))
                        conn.commit()
                        st.success(f"Yeni Davetiye Kodu Oluşturuldu: {yeni_kod.upper()} (Kullanım Hakkı: 2)")
                        time.sleep(1)
                        st.rerun()
                    except IntegrityError:
                        st.error("Bu davetiye kodu zaten kullanımda, başka bir isim seçin!")
                    finally:
                        release_db(conn)
            
            st.markdown("##### Aktif Davetiye Kodları")
            conn = get_db()
            try:
                # Tablo yoksa anında oluşturması için güvenlik kilidi:
                c = conn.cursor()
                c.execute("CREATE TABLE IF NOT EXISTS davetiyeler (kod TEXT PRIMARY KEY, kullanim_hakki INTEGER DEFAULT 2)")
                c.execute("INSERT INTO davetiyeler (kod, kullanim_hakki) VALUES ('MERGEN_VIP_2026', 999) ON CONFLICT DO NOTHING")
                conn.commit()
                
                # Kodları veritabanından çek (Kullanım hakkı çok olan en üstte çıksın)
                c.execute("SELECT kod, kullanim_hakki FROM davetiyeler ORDER BY kullanim_hakki DESC")
                davetiyeler = c.fetchall()

                if davetiyeler:
                    # Kullanıcı kartları gibi 3 sütunlu şık grid yapısı
                    cols = st.columns(3)
                    for i, (d_kod, d_hak) in enumerate(davetiyeler):
                        with cols[i % 3]:
                            renk = "#00ff00" if d_hak > 0 else "#FF5252"
                            durum_yazi = "Aktif" if d_hak > 0 else "Tükendi"
                            
                            kart_html = f"""
                            <div style='background: rgba(15,15,15,0.8); border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid {renk}; border-radius: 8px; padding: 15px; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3);'>
                                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;'>
                                    <span style='color: gray; font-size: 0.75em; letter-spacing: 1px;'>KOD</span>
                                    <span style='color: {renk}; font-size: 0.75em; border: 1px solid {renk}; padding: 2px 6px; border-radius: 4px;'>{durum_yazi}</span>
                                </div>
                                <div style='color: white; font-size: 1.3em; font-family: Consolas; font-weight: bold; margin-bottom: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{d_kod}</div>
                                <div style='display: flex; justify-content: space-between; align-items: center;'>
                                    <span style='color: gray; font-size: 0.8em;'>Kalan Hak:</span>
                                    <span style='color: white; font-size: 1.2em; font-weight: bold;'>{d_hak}</span>
                                </div>
                            </div>
                            """
                            st.markdown(kart_html, unsafe_allow_html=True)
                            
                            # Silme Butonu (MERGEN_VIP_2026 anahtar koddur, silinemez)
                            if d_kod != 'MERGEN_VIP_2026':
                                if st.button("🗑️ Kodu Sil", key=f"del_davet_{d_kod}", use_container_width=True):
                                    c.execute("DELETE FROM davetiyeler WHERE kod = %s", (d_kod,))
                                    conn.commit()
                                    st.rerun()
                            else:
                                st.button("🔒 Ana Kod (Silinemez)", key="del_vip_disabled", disabled=True, use_container_width=True)
                else:
                    st.info("Sistemde aktif davetiye kodu bulunmuyor.")
            finally:
                release_db(conn)
                
        with t_kullanici:
            st.markdown("##### Sisteme Kayıtlı Kullanıcılar")
            conn = get_db()
            try:
                c = conn.cursor()
                # Hem kullanıcı adını, hem ismini hem de profil fotoğrafını çekiyoruz
                c.execute("SELECT kullanici_adi, isim_soyisim, profil_fotosu FROM kullanicilar")
                kullanicilar = c.fetchall()
                
                if kullanicilar:
                    # Kullanıcıları 3 sütunlu şık bir grid (ızgara) yapısında diziyoruz
                    cols = st.columns(3)
                    for i, (k_kod, k_isim, k_foto) in enumerate(kullanicilar):
                        with cols[i % 3]:
                            # Fotoğraf varsa onu, yoksa baş harfini neon çerçeveye alıyoruz
                            bas_harf = k_isim[0].upper() if k_isim else k_kod[0].upper()
                            
                            if k_foto:
                                img_html = f"<img src='data:image/png;base64,{k_foto}' style='width: 70px; height: 70px; border-radius: 50%; object-fit: cover; border: 2px solid #00ff00; padding: 3px; background: rgba(0,255,0,0.05);'>"
                            else:
                                img_html = f"<div style='width: 70px; height: 70px; border-radius: 50%; border: 2px solid #00ff00; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: bold; color: #00ff00; background: rgba(0,255,0,0.05); font-family: Consolas;'>{bas_harf}</div>"
                            
                            isim_goster = k_isim if k_isim else "İsimsiz Kullanıcı"
                            
                            # Siber tasarımlı Kullanıcı Kartı HTML'i
                            kart_html = f"""
                            <div style='background: rgba(15,15,15,0.8); border: 1px solid rgba(0,255,0,0.2); border-radius: 12px; padding: 20px 10px; text-align: center; margin-bottom: 15px; box-shadow: 0 6px 12px rgba(0,0,0,0.4); border-bottom: 3px solid #00ff00;'>
                                <div style='display: flex; justify-content: center; margin-bottom: 12px;'>
                                    {img_html}
                                </div>
                                <div style='color: white; font-weight: bold; font-size: 1.15em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{isim_goster}</div>
                                <div style='color: #888; font-size: 0.85em; font-family: Consolas; margin-top: 5px; background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 4px; display: inline-block;'>@{k_kod}</div>
                            </div>
                            """
                            st.markdown(kart_html, unsafe_allow_html=True)
                else:
                    st.info("Sistemde henüz kayıtlı kullanıcı yok.")
            finally:
                release_db(conn)
