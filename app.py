import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Radar P2P Inteligente", layout="wide", page_icon="📈")

# --- FUNCIONES DE DATOS ---
def fetch_p2p_data(asset, fiat, trade_type, trans_amount=0):
    """Obtiene datos directamente del endpoint interno de Binance P2P"""
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {
        "asset": asset,
        "fiat": fiat,
        "merchantCheck": False,
        "page": 1,
        "payTypes": [],
        "publisherType": None,
        "rows": 20,
        "tradeType": trade_type,
        "transAmount": trans_amount
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        if data['success']:
            return data['data']
        return []
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return []

def process_ads(ads):
    """Limpia y estructura los anuncios"""
    processed = []
    for ad in ads:
        adv = ad['adv']
        advertiser = ad['advertiser']
        processed.append({
            "User": advertiser['nickName'],
            "Price": float(adv['price']),
            "Available": float(adv['surplusAmount']),
            "Min_Order": float(adv['minSingleTransAmount']),
            "Rating": float(advertiser['monthFinishRate']) * 100,
            "Orders": advertiser['monthOrderCount'],
            "Methods": [p['identifier'] for p in adv['tradeMethods']]
        })
    return pd.DataFrame(processed)

# --- INTERFAZ SIDEBAR ---
st.sidebar.header("⚙️ Configuración del Radar")
capital_usd = st.sidebar.selectbox("Capital de Simulación (USD)", [500, 1000, 5000, 10000], index=1)
fee_percent = st.sidebar.slider("Comisión Operativa (%)", 0.0, 5.0, 1.5)
update_btn = st.sidebar.button("🔄 Actualizar Mercado")

# --- LÓGICA PRINCIPAL ---
st.title("🛡️ Radar P2P: Arbitraje BR-VE")
st.caption(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")

col1, col2 = st.columns(2)

# Obtención de datos
with st.spinner('Escaneando Binance P2P...'):
    df_brl = process_ads(fetch_p2p_data("USDT", "BRL", "BUY"))
    df_ves = process_ads(fetch_p2p_data("USDT", "VES", "SELL"))

if not df_brl.empty and not df_ves.empty:
    price_brl = df_brl['Price'].iloc[0]
    price_ves = df_ves['Price'].iloc[0]
    
    # Métricas principales
    with col1:
        st.metric("USDT / BRL (Compra)", f"R$ {price_brl:,.2f}")
    with col2:
        st.metric("USDT / VES (Venta)", f"Bs {price_ves:,.2f}")

    # --- CÁLCULO DE ARBITRAJE ---
    # Simulando que el usuario tiene USD y compra en BRL para vender en VES (o viceversa)
    # Aquí puedes ajustar la lógica según tu flujo real de cuentas.
    st.divider()
    st.subheader("📊 Análisis de Oportunidades")
    
    # Ejemplo: Spread bruto entre mercados
    # Nota: Requiere una tasa de cambio BRL/VES actualizada para mayor precisión
    st.info("El sistema detecta los mejores anuncios actuales para tu capital seleccionado.")

    # --- DETECCIÓN DE BALLENAS ---
    st.subheader("🐋 Detección de Ballenas (> 5,000 USDT)")
    all_ads = pd.concat([df_brl.assign(Market='BRL'), df_ves.assign(Market='VES')])
    whales = all_ads[all_ads['Available'] >= 5000]
    
    if not whales.empty:
        st.warning(f"Se detectaron {len(whales)} ballenas operando ahora.")
        st.dataframe(whales[['Market', 'User', 'Price', 'Available', 'Rating']])
    else:
        st.success("Mercado distribuido: No hay ballenas grandes bloqueando liquidez.")

    # --- TABLAS DE MERCADO ---
    tab1, tab2 = st.tabs(["🇧🇷 Mercado Brasil (BRL)", "🇻🇪 Mercado Venezuela (VES)"])
    
    with tab1:
        st.dataframe(df_brl.style.highlight_max(axis=0, subset=['Rating']))
        
    with tab2:
        st.dataframe(df_ves.style.highlight_max(axis=0, subset=['Rating']))

else:
    st.error("No se pudieron obtener datos. Binance podría estar limitando las peticiones temporales.")

st.divider()
st.caption("Aviso: Esta herramienta es informativa. El trading P2P conlleva riesgos de contraparte.")
