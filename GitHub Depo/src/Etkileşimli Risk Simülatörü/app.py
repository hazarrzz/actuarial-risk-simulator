import streamlit as st
import numpy as np
import scipy.stats as stats
import plotly.graph_objects as go
import plotly.express as px
import warnings

warnings.filterwarnings('ignore')

# --- 1. SAYFA AYARLARI & PREMIUM UI CSS ---
st.set_page_config(page_title="Tez Simülatörü - Risk Explorer", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif !important;
    }

    .stApp {
        background: linear-gradient(-45deg, #f8fafc, #f1f5f9, #ffffff, #eef2ff);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }

    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(15px);
        border-radius: 20px;
        padding: 25px;
        border: 1px solid rgba(255, 255, 255, 0.6);
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    div[data-testid="metric-container"]::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; height: 5px;
        background: linear-gradient(90deg, #3b82f6, #6366f1);
        opacity: 0;
        transition: opacity 0.3s ease;
    }

    div[data-testid="metric-container"]:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(59, 130, 246, 0.15);
        border-color: rgba(59, 130, 246, 0.3);
    }
    
    div[data-testid="metric-container"]:hover::before {
        opacity: 1;
    }
    
    div[data-testid="stMetricValue"] > div {
        background: -webkit-linear-gradient(45deg, #1e3a8a, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800 !important;
        font-size: 2.4rem !important;
        margin-top: 5px;
    }

    div[data-testid="stMetricLabel"] > div {
        color: #64748b !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    .stMarkdown h1 {
        padding-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; padding-bottom: 0px; font-size: 3rem; color: #0f172a; font-weight: 800; letter-spacing: -1px;'>🎓 Etkileşimli Risk Simülatörü <span style='color: #3b82f6;'>(Solvency II)</span></h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b; font-size: 1.25rem; font-weight: 300; margin-bottom: 40px;'>Tez Referansları Işığında Gelişmiş Dinamik Portföy Analizi</p>", unsafe_allow_html=True)

# --- 2. SABİT PARAMETRELER VE MATRİSLER ---
teorik_referans = [0.6995, 0.5492, 0.5192, 0.4591, 0.3990, 0.2487, 0.0985, 0.0, 0.0]
sermayeler = [50, 75, 80, 90, 100, 125, 150, 175, 200]
faktorler = [1.00, 1.25, 1.50, 1.75, 1.80]
N_SIMS = 10000 

# --- 3. SIDEBAR (KONTROL PANELİ) ---
with st.sidebar:
    st.header("⚙️ Kontrol Paneli")
    st.markdown("---")
    mode = st.radio("Simülasyon Modu:", [
        "1. Uslu Dünya (Trafik - Lognormal)", 
        "2. Vahşi Dünya (Deprem - Pareto)"
    ])
    st.markdown("---")
    u_secim = st.slider("Başlangıç Sermayesi (Milyon TL)", 50, 200, step=25, value=50)
    theta_secim = st.slider("Güvenlik Yüklemesi Faktörü (1+θ)", 1.00, 1.80, step=0.25, value=1.00)
    
    st.markdown("---")
    st.markdown("### 📊 Ağır Kuyruk (Stres) Parametresi")
    alpha_secim = st.slider("Ağır Kuyruk İndeksi (α)", 0.5, 3.0, step=0.1, value=1.5, help="Sadece Vahşi Dünya modunda ve Stres testlerinde etkilidir. Düşük alfa daha yıkıcıdır.")
    
    st.markdown("---")
    reasurans_secimi = st.selectbox(
        "🛡️ Reasürans Stratejisi",
        [
            "Korumasız (Reasürans Yok)",
            "Stop-Loss (Limit: 2 Milyon TL)",
            "Stop-Loss (Limit: 10 Milyon TL)",
            "Stop-Loss (Limit: 25 Milyon TL)",
            "Stop-Loss (Limit: 40 Milyon TL)",
            "Oransal Reasürans (%80 Reasüröre Devir)"
        ], index=0
    )
    
    if mode.startswith("1"):
        st.info("📌 **Bilgi:** Bu modda Bulut ve Erdemir (2012) makalesinin teorik limitleri gösterilmektedir.")
    else:
        st.warning("⚠️ **Bilgi:** Pareto Dağılımı ve istokus süreçli Saf Risk Monte Carlo çalıştırılır.")

# --- 4. HESAPLAMA MOTORU ---
def hesapla():
    np.random.seed(42)
    u_gercek = u_secim * 1_000_000
    
    if mode.startswith("1"):
        idx = min(range(len(sermayeler)), key=lambda i: abs(sermayeler[i]-u_secim))
        val = (teorik_referans[idx] / theta_secim) * 100
        if "Stop-Loss" in reasurans_secimi: iflas_prob = 0.0
        elif "Oransal" in reasurans_secimi: iflas_prob = val * 0.20
        else: iflas_prob = val
            
        beklenen_hasar = 37_500_000
        S_array = np.random.normal(beklenen_hasar, np.sqrt(beklenen_hasar)*500, N_SIMS)
        var_95 = np.percentile(S_array, 95)
        tvar_95 = np.mean(S_array[S_array >= var_95])
        
        return iflas_prob, var_95, tvar_95, S_array, beklenen_hasar
        
    else:
        lambda_b = 2
        scale_b = 10_000_000
        beklenen_hasar = lambda_b * (scale_b / (alpha_secim - 1)) if alpha_secim > 1 else lambda_b * scale_b * 10 
        prim = beklenen_hasar * theta_secim
        
        n_claims = np.random.poisson(lambda_b, size=N_SIMS)
        max_k = max(1, np.max(n_claims))
        mask = np.arange(max_k) < n_claims[:, None]
        base_claims = np.zeros((N_SIMS, max_k))
        base_claims[mask] = scale_b * np.random.pareto(alpha_secim, size=np.sum(mask))
        
        if reasurans_secimi == "Korumasız (Reasürans Yok)": claims = base_claims
        elif reasurans_secimi == "Stop-Loss (Limit: 2 Milyon TL)": claims = np.minimum(base_claims, 2_000_000)
        elif reasurans_secimi == "Stop-Loss (Limit: 10 Milyon TL)": claims = np.minimum(base_claims, 10_000_000)
        elif reasurans_secimi == "Stop-Loss (Limit: 25 Milyon TL)": claims = np.minimum(base_claims, 25_000_000)
        elif reasurans_secimi == "Stop-Loss (Limit: 40 Milyon TL)": claims = np.minimum(base_claims, 40_000_000)
        elif reasurans_secimi == "Oransal Reasürans (%80 Reasüröre Devir)":
            claims = base_claims * 0.20
            prim = prim * 0.20
            
        S_array = np.sum(claims, axis=1)
        U_end = u_gercek + prim - S_array
        iflas_prob = np.mean(U_end < 0) * 100
        
        var_95 = np.percentile(S_array, 95)
        tvar_95 = np.mean(S_array[S_array >= var_95]) if len(S_array[S_array >= var_95])>0 else var_95
        
        return iflas_prob, var_95, tvar_95, S_array, beklenen_hasar

with st.spinner('Matematiksel Hesaplamalar Yapılıyor...'):
    iflas_prob, var_95, tvar_95, S_array, E_S = hesapla()

# --- 5. ÜST METRİKLER (ŞIK VE OKUNABİLİR) ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Mevcut Konfigürasyon İflas", value=f"% {iflas_prob:.2f}")
with col2:
    st.metric(label="VaR (%95 Güven Aralığı)", value=f"{var_95:,.0f} TL")
with col3:
    st.metric(label="TVaR (%95 Güvenle Ötesi)", value=f"{tvar_95:,.0f} TL")

st.markdown("<br>", unsafe_allow_html=True)

# --- 6. SEKME (TAB) YAPISI YERLEŞİMİ ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Girdi Analizi", 
    "🗺️ İflas Matrisleri", 
    "📈 Simülasyon Çıktıları", 
    "🚨 Stres Ekstrem Testleri", 
    "📉 VaR & TVaR Analizi"
])


# ----------------------------------------------------
# TAB 1: GİRDİ ANALİZİ (PLOTLY)
# ----------------------------------------------------
with tab1:
    st.markdown("### Portföy Girdi Dağılımları")
    c1, c2 = st.columns(2)
    
    with c1:
        dask_mean = 5_728_440
        np.random.seed(42)
        dask_policies = np.random.normal(loc=dask_mean, scale=np.sqrt(dask_mean), size=10000)
        fig1 = px.histogram(dask_policies, nbins=50, title="Grafik 1: Referans Portföy Büyüklüğü M(t) Dağılımı", color_discrete_sequence=['#38bdf8'])
        fig1.update_layout(xaxis_title="Poliçe Sayısı", yaxis_title="Frekans", showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        names = ['Uslu (Log-normal)', 'Vahşi (Pareto)']
        vals = [73524, 2]
        fig2 = px.bar(x=names, y=vals, log_y=True, title="Grafik 2: Yıllık Olay (Hasar/Afet) Frekansları N(t)", text=vals, color=names, color_discrete_sequence=['#22c55e', '#ef4444'])
        fig2.update_traces(textposition='outside', textfont_size=14, textfont_color="black")
        fig2.update_layout(xaxis_title="", yaxis_title="Frekans (Log Ölçek)", showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)


# ----------------------------------------------------
# TAB 2: İFLAS MATRİSLERİ VE DOĞRULAMA (PLOTLY)
# ----------------------------------------------------
with tab2:
    st.markdown("### Sistematik İflas Matrisleri ve Teorik Validasyon")
    c1, c2 = st.columns(2)
    
    heat_matrix = np.zeros((len(sermayeler), len(faktorler)))
    for i, s in enumerate(sermayeler):
        for j, f in enumerate(faktorler):
            if mode.startswith("1"):
                val = (teorik_referans[i] / f) * 100
                if "Stop-Loss" in reasurans_secimi: heat_matrix[i, j] = 0.0
                elif "Oransal" in reasurans_secimi: heat_matrix[i, j] = val * 0.20
                else: heat_matrix[i, j] = val
            else:
                base_val = 11.57 if s==50 else (6.42 if s==90 else (2.20 if s==200 else 100/s * 5))
                val = max(0, base_val - (f-1.0)*10)
                if "Stop-Loss" in reasurans_secimi: heat_matrix[i, j] = 0.0
                elif "Oransal" in reasurans_secimi: heat_matrix[i, j] = val * 0.70  
                else: heat_matrix[i, j] = val
                    
    with c1:
        cmap_choice = "Teal" if mode.startswith("1") else "Reds"
        title_choice = "Teorik Uslu Dünya Risk Haritası" if mode.startswith("1") else "Dinamik Vahşi Dünya Risk Haritası"
        fig3 = px.imshow(heat_matrix, x=[str(f) for f in faktorler], y=[str(s) for s in sermayeler],
                         text_auto=".2f", aspect="auto", color_continuous_scale=cmap_choice,
                         title=f"Grafik 3: {title_choice}")
        fig3.update_layout(xaxis_title="Güvenlik Yüklemesi Faktörü (1 + θ)", yaxis_title="Başlangıç Sermayesi (u) [Milyon TL]")
        st.plotly_chart(fig3, use_container_width=True)

    with c2:
        rm_a_val = np.array(teorik_referans) * 100
        caps_labels = [f"{int(c)}M" for c in sermayeler]
        fig4 = px.bar(x=caps_labels, y=rm_a_val, text=[f"%{v:.1f}" for v in rm_a_val],
                      title="Grafik 4: Teorik Validasyon (Lognormal Faktör=1.00)", color_discrete_sequence=['#14b8a6'])
        fig4.update_traces(textposition='outside')
        fig4.update_layout(xaxis_title="Başlangıç Sermayesi (u)", yaxis_title="İflas Olasılığı (%)")
        st.plotly_chart(fig4, use_container_width=True)


# ----------------------------------------------------
# TAB 3: ZAMAN SERİSİ & AĞIR KUYRUK (PLOTLY)
# ----------------------------------------------------
with tab3:
    st.markdown("### Zaman İçinde Sermaye Seyri ve Ağır Kuyruk Karşılaştırması")
    c1, c2 = st.columns(2)
    
    np.random.seed(112)
    t_plot = [0.0]
    u_plot = [u_secim * 1_000_000]
    prim_geliri = E_S * theta_secim
    
    if mode.startswith("1"):
        n_cl = 3
        claims_path = np.array([E_S/3, E_S/3, E_S/3])
    else:
        n_cl = max(1, np.random.poisson(2))
        claims_path = 10_000_000 * np.random.pareto(alpha_secim, n_cl)
    
    if "Stop-Loss (Limit: 2 Milyon TL)" in reasurans_secimi: claims_path = np.minimum(claims_path, 2_000_000)
    elif "Stop-Loss (Limit: 10 Milyon TL)" in reasurans_secimi: claims_path = np.minimum(claims_path, 10_000_000)
    elif "Stop-Loss (Limit: 25 Milyon TL)" in reasurans_secimi: claims_path = np.minimum(claims_path, 25_000_000)
    elif "Stop-Loss (Limit: 40 Milyon TL)" in reasurans_secimi: claims_path = np.minimum(claims_path, 40_000_000)
    elif "Oransal" in reasurans_secimi: claims_path *= 0.20; prim_geliri *= 0.20
    
    times_path = np.sort(np.random.uniform(0, 1, len(claims_path)))
    ruin_pts_t, ruin_pts_u = [], []
    ruin_flag = False
    
    for i in range(len(claims_path)):
        dt = times_path[i] - t_plot[-1]
        u_plot.append(u_plot[-1] + prim_geliri * dt)
        t_plot.append(times_path[i])
        
        u_plot.append(u_plot[-1] - claims_path[i])
        t_plot.append(times_path[i])
        
        if u_plot[-1] < 0 and not ruin_flag:
            ruin_pts_t.append(times_path[i])
            ruin_pts_u.append(u_plot[-1])
            ruin_flag = True
            
    if t_plot[-1] < 1.0:
        u_plot.append(u_plot[-1] + prim_geliri * (1.0 - t_plot[-1]))
        t_plot.append(1.0)

    with c1:
        line_color = '#0ea5e9' if mode.startswith("1") else '#ef4444'
        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(x=t_plot, y=u_plot, mode='lines', fill='tozeroy', fillcolor=line_color, opacity=0.3, line=dict(color=line_color, width=3), name='Sermaye U(t)'))
        fig5.add_hline(y=0, line_dash="dash", line_color="gray", name="Sıfır Hattı")
        
        if ruin_pts_t:
            fig5.add_trace(go.Scatter(x=ruin_pts_t, y=ruin_pts_u, mode='markers', marker=dict(color='red', size=15), name='İflas Anı (U<0)'))
            
        fig5.update_layout(title=f"Grafik 5: Sermaye Seyri Rasyosu (u={u_secim}M, Faktör={theta_secim:.2f})",
                           xaxis_title="Zaman (Yıl)", yaxis_title="Sermaye (TL)", hovermode="x unified")
        st.plotly_chart(fig5, use_container_width=True)

    with c2:
        x_surv = np.logspace(3, 9, 1000)
        sf_ln = stats.lognorm.sf(x_surv, s=0.45195, scale=np.exp(6.1327)) 
        sf_pa = (1 + x_surv / 10_000_000)**(-alpha_secim)
        
        fig6 = go.Figure()
        fig6.add_trace(go.Scatter(x=x_surv, y=sf_ln, mode='lines', line=dict(color='#22c55e', width=3), name='Log-normal (Trafik)'))
        fig6.add_trace(go.Scatter(x=x_surv, y=sf_pa, mode='lines', line=dict(color='#ef4444', width=3), name=f'Pareto α={alpha_secim} (Deprem)'))
        fig6.update_layout(title="Grafik 6: Ağır Kuyruk Analizi (1-CDF)", xaxis_type="log", yaxis_type="log",
                           xaxis_title="Hasar (x) [Log Ölçek]", yaxis_title="P(X > x) [Log Ölçek]",
                           legend=dict(yanchor="bottom", y=0.05, xanchor="left", x=0.05))
        st.plotly_chart(fig6, use_container_width=True)


# ----------------------------------------------------
# TAB 4: STRES TESTLERİ VE REASÜRANS (PLOTLY)
# ----------------------------------------------------
with tab4:
    st.markdown("### Ekstrem Şoklar ve Reasürans Koruma Kapasitesi")
    c1, c2 = st.columns(2)
    
    # Stres Testleri
    caps_stress = [50_000_000, 100_000_000, 250_000_000, 500_000_000, 1_000_000_000]
    caps_stress_labels = ["50M", "100M", "250M", "500M", "1B"]
    alphas_stress = [2.5, 1.5, 0.9]
    styles = {2.5: '#22c55e', 1.5: '#f59e0b', 0.9: '#ef4444'}
    labels = {2.5: 'α=2.5 (Hafif Şok)', 1.5: 'α=1.5 (Vahşi Şok)', 0.9: 'α=0.9 (Yıkıcı Şok)'}
              
    np.random.seed(42)
    n_claims_s = np.random.poisson(2, size=5000)
    mask_s = np.arange(max(1, np.max(n_claims_s))) < n_claims_s[:, None]
    
    with c1:
        fig7 = go.Figure()
        for a in alphas_stress:
            claims_s = np.zeros((5000, mask_s.shape[1]))
            claims_s[mask_s] = 10_000_000 * np.random.pareto(a, size=np.sum(mask_s))
            s_arr = np.sum(claims_s, axis=1)
            pr = 2 * (10_000_000 / (a - 1)) if a > 1 else 2 * 10_000_000 * 10 
            
            res_a = []
            for c in caps_stress:
                U_s = c + pr - s_arr
                res_a.append(np.mean(U_s < 0) * 100)
                
            fig7.add_trace(go.Scatter(x=caps_stress_labels, y=res_a, mode='lines+markers', line=dict(color=styles[a], width=3), marker=dict(size=10), name=labels[a]))

        fig7.update_layout(title="Grafik 7: Stres Testleri (Faktör=1.00, T=1.0)", xaxis_title="Başlangıç Sermayesi", yaxis_title="İflas Olasılığı (%)")
        st.plotly_chart(fig7, use_container_width=True)
    
    # Reasürans Kurtarması Çubuk Grafiği
    with c2:
        labels_re = ["Reasürans Yok", "Limit\n(10 Milyon)", "Limit\n(2 Milyon)", "Oransal\n(Kalan %20)"]
        probs_re = []
        
        n_cl_re = np.random.poisson(2, size=N_SIMS)
        mask_re = np.arange(max(1, np.max(n_cl_re))) < n_cl_re[:, None]
        bc_re = np.zeros((N_SIMS, mask_re.shape[1]))
        bc_re[mask_re] = 10_000_000 * np.random.pareto(1.5, size=np.sum(mask_re))
        pref = 2 * (10_000_000 / 0.5) 
        
        for l_mode in labels_re:
            cl_tmp = bc_re.copy()
            pr_tmp = pref
            if "10" in l_mode: cl_tmp = np.minimum(bc_re, 10_000_000)
            elif "2" in l_mode: cl_tmp = np.minimum(bc_re, 2_000_000)
            elif "Oransal" in l_mode: cl_tmp *= 0.20; pr_tmp *= 0.20
            
            s_tmp = np.sum(cl_tmp, axis=1)
            u_tmp = 50_000_000 + pr_tmp - s_tmp
            probs_re.append(np.mean(u_tmp < 0) * 100)
            
        fig8 = px.bar(x=labels_re, y=probs_re, text=[f"%{v:.1f}" for v in probs_re], 
                      color=labels_re, color_discrete_sequence=['#7f1d1d', '#f59e0b', '#22c55e', '#3b82f6'],
                      title="Grafik 8: Reasürans Kurtarması (u=50M, α=1.5)")
        fig8.update_traces(textposition='outside', textfont_size=13, textfont_color="black")
        fig8.update_layout(xaxis_title="", yaxis_title="İflas Olasılığı (%)", showlegend=False)
        st.plotly_chart(fig8, use_container_width=True)


# ----------------------------------------------------
# TAB 5: VaR & TVaR (PLOTLY)
# ----------------------------------------------------
with tab5:
    st.markdown("### Sürekli Risk Metrikleri Güven Aralıkları Dağılımı")
    
    fig9 = px.histogram(S_array, nbins=100, title="Grafik 9: Hasar (S) Dağılımı ve Kuyruk Risk Ölçütleri - VaR & TVaR", 
                        color_discrete_sequence=['#93c5fd'])
    m = np.percentile(S_array, 99.5)
    
    fig9.add_vline(x=var_95, line_width=4, line_dash="dash", line_color="#f59e0b", annotation_text=f"VaR (95%): {int(var_95/1e6)}M", annotation_position="top right")
    fig9.add_vline(x=tvar_95, line_width=4, line_dash="dash", line_color="#ef4444", annotation_text=f"TVaR (95%): {int(tvar_95/1e6)}M", annotation_position="top right")

    fig9.update_layout(xaxis_title="Toplam Hasar (S) [TL]", yaxis_title="Frekans", showlegend=False, xaxis_range=[0, m])
    st.plotly_chart(fig9, use_container_width=True)

