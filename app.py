import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time
import random

# Configuración profesional de la página
st.set_page_config(page_title="Radar P2P: Arbitraje BR-VE", layout="wide", page_icon="🕵️‍♂️")

# --- MOTOR DE DATOS CON CAMUFLAJE ---
def fetch_p2p_data(asset, fiat, trade_type, trans_amount=0):
    """Simula una petición desde un navegador Chrome en Mac"""
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    
    # Lista de User-Agents para variar y no parecer un bot fijo
    user_agents = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    ]
    
    headers = {
        "Accept": "*/*",
        "Accept-Language": "es-ES,es;q=0.9",
        "Content-Type": "application/json",
        "Origin": "https://p2p.binance.com",
        "Referer": f"https://p2p.binance.com/es/trade/sell/{asset}?fiat={fiat}",
        "User-Agent": random.choice(user_agents),
        "clienttype": "web"
    }
    
    payload = {
        "asset": asset,
        "fiat": fiat,
        "merchantCheck": False,
        "page": 1,
        "payTypes": [],
        "publisherType": None,
        "rows": 10,
        "tradeType": trade_type,
        "transAmount": trans_amount
    }
    
    try:
        # Retraso humano aleatorio
        time.sleep(random.uniform(0.5, 1.2))
        response = requests.post(url, json=payload, headers=headers, timeout=12)
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        return []
    except:
        return []

def process_ads(ads):
    if not ads: return pd.DataFrame()
    processed = []
    for ad in ads:
        adv = ad['adv']
        advertiser = ad['advertiser']
        processed.append({
            "Comerciante": advertiser['nickName'],
            "Precio": float(adv['price']),
            "Disponible": float(adv['surplusAmount']),
            "Confianza": f"{float(advertiser['monthFinishRate']) * 100:.1f}%",
            "Órdenes": advertiser['monthOrderCount'],
            "Pagos": [p['identifier'] for p in adv['tradeMethods']]
        })
    return pd.DataFrame(processed)

# --- INTERFAZ DEL RADAR ---
st.title("🛡️ Radar P2P: Inteligencia de Arbitraje")
st.write(f"**Estado del Mercado:** Actualizado a las {datetime.now().strftime('%H:%M:%S')}")

# Panel lateral
st.sidebar.header("⚙️ Ajustes")
capital = st.sidebar.number_input("Capital de trabajo (USD)", value=1000)
comision = st.sidebar.slider("Comisión bancaria/envío (%)", 0.0, 5.0, 1.5)
if st.sidebar.button("🔄 Refrescar Datos"):
    st.rerun()

col1, col2 = st.columns(2)

with st.spinner('Consultando Binance P2P...'):
    # Brasil: Queremos COMPRAR USDT con BRL
    df_brl = process_ads(fetch_p2p_data("USDT", "BRL", "BUY", capital))
    # Venezuela: Queremos VENDER USDT por VES
    df_ves = process_ads(fetch_p2p_data("USDT", "VES", "SELL", capital))

if not df_brl.empty and not df_ves.empty:
    p_brl = df_brl['Precio'].iloc[0]
    p_ves = df_ves['Precio'].iloc[0]
    
    with col1:
        st.success("🇧🇷 Mercado Brasil (BRL)")
        st.metric("Precio Compra", f"R$ {p_brl:,.2f}")
    with col2:
        st.warning("🇻🇪 Mercado Venezuela (VES)")
        st.metric("Precio Venta", f"Bs {p_ves:,.2f}")

    # Análisis de ganancia
    st.divider()
    spread_bruto = ((p_ves / p_brl) - 1) * 100 # Nota: aproximación
    st.subheader(f"📈 Análisis de oportunidad")
    st.write(f"El spread detectado entre puntas es de aproximadamente **{spread_bruto:.2f}%**.")
    
    tab1, tab2 = st.tabs(["📋 Anuncios en Brasil", "📋 Anuncios en Venezuela"])
    with tab1: st.table(df_brl.head(5))
    with t2: st.table(df_ves.head(5))

else:
    st.error("⚠️ Binance bloqueó la conexión automática.")
    st.info("💡 **Qué hacer:** Espera 1 minuto y recarga la página. Los servidores de Streamlit a veces son detectados como bots.")

st.divider()
st.caption("Uso informativo. Los precios pueden variar según el método de pago.")
