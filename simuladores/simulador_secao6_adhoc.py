"""
============================================================
SEÇÃO 6 — TERCEIRA SOLUÇÃO: REDES AD-HOC COM SELEÇÃO ÓTIMA
DE RELAYS
Projeto: Cidade de 1 Milhão de Habitantes — UFABC
============================================================
Cenário: Zona de sombra rural/periférica (6×6 km)
  - 4 ERBs âncora nas bordas (cobertura parcial)
  - Usuários concentrados na área central (shadow zone)
  - Relays móveis (D2D Sidelink 3GPP) e fixos (postes)

Modelo de propagação:
  Macro (ERB→relay):   700 MHz, n=3.5, σ=8dB   [ITU-R P.1411]
  D2D  (relay→user):   2.4 GHz, n=2.5, σ=4dB   [Jamshed et al. 2024]

BER: QPSK/AWGN — BER = 0.5·erfc(√SNR)          [Proakis, 2008]
Relay: seleção por max[min(SINR_h1, SINR_h2)] × f(bateria)
       [Khan et al. 2019]
============================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from scipy.special import erfc
import pandas as pd
import os, warnings
warnings.filterwarnings('ignore')

np.random.seed(42)  # Reprodutibilidade garantida

# ============================================================
# 1. PARÂMETROS DO CENÁRIO
# ============================================================
AREA_KM        = 6           # 6×6 km (zona periférica / rural)
GRID_RES       = 120         # grade 120×120 pontos de avaliação
N_USUARIOS     = 150         # usuários na zona de sombra central
N_RELAYS_MOB   = 60          # relays móveis (smartphones D2D)
N_RELAYS_FIXOS = 25          # relays fixos (postes de iluminação pública)
N_ERB_ANCORA   = 4           # ERBs âncora nas bordas do cenário

# --- Modelo Macro: ERB → relay (700 MHz / LTE Rural) ---
FREQ_MACRO     = 700e6
C              = 3e8
LAMBDA_MACRO   = C / FREQ_MACRO
PL0_MACRO      = 20 * np.log10(4 * np.pi * 1 / LAMBDA_MACRO)   # ≈ 29.3 dB
N_MACRO        = 3.5         # expoente urbano-suburbano
SIGMA_MACRO    = 8.0         # shadowing (dB)
P_TX_ERB_DBM   = 46.0        # Potência ERB (dBm) — tipicamente 40 W EIRP

# --- Modelo D2D: relay → usuário (2.4 GHz Sidelink 3GPP) ---
FREQ_D2D       = 2.4e9
LAMBDA_D2D     = C / FREQ_D2D
PL0_D2D        = 20 * np.log10(4 * np.pi * 1 / LAMBDA_D2D)     # ≈ 40.1 dB
N_D2D          = 2.5         # expoente D2D (linha de visada parcial)
SIGMA_D2D      = 4.0         # shadowing reduzido (curta distância)
P_TX_RELAY_MOB = 23.0        # Potência relay móvel (dBm) — 200 mW
P_TX_RELAY_FIX = 30.0        # Potência relay fixo (dBm) — 1 W

# --- Ruído e limiar ---
N0_DBM_HZ     = -174.0
BW_HZ         = 20e6
RUIDO_DBM     = N0_DBM_HZ + 10 * np.log10(BW_HZ)   # ≈ -101 dBm
SINR_MIN_DB   = 3.0          # limiar mínimo QPSK (BER ≈ 5×10⁻³)

# --- Energia ---
P_TOTAL_ERB_W  = 1500.0      # consumo total 1 ERB 4G macro
P_SC_6G_W      = 300.0       # consumo 1 small cell 6G
P_ANC_6G_W     = 2000.0      # consumo 1 âncora 6G
P_RELAY_FIX_W  = 5.0         # consumo relay fixo (poste)
P_RELAY_MOB_W  = 0.25        # consumo relay móvel (D2D mode)

# ============================================================
# 2. POSICIONAMENTO DOS NÓS
# ============================================================
# ERBs âncora: 4 cantos (cobertura borda → centro = sombra)
erb_x = np.array([0.4, AREA_KM-0.4, 0.4,          AREA_KM-0.4])
erb_y = np.array([0.4, 0.4,          AREA_KM-0.4, AREA_KM-0.4])

# Usuários: concentrados na área central (zona de sombra)
# Distribuição gaussiana centrada no meio, σ≈1.2km
cx, cy = AREA_KM/2, AREA_KM/2
user_x = np.clip(np.random.normal(cx, 1.2, N_USUARIOS), 0.3, AREA_KM-0.3)
user_y = np.clip(np.random.normal(cy, 1.2, N_USUARIOS), 0.3, AREA_KM-0.3)

# Relays móveis: distribuição uniforme (em trânsito pela área)
relay_mob_x = np.random.uniform(0.5, AREA_KM-0.5, N_RELAYS_MOB)
relay_mob_y = np.random.uniform(0.5, AREA_KM-0.5, N_RELAYS_MOB)

# Bateria dos relays móveis: distribuição Beta realista
batt_mob = np.random.beta(2.5, 1.5, N_RELAYS_MOB)   # maioria com > 50%
BATT_LIMIAR = 0.20   # relay excluído se bateria < 20%

# Relays fixos: grade semi-regular (postes de iluminação)
fix_cols = 5; fix_rows = 5
relay_fix_x = np.tile(np.linspace(0.8, AREA_KM-0.8, fix_cols), fix_rows)
relay_fix_y = np.repeat(np.linspace(0.8, AREA_KM-0.8, fix_rows), fix_cols)
relay_fix_x += np.random.uniform(-0.2, 0.2, N_RELAYS_FIXOS)
relay_fix_y += np.random.uniform(-0.2, 0.2, N_RELAYS_FIXOS)

# Combinar relays
all_rx  = np.concatenate([relay_mob_x, relay_fix_x])
all_ry  = np.concatenate([relay_mob_y, relay_fix_y])
all_ptx = np.concatenate([
    np.full(N_RELAYS_MOB, P_TX_RELAY_MOB),
    np.full(N_RELAYS_FIXOS, P_TX_RELAY_FIX)
])
all_batt = np.concatenate([batt_mob, np.ones(N_RELAYS_FIXOS)])

# ============================================================
# 3. FUNÇÕES DE PROPAGAÇÃO
# ============================================================
def pl_macro(dist_m):
    """Path loss macro (700MHz, n=3.5) com shadowing."""
    d = np.maximum(dist_m, 1.0)
    shadow = np.random.normal(0, SIGMA_MACRO, np.shape(d))
    return PL0_MACRO + 10 * N_MACRO * np.log10(d) + shadow

def pl_d2d(dist_m):
    """Path loss D2D Sidelink (2.4GHz, n=2.5) com shadowing reduzido."""
    d = np.maximum(dist_m, 1.0)
    shadow = np.random.normal(0, SIGMA_D2D, np.shape(d))
    return PL0_D2D + 10 * N_D2D * np.log10(d) + shadow

def km_to_m(x1, y1, x2, y2):
    return np.sqrt((x1-x2)**2 + (y1-y2)**2) * 1000  # km → m

def sinr_macro(p_tx_dbm, dist_m):
    return p_tx_dbm - pl_macro(dist_m) - RUIDO_DBM

def sinr_d2d(p_tx_dbm, dist_m):
    return p_tx_dbm - pl_d2d(dist_m) - RUIDO_DBM

# ============================================================
# 4. COBERTURA DIRETA (sem relay)
# ============================================================
sinr_direto = np.zeros(N_USUARIOS)
for i in range(N_USUARIOS):
    s_list = [sinr_macro(P_TX_ERB_DBM, km_to_m(user_x[i], user_y[i], erb_x[j], erb_y[j]))
              for j in range(N_ERB_ANCORA)]
    sinr_direto[i] = max(s_list)

cob_direta = sinr_direto >= SINR_MIN_DB
n_cob_dir  = cob_direta.sum()
n_sem_cob  = (~cob_direta).sum()
pct_dir    = cob_direta.mean() * 100
print(f"Cobertura direta:     {pct_dir:.1f}%  ({n_cob_dir} usuários)")
print(f"Sem cobertura:        {100-pct_dir:.1f}%  ({n_sem_cob} usuários)")

# ============================================================
# 5. SELEÇÃO ÓTIMA DE RELAY
# ============================================================
sinr_relay_out = sinr_direto.copy()
relay_sel = np.full(N_USUARIOS, -1)
sinr_hop1_reg = np.zeros(N_USUARIOS)
sinr_hop2_reg = np.zeros(N_USUARIOS)

for i in range(N_USUARIOS):
    if cob_direta[i]:
        continue    # já tem cobertura direta

    melhor_score = -np.inf
    melhor_idx = -1

    for k in range(len(all_rx)):
        # Filtro de bateria
        if all_batt[k] < BATT_LIMIAR and k < N_RELAYS_MOB:
            continue

        # Hop 1: melhor ERB → relay k (enlace macro)
        sinr_h1_list = [sinr_macro(P_TX_ERB_DBM,
                        km_to_m(erb_x[j], erb_y[j], all_rx[k], all_ry[k]))
                        for j in range(N_ERB_ANCORA)]
        sinr_h1 = max(sinr_h1_list)
        if sinr_h1 < SINR_MIN_DB - 5:   # relay não tem cobertura útil
            continue

        # Hop 2: relay k → usuário i (enlace D2D)
        d_ru = km_to_m(all_rx[k], all_ry[k], user_x[i], user_y[i])
        sinr_h2 = sinr_d2d(all_ptx[k], d_ru)

        # SINR efetiva 2 saltos = gargalo
        sinr_e2e = min(sinr_h1, sinr_h2)

        # Score: prioriza SINR e bateria disponível
        f_batt = all_batt[k] if k < N_RELAYS_MOB else 1.0
        score  = sinr_e2e + 4 * np.log10(max(f_batt, 0.01))

        if score > melhor_score:
            melhor_score = score
            melhor_idx   = k
            sinr_hop1_reg[i] = sinr_h1
            sinr_hop2_reg[i] = sinr_h2

    if melhor_idx >= 0:
        sinr_relay_out[i] = min(sinr_hop1_reg[i], sinr_hop2_reg[i])
        relay_sel[i] = melhor_idx

cob_relay  = sinr_relay_out >= SINR_MIN_DB
pct_relay  = cob_relay.mean() * 100
ganho_pp   = pct_relay - pct_dir
relays_ativos = np.unique(relay_sel[relay_sel >= 0])
n_cobertos_relay = ((~cob_direta) & cob_relay).sum()
n_ainda_sem  = ((~cob_direta) & (~cob_relay)).sum()

print(f"Cobertura com relay:  {pct_relay:.1f}%  (ganho: +{ganho_pp:.1f} p.p.)")
print(f"Usuários resgatados:  {n_cobertos_relay}")
print(f"Relays ativados:      {len(relays_ativos)} de {len(all_rx)}")

# ============================================================
# 6. BER — QPSK / AWGN
# ============================================================
def ber_qpsk(snr_db_arr):
    snr = 10**(np.asarray(snr_db_arr)/10)
    snr = np.maximum(snr, 1e-10)
    return 0.5 * erfc(np.sqrt(snr))

ber_dir   = ber_qpsk(sinr_direto)
ber_rel   = ber_qpsk(sinr_relay_out)
ber_dir_m = float(ber_dir.mean())
ber_rel_m = float(ber_rel.mean())

msk_sem = ~cob_direta
ber_sem_antes  = float(ber_dir[msk_sem].mean())
ber_sem_depois = float(ber_rel[msk_sem].mean())
sinr_sem_antes = float(sinr_direto[msk_sem].mean())
sinr_sem_depois= float(sinr_relay_out[msk_sem].mean())

print(f"\nBER médio (todos, antes):  {ber_dir_m:.2e}")
print(f"BER médio (todos, depois): {ber_rel_m:.2e}")
print(f"BER zona sombra (antes):   {ber_sem_antes:.2e}  | SINR={sinr_sem_antes:.1f}dB")
print(f"BER zona sombra (depois):  {ber_sem_depois:.2e} | SINR={sinr_sem_depois:.1f}dB")

# Curvas BER vs SNR para o gráfico
snr_x = np.linspace(-5, 25, 300)
ber_curva_dir = ber_qpsk(snr_x)
ber_curva_rel = ber_qpsk(snr_x - 1.5)   # penalidade 2 saltos ≈ 1.5 dB

# ============================================================
# 7. CONSUMO ENERGÉTICO — 3 SOLUÇÕES
# ============================================================
E_4G_KW   = 305 * P_TOTAL_ERB_W / 1000
E_6G_KW   = (5225 * P_SC_6G_W + 62 * P_ANC_6G_W) / 1000
# Ad-Hoc híbrida: 153 ERBs 4G + 3125 SCs 6G + 62 âncoras + 100 relays fixos
E_AH_KW   = (153*P_TOTAL_ERB_W + 3125*P_SC_6G_W + 62*P_ANC_6G_W + 100*P_RELAY_FIX_W) / 1000
eco_6g    = (1 - E_AH_KW/E_6G_KW)*100
eco_4g    = (E_AH_KW/E_4G_KW - 1)*100

print(f"\nEnergia 4G:     {E_4G_KW:.1f} kW")
print(f"Energia 6G:     {E_6G_KW:.1f} kW")
print(f"Energia Ad-Hoc: {E_AH_KW:.1f} kW  ({eco_6g:.0f}% abaixo do 6G puro)")

# ============================================================
# 8. MAPA DE COBERTURA — GRADE 120×120
# ============================================================
xi = np.linspace(0, AREA_KM, GRID_RES)
yi = np.linspace(0, AREA_KM, GRID_RES)
Xg, Yg = np.meshgrid(xi, yi)

# Cobertura direta
cob_dir_grid = np.full((GRID_RES, GRID_RES), -np.inf)
for j in range(N_ERB_ANCORA):
    d_g = km_to_m(Xg, Yg, erb_x[j], erb_y[j])
    s_g = sinr_macro(P_TX_ERB_DBM, d_g)
    cob_dir_grid = np.maximum(cob_dir_grid, s_g)

# Cobertura com relay
cob_rel_grid = cob_dir_grid.copy()
for k in range(len(all_rx)):
    if all_batt[k] < BATT_LIMIAR and k < N_RELAYS_MOB:
        continue
    # hop1: melhor ERB → relay k
    sinr_h1_k = max(sinr_macro(P_TX_ERB_DBM, km_to_m(erb_x[j], erb_y[j], all_rx[k], all_ry[k]))
                    for j in range(N_ERB_ANCORA))
    if sinr_h1_k < SINR_MIN_DB - 5:
        continue
    # hop2: relay k → grade
    d_rg   = km_to_m(Xg, Yg, all_rx[k], all_ry[k])
    sinr_h2_g = sinr_d2d(all_ptx[k], d_rg)
    sinr_e2e_g = np.minimum(sinr_h1_k, sinr_h2_g)
    cob_rel_grid = np.maximum(cob_rel_grid, sinr_e2e_g)

mask_dir  = cob_dir_grid >= SINR_MIN_DB
mask_rel  = cob_rel_grid >= SINR_MIN_DB
mask_gain = mask_rel & ~mask_dir

pct_dir_g  = mask_dir.mean()*100
pct_rel_g  = mask_rel.mean()*100
pct_gain_g = mask_gain.mean()*100
print(f"\nCobertura direta (grade):     {pct_dir_g:.1f}%")
print(f"Cobertura c/ relay (grade):   {pct_rel_g:.1f}%")
print(f"Área adicional coberta:        +{pct_gain_g:.1f} p.p.")

# ============================================================
# 9. FIGURAS
# ============================================================
COR_4G    = '#1A6BAF'
COR_6G    = '#7B2D8B'
COR_ADHOC = '#1A7A4A'
COR_FUNDO = '#F7F7F2'
BOX       = dict(boxstyle='round,pad=0.35', linewidth=1.4)


OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'figuras') if not os.path.exists('/content') else ('/content/drive/MyDrive' if os.path.exists('/content/drive/MyDrive') else '/content')

cmap_cov  = LinearSegmentedColormap.from_list("cov", ['#922B21','#E67E22','#27AE60'], N=256)
cmap_g    = LinearSegmentedColormap.from_list("g",   ['#1A252F','#C0392B','#F39C12','#27AE60'], N=256)
SUBTITULO = (f"Zona de sombra {AREA_KM}×{AREA_KM} km  |  {N_USUARIOS} usuários  |  "
             f"{N_RELAYS_MOB} relays móveis D2D  +  {N_RELAYS_FIXOS} relays fixos  |  "
             f"{N_ERB_ANCORA} ERBs âncora")

# ══════════════════════════════════════════════════════════════
# FIGURA 4 — MAPAS DE COBERTURA (3 painéis)
# ══════════════════════════════════════════════════════════════
fig4, axes4 = plt.subplots(1, 3, figsize=(22, 8), dpi=110, facecolor=COR_FUNDO)
fig4.suptitle(
    "Figura 4 — Mapas de Cobertura: Enlace Direto vs. Relay-Assistido\n" + SUBTITULO,
    fontsize=14, fontweight='bold', y=1.01)

# ── Painel A: sem relay
ax1 = axes4[0]
im1 = ax1.imshow(cob_dir_grid, cmap=cmap_cov, vmin=-10, vmax=25,
                 origin='lower', extent=[0,AREA_KM,0,AREA_KM], aspect='equal')
cb1 = plt.colorbar(im1, ax=ax1, shrink=0.88, pad=0.02)
cb1.set_label('SINR (dB)', fontsize=11); cb1.ax.tick_params(labelsize=10)
ax1.scatter(erb_x, erb_y, marker='*', c='white', s=400, zorder=10,
            edgecolors='black', lw=1.5, label='ERB âncora')
ax1.scatter(user_x[~cob_direta], user_y[~cob_direta],
            c='red', s=40, zorder=8, alpha=0.85, label=f'Sem cobertura ({n_sem_cob})')
ax1.scatter(user_x[cob_direta], user_y[cob_direta],
            c='lime', s=40, zorder=8, alpha=0.75, label=f'Com cobertura ({n_cob_dir})')
ax1.set_title(f"CENÁRIO A — Enlace Direto (sem relay)\n"
              f"Cobertura: {pct_dir:.1f}%  |  {n_sem_cob} usuários isolados",
              fontsize=12, fontweight='bold', color='#7B241C')
ax1.set_xlabel("Distância Leste-Oeste (km)", fontsize=11)
ax1.set_ylabel("Distância Norte-Sul (km)", fontsize=11)
ax1.legend(fontsize=10, loc='upper right', framealpha=0.92)
ax1.tick_params(labelsize=10)
# Anotação explicativa
ax1.annotate("ERBs cobrem apenas\nas bordas do cenário\n(zonas centrais = sombra)",
             xy=(AREA_KM/2, AREA_KM/2), xytext=(0.6, AREA_KM*0.6),
             fontsize=9.5, ha='left', color='white', fontweight='bold',
             bbox=dict(facecolor='#922B21', alpha=0.80, boxstyle='round,pad=0.4'),
             arrowprops=dict(arrowstyle='->', color='white', lw=1.8))

# ── Painel B: com relay
ax2 = axes4[1]
im2 = ax2.imshow(cob_rel_grid, cmap=cmap_cov, vmin=-10, vmax=25,
                 origin='lower', extent=[0,AREA_KM,0,AREA_KM], aspect='equal')
cb2 = plt.colorbar(im2, ax=ax2, shrink=0.88, pad=0.02)
cb2.set_label('SINR (dB)', fontsize=11); cb2.ax.tick_params(labelsize=10)
cob_ganhos = (~cob_direta) & cob_relay
ainda_sem  = (~cob_direta) & (~cob_relay)
relays_ativos = np.unique(relay_sel[relay_sel >= 0])
ax2.scatter(erb_x, erb_y, marker='*', c='white', s=400, zorder=10,
            edgecolors='black', lw=1.5, label='ERB âncora')
ax2.scatter(all_rx[relays_ativos], all_ry[relays_ativos],
            marker='^', c='cyan', s=70, edgecolors='black', lw=0.8, zorder=9,
            label=f'Relay ativo ({len(relays_ativos)} de {len(all_rx)})')
ax2.scatter(user_x[cob_ganhos], user_y[cob_ganhos],
            c='yellow', s=50, zorder=8, alpha=0.92,
            label=f'Resgatados pelo relay ({cob_ganhos.sum()})')
if ainda_sem.sum() > 0:
    ax2.scatter(user_x[ainda_sem], user_y[ainda_sem],
                c='red', s=40, zorder=8, alpha=0.7,
                label=f'Ainda isolados ({ainda_sem.sum()})')
ax2.set_title(f"CENÁRIO B — Com Seleção de Relay\n"
              f"Cobertura: {pct_relay:.1f}%  |  Ganho: +{ganho_pp:.1f} p.p.",
              fontsize=12, fontweight='bold', color=COR_ADHOC)
ax2.set_xlabel("Distância Leste-Oeste (km)", fontsize=11)
ax2.set_ylabel("Distância Norte-Sul (km)", fontsize=11)
ax2.legend(fontsize=10, loc='upper right', framealpha=0.92)
ax2.tick_params(labelsize=10)
ax2.annotate(f"Relays D2D preenchem\na zona de sombra\n({cob_ganhos.sum()} usuários resgatados)",
             xy=(AREA_KM/2, AREA_KM/2), xytext=(0.4, AREA_KM*0.55),
             fontsize=9.5, ha='left', color='black', fontweight='bold',
             bbox=dict(facecolor='yellow', alpha=0.85, boxstyle='round,pad=0.4'),
             arrowprops=dict(arrowstyle='->', color='#7D6608', lw=1.8))

# ── Painel C: mapa de ganho
ax3 = axes4[2]
ganho_grid = np.where(mask_gain, cob_rel_grid,
             np.where(mask_dir, 8.0, -15.0))
im3 = ax3.imshow(ganho_grid, cmap=cmap_g, origin='lower',
                 extent=[0,AREA_KM,0,AREA_KM], aspect='equal', vmin=-15, vmax=22)
cb3 = plt.colorbar(im3, ax=ax3, shrink=0.88, pad=0.02)
cb3.set_label('SINR (dB)', fontsize=11); cb3.ax.tick_params(labelsize=10)
ax3.scatter(erb_x, erb_y, marker='*', c='white', s=400, zorder=10,
            edgecolors='black', lw=1.5, label='ERB âncora')
ax3.scatter(all_rx, all_ry, marker='^', c='cyan', s=22, alpha=0.5,
            edgecolors='none', zorder=8, label=f'Relays candidatos ({len(all_rx)})')
ax3.set_title(f"MAPA DE GANHO — Área adicional habilitada pelos relays\n"
              f"+{pct_gain_g:.1f}% da área total coberta exclusivamente pela malha D2D",
              fontsize=12, fontweight='bold', color='#7D6608')
ax3.set_xlabel("Distância Leste-Oeste (km)", fontsize=11)
ax3.set_ylabel("Distância Norte-Sul (km)", fontsize=11)
leg3 = [mpatches.Patch(color='#27AE60', label=f'Nova área coberta (relay)  +{pct_gain_g:.1f}%'),
        mpatches.Patch(color='#F39C12', label='Cobertura limítrofe pelo relay'),
        mpatches.Patch(color='#5D6D7E', label='Cobertura direta pela ERB'),
        mpatches.Patch(color='#1A252F', label='Zona de sombra (sem cobertura)')]
ax3.legend(handles=leg3, fontsize=10, loc='upper right', framealpha=0.92)
ax3.tick_params(labelsize=10)

plt.tight_layout()
fig4.savefig(os.path.join(OUTPUT_DIR, 'fig4_mapas_cobertura.png'),
             dpi=120, bbox_inches='tight', facecolor=COR_FUNDO)
print("✔ Figura 4 salva: fig4_mapas_cobertura.png")
plt.close(fig4)

# ══════════════════════════════════════════════════════════════
# FIGURA 5 — BER vs SNR
# ══════════════════════════════════════════════════════════════
fig5, ax5 = plt.subplots(figsize=(14, 8), dpi=110, facecolor=COR_FUNDO)
fig5.suptitle("Figura 5 — BER Comparativo: Enlace Direto vs. Relay-Assistido\n" + SUBTITULO,
              fontsize=14, fontweight='bold', y=1.01)

ax5.semilogy(snr_x, ber_curva_dir, color=COR_4G, lw=3,
             label='Enlace direto — 1 salto  (QPSK / AWGN)')
ax5.semilogy(snr_x, ber_curva_rel, color=COR_ADHOC, lw=3, linestyle='--',
             label='Relay-assistido — 2 saltos  (penalidade ≈ 1,5 dB)')

ax5.axvline(SINR_MIN_DB, color='gray', linestyle=':', lw=2, alpha=0.85)
ax5.text(SINR_MIN_DB + 0.4, 0.35,
         f'Limiar mínimo\nQPSK ({SINR_MIN_DB} dB)', fontsize=11, color='#555')

# Ponto de operação: sem relay
ax5.scatter([sinr_sem_antes], [ber_qpsk(sinr_sem_antes)],
            s=180, c=COR_4G, zorder=10, edgecolors='black', lw=1.5, marker='o')
ax5.annotate(
    f"Zona de sombra — SEM relay\n"
    f"SINR médio: {sinr_sem_antes:.1f} dB\n"
    f"BER: {ber_sem_antes:.2e}  (canal inutilizável)",
    xy=(sinr_sem_antes, ber_qpsk(sinr_sem_antes)),
    xytext=(sinr_sem_antes - 11, ber_qpsk(sinr_sem_antes) * 8),
    fontsize=11, color=COR_4G, fontweight='bold',
    bbox=dict(facecolor='#EBF5FB', edgecolor=COR_4G, boxstyle='round,pad=0.5', lw=1.5),
    arrowprops=dict(arrowstyle='->', color=COR_4G, lw=2.0))

# Ponto de operação: com relay
ax5.scatter([sinr_sem_depois], [ber_qpsk(sinr_sem_depois)],
            s=180, c=COR_ADHOC, zorder=10, edgecolors='black', lw=1.5, marker='D')
ax5.annotate(
    f"Zona de sombra — COM relay\n"
    f"SINR médio: {sinr_sem_depois:.1f} dB\n"
    f"BER: {ber_sem_depois:.2e}  (redução de {ber_sem_antes/ber_sem_depois:.0f}×)",
    xy=(sinr_sem_depois, ber_qpsk(sinr_sem_depois)),
    xytext=(sinr_sem_depois - 9, ber_qpsk(sinr_sem_depois) * 200),
    fontsize=11, color=COR_ADHOC, fontweight='bold',
    bbox=dict(facecolor='#EAFAF1', edgecolor=COR_ADHOC, boxstyle='round,pad=0.5', lw=1.5),
    arrowprops=dict(arrowstyle='->', color=COR_ADHOC, lw=2.0))

# Faixas de referência de BER
ax5.axhspan(1e-3, 1, alpha=0.06, color='red')
ax5.axhspan(1e-6, 1e-3, alpha=0.06, color='orange')
ax5.axhspan(1e-9, 1e-6, alpha=0.06, color='green')
ax5.text(20, 2e-1, 'BER inaceitável\n(> 10⁻³)', fontsize=9.5, color='#C0392B', ha='right')
ax5.text(20, 3e-5, 'BER para voz (VoIP)', fontsize=9.5, color='#E67E22', ha='right')
ax5.text(20, 3e-8, 'BER para dados críticos', fontsize=9.5, color='#27AE60', ha='right')

ax5.set_xlim(-5, 25); ax5.set_ylim(1e-9, 1)
ax5.set_xlabel("SINR / Eb·N₀⁻¹  (dB)", fontsize=13)
ax5.set_ylabel("BER — Taxa de Erro de Bit", fontsize=13)
ax5.set_title("Modulação QPSK · Canal AWGN · Ref: Proakis (2008), Digital Communications, 5ª ed.",
              fontsize=11, style='italic')
ax5.legend(fontsize=12, loc='upper right')
ax5.grid(True, which='both', alpha=0.3)
ax5.set_facecolor('#FAFAFA')
ax5.spines[['top','right']].set_visible(False)
ax5.tick_params(labelsize=11)

plt.tight_layout()
fig5.savefig(os.path.join(OUTPUT_DIR, 'fig5_ber_comparativo.png'),
             dpi=120, bbox_inches='tight', facecolor=COR_FUNDO)
print("✔ Figura 5 salva: fig5_ber_comparativo.png")
plt.close(fig5)

# ══════════════════════════════════════════════════════════════
# FIGURA 6 — CONSUMO ENERGÉTICO + DISTRIBUIÇÃO DE SINR
# ══════════════════════════════════════════════════════════════
fig6, (ax6a, ax6b) = plt.subplots(1, 2, figsize=(18, 8), dpi=110, facecolor=COR_FUNDO)
fig6.suptitle("Figura 6 — Consumo Energético e Distribuição de SINR\n" + SUBTITULO,
              fontsize=14, fontweight='bold', y=1.01)

# ── Painel esquerdo: energia
nomes_e = ['4G Puro\n(305 ERBs)', '6G Puro\n(5.287 sites)', 'Ad-Hoc\nHíbrida']
vals_e  = [E_4G_KW, E_6G_KW, E_AH_KW]
cores_e = [COR_4G, COR_6G, COR_ADHOC]
bars_e  = ax6a.bar(nomes_e, vals_e, color=cores_e, edgecolor='white', lw=1.5, width=0.5, zorder=3)
for bar, val in zip(bars_e, vals_e):
    ax6a.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 18,
              f'{val:.0f} kW', ha='center', va='bottom',
              fontsize=13, fontweight='bold', color=bar.get_facecolor())

ax6a.annotate(
    f"Ad-Hoc é\n−{eco_6g:.0f}% vs 6G puro\ncom cobertura plena",
    xy=(2, E_AH_KW), xytext=(1.55, E_AH_KW + 280),
    fontsize=11, fontweight='bold', color=COR_ADHOC,
    bbox=dict(facecolor='#EAFAF1', edgecolor=COR_ADHOC, boxstyle='round,pad=0.45', lw=1.5),
    arrowprops=dict(arrowstyle='->', color=COR_ADHOC, lw=2.0))

# Composição da Ad-Hoc
ax6a.text(0.98, 0.98,
    f"Composição Ad-Hoc:\n"
    f"  {153} ERBs 4G ×  1.500 W  =  {153*1500/1000:.0f} kW\n"
    f"  3.125 SCs 6G ×  300 W  =  {3125*300/1000:.0f} kW\n"
    f"  62 âncoras  × 2.000 W  =  {62*2000/1000:.0f} kW\n"
    f"  100 relays fixos × 5 W  =  0,5 kW\n"
    f"  ─────────────────────────────\n"
    f"  Total:  {E_AH_KW:.1f} kW",
    transform=ax6a.transAxes, fontsize=9.5, va='top', ha='right', family='monospace',
    bbox=dict(facecolor='white', alpha=0.92, edgecolor='lightgray',
              boxstyle='round,pad=0.5', lw=1.2))

ax6a.set_title("Consumo Energético Total da Rede (kW contínuos)\n"
               "Comparativo das 3 soluções — rede completa (500 km²)",
               fontsize=12, fontweight='bold')
ax6a.set_ylabel("Megawatts (kW)", fontsize=12)
ax6a.set_ylim(0, max(vals_e)*1.38)
ax6a.grid(axis='y', alpha=0.3, zorder=0)
ax6a.set_facecolor('#FAFAFA')
ax6a.spines[['top','right']].set_visible(False)
ax6a.tick_params(labelsize=11)

# ── Painel direito: histograma SINR
bins_s = np.linspace(-18, 30, 55)
ax6b.hist(sinr_direto[~cob_direta], bins=bins_s, alpha=0.65, color=COR_4G,
          edgecolor='white', lw=0.5,
          label=f'Sem relay — {n_sem_cob} usuários isolados')
ax6b.hist(sinr_relay_out[~cob_direta], bins=bins_s, alpha=0.65, color=COR_ADHOC,
          edgecolor='white', lw=0.5,
          label=f'Com relay-assistido — mesmos {n_sem_cob} usuários')
ax6b.axvline(SINR_MIN_DB, color='red', lw=2.5, linestyle='--',
             label=f'Limiar QPSK ({SINR_MIN_DB} dB)')

# Anotações de SINR médio
ax6b.axvline(sinr_sem_antes, color=COR_4G, lw=1.5, linestyle=':')
ax6b.axvline(sinr_sem_depois, color=COR_ADHOC, lw=1.5, linestyle=':')
ax6b.text(sinr_sem_antes - 0.5, ax6b.get_ylim()[1]*0.01 + 1,
          f'Média sem relay\n{sinr_sem_antes:.1f} dB',
          fontsize=9.5, color=COR_4G, ha='right', fontweight='bold')
ax6b.text(sinr_sem_depois + 0.5, ax6b.get_ylim()[1]*0.01 + 1,
          f'Média com relay\n{sinr_sem_depois:.1f} dB',
          fontsize=9.5, color=COR_ADHOC, ha='left', fontweight='bold')

ax6b.set_xlabel("SINR (dB)", fontsize=13)
ax6b.set_ylabel("Número de usuários", fontsize=13)
ax6b.set_title("Distribuição de SINR — Antes e Após Seleção de Relay\n"
               "Usuários na zona de sombra periférica (sem cobertura direta)",
               fontsize=12, fontweight='bold')
ax6b.legend(fontsize=11); ax6b.grid(alpha=0.3); ax6b.set_facecolor('#FAFAFA')
ax6b.spines[['top','right']].set_visible(False)
ax6b.tick_params(labelsize=11)

# Caixa de ganho
ax6b.text(0.98, 0.98,
    f"Ganho de SINR:\n"
    f"  Antes:   {sinr_sem_antes:.1f} dB  (BER={ber_sem_antes:.1e})\n"
    f"  Depois: {sinr_sem_depois:.1f} dB  (BER={ber_sem_depois:.1e})\n"
    f"  Δ SINR: +{sinr_sem_depois - sinr_sem_antes:.1f} dB\n"
    f"  Redução BER: {ber_sem_antes/ber_sem_depois:.0f}×",
    transform=ax6b.transAxes, fontsize=10, va='top', ha='right', family='monospace',
    bbox=dict(facecolor='#EAFAF1', alpha=0.95, edgecolor=COR_ADHOC,
              boxstyle='round,pad=0.5', lw=1.5))

plt.tight_layout()
fig6.savefig(os.path.join(OUTPUT_DIR, 'fig6_energia_sinr.png'),
             dpi=120, bbox_inches='tight', facecolor=COR_FUNDO)
print("✔ Figura 6 salva: fig6_energia_sinr.png")
plt.close(fig6)

# ── Relatório final ───────────────────────────────────────────────────
print("\n" + "="*65)
print("RELATÓRIO — SEÇÃO 6: TERCEIRA SOLUÇÃO (AD-HOC)")
print("="*65)
print(f"""
COBERTURA:
  Enlace direto:        {pct_dir:.1f}%  ({n_sem_cob} usuários isolados)
  Com relay:            {pct_relay:.1f}%  (ganho: +{ganho_pp:.1f} p.p.)
  Área adicional:       +{pct_gain_g:.1f} p.p.  (grade {GRID_RES}×{GRID_RES})

BER (QPSK/AWGN — Proakis 2008):
  BER médio antes:      {ber_dir_m:.2e}
  BER médio depois:     {ber_rel_m:.2e}
  BER zona sombra antes:{ber_sem_antes:.2e}  (SINR={sinr_sem_antes:.1f} dB)
  BER zona sombra dep.: {ber_sem_depois:.2e}  (SINR={sinr_sem_depois:.1f} dB)

RELAYS:
  Total candidatos:     {len(all_rx)}
  Ativados:             {len(relays_ativos)}
  Usuários resgatados:  {n_cobertos_relay}
  Ainda sem cobertura:  {n_ainda_sem}

ENERGIA:
  4G puro:              {E_4G_KW:.1f} kW
  6G puro:              {E_6G_KW:.1f} kW
  Ad-Hoc híbrida:       {E_AH_KW:.1f} kW  (−{eco_6g:.0f}% vs 6G)
""")
print("="*65)
