import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

warnings.filterwarnings('ignore')

# -------------------------------------------------------------------------------------
# SİMÜLASYON PARAMETRELERİ (HİBRİT MODEL - SOLVENCY II DOĞAL AKIŞ)
# -------------------------------------------------------------------------------------
N_SIMS = 10000      
T = 1.0             

sns.set_theme(style="whitegrid", rc={"axes.spines.top": False, "axes.spines.right": False})

# =====================================================================================
# PORTFÖY A - USLU DÜNYA (LOG-NORMAL) - TRAFİK (TEORİK)
# =====================================================================================
lambda_a = 73_524  # Kesin kural
mu_a = 6.1327
sigma_a = 0.45195

capitals_theoretical_a = [50_000_000, 75_000_000, 80_000_000, 90_000_000, 100_000_000, 125_000_000, 150_000_000, 175_000_000, 200_000_000]
factors_theoretical_a = [1.00, 1.25, 1.50, 1.75, 1.80]
base_values_a = [0.6995, 0.5492, 0.5192, 0.4591, 0.3990, 0.2487, 0.0985, 0.0000, 0.0000]

# Teorik Matrisin Üretilmesi (Satır: i, Sütun: j -> Değer: Base[i] / Faktör[j])
ruin_matrix_a_theoretical = np.zeros((len(capitals_theoretical_a), len(factors_theoretical_a)))
for i in range(len(capitals_theoretical_a)):
    for j in range(len(factors_theoretical_a)):
        val = base_values_a[i] / factors_theoretical_a[j]
        # Eğer iflas olasılığı zaten teorik olarak 0 ise veya çok küçükse sifrila (tablodaki gibi). Aksi takdirde max(0, val)
        ruin_matrix_a_theoretical[i, j] = max(0, val)

# =====================================================================================
# PORTFÖY B - VAHŞİ DÜNYA (PARETO) - DEPREM (MONTE CARLO, T=1.0)
# =====================================================================================
lambda_b = 2  # Kesin kural
alpha_b = 1.5
scale_b = 10_000_000

E_X_b = scale_b / (alpha_b - 1)
expected_loss_B = lambda_b * E_X_b

def simulate_portfolio_B(capitals, factors, n_sims=N_SIMS, alpha=alpha_b):
    ruin_matrix = np.zeros((len(capitals), len(factors)))
    n_claims = np.random.poisson(lambda_b * T, size=n_sims)
    max_k = np.max(n_claims) if np.max(n_claims) > 0 else 1
    
    mask = np.arange(max_k) < n_claims[:, None]
    
    times = np.random.uniform(0, T, size=(n_sims, max_k))
    times[~mask] = T
    times.sort(axis=1)
    
    claims = np.zeros((n_sims, max_k))
    valid_counts = np.sum(mask)
    
    # Pareto Tip II (Lomax)
    claims[mask] = scale_b * np.random.pareto(alpha, size=valid_counts)
    
    cum_claims = np.cumsum(claims, axis=1)
    
    P_base_E_X = scale_b / (1.5 - 1)
    P_base_Expected = lambda_b * P_base_E_X
    
    for j, f in enumerate(factors):
        P = P_base_Expected * f
        surplus_base = P * times - cum_claims
        min_surplus_base = np.min(surplus_base, axis=1)
        
        for i, u in enumerate(capitals):
            ruined = np.sum((u + min_surplus_base) < 0)
            ruin_matrix[i, j] = ruined / n_sims
            
    return ruin_matrix

# =====================================================================================
# MATRİS HESAPLAMALARI
# =====================================================================================
caps_heatmap = capitals_theoretical_a
factors_heatmap = factors_theoretical_a
factors_labels = [f"{f:.2f}" for f in factors_heatmap]
caps_labels = [f"{int(c/1e6)}M" for c in caps_heatmap]

np.random.seed(42)
rm_b = simulate_portfolio_B(caps_heatmap, factors_heatmap, n_sims=N_SIMS)


# =====================================================================================
# BÖLÜM 1: GİRDİ ANALİZİ VE İFLAS MATRİSLERİ (Figür 1 - 2x2 Subplot)
# =====================================================================================
fig1, axs1 = plt.subplots(2, 2, figsize=(15, 8.5))
fig1.subplots_adjust(left=0.08, right=0.95, top=0.88, bottom=0.1, wspace=0.35, hspace=0.45)
fig1.suptitle('BÖLÜM 1: GİRDİ ANALİZİ VE İFLAS MATRİSLERİ (HİBRİT MODEL)', fontsize=16, fontweight='bold')

# Grafik 1: DASK Poliçe Sayısı Dağılımı
dask_mean = 5_728_440
dask_policies = np.random.normal(loc=dask_mean, scale=np.sqrt(dask_mean), size=100000)
sns.histplot(dask_policies, bins=50, kde=True, color='skyblue', ax=axs1[0, 0], edgecolor='black')
axs1[0, 0].set_title('Grafik 1: DASK Poliçe Sayısı\nDağılımı ($\\lambda=5.7M$)', fontsize=13, fontweight='bold')
axs1[0, 0].set_xlabel('Poliçe Sayısı', fontsize=11)
axs1[0, 0].set_ylabel('Olasılık Yoğunluk', fontsize=11)

# Grafik 2: Hasar Frekansları Karşılaştırması
bars_freq = axs1[0, 1].bar(['Trafik\n(Log-normal)', 'Deprem\n(Pareto)'], [lambda_a, lambda_b], color=['#2ca02c', '#d62728'], edgecolor='black')
axs1[0, 1].set_yscale('log')
axs1[0, 1].set_title('Grafik 2: Yıllık Olay (Hasar/Afet)\nFrekansları', fontsize=13, fontweight='bold')
axs1[0, 1].set_ylabel('Frekans (Log Ölçek)', fontsize=11)
for bar in bars_freq:
    yval = bar.get_height()
    axs1[0, 1].text(bar.get_x() + bar.get_width()/2, yval*1.3, f"{yval:,.0f}".replace(',', '.'), ha='center', va='bottom', fontsize=11, fontweight='bold')

# Grafik 3: Uslu Dünya (Lognormal) Teorik İflas Matrisi (Bulut ve Erdemir)
sns.heatmap(ruin_matrix_a_theoretical, annot=True, fmt=".4f", cmap="YlGn_r", 
            xticklabels=factors_labels, 
            yticklabels=caps_labels, 
            ax=axs1[1, 0], annot_kws={"size": 10, "weight": "bold"})
axs1[1, 0].set_title('Grafik 3: Çizelge 2 Teorik Log-normal Heatmap', fontsize=13, fontweight='bold')
axs1[1, 0].set_xlabel('Güvenlik Yükleme Faktörü ($1+\\theta$)', fontsize=11)
axs1[1, 0].set_ylabel('Başlangıç Sermayesi ($u$)', fontsize=11)
axs1[1, 0].tick_params(axis='y', rotation=0)

# Grafik 4: Vahşi Dünya İstokus (Pareto) Simülasyon İflas Matrisi (T=1.0)
sns.heatmap(rm_b, annot=True, fmt=".4f", cmap="Reds", 
            xticklabels=factors_labels, 
            yticklabels=caps_labels, 
            ax=axs1[1, 1], annot_kws={"size": 10, "weight": "bold"})
axs1[1, 1].set_title('Grafik 4: Saf Risk Pareto Monte Carlo Heatmap (T=1.0)', fontsize=13, fontweight='bold')
axs1[1, 1].set_xlabel('Güvenlik Yükleme Faktörü ($1+\\theta$)', fontsize=11)
axs1[1, 1].set_ylabel('Başlangıç Sermayesi ($u$)', fontsize=11)
axs1[1, 1].tick_params(axis='y', rotation=0)

plt.tight_layout(rect=[0, 0.05, 1, 0.93], h_pad=5.0, w_pad=4.0)


# =====================================================================================
# BÖLÜM 2: TEZ ANATOMİSİ VE ÇIKTILAR (Figür 2 - 2x3 Subplot)
# =====================================================================================
# 15.6 inç laptop ekranına tam oturacak yatay pano ölçüsü (en:16, boy:9 orantısı dikkate alındı)
fig2, axs2 = plt.subplots(2, 3, figsize=(16, 9))
fig2.subplots_adjust(left=0.06, right=0.98, top=0.88, bottom=0.12, wspace=0.35, hspace=0.45)
fig2.suptitle('BÖLÜM 2: TEZ ANATOMİSİ VE ÇIKTILAR (HİBRİT MODEL)', fontsize=16, fontweight='bold')

# Grafik 2.1: Sample Path / Simülasyon Motoru (Adım 1)
ruin_found = False
np.random.seed(110) 
while not ruin_found:
    n_cl_path = np.random.poisson(lambda_b)
    if n_cl_path == 0: continue
    times_path = np.sort(np.random.uniform(0, 1, n_cl_path))
    claims_path = scale_b * np.random.pareto(1.5, n_cl_path)
    P_path = expected_loss_B * 1.25 # Faktör = 1.25
    
    t_plot = [0]
    u_plot = [50_000_000]
    ruin_t, ruin_u = None, None
    ruin_found_path = False
    
    for tc, c in zip(times_path, claims_path):
        dt_step = tc - t_plot[-1]
        u_plot.append(u_plot[-1] + P_path * dt_step)
        t_plot.append(tc)
        
        u_plot.append(u_plot[-1] - c)
        t_plot.append(tc)
        
        if u_plot[-1] < 0 and ruin_t is None:
            ruin_t = tc
            ruin_u = u_plot[-1]
            ruin_found_path = True
            
    if ruin_found_path:
        ruin_found = True

if t_plot[-1] < 1.0:
    u_plot.append(u_plot[-1] + P_path * (1.0 - t_plot[-1]))
    t_plot.append(1.0)

axs2[0, 0].plot(t_plot, u_plot, color='navy', lw=2, label='U(t)')
axs2[0, 0].scatter([ruin_t], [ruin_u], color='red', s=80, zorder=5, label='İflas Anı (U<0)')
axs2[0, 0].axhline(0, color='black', linestyle='--', lw=1.5)
axs2[0, 0].set_title('Grafik 1: Sample Path\n(u=50M, Faktör=1.25, Pareto $\\alpha=1.5$)', fontsize=12, fontweight='bold')
axs2[0, 0].set_ylabel('Sermaye', fontsize=11)
axs2[0, 0].set_xlabel('Zaman (Yıl)', fontsize=11)
axs2[0, 0].legend(fontsize=9, loc='upper right')


# Grafik 2.2: Teorik Validasyon Bar Chart (Faktör = 1.00)
# base_values_a dizisi = Faktör 1.00 için [50M, 75M, 80M, 90M, 100M, 125M, 150M, 175M, 200M] p değerleri
rm_a_val = np.array(base_values_a) * 100

bars_valid = axs2[0, 1].bar(caps_labels, rm_a_val, color='lightseagreen', edgecolor='black')
axs2[0, 1].set_title('Grafik 2: Teorik Validasyon\n(Faktör=1.00, Çizelge 2)', fontsize=12, fontweight='bold')
axs2[0, 1].set_ylabel('İflas Olasılığı (%)', fontsize=11)
axs2[0, 1].set_xlabel('Başlangıç Sermayesi ($u$)', fontsize=11)
axs2[0, 1].tick_params(axis='x', rotation=45, labelsize=9)

for bar in bars_valid:
    yval = bar.get_height()
    axs2[0, 1].text(bar.get_x() + bar.get_width()/2, yval + 1, f"%{yval:.1f}", ha='center', fontweight='bold', fontsize=9, rotation=45)


# Grafik 2.3: Ağır Kuyruk Analizi (Survival İşlevleri)
x_surv = np.logspace(3, 9, 1000)
sf_ln = stats.lognorm.sf(x_surv, s=sigma_a, scale=np.exp(mu_a)) 
sf_pa = (1 + x_surv / scale_b)**(-1.5)

axs2[0, 2].loglog(x_surv, sf_ln, label='Log-normal', color='green', lw=2)
axs2[0, 2].loglog(x_surv, sf_pa, label='Pareto $\\alpha=1.5$', color='red', lw=2)
axs2[0, 2].set_title('Grafik 3: Ağır Kuyruk\nAnalizi (1-CDF)', fontsize=12, fontweight='bold')
axs2[0, 2].set_xlabel('Hasar ($x$) [Log Ölçek]', fontsize=11)
axs2[0, 2].set_ylabel('P(X > x) [Log Ölçek]', fontsize=11)
axs2[0, 2].legend(fontsize=9, loc='lower left')


# Grafik 2.4: Stres Testleri (Faktör = 1.00, Pareto T=1.0)
caps_stress = [50_000_000, 100_000_000, 250_000_000, 500_000_000, 1_000_000_000]
caps_stress_labels = [f"{int(c/1e6)}M" if c < 1e9 else "1B" for c in caps_stress]
alphas_stress = [2.5, 1.5, 0.9]
styles = {2.5: {'color': 'green', 'marker': 'o', 'label': '$\\alpha=2.5$ (Hafif)'},
          1.5: {'color': 'orange', 'marker': 's', 'label': '$\\alpha=1.5$ (Vahşi)'},
          0.9: {'color': 'red', 'marker': '^', 'label': '$\\alpha=0.9$ (Yıkıcı)'}}

for a in alphas_stress:
    res = simulate_portfolio_B(caps_stress, factors=[1.00], n_sims=N_SIMS, alpha=a)[:, 0] * 100
    axs2[1, 0].plot(caps_stress_labels, res, color=styles[a]['color'], marker=styles[a]['marker'], lw=2, markersize=6, label=styles[a]['label'])
axs2[1, 0].set_title('Grafik 4: Stres Testleri\n(Faktör=1.00, T=1.0)', fontsize=12, fontweight='bold')
axs2[1, 0].set_ylabel('İflas Olasılığı (%)', fontsize=11)
axs2[1, 0].set_xlabel('Başlangıç Sermayesi', fontsize=11)
axs2[1, 0].tick_params(axis='x', rotation=45, labelsize=9)
axs2[1, 0].legend(fontsize=9, loc='upper right')


# Grafik 2.5: Reasürans Stratejileri (Stop-Loss ve Oransal)
labels_re = ["Korumasız", "Limit 10M", "Limit 25M", "Limit 40M", "Oransal\n(%80 Devir)"]
probs_re = []

np.random.seed(99)
n_cl_re = np.random.poisson(lambda_b * T, size=N_SIMS)
max_k_re = np.max(n_cl_re) if np.max(n_cl_re) > 0 else 1
mask_re = np.arange(max_k_re) < n_cl_re[:, None]

# Zamanları üretme (Aynı kalsın)
t_re = np.random.uniform(0, T, size=(N_SIMS, max_k_re))
t_re[~mask_re] = T
t_re.sort(axis=1)

base_claims_re = np.zeros((N_SIMS, max_k_re))
valid_counts_re = np.sum(mask_re)
base_claims_re[mask_re] = scale_b * np.random.pareto(1.5, size=valid_counts_re)

P_base_re = expected_loss_B * 1.0 # Faktör = 1.00
u_re_start = 50_000_000

for label in labels_re:
    if label == "Korumasız":
        claims = base_claims_re.copy()
        P_net = P_base_re
        
    elif label == "Limit 10M":
        claims = np.minimum(base_claims_re, 10_000_000)
        P_net = P_base_re 
        
    elif label == "Limit 25M":
        claims = np.minimum(base_claims_re, 25_000_000)
        P_net = P_base_re
        
    elif label == "Limit 40M":
        claims = np.minimum(base_claims_re, 40_000_000)
        P_net = P_base_re
        
    elif label == "Oransal\n(%80 Devir)":
        # Oransal reasüransta riskin ve primin %80'i devredilir, şirkete %20'si kalır.
        claims = base_claims_re * 0.20
        P_net = P_base_re * 0.20

    # O simülasyon stratejisi için iflas oranını hesapla
    S_array_re = np.sum(claims, axis=1)
    U_end_re = u_re_start + P_net - S_array_re
    iflas_orani_re = np.mean(U_end_re < 0) * 100
    probs_re.append(iflas_orani_re)

# Sütun grafiğini çizme
bars_re = axs2[1, 1].bar(labels_re, probs_re, color=['darkred', 'forestgreen', 'mediumseagreen', 'orange', 'purple'], edgecolor='black')
axs2[1, 1].set_title('Grafik 5: Reasürans Stratejileri (u=50M, Faktör=1.00)', fontsize=11, fontweight='bold')
axs2[1, 1].set_ylabel('İflas Olasılığı (%)', fontsize=10)
axs2[1, 1].tick_params(axis='x', labelsize=9) # Uzun etiketler sığsın diye

# Barların üstüne iflas oranlarını yazdırma
for bar in bars_re:
    yval = bar.get_height()
    axs2[1, 1].text(bar.get_x() + bar.get_width()/2, yval + 0.3, f"%{yval:.1f}", ha='center', fontweight='bold', fontsize=10)


# Grafik 2.6: Risk Metrikleri - VaR ve TVaR
S_array = np.sum(base_claims_re, axis=1)
var_95 = np.percentile(S_array, 95)
tvar_95 = np.mean(S_array[S_array >= var_95]) if len(S_array[S_array >= var_95]) > 0 else var_95

sns.histplot(S_array, bins=100, color='lightsteelblue', edgecolor='black', ax=axs2[1, 2], kde=False)
axs2[1, 2].axvline(var_95, color='orange', linestyle='--', lw=2, label=f'VaR (%95):\n{int(var_95/1e6)}M')
axs2[1, 2].axvline(tvar_95, color='red', linestyle='--', lw=2, label=f'TVaR (%95):\n{int(tvar_95/1e6)}M')
axs2[1, 2].set_title('Grafik 6: VaR ve TVaR\nKuyruğu', fontsize=12, fontweight='bold')
axs2[1, 2].set_xlabel('Toplam Hasar (S)', fontsize=11)
axs2[1, 2].set_ylabel('Frekans', fontsize=11)
axs2[1, 2].set_xlim(0, np.percentile(S_array, 99.5)) 
axs2[1, 2].legend(fontsize=9, loc='upper right')

# Sadece grafik kaydetme
plt.savefig("simulasyon_gosterge_panelleri_hibrit.png", dpi=300)
plt.show()
