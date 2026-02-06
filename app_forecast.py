import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="Forecasting Strategico Pro", layout="wide")

# STILE CSS PROFESSIONALE
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e6e6e6; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    div[data-testid="stExpander"] { background-color: #ffffff; border-radius: 10px; border: 1px solid #e1e4e8; }
    h1, h2, h3 { color: #2c3e50; }
    div[data-testid="stMarkdownContainer"] p { font-size: 0.95rem; }
    div.stButton > button { width: 100%; border-radius: 5px; }
    
    /* Stile personalizzato per Tab AI */
    .ai-box { padding: 20px; border-radius: 10px; margin-bottom: 20px; border: 1px solid #e0e0e0; }
    .ai-score-high { background-color: #f0fff4; border-left: 5px solid #48bb78; }
    .ai-score-med { background-color: #fffaf0; border-left: 5px solid #ed8936; }
    .ai-score-low { background-color: #fff5f5; border-left: 5px solid #f56565; }
    .ai-title { font-weight: bold; font-size: 1.1em; margin-bottom: 10px; display: flex; justify-content: space-between; }
    .ai-tag { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; font-weight: bold; margin-right: 5px; background-color: #e2e8f0; color: #4a5568; }
    .tag-blue { background-color: #ebf8ff; color: #2b6cb0; }
    .tag-retention { background-color: #f0fdf4; color: #15803d; }
    </style>
    """, unsafe_allow_html=True)

# --- INIZIALIZZAZIONE SESSION STATE ---
if 'trend_val' not in st.session_state: st.session_state.trend_val = 0.0
if 'google_scale' not in st.session_state: st.session_state.google_scale = 1.0
if 'meta_scale' not in st.session_state: st.session_state.meta_scale = 1.0
if 'sat_val' not in st.session_state: st.session_state.sat_val = 0.85
if 'last_uploaded_file' not in st.session_state: st.session_state.last_uploaded_file = None

# --- FUNZIONI DI UTILITÀ ---

def clean_currency_us(column):
    if column is None: return 0
    s = column.astype(str)
    s = s.str.replace('€', '', regex=False).str.strip()
    s = s.str.replace(',', '', regex=False) 
    return pd.to_numeric(s, errors='coerce').fillna(0)

def parse_iso_week(week_str):
    try:
        week_str = str(week_str).strip()
        if len(week_str) < 6: return pd.NaT
        year = int(week_str[:4])
        week = int(week_str[4:])
        return datetime.fromisocalendar(year, week, 1) 
    except:
        return pd.NaT

def get_week_range_label_with_year(date):
    if pd.isna(date): return ""
    start = date
    end = date + timedelta(days=6)
    return f"{start.strftime('%d %b')} - {end.strftime('%d %b %Y')}"

def clean_percentage(val):
    if pd.isna(val): return 0.0
    s = str(val).replace('%', '').strip()
    try: return float(s)
    except: return 0.0

# --- HEADER ---
st.title("📈 Simulatore Business & Forecasting")

with st.expander("ℹ️ Guida Rapida: Cosa fa questo strumento?"):
    st.markdown("""
    Questo strumento è un **CFO Virtuale e Simulatore Strategico** progettato per e-commerce. Non si limita a visualizzare i dati passati, ma ti aiuta a pianificare il futuro economico.
    
    **A cosa serve:**
    1.  **💰 Controllo Profittabilità (Business Economics):** Inserendo i tuoi margini nella colonna di sinistra, il tool calcola il *Break-Even ROAS* (il punto di pareggio) e ti dice se stai realmente guadagnando o se stai solo "muovendo soldi".
    2.  **🔮 Forecasting (Previsione):** Ti permette di simulare scenari futuri ("Cosa succede se raddoppio il budget su Meta?"). Usa i dati storici e la stagionalità per proiettare fatturato e costi.
    3.  **⚖️ Analisi Efficienza (Saturazione):** Ti aiuta a capire se aumentando la spesa pubblicitaria il fatturato cresce di pari passo (alta elasticità) o se stai saturando il pubblico (bassa efficienza).
    4.  **🧠 Intelligence Automatica (AI):** Un algoritmo analizza la qualità del business (Retention, Sconti, Canali) e ti dà un punteggio di salute mensile.
    """)

# --- SIDEBAR: BUSINESS ECONOMICS ---
st.sidebar.header("⚙️ Business Economics")
with st.sidebar.expander("1. Input Metriche", expanded=True):
    # INPUT UTENTE
    be_aov = st.number_input(
        "Average Order Value (€)", 
        value=122.0, step=1.0,
        help="Il valore medio del carrello (Lordo). Corrisponde al prezzo pagato dal cliente alla cassa."
    )
    
    be_vat = st.number_input(
        "Tax/VAT (%)", 
        value=22.0, step=1.0,
        help="Aliquota IVA media. Il calcolo scorpora l'IVA dal fatturato lordo. (Es. 22% in Italia)."
    )
    
    be_returns = st.number_input(
        "Return Rate (%)", 
        value=13.0, step=0.5,
        help="Percentuale di fatturato persa a causa dei resi. Questi soldi vengono sottratti prima di calcolare i margini."
    )
    
    be_margin_prod = st.number_input(
        "Gross Margin (%)", 
        value=30.0, step=5.0,
        help="Margine lordo sul prodotto dopo il costo del venduto (COGS). Esempio: Vendi a 100€, ti costa 70€ produrlo -> Margine 30%."
    )
    
    be_fulfillment = st.number_input(
        "Fulfillment Cost (€)", 
        value=5.0, step=0.5,
        help="Costo fisso per ordine per logistica, imballaggio e spedizione (Pick & Pack + Shipping)."
    )
    
    st.markdown("**Metriche Retention**")
    be_returning_perc = st.number_input(
        "Returning Customers (%)", 
        value=13.0, step=1.0,
        help="Percentuale di clienti che effettuano un secondo acquisto."
    )
    
    be_repeat_rate = st.number_input(
        "Repeat Order Rate (Freq)", 
        value=1.0, step=0.1,
        help="Frequenza media di riacquisto per i clienti che ritornano (es. 1.0 = comprano 1 volta in più)."
    )

    # --- CALCOLI (BACKEND) ---
    
    # 1. AOV Netto
    # Formula: (AOV * (1 - %Resi)) / (1 + %IVA)
    aov_post_tax_returns = (be_aov * (1 - be_returns/100)) / (1 + be_vat/100)

    # 2. Profit per Order (Margine di Contribuzione I livello)
    # Formula: (AOV Netto * %Margine) - Costi Spedizione
    profit_per_order = (aov_post_tax_returns * (be_margin_prod/100)) - be_fulfillment

    # 3. Profit per Customer (LTV Marginale)
    # Formula: Profitto Ordine + (Profitto Ordine * %Returning * Frequenza)
    profit_per_customer = profit_per_order + (profit_per_order * (be_returning_perc/100) * be_repeat_rate)

    # 4. Break Even CPA
    # Logica: Posso spendere per acquisire un cliente fino all'intero profitto che quel cliente mi genererà.
    be_cpa = profit_per_customer

    # 5. Break Even ROAS
    # Formula: AOV Lordo / Break Even CPA
    be_roas_val = be_aov / be_cpa if be_cpa > 0 else 99.9

with st.sidebar.expander("2. Output Calcolati (Live)", expanded=True):
    st.markdown("---")
    
    st.markdown(f"**AOV (Netto)**: € {aov_post_tax_returns:.2f}")
    st.caption("Formula: `(AOV * (1-Resi)) / (1+IVA)`")
    
    st.markdown(f"**Profitto/Ordine**: € {profit_per_order:.2f}")
    st.caption("Formula: `(AOV Netto * Margine%) - Spedizioni`")
    
    st.markdown(f"**Profitto/Cliente**: € {profit_per_customer:.2f}")
    st.caption("Formula: `Profitto Ordine + Valore Ricorsivo`")
    
    st.markdown("---")
    
    st.metric(
        "🎯 Break-Even CPA", 
        f"€ {be_cpa:.2f}",
        help="Costo per Acquisizione massimo sostenibile. Se spendi più di così per acquisire un cliente, sei in perdita."
    )
    
    st.metric(
        "🎯 Break-Even ROAS", 
        f"{be_roas_val*100:.0f}% ({be_roas_val:.2f})",
        help="Ritorno sulla spesa pubblicitaria minimo necessario. Formula: `AOV / Break Even CPA`."
    )

st.sidebar.divider()

# --- SIDEBAR: CONTROLLI ---
st.sidebar.header("🕹️ Pannello di Controllo")
uploaded_file = st.sidebar.file_uploader("Carica il file META_GOOGLE_SHOPIFY.csv", type="csv")

if uploaded_file is not None:
    try:
        # --- CARICAMENTO E PULIZIA ---
        df = pd.read_csv(uploaded_file, sep=None, engine='python')
        df = df.dropna(how='all')
        df.columns = df.columns.str.strip()

        col_date = next((c for c in df.columns if 'Year Week' in c or 'Settimana' in c), None)
        col_google = next((c for c in df.columns if 'Cost' in c), 'Cost')
        col_meta = next((c for c in df.columns if 'Amount Spent' in c), 'Amount Spent')
        col_sales = next((c for c in df.columns if 'Total sales' in c), 'Total sales')
        col_returns = next((c for c in df.columns if 'Returns' in c), 'Returns')
        col_orders = next((c for c in df.columns if 'Orders' in c), 'Orders')
        col_aov = next((c for c in df.columns if 'Average order value' in c), 'Average order value')
        
        col_g_val = 'Conversions Value'
        col_m_val = 'Website Purchases Conversion Value'
        col_g_cpc = 'Avg. CPC'
        col_m_cpc = 'CPC (All)'
        col_m_cpm = 'CPM (Cost per 1,000 Impressions)'
        col_g_imps = 'Impressions'
        col_m_freq = 'Frequency'
        
        # Colonne aggiuntive per AI
        col_items = 'Items'
        col_ret_rate = 'Returning customer rate'
        col_discounts = 'Discounts'

        if not col_date:
            st.error("Errore: Manca colonna data.")
            st.stop()

        df['Data_Interna'] = df[col_date].apply(parse_iso_week)
        df = df.dropna(subset=['Data_Interna']).sort_values('Data_Interna')
        df['Periodo'] = df['Data_Interna'].apply(get_week_range_label_with_year)

        money_cols = [col_google, col_meta, col_sales, col_returns, col_aov, 'Gross sales', col_discounts, 
                      col_g_val, col_m_val, col_g_cpc, col_m_cpc, col_m_cpm]
        for c in money_cols:
            if c in df.columns: df[c] = clean_currency_us(df[c])

        if col_g_imps in df.columns: df[col_g_imps] = pd.to_numeric(df[col_g_imps], errors='coerce').fillna(0)
        if col_m_freq in df.columns: df[col_m_freq] = pd.to_numeric(df[col_m_freq], errors='coerce').fillna(0)
        
        # Pulizia specifica per l'AI
        if col_ret_rate in df.columns: df[col_ret_rate] = df[col_ret_rate].apply(clean_percentage)
        if col_items in df.columns: df[col_items] = pd.to_numeric(df[col_items], errors='coerce').fillna(0)

        df = df.fillna(0)

        df['Fatturato_Netto'] = df[col_sales].clip(lower=0)
        df['Spesa_Ads_Totale'] = df[col_google] + df[col_meta]
        df['Tasso_Resi'] = (df[col_returns].abs() / df[col_sales].replace(0, np.nan)) * 100
        df['Tasso_Resi'] = df['Tasso_Resi'].fillna(0)
        
        # Calcolo CoS Storico
        df['CoS'] = (df['Spesa_Ads_Totale'] / df['Fatturato_Netto'].replace(0, np.nan)) * 100
        df['CoS'] = df['CoS'].fillna(0)
        
        # Profitto Operativo Storico (Usa Profitto per Ordine)
        num_orders = df[col_orders] if col_orders in df.columns else (df['Fatturato_Netto'] / be_aov)
        df['Profitto_Operativo'] = (num_orders * profit_per_order) - df['Spesa_Ads_Totale']

        # Inizializzazione sicura ROAS
        df['ROAS_Google'] = 0.0; df['ROAS_Meta'] = 0.0
        if col_g_val in df.columns: df['ROAS_Google'] = df[col_g_val] / df[col_google].replace(0, np.nan).fillna(0)
        if col_m_val in df.columns: df['ROAS_Meta'] = df[col_m_val] / df[col_meta].replace(0, np.nan).fillna(0)

        # --- PRE-CALCOLO METRICHE PER SIDEBAR ---
        
        # 1. Calcolo Saturazione Storica
        df['Year'] = df['Data_Interna'].dt.year
        df_annual = df.groupby('Year').agg({'Spesa_Ads_Totale': 'sum', 'Fatturato_Netto': 'sum'}).sort_index()
        suggested_saturation = 0.85 
        if len(df_annual) >= 2:
            d_spend = (df_annual.loc[df_annual.index[-1], 'Spesa_Ads_Totale'] - df_annual.loc[df_annual.index[-2], 'Spesa_Ads_Totale']) / df_annual.loc[df_annual.index[-2], 'Spesa_Ads_Totale']
            d_rev = (df_annual.loc[df_annual.index[-1], 'Fatturato_Netto'] - df_annual.loc[df_annual.index[-2], 'Fatturato_Netto']) / df_annual.loc[df_annual.index[-2], 'Fatturato_Netto']
            if d_spend > 0.05:
                suggested_saturation = np.clip(d_rev / d_spend, 0.60, 1.0)

        # 2. Calcolo Trend Rolling YoY (Ultimi 12 mesi vs 12 mesi precedenti)
        last_date = df['Data_Interna'].max()
        start_LTM = last_date - pd.Timedelta(weeks=52)
        start_LTM_prev = start_LTM - pd.Timedelta(weeks=52)
        
        sales_LTM = df[(df['Data_Interna'] > start_LTM) & (df['Data_Interna'] <= last_date)]['Fatturato_Netto'].sum()
        sales_LTM_prev = df[(df['Data_Interna'] > start_LTM_prev) & (df['Data_Interna'] <= start_LTM)]['Fatturato_Netto'].sum()
        
        growth_rate = (sales_LTM - sales_LTM_prev) / sales_LTM_prev if sales_LTM_prev > 0 else 0.0

        # 3. Calcolo Crescita Storica Annuale (Tabella)
        historical_growth_data = []
        years_avail = sorted(df['Year'].unique(), reverse=True)
        for i in range(len(years_avail) - 1):
            curr_y = years_avail[i]
            prev_y = years_avail[i+1]
            val_curr = df_annual.loc[curr_y, 'Fatturato_Netto']
            val_prev = df_annual.loc[prev_y, 'Fatturato_Netto']
            g_y = (val_curr - val_prev) / val_prev if val_prev > 0 else 0
            historical_growth_data.append(f"📅 {curr_y} vs {prev_y}: **{g_y:+.1%}**")

        # === 🚀 AUTO-SETTING AL PRIMO CARICAMENTO ===
        if st.session_state.last_uploaded_file != uploaded_file.name:
            st.session_state.trend_val = 0.0
            st.session_state.google_scale = 1.2
            st.session_state.meta_scale = 1.2
            st.session_state.sat_val = float(suggested_saturation)
            st.session_state.last_uploaded_file = uploaded_file.name
            st.rerun()
        # =============================================

        # --- SIDEBAR: AZIONI RAPIDE ---
        st.sidebar.subheader("⚡ Azioni Rapide")
        
        with st.sidebar.expander("ℹ️ Info Scenari"):
            st.markdown("""
            * **🛡️ Prudente:** Mantiene budget attuali, stima efficienza bassa (0.80).
            * **🚀 Aggressivo:** Aumenta budget del 50%, assume trend positivo (+15%) e ottima efficienza.
            * **🎯 Auto-Calibra:** Usa i tuoi dati storici per settare la saturazione reale e propone una crescita sostenibile (+20% budget).
            """)

        col_b1, col_b2 = st.sidebar.columns(2)
        if col_b1.button("🛡️ Prudente"):
            st.session_state.trend_val = 0.0; st.session_state.google_scale = 1.0; st.session_state.meta_scale = 1.0; st.session_state.sat_val = 0.80; st.rerun()
        if col_b2.button("🚀 Aggressivo"):
            st.session_state.trend_val = 0.15; st.session_state.google_scale = 1.5; st.session_state.meta_scale = 1.5; st.session_state.sat_val = 0.90; st.rerun()
        if st.sidebar.button(f"🎯 Auto-Calibra (Sat: {suggested_saturation:.2f})"):
            st.session_state.trend_val = 0.0; st.session_state.google_scale = 1.2; st.session_state.meta_scale = 1.2; st.session_state.sat_val = float(suggested_saturation); st.rerun()

        st.sidebar.divider()

        # --- SIDEBAR: TREND & CRESCITA (AGGIORNATO) ---
        st.sidebar.subheader("🚀 Trend & Crescita")
        
        # Spiegazione con dati reali
        with st.sidebar.expander("ℹ️ Come viene calcolato?"):
            st.markdown(f"""
            **Formula:** `(Fatturato Ultimi 12 Mesi - Fatturato 12 Mesi Precedenti) / Precedenti`
            
            **Esempio con i tuoi dati:**
            * **Ultimi 12 Mesi:** € {sales_LTM:,.0f}
            * **12 Mesi Prec.:** € {sales_LTM_prev:,.0f}
            * **Calcolo:** `({sales_LTM:,.0f} - {sales_LTM_prev:,.0f}) / {sales_LTM_prev:,.0f}` = **{growth_rate:+.1%}**
            
            Questo trend (+{growth_rate*100:.1f}%) è la "velocità base" che il sistema usa per le proiezioni se lasci lo slider a 0.
            """)
            
            if historical_growth_data:
                st.markdown("---")
                st.markdown("**📜 Storico Crescita Annuale:**")
                for hist_row in historical_growth_data[:4]: # Mostra ultimi 4 anni
                    st.markdown(hist_row)

        st.sidebar.markdown(f"**Crescita Rilevata (YoY):** `{growth_rate:+.1%}`.")
        manual_trend = st.sidebar.slider("Aggiusta Trend Futuro", -0.5, 2.0, key="trend_val", help="Aggiunge o toglie punti percentuali al trend storico rilevato.")

        st.sidebar.divider()
        st.sidebar.subheader("Scenari Budget")
        m_google = st.sidebar.slider("Scala Google Ads", 0.5, 5.0, key="google_scale")
        m_meta = st.sidebar.slider("Scala Meta Ads", 0.5, 5.0, key="meta_scale")
        
        st.sidebar.divider()
        st.sidebar.subheader("Calibrazione")
        sat_factor = st.sidebar.slider("Saturazione", 0.5, 1.0, key="sat_val")
        
        # Grafico Saturazione con Assi
        x_sat = np.linspace(1, 4, 20); y_sat = x_sat ** sat_factor
        fig_sat, ax_sat = plt.subplots(figsize=(4, 2))
        ax_sat.plot(x_sat, x_sat, ls='--', color='gray', alpha=0.5, label='Ideale')
        ax_sat.plot(x_sat, y_sat, color='#e74c3c', lw=2, label='Reale')
        ax_sat.set_title("Curva Rendimenti", fontsize=9)
        ax_sat.set_xlabel("Moltiplicatore Spesa", fontsize=7)
        ax_sat.set_ylabel("Moltiplicatore Ricavi", fontsize=7)
        ax_sat.tick_params(labelsize=6)
        ax_sat.legend(fontsize=6, frameon=False)
        ax_sat.spines['top'].set_visible(False)
        ax_sat.spines['right'].set_visible(False)
        st.sidebar.pyplot(fig_sat)

        mesi_prev = st.sidebar.number_input("Mesi di Previsione", 1, 24, 6)

        # --- 4. DASHBOARD KPI (Ultime 4 Settimane) ---
        st.divider()
        last_4 = df.tail(4)
        tot_sales = last_4['Fatturato_Netto'].sum()
        tot_ads = last_4['Spesa_Ads_Totale'].sum()
        mer = tot_sales / tot_ads if tot_ads > 0 else 0
        cos = (tot_ads / tot_sales * 100) if tot_sales > 0 else 0
        avg_return_rate = last_4['Tasso_Resi'].mean()
        profit = last_4['Profitto_Operativo'].sum()

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Fatturato (4w)", f"€ {tot_sales:,.0f}")
        c2.metric("Spesa Ads (4w)", f"€ {tot_ads:,.0f}")
        c3.metric("MER / BE", f"{mer:.2f} / {be_roas_val:.2f}", delta=f"{mer-be_roas_val:.2f}")
        c4.metric("CoS (Spesa/Fatt.)", f"{cos:.1f}%")
        c5.metric("Profitto Stimato", f"€ {profit:,.0f}", help="Profitto Operativo dopo Merce, Tasse, Logistica e Ads.")

        # --- 5. CALCOLO PREVISIONALE ---
        df['Week_Num'] = df['Data_Interna'].dt.isocalendar().week
        seasonal = df.groupby('Week_Num').agg({
            'Fatturato_Netto': 'mean', col_google: 'mean', col_meta: 'mean', col_orders: 'mean'
        }).reset_index()

        future_dates = pd.date_range(start=last_date + pd.Timedelta(weeks=1), periods=int(mesi_prev*4.34), freq='W-MON')

        rows = []
        for d in future_dates:
            w = d.isocalendar().week
            base = seasonal[seasonal['Week_Num'] == w]
            if base.empty: base = seasonal.mean().to_frame().T
            
            # Trend applicato: (Vendite Ultimi 12 Mesi / Media Storica) * (1 + Slider Manuale)
            # Usiamo growth_rate calcolato sopra come base inerziale
            # Se growth_rate è +7%, e manual_trend è 0, il moltiplicatore sarà 1.078
            base_trend = (1 + growth_rate) * (1 + manual_trend)
            
            # Applichiamo il trend alla media stagionale
            proj_sales_base = base['Fatturato_Netto'].values[0] * base_trend
            proj_google_base = base[col_google].values[0] * base_trend
            proj_meta_base = base[col_meta].values[0] * base_trend
            
            new_g, new_m = proj_google_base * m_google, proj_meta_base * m_meta
            ratio = (new_g + new_m) / (proj_google_base + proj_meta_base) if (proj_google_base + proj_meta_base) > 0 else 1.0
            f_sales = proj_sales_base * (ratio ** sat_factor)
            
            f_orders = f_sales / be_aov
            
            rows.append({
                'Data': d, 
                'Periodo': get_week_range_label_with_year(d),
                'Google Previsto': new_g, 
                'Meta Previsto': new_m, 
                'Fatturato Previsto': f_sales, 
                'Ordini Previsti': f_orders
            })
        
        df_prev = pd.DataFrame(rows)
        df_prev['Spesa Totale'] = df_prev['Google Previsto'] + df_prev['Meta Previsto']
        df_prev['MER Previsto'] = df_prev['Fatturato Previsto'] / df_prev['Spesa Totale']
        # Calcolo CoS Previsto
        df_prev['CoS Previsto'] = (df_prev['Spesa Totale'] / df_prev['Fatturato Previsto'].replace(0, np.nan)) * 100
        df_prev['CoS Previsto'] = df_prev['CoS Previsto'].fillna(0)
        
        # --- 6. VISUALIZZAZIONE TABS ---
        tabs = st.tabs([
            "📉 Grafico Previsionale", "📋 Dettaglio Previsione", "🔵 Analisi Google Ads", 
            "🔵 Analisi Meta Ads", "🧪 Analisi Saturazione Storica", "📊 Analisi Resi", 
            "🗂️ Dati CSV", "🧠 Insight AI"
        ])
        
        # COLORI
        DARKEST_BLUE = '#000080'  
        META_COLOR = '#3b5998'    
        GREEN_COLOR = '#2ecc71'   
        ORANGE_COLOR = '#e67e22'  
        
        with tabs[0]:
            st.caption("Confronto Storico (Verde) vs Previsione (Arancione) basata sui tuoi Scenari.")
            fig, ax1 = plt.subplots(figsize=(12, 6))
            ax1.plot(df['Data_Interna'], df['Fatturato_Netto'], color=GREEN_COLOR, label='Storico', linewidth=1)
            ax1.plot(df_prev['Data'], df_prev['Fatturato Previsto'], color=ORANGE_COLOR, linestyle='--', label='Previsione', linewidth=2)
            ax1.set_ylabel("Fatturato (€)")
            ax2 = ax1.twinx()
            ax2.stackplot(pd.concat([df['Data_Interna'], df_prev['Data']]),
                          np.concatenate([df[col_google], df_prev['Google Previsto']]),
                          np.concatenate([df[col_meta], df_prev['Meta Previsto']]),
                          colors=[DARKEST_BLUE, META_COLOR], alpha=0.3, labels=['Google Ads', 'Meta Ads'])
            ax1.legend(loc='upper left')
            st.pyplot(fig)

        with tabs[1]:
            st.caption("Dettaglio numerico delle previsioni (Mensile e Settimanale).")
            st.subheader("📅 Riepilogo Mensile")
            df_prev['Mese'] = df_prev['Data'].dt.strftime('%B %Y')
            df_monthly = df_prev.groupby('Mese', sort=False).agg({'Spesa Totale': 'sum', 'Fatturato Previsto': 'sum'}).reset_index()
            df_monthly['MER Previsto'] = df_monthly['Fatturato Previsto'] / df_monthly['Spesa Totale']
            # Calcolo CoS Mensile
            df_monthly['CoS Previsto'] = (df_monthly['Spesa Totale'] / df_monthly['Fatturato Previsto'].replace(0, np.nan)) * 100
            
            st.dataframe(df_monthly.style.format({'Spesa Totale': '€ {:,.0f}', 'Fatturato Previsto': '€ {:,.0f}', 'MER Previsto': '{:.2f}', 'CoS Previsto': '{:.1f}%'}))
            
            st.write("**Dettaglio Settimanale**")
            st.dataframe(df_prev[['Periodo', 'Spesa Totale', 'Fatturato Previsto', 'MER Previsto', 'CoS Previsto']].style.format({'Spesa Totale': '€ {:,.0f}', 'Fatturato Previsto': '€ {:,.0f}', 'MER Previsto': '{:.2f}', 'CoS Previsto': '{:.1f}%'}))

        with tabs[2]:
            st.caption("Focus sulle performance storiche di Google Ads: Spesa vs Conversion Value.")
            st.subheader("🔵 Performance Google Ads")
            if col_g_val in df.columns:
                g_metrics = df.tail(4)[[col_google, col_g_val, 'ROAS_Google', col_g_cpc, col_g_imps]].sum()
                avg_roas_g = g_metrics[col_g_val] / g_metrics[col_google] if g_metrics[col_google] > 0 else 0
                st.columns(5)[0].metric("Spesa (4w)", f"€ {g_metrics[col_google]:,.0f}")
                
                fig_g, ax_g1 = plt.subplots(figsize=(12, 5))
                ax_g1.bar(df['Data_Interna'], df[col_google], color=DARKEST_BLUE, alpha=0.7, label='Spesa Google')
                ax_g2 = ax_g1.twinx()
                ax_g2.plot(df['Data_Interna'], df[col_g_val], color=GREEN_COLOR, linewidth=2, label='Valore Conversione')
                st.pyplot(fig_g)
                st.dataframe(df[['Periodo', col_date, col_google, col_g_val, 'ROAS_Google', col_g_cpc]].iloc[::-1].style.format({col_google: '€ {:,.2f}', col_g_val: '€ {:,.2f}', 'ROAS_Google': '{:.2f}', col_g_cpc: '€ {:,.2f}'}))

        with tabs[3]:
            st.caption("Focus sulle performance storiche di Meta Ads: Spesa vs Conversion Value.")
            st.subheader("🔵 Performance Meta Ads")
            if col_m_val in df.columns:
                m_metrics = df.tail(4)[[col_meta, col_m_val, 'ROAS_Meta', col_m_cpc, col_m_cpm, col_m_freq]].sum()
                st.columns(6)[0].metric("Spesa (4w)", f"€ {m_metrics[col_meta]:,.0f}")
                
                fig_m, ax_m1 = plt.subplots(figsize=(12, 5))
                ax_m1.bar(df['Data_Interna'], df[col_meta], color=DARKEST_BLUE, alpha=0.7, label='Spesa Meta')
                ax_m2 = ax_m1.twinx()
                ax_m2.plot(df['Data_Interna'], df[col_m_val], color=GREEN_COLOR, linewidth=2, label='Website Purch. Value')
                st.pyplot(fig_m)
                st.dataframe(df[['Periodo', col_date, col_meta, col_m_val, 'ROAS_Meta', col_m_cpc, col_m_cpm, col_m_freq]].iloc[::-1].style.format({col_meta: '€ {:,.2f}', col_m_val: '€ {:,.2f}', 'ROAS_Meta': '{:.2f}', col_m_cpc: '€ {:,.2f}', col_m_cpm: '€ {:,.2f}', col_m_freq: '{:.2f}'}))

        with tabs[4]:
            st.caption("Analisi dell'elasticità: misura quanto il fatturato reagisce alle variazioni di spesa pubblicitaria.")
            st.header("🧪 Analisi Saturazione e Scalabilità")
            st.subheader("1. Riepilogo Annuale Completo (Anno su Anno)")
            
            df['Year'] = df['Data_Interna'].dt.year
            df['Week'] = df['Data_Interna'].dt.isocalendar().week
            
            annual_agg = df.groupby('Year').agg({'Spesa_Ads_Totale': 'sum', 'Fatturato_Netto': 'sum'}).sort_index(ascending=False)
            annual_rows = []
            years_list = annual_agg.index.tolist()
            
            for i in range(len(years_list) - 1):
                curr_y, prev_y = years_list[i], years_list[i+1]
                s_curr, s_prev = annual_agg.loc[curr_y, 'Spesa_Ads_Totale'], annual_agg.loc[prev_y, 'Spesa_Ads_Totale']
                r_curr, r_prev = annual_agg.loc[curr_y, 'Fatturato_Netto'], annual_agg.loc[prev_y, 'Fatturato_Netto']
                
                d_spend = ((s_curr - s_prev) / s_prev * 100) if s_prev > 0 else 0
                d_rev = ((r_curr - r_prev) / r_prev * 100) if r_prev > 0 else 0
                elasticity = d_rev / d_spend if d_spend != 0 else 0
                
                annual_rows.append({'Confronto': f"{curr_y} vs {prev_y}", 'Delta Spesa %': d_spend, 'Delta Fatturato %': d_rev, 'Elasticità': elasticity})
            
            if annual_rows:
                st.dataframe(pd.DataFrame(annual_rows).style.format({'Delta Spesa %': '{:+.1f}%', 'Delta Fatturato %': '{:+.1f}%', 'Elasticità': '{:.2f}'}).background_gradient(subset=['Elasticità'], cmap='RdYlGn', vmin=0.5, vmax=1.5))

            st.divider()
            st.subheader("2. Dettaglio Settimanale")
            
            if not annual_rows:
                st.warning("Dati insufficienti.")
            else:
                comp_options = [row['Confronto'] for row in annual_rows]
                selected_comp = st.selectbox("Seleziona Anno da Confrontare", comp_options)
                curr_year_sel = int(selected_comp.split(" vs ")[0])
                prev_year_sel = int(selected_comp.split(" vs ")[1])
                
                all_weeks = pd.DataFrame({'Week': range(1, 54)})
                df_curr = df[df['Year'] == curr_year_sel][['Week', 'Spesa_Ads_Totale', 'Fatturato_Netto', 'Periodo']]
                df_prev = df[df['Year'] == prev_year_sel][['Week', 'Spesa_Ads_Totale', 'Fatturato_Netto']]
                
                df_comp = pd.merge(all_weeks, df_curr, on='Week', how='left')
                df_comp = pd.merge(df_comp, df_prev, on='Week', suffixes=('_Curr', '_Prev'), how='left').fillna(0)
                
                df_comp['Delta Spesa %'] = np.where(df_comp['Spesa_Ads_Totale_Prev'] > 0, ((df_comp['Spesa_Ads_Totale_Curr'] - df_comp['Spesa_Ads_Totale_Prev']) / df_comp['Spesa_Ads_Totale_Prev']) * 100, 0)
                df_comp['Delta Ricavi %'] = np.where(df_comp['Fatturato_Netto_Prev'] > 0, ((df_comp['Fatturato_Netto_Curr'] - df_comp['Fatturato_Netto_Prev']) / df_comp['Fatturato_Netto_Prev']) * 100, 0)
                df_comp['Elasticità'] = np.where(df_comp['Delta Spesa %'] != 0, df_comp['Delta Ricavi %'] / df_comp['Delta Spesa %'], 0)
                
                df_view = df_comp[(df_comp['Spesa_Ads_Totale_Curr'] > 0) | (df_comp['Spesa_Ads_Totale_Prev'] > 0)].sort_values('Week', ascending=False)
                
                st.dataframe(df_view[['Week', 'Periodo', 'Spesa_Ads_Totale_Curr', 'Spesa_Ads_Totale_Prev', 'Delta Spesa %', 'Delta Ricavi %', 'Elasticità']].style.format({'Spesa_Ads_Totale_Curr': '€ {:,.0f}', 'Spesa_Ads_Totale_Prev': '€ {:,.0f}', 'Delta Spesa %': '{:+.1f}%', 'Delta Ricavi %': '{:+.1f}%', 'Elasticità': '{:.2f}'}).background_gradient(subset=['Elasticità'], cmap='RdYlGn', vmin=0.5, vmax=1.5))
                
                fig_sat, ax_sat = plt.subplots(figsize=(10, 5))
                ax_sat.plot([-100, 500], [-100, 500], ls='--', color='gray', alpha=0.5)
                scatter = ax_sat.scatter(df_view['Delta Spesa %'], df_view['Delta Ricavi %'], c=df_view['Elasticità'], cmap='RdYlGn', s=80, edgecolor='black', vmin=0.6, vmax=1.4)
                ax_sat.set_xlabel("Variazione Spesa (%)")
                ax_sat.set_ylabel("Variazione Fatturato (%)")
                plt.colorbar(scatter, label='Elasticità')
                st.pyplot(fig_sat)

        with tabs[5]:
            st.caption("Confronto tra quanto spendi in pubblicità e la percentuale di prodotti resi. Se salgono insieme, stai acquisendo traffico di bassa qualità.")
            st.subheader("🔍 Spesa Ads vs Tasso Resi")
            fig2, ax1_2 = plt.subplots(figsize=(12, 6))
            ax1_2.bar(df['Data_Interna'], df['Spesa_Ads_Totale'], color=DARKEST_BLUE, alpha=0.5)
            ax2_2 = ax1_2.twinx()
            ax2_2.plot(df['Data_Interna'], df['Tasso_Resi'].rolling(4).mean(), color='#e74c3c', linewidth=2)
            st.pyplot(fig2)

        with tabs[6]:
            st.caption("Il database grezzo importato dal CSV per verifiche puntuali.")
            st.subheader("🗂️ Database Storico")
            display_cols = [col_date, 'Periodo', 'Total sales', col_google, col_g_val, col_g_cpc, col_g_imps, 
                            col_meta, col_m_val, col_m_cpc, col_m_cpm, col_m_freq, 'CoS', 'Profitto_Operativo']
            valid_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[valid_cols].iloc[::-1].style.format({'CoS': '{:.1f}%', 'Profitto_Operativo': '€ {:,.0f}'}, precision=2))

        # --- 8. TAB AI AVANZATA ---
        with tabs[7]:
            st.caption("Intelligence Automatica: Punteggio di salute mensile basato su Profitto, Retention, Sconti e Canali.")
            st.header("🧠 Insight AI: Analisi Strategica Completa")
            
            # Prepare monthly data
            df['Month_Date'] = df['Data_Interna'].dt.to_period('M')
            ai_agg = {
                'Spesa_Ads_Totale': 'sum', 'Fatturato_Netto': 'sum', 'Orders': 'sum', 
                col_returns: 'sum', col_discounts: 'sum', col_google: 'sum', col_meta: 'sum', 
                col_g_val: 'sum', col_m_val: 'sum', 'Gross sales': 'sum', 'Profitto_Operativo': 'sum'
            }
            # Add complex metrics if present
            if col_ret_rate in df.columns: ai_agg[col_ret_rate] = 'mean'
            if col_m_freq in df.columns: ai_agg[col_m_freq] = 'mean'
            if col_m_cpm in df.columns: ai_agg[col_m_cpm] = 'mean'
            if col_g_cpc in df.columns: ai_agg[col_g_cpc] = 'mean'
            if col_m_cpc in df.columns: ai_agg[col_m_cpc] = 'mean'

            ai_df = df.groupby('Month_Date').agg(ai_agg).sort_index(ascending=False)
            
            # Metrics
            ai_df['MER'] = ai_df['Fatturato_Netto'] / ai_df['Spesa_Ads_Totale'].replace(0, np.nan)
            ai_df['Discount_Rate'] = (ai_df[col_discounts].abs() / ai_df['Gross sales'].replace(0, np.nan)) * 100
            ai_df['ROAS_Google'] = ai_df[col_g_val] / ai_df[col_google].replace(0, np.nan)
            ai_df['ROAS_Meta'] = ai_df[col_m_val] / ai_df[col_meta].replace(0, np.nan)
            
            # Seasonality Index
            avg_sales = ai_df['Fatturato_Netto'].mean()
            ai_df['Seasonality'] = ai_df['Fatturato_Netto'] / avg_sales
            
            # Benchmarks
            bench_mer = ai_df['MER'].mean()
            bench_ret = ai_df[col_ret_rate].mean() if col_ret_rate in df.columns else 0
            bench_disc = ai_df['Discount_Rate'].mean()
            
            for m in ai_df.index[:12]:
                row = ai_df.loc[m]
                m_str = str(m)
                
                score = 50
                tags = []
                alerts = []
                
                # Logic based on Break Even
                if row['MER'] >= be_roas_val: 
                    score += 20
                    tags.append(f"Profittevole (> {be_roas_val:.2f})")
                else: 
                    score -= 20
                    alerts.append(f"Sotto Break-Even (MER {row['MER']:.2f})")
                
                if col_ret_rate in df.columns:
                    if row[col_ret_rate] > bench_ret * 1.1: score += 15; tags.append(f"Retention {row[col_ret_rate]:.1f}%")
                    elif row[col_ret_rate] < bench_ret * 0.8: score -= 10; alerts.append("Crollo Retention")
                
                if row['ROAS_Google'] > row['ROAS_Meta']: tags.append("Win: Google")
                else: tags.append("Win: Meta")
                
                seas_txt = "Media"
                if row['Seasonality'] > 1.2: seas_txt = "Alta Stagionalità 🔥"
                elif row['Seasonality'] < 0.8: seas_txt = "Bassa Stagionalità ❄️"
                
                # Card Render
                color_class = "ai-score-high" if score >= 70 else "ai-score-med" if score >= 50 else "ai-score-low"
                
                with st.container():
                    st.markdown(f"""
                    <div class="ai-box {color_class}">
                        <div class="ai-title" style="display:flex; justify-content:space-between;">
                            <span>📅 {m_str} | Score: {score}/100</span>
                            <span style="font-size:0.8em; color:#666;">{seas_txt}</span>
                        </div>
                        <div style="margin:8px 0;">
                            {' '.join([f'<span class="ai-tag tag-blue">{t}</span>' for t in tags])}
                        </div>
                        <p style="margin:0; font-size:0.95em;">
                            Generati <b>€ {row['Fatturato_Netto']:,.0f}</b> con MER <b>{row['MER']:.2f}</b>. 
                            Profitto Operativo: <b>€ {row['Profitto_Operativo']:,.0f}</b>.
                            Incidenza sconti: <b>{row['Discount_Rate']:.1f}%</b>.
                        </p>
                        {''.join([f'<div class="ai-alert">⚠️ {a}</div>' for a in alerts])}
                    </div>
                    """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"⚠️ Errore: {e}")
else:
    st.info("👋 Carica il file CSV per iniziare.")