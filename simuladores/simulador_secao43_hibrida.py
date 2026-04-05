"""
============================================================
SEÇÃO 4.3 — SOLUÇÃO HÍBRIDA 4G + 6G
Projeto de Comunicação: Cidade de 1 Milhão de Habitantes
UFABC — Núcleo de Tecnologia da Informação
============================================================
Conceito: arquitetura dual-layer que combina
  • 6G (sub-THz, small cells) nas zonas de ALTA e MÉDIA densidade
  • 4G (LTE macro) como camada de cobertura RURAL e de fallback

Métricas calculadas por zona:
  - Retardo (ms), Jitter (ms)
  - Vazão de pico (Gbps / Mbps)
  - BER (QPSK/AWGN, Proakis 2008)
  - SINR média por zona
  - CAPEX / OPEX / TCO 10 anos
  - Consumo energético (kW)

Comparativo final: 4G puro | 6G puro | Híbrida 4G+6G
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
# 1. PARÂMETROS GLOBAIS
# ============================================================
GRID_COLS, GRID_ROWS = 25, 20          # Grade 25×20 km = 500 km²
AREA_TOTAL = GRID_COLS * GRID_ROWS     # 500 km²

# ── Zonas (mesmas da Seção 4) ────────────────────────────────
AREA_ALTA  = 125   # km²  — Alta densidade (comercial/industrial)
AREA_MEDIA = 350   # km²  — Urbana média (residencial)
AREA_RURAL = 25    # km²  — Rural/periférica

# ── Parâmetros 4G ────────────────────────────────────────────
BW_4G      = 20e6          # 20 MHz
EFF_4G     = 5.0           # bits/s/Hz (LTE-A, 3GPP TR 36.814)
P_ERB_KW   = 1.5           # kW por ERB macro
CAPEX_ERB  = 500_000       # R$ por ERB
OPEX_ERB_A = 80_000        # R$ por ERB por ano

# ── Parâmetros 6G ────────────────────────────────────────────
BW_6G      = 2e9           # 2 GHz (sub-THz)
EFF_6G     = 30.0          # bits/s/Hz (ITU-R IMT-2030, projeção)
P_SC_KW    = 0.3           # kW por small cell
P_ANC_KW   = 2.0           # kW por âncora macro 6G
CAPEX_SC   = 150_000       # R$ por small cell
CAPEX_ANC  = 1_200_000     # R$ por âncora
OPEX_SC_A  = 25_000        # R$ por SC por ano
OPEX_ANC_A = 180_000       # R$ por âncora por ano

ANOS_TCO   = 10

# ── Densidades de sítios por zona ────────────────────────────
# 4G puro
BS4G_ALTA  = 1.0   # ERB/km²
BS4G_MEDIA = 0.5   # ERB/km²
BS4G_RURAL = 0.2   # ERB/km²

# 6G puro
SC6G_ALTA  = 25    # SC/km²
SC6G_MEDIA = 6     # SC/km²
ANC6G_ALTA = 0.5   # âncora/km²

# Híbrida: 6G apenas na zona de ALTA densidade
#           4G na zona MÉDIA e RURAL
# Racional: sub-THz economicamente justificado apenas onde
#           densidade > 4.000 hab/km² (ROI em < 3 anos)
HYB_SC_ALTA  = 25   # SC 6G/km² (zona alta — 3.125 SCs total)
HYB_SC_MEDIA = 0    # 4G na zona média (0 SCs 6G)
HYB_ANC_ALTA = 0.5  # âncoras 6G/km² (zona alta)
HYB_ERB_MEDIA= 0.5  # ERB 4G/km² (zona média — igual ao 4G puro)
HYB_ERB_RURAL= 0.2  # ERB 4G/km² (zona rural — fallback)

# ============================================================
# 2. CONSTRUÇÃO DO MAPA DE ZONAS
# ============================================================
zone_map = np.ones((GRID_ROWS, GRID_COLS), dtype=int)  # 1 = média
zone_map[4:14, 6:16] = 2   # alta densidade — centro comercial
zone_map[14:18, 3:8]  = 2  # polo industrial
zone_map[2:4, 18:21]  = 2  # polo tech
zone_map[14, 3]        = 1  # ajuste fino → 125 km² ✓
zone_map[0, :]         = 0  # rural (faixa norte)

n_alta  = int((zone_map == 2).sum())   # 125 km²
n_media = int((zone_map == 1).sum())   # 350 km²
n_rural = int((zone_map == 0).sum())   # 25 km²

# ============================================================
# 3. CÁLCULO DE MÉTRICAS POR ZONA — 3 SOLUÇÕES
# ============================================================

def ber_qpsk(sinr_db):
    snr = np.maximum(10**(np.asarray(sinr_db)/10), 1e-12)
    return 0.5 * erfc(np.sqrt(snr))

def calcular_metricas(nome_zona, tipo_4g, tipo_6g, tipo_hyb):
    """Retorna dict com métricas para as 3 soluções em uma zona."""

    # ── 4G ──────────────────────────────────────────────────
    if tipo_4g == "alta":
        ret4, jit4, sinr4 = np.random.uniform(22,35), np.random.uniform(4,9),  14.0
    elif tipo_4g == "media":
        ret4, jit4, sinr4 = np.random.uniform(35,50), np.random.uniform(8,14), 9.0
    else:
        ret4, jit4, sinr4 = np.random.uniform(50,65), np.random.uniform(12,20), 3.5

    vaz4 = (BW_4G * EFF_4G) / 1e6  # Mbps

    # ── 6G ──────────────────────────────────────────────────
    if tipo_6g == "alta":
        ret6, jit6, sinr6 = np.random.uniform(0.2,0.7), np.random.uniform(0.01,0.04), 28.0
    elif tipo_6g == "media":
        ret6, jit6, sinr6 = np.random.uniform(0.4,1.2), np.random.uniform(0.03,0.08), 22.0
    else:
        ret6, jit6, sinr6 = None, None, None   # inviável

    vaz6 = (BW_6G * EFF_6G) / 1e9 if tipo_6g != "rural" else None  # Gbps

    # ── Híbrida ─────────────────────────────────────────────
    if tipo_hyb == "6g_alta":
        ret_h, jit_h, sinr_h = np.random.uniform(0.2,0.7),  np.random.uniform(0.01,0.04), 28.0
        vaz_h  = vaz6
        vaz_un = "Gbps"
    elif tipo_hyb == "6g_media":
        ret_h, jit_h, sinr_h = np.random.uniform(0.5,1.5),  np.random.uniform(0.04,0.10), 20.0
        vaz_h  = vaz6
        vaz_un = "Gbps"
    else:  # 4G rural fallback
        ret_h, jit_h, sinr_h = np.random.uniform(50,65),    np.random.uniform(12,20),     3.5
        vaz_h  = vaz4
        vaz_un = "Mbps"

    return {
        "zona": nome_zona,
        # 4G
        "ret_4g": ret4, "jit_4g": jit4,
        "vaz_4g": f"{vaz4:.0f} Mbps",
        "ber_4g": ber_qpsk(sinr4),
        "sinr_4g": sinr4,
        # 6G
        "ret_6g": ret6, "jit_6g": jit6,
        "vaz_6g": f"{vaz6:.0f} Gbps" if vaz6 else "N/A (inviável)",
        "ber_6g": ber_qpsk(sinr6) if sinr6 else None,
        "sinr_6g": sinr6,
        # Híbrida
        "ret_h": ret_h, "jit_h": jit_h,
        "vaz_h": f"{vaz_h:.0f} {vaz_un}",
        "ber_h": ber_qpsk(sinr_h),
        "sinr_h": sinr_h,
        "tech_h": "6G" if tipo_hyb.startswith("6g") else "4G (fallback)",
    }

zonas_metricas = [
    calcular_metricas("Alta densidade\n(Comerc./Indust.)", "alta",  "alta",  "6g_alta"),
    calcular_metricas("Urbana média\n(Residencial)",       "media", "media", "4g_media"),
    calcular_metricas("Rural / Periférica",                "rural", "rural", "4g_rural"),
]

# ============================================================
# 4. CONSUMO ENERGÉTICO
# ============================================================
# 4G puro
E_4G = (n_alta*BS4G_ALTA  * P_ERB_KW +
        n_media*BS4G_MEDIA * P_ERB_KW +
        n_rural*BS4G_RURAL * P_ERB_KW)

# 6G puro
E_6G = (n_alta*(SC6G_ALTA*P_SC_KW + ANC6G_ALTA*P_ANC_KW) +
        n_media*SC6G_MEDIA*P_SC_KW +
        n_rural*BS4G_RURAL*P_ERB_KW)   # fallback 4G no rural

# Híbrida: 6G em alta, 4G em média e rural
E_HYB = (n_alta *(HYB_SC_ALTA*P_SC_KW + HYB_ANC_ALTA*P_ANC_KW) +
         n_media * HYB_ERB_MEDIA * P_ERB_KW +
         n_rural * HYB_ERB_RURAL * P_ERB_KW)

eco_hyb_vs_6g = (1 - E_HYB/E_6G)*100
eco_hyb_vs_4g = (E_HYB/E_4G - 1)*100

# ============================================================
# 5. CUSTOS (CAPEX / OPEX / TCO)
# ============================================================
# 4G
N_ERB_4G_T = n_alta*BS4G_ALTA + n_media*BS4G_MEDIA + n_rural*BS4G_RURAL
CAPEX_4G = N_ERB_4G_T * CAPEX_ERB
OPEX_4G  = N_ERB_4G_T * OPEX_ERB_A * ANOS_TCO
TCO_4G   = CAPEX_4G + OPEX_4G

# 6G
N_SC_6G  = n_alta*SC6G_ALTA + n_media*SC6G_MEDIA
N_ANC_6G = n_alta*ANC6G_ALTA
N_ERB_6G_RUR = n_rural*BS4G_RURAL
CAPEX_6G = N_SC_6G*CAPEX_SC + N_ANC_6G*CAPEX_ANC + N_ERB_6G_RUR*CAPEX_ERB
OPEX_6G  = (N_SC_6G*OPEX_SC_A + N_ANC_6G*OPEX_ANC_A + N_ERB_6G_RUR*OPEX_ERB_A)*ANOS_TCO
TCO_6G   = CAPEX_6G + OPEX_6G

# Híbrida: 6G em alta, 4G em média e rural
N_SC_HYB      = n_alta * HYB_SC_ALTA                    # apenas zona alta
N_ANC_HYB     = n_alta * HYB_ANC_ALTA
N_ERB_HYB_MED = n_media * HYB_ERB_MEDIA                 # 4G zona média
N_ERB_HYB_RUR = n_rural * HYB_ERB_RURAL
N_ERB_HYB_TOT = N_ERB_HYB_MED + N_ERB_HYB_RUR
CAPEX_HYB = (N_SC_HYB*CAPEX_SC + N_ANC_HYB*CAPEX_ANC +
             N_ERB_HYB_TOT*CAPEX_ERB)
OPEX_HYB  = (N_SC_HYB*OPEX_SC_A + N_ANC_HYB*OPEX_ANC_A +
             N_ERB_HYB_TOT*OPEX_ERB_A) * ANOS_TCO
TCO_HYB   = CAPEX_HYB + OPEX_HYB

print("="*65)
print("RELATÓRIO — SEÇÃO 4.3: SOLUÇÃO HÍBRIDA 4G+6G")
print("="*65)
print(f"\nCOMPOSIÇÃO DA SOLUÇÃO HÍBRIDA:")
print(f"  Small cells 6G (alta+média): {int(N_SC_HYB)}")
print(f"  Âncoras 6G (alta dens.):     {int(N_ANC_HYB)}")
print(f"  ERBs 4G (rural fallback):    {int(N_ERB_HYB_RUR)}")
print(f"\nCONSUMO ENERGÉTICO:")
print(f"  4G puro:     {E_4G:.1f} kW")
print(f"  6G puro:     {E_6G:.1f} kW")
print(f"  Híbrida:     {E_HYB:.1f} kW  ({eco_hyb_vs_6g:.0f}% abaixo do 6G puro)")
print(f"\nCUSTO (CAPEX / TCO 10 anos):")
print(f"  4G  CAPEX: R$ {CAPEX_4G/1e9:.2f} bi  |  TCO: R$ {TCO_4G/1e9:.2f} bi")
print(f"  6G  CAPEX: R$ {CAPEX_6G/1e9:.2f} bi  |  TCO: R$ {TCO_6G/1e9:.2f} bi")
print(f"  HYB CAPEX: R$ {CAPEX_HYB/1e9:.2f} bi  |  TCO: R$ {TCO_HYB/1e9:.2f} bi")
print(f"\nMÉTRICAS POR ZONA:")
for z in zonas_metricas:
    print(f"\n  {z['zona'].replace(chr(10),' ')}:")
    print(f"    4G  → Retardo: {z['ret_4g']:.0f}ms | Jitter: {z['jit_4g']:.0f}ms | BER: {z['ber_4g']:.2e} | Vazão: {z['vaz_4g']}")
    r6 = f"{z['ret_6g']:.2f}ms" if z['ret_6g'] else "N/A"
    j6 = f"{z['jit_6g']:.3f}ms" if z['jit_6g'] else "N/A"
    b6 = f"{z['ber_6g']:.2e}" if z['ber_6g'] else "N/A"
    print(f"    6G  → Retardo: {r6} | Jitter: {j6} | BER: {b6} | Vazão: {z['vaz_6g']}")
    print(f"    HYB → Retardo: {z['ret_h']:.2f}ms | Jitter: {z['jit_h']:.3f}ms | BER: {z['ber_h']:.2e} | Vazão: {z['vaz_h']} [{z['tech_h']}]")

# ============================================================
# 6. MAPA DE COBERTURA HÍBRIDA
# ============================================================
cob_map = np.zeros((GRID_ROWS, GRID_COLS, 3))  # RGB
for r in range(GRID_ROWS):
    for c in range(GRID_COLS):
        z = zone_map[r, c]
        if z == 2:   # 6G alta — roxo
            cob_map[r,c] = [0.48, 0.18, 0.55]
        elif z == 1: # 4G média — azul (4G)
            cob_map[r,c] = [0.10, 0.42, 0.69]
        else:        # 4G rural — azul escuro
            cob_map[r,c] = [0.10, 0.25, 0.45]

# ============================================================
# 7. GERAÇÃO DOS GRÁFICOS
# ============================================================
OUTPUT_DIR = '/mnt/user-data/outputs' if os.path.exists('/mnt/user-data/outputs') \
             else ('/content/drive/MyDrive' if os.path.exists('/content/drive/MyDrive') \
             else '/content')

COR_4G   = '#1A6BAF'
COR_6G   = '#7B2D8B'
COR_HYB  = '#1A6B42'
COR_FUNDO= '#F7F7F2'
BOX = dict(boxstyle='round,pad=0.4', linewidth=1.5)
SUBTIT = "Cidade de 1.000.000 hab.  |  500 km²  (grade 25×20 km)  |  Projeção 10 anos"

# ── FIGURA A — Mapa de cobertura híbrida ─────────────────────
figA, axA = plt.subplots(figsize=(13, 9), dpi=110, facecolor=COR_FUNDO)
figA.suptitle("Figura 4.3a — Mapa de Cobertura Tecnológica: Solução Híbrida 4G+6G\n" + SUBTIT,
              fontsize=14, fontweight='bold', y=1.01)

imA = axA.imshow(cob_map, origin='upper', aspect='equal',
                 extent=[0, GRID_COLS, GRID_ROWS, 0])

axA.set_title("Distribuição tecnológica por zona — 6G nas zonas densas, 4G no rural",
              fontsize=12, fontweight='bold')
axA.set_xlabel("Distância Leste–Oeste (km)", fontsize=12)
axA.set_ylabel("Distância Norte–Sul (km)", fontsize=12)
axA.tick_params(labelsize=11)

# Anotações sobre o mapa
axA.text(10.5, 8.5, "ZONA ALTA\n6G Sub-THz\n25 SCs/km²\nLatência < 1 ms",
         ha='center', va='center', fontsize=10, fontweight='bold', color='white',
         bbox=dict(facecolor='#7B2D8B', alpha=0.85, boxstyle='round,pad=0.5'))

axA.text(21.5, 12.5, "ZONA MÉDIA\n4G LTE\n0,5 ERB/km²\nLatência 35–50 ms",
         ha='center', va='center', fontsize=10, fontweight='bold', color='white',
         bbox=dict(facecolor='#1A6BAF', alpha=0.85, boxstyle='round,pad=0.5'))

axA.text(12.5, 0.7, "ZONA RURAL  —  4G LTE  |  0,2 ERB/km²  |  Latência 50–65 ms  (camada de fallback)",
         ha='center', va='center', fontsize=10, fontweight='bold', color='white',
         bbox=dict(facecolor='#1A3F72', alpha=0.85, boxstyle='round,pad=0.4'))

# Legenda
leg_patches = [
    mpatches.Patch(color='#7B2D8B', label=f'Alta dens. (125 km²) — 6G Sub-THz: {int(n_alta*HYB_SC_ALTA)} SCs + {int(n_alta*HYB_ANC_ALTA)} âncoras'),
    mpatches.Patch(color='#1A6BAF', label=f'Urbana média (350 km²) — 4G LTE: {int(n_media*HYB_ERB_MEDIA)} ERBs  (racional: ROI sub-THz insuficiente)'),
    mpatches.Patch(color='#1A3F72', label=f'Rural (25 km²) — 4G LTE: {int(n_rural*HYB_ERB_RURAL)} ERBs (fallback)'),
]
axA.legend(handles=leg_patches, loc='lower right', fontsize=10.5,
           framealpha=0.95, edgecolor='gray', title='Tecnologia por zona', title_fontsize=11)

# Caixa de totais
axA.text(0.02, 0.98,
    f"  Composição da solução híbrida  \n"
    f"  SCs 6G:        {int(N_SC_HYB):>6}  \n"
    f"  Âncoras 6G:    {int(N_ANC_HYB):>6}  \n"
    f"  ERBs 4G rural: {int(N_ERB_HYB_RUR):>6}  \n"
    f"  ──────────────────────────  \n"
    f"  CAPEX:  R$ {CAPEX_HYB/1e9:.2f} bilhões  \n"
    f"  TCO 10a: R$ {TCO_HYB/1e9:.2f} bilhões  ",
    transform=axA.transAxes, fontsize=10, va='top', ha='left', family='monospace',
    bbox=dict(facecolor='white', alpha=0.93, edgecolor=COR_HYB,
              boxstyle='round,pad=0.5', lw=1.8))

plt.tight_layout()
fA = os.path.join(OUTPUT_DIR, 'fig4a_mapa_hibrida.png')
figA.savefig(fA, dpi=120, bbox_inches='tight', facecolor=COR_FUNDO)
print(f"\n✔ Figura 4.3a salva: {fA}")
plt.close(figA)

# ── FIGURA B — Métricas por zona (3 soluções lado a lado) ────
figB, axes = plt.subplots(2, 2, figsize=(18, 12), dpi=110, facecolor=COR_FUNDO)
figB.suptitle("Figura 4.3b — Métricas por Zona: 4G Puro vs. 6G Puro vs. Híbrida 4G+6G\n" + SUBTIT,
              fontsize=14, fontweight='bold', y=1.01)

zonas_lab = ["Alta\ndens.", "Urb.\nmédia", "Rural"]
x = np.arange(3)
w = 0.26

# ── Retardo ─────────────────────────────────────────────────
ax_r = axes[0,0]
ret4  = [z['ret_4g'] for z in zonas_metricas]
ret6  = [z['ret_6g'] if z['ret_6g'] else 0 for z in zonas_metricas]
ret_h = [z['ret_h']  for z in zonas_metricas]
b4=ax_r.bar(x-w, ret4,  w, color=COR_4G, edgecolor='white', lw=1.2, label='4G Puro', zorder=3)
b6=ax_r.bar(x,   ret6,  w, color=COR_6G, edgecolor='white', lw=1.2, label='6G Puro', zorder=3)
bh=ax_r.bar(x+w, ret_h, w, color=COR_HYB,edgecolor='white', lw=1.2, label='Híbrida 4G+6G', zorder=3)
for b,v in zip(list(b4)+list(b6)+list(bh), ret4+ret6+ret_h):
    if v > 0:
        ax_r.text(b.get_x()+b.get_width()/2, b.get_height()+0.5,
                  f'{v:.1f}' if v < 5 else f'{v:.0f}', ha='center', va='bottom', fontsize=9)
ax_r.set_title("Retardo médio por zona (ms)\n(menor é melhor)", fontsize=12, fontweight='bold')
ax_r.set_xticks(x); ax_r.set_xticklabels(zonas_lab, fontsize=11)
ax_r.set_ylabel("ms", fontsize=11); ax_r.legend(fontsize=10)
ax_r.grid(axis='y', alpha=0.3, zorder=0); ax_r.set_facecolor('#FAFAFA')
ax_r.spines[['top','right']].set_visible(False)
# Nota zona rural
ax_r.text(2+w, ret_h[2]+3, "4G\nfallback", ha='center', fontsize=8.5, color=COR_HYB,
          bbox=dict(facecolor='#EAFAF1', edgecolor=COR_HYB, boxstyle='round,pad=0.2', lw=1))

# ── BER ─────────────────────────────────────────────────────
ax_b = axes[0,1]
ber4  = [z['ber_4g'] for z in zonas_metricas]
ber6  = [z['ber_6g'] if z['ber_6g'] else 1 for z in zonas_metricas]
ber_h = [z['ber_h']  for z in zonas_metricas]
for pos, (b4v,b6v,bhv) in enumerate(zip(ber4,ber6,ber_h)):
    ax_b.bar(pos-w, b4v,  w, color=COR_4G, edgecolor='white', lw=1.2, zorder=3,
             label='4G Puro' if pos==0 else '')
    ax_b.bar(pos,   b6v,  w, color=COR_6G, edgecolor='white', lw=1.2, zorder=3,
             label='6G Puro' if pos==0 else '')
    ax_b.bar(pos+w, bhv,  w, color=COR_HYB,edgecolor='white', lw=1.2, zorder=3,
             label='Híbrida 4G+6G' if pos==0 else '')
ax_b.set_yscale('log')
ax_b.set_title("BER por zona — escala logarítmica\n(QPSK/AWGN, Proakis 2008)", fontsize=12, fontweight='bold')
ax_b.set_xticks(x); ax_b.set_xticklabels(zonas_lab, fontsize=11)
ax_b.set_ylabel("Taxa de Erro de Bit (BER)", fontsize=11)
ax_b.legend(fontsize=10); ax_b.grid(axis='y', alpha=0.3, which='both', zorder=0)
ax_b.set_facecolor('#FAFAFA'); ax_b.spines[['top','right']].set_visible(False)
ax_b.axhline(1e-3, color='red', lw=1.5, linestyle=':', alpha=0.7)
ax_b.text(2.5, 1.5e-3, 'Limiar VoIP', fontsize=9, color='red', ha='right')

# ── CAPEX / TCO ─────────────────────────────────────────────
ax_c = axes[1,0]
labels_c = ['CAPEX', f'OPEX\n({ANOS_TCO}a)', f'TCO\n({ANOS_TCO}a)']
v4c  = [CAPEX_4G/1e9,  (TCO_4G-CAPEX_4G)/1e9,   TCO_4G/1e9]
v6c  = [CAPEX_6G/1e9,  (TCO_6G-CAPEX_6G)/1e9,   TCO_6G/1e9]
vhc  = [CAPEX_HYB/1e9, (TCO_HYB-CAPEX_HYB)/1e9, TCO_HYB/1e9]
xc   = np.arange(3)
b4c  = ax_c.bar(xc-w, v4c, w, color=COR_4G,  edgecolor='white', lw=1.2, label='4G Puro',      zorder=3)
b6c  = ax_c.bar(xc,   v6c, w, color=COR_6G,  edgecolor='white', lw=1.2, label='6G Puro',      zorder=3)
bhc  = ax_c.bar(xc+w, vhc, w, color=COR_HYB, edgecolor='white', lw=1.2, label='Híbrida 4G+6G',zorder=3)
for b,v in zip(list(b4c)+list(b6c)+list(bhc), v4c+v6c+vhc):
    ax_c.text(b.get_x()+b.get_width()/2, b.get_height()+0.02,
              f'R${v:.2f}bi', ha='center', va='bottom', fontsize=8.5,
              color=b.get_facecolor(), fontweight='bold')
ax_c.set_title("Comparativo de Custos — 4G vs. 6G vs. Híbrida\n(CAPEX, OPEX e TCO em 10 anos)",
               fontsize=12, fontweight='bold')
ax_c.set_xticks(xc); ax_c.set_xticklabels(labels_c, fontsize=11)
ax_c.set_ylabel("R$ Bilhões", fontsize=11)
ax_c.legend(fontsize=10); ax_c.grid(axis='y', alpha=0.3, zorder=0)
ax_c.set_facecolor('#FAFAFA'); ax_c.spines[['top','right']].set_visible(False)

# ── Energia ─────────────────────────────────────────────────
ax_e = axes[1,1]
# Decomposto por camada
comp_4g  = [n_alta*BS4G_ALTA*P_ERB_KW,  n_media*BS4G_MEDIA*P_ERB_KW, n_rural*BS4G_RURAL*P_ERB_KW]
comp_6g  = [n_alta*(SC6G_ALTA*P_SC_KW+ANC6G_ALTA*P_ANC_KW), n_media*SC6G_MEDIA*P_SC_KW, n_rural*BS4G_RURAL*P_ERB_KW]
comp_hyb = [n_alta*(HYB_SC_ALTA*P_SC_KW+HYB_ANC_ALTA*P_ANC_KW), n_media*HYB_ERB_MEDIA*P_ERB_KW, n_rural*HYB_ERB_RURAL*P_ERB_KW]

zonas_e = ["Alta dens.", "Urb. média", "Rural"]
xe = np.arange(3)
for pos, (e4,e6,eh) in enumerate(zip(comp_4g,comp_6g,comp_hyb)):
    ax_e.bar(pos-w, e4, w, color=COR_4G,  edgecolor='white', lw=1.2, zorder=3,
             label='4G Puro'       if pos==0 else '')
    ax_e.bar(pos,   e6, w, color=COR_6G,  edgecolor='white', lw=1.2, zorder=3,
             label='6G Puro'       if pos==0 else '')
    ax_e.bar(pos+w, eh, w, color=COR_HYB, edgecolor='white', lw=1.2, zorder=3,
             label='Híbrida 4G+6G' if pos==0 else '')
    for b,v in [(pos-w,e4),(pos,e6),(pos+w,eh)]:
        ax_e.text(b, v+5, f'{v:.0f}kW', ha='center', va='bottom', fontsize=8.5)
ax_e.set_title(f"Consumo Energético por Zona (kW)\n"
               f"Total — 4G: {E_4G:.0f}kW | 6G: {E_6G:.0f}kW | Híbrida: {E_HYB:.0f}kW",
               fontsize=12, fontweight='bold')
ax_e.set_xticks(xe); ax_e.set_xticklabels(zonas_e, fontsize=11)
ax_e.set_ylabel("kW (consumo contínuo)", fontsize=11)
ax_e.legend(fontsize=10); ax_e.grid(axis='y', alpha=0.3, zorder=0)
ax_e.set_facecolor('#FAFAFA'); ax_e.spines[['top','right']].set_visible(False)
# Anotação de economia
ax_e.annotate(f"Híbrida: {eco_hyb_vs_6g:.0f}%\nabaixo do 6G",
              xy=(2+w, comp_hyb[2]+30), xytext=(2.3, max(comp_6g)*0.6),
              fontsize=9.5, color=COR_HYB, fontweight='bold',
              bbox=dict(facecolor='#EAFAF1', edgecolor=COR_HYB, boxstyle='round,pad=0.3', lw=1.2),
              arrowprops=dict(arrowstyle='->', color=COR_HYB, lw=1.5))

plt.tight_layout()
fB = os.path.join(OUTPUT_DIR, 'fig4b_metricas_hibrida.png')
figB.savefig(fB, dpi=120, bbox_inches='tight', facecolor=COR_FUNDO)
print(f"✔ Figura 4.3b salva: {fB}")
plt.close(figB)

# ── FIGURA C — Tabela visual comparativa ─────────────────────
figC, axC = plt.subplots(figsize=(18, 7), dpi=110, facecolor=COR_FUNDO)
figC.suptitle("Figura 4.3c — Tabela Consolidada: 4G Puro | 6G Puro | Híbrida 4G+6G\n" + SUBTIT,
              fontsize=14, fontweight='bold', y=1.01)
axC.axis('off')

col_labels = ["Parâmetro", "Zona",
              "4G Puro", "6G Puro", "Híbrida 4G+6G", "Observação"]

def fmt_ret(v): return f"{v:.2f} ms" if v and v < 5 else (f"{v:.0f} ms" if v else "N/A")
def fmt_ber(v): return f"{v:.2e}" if v else "N/A"

rows_data = []
for z in zonas_metricas:
    zona_nome = z['zona'].replace('\n',' ')
    rows_data.append([
        "Retardo", zona_nome,
        fmt_ret(z['ret_4g']), fmt_ret(z['ret_6g']), fmt_ret(z['ret_h']),
        f"Híbrida usa {z['tech_h']}"
    ])
    rows_data.append([
        "BER", zona_nome,
        fmt_ber(z['ber_4g']), fmt_ber(z['ber_6g']), fmt_ber(z['ber_h']),
        "QPSK/AWGN [Proakis 2008]"
    ])
    rows_data.append([
        "Vazão pico", zona_nome,
        z['vaz_4g'], z['vaz_6g'], z['vaz_h'],
        "Teórica (Shannon)"
    ])

rows_data.append(["Energia total", "Rede completa",
    f"{E_4G:.0f} kW", f"{E_6G:.0f} kW", f"{E_HYB:.0f} kW",
    f"Híbrida: {eco_hyb_vs_6g:.0f}% < 6G"])
rows_data.append(["CAPEX", "Rede completa",
    f"R$ {CAPEX_4G/1e9:.2f} bi", f"R$ {CAPEX_6G/1e9:.2f} bi", f"R$ {CAPEX_HYB/1e9:.2f} bi",
    f"Híbrida: {(1-CAPEX_HYB/CAPEX_6G)*100:.0f}% < 6G"])
rows_data.append([f"TCO {ANOS_TCO}a", "Rede completa",
    f"R$ {TCO_4G/1e9:.2f} bi", f"R$ {TCO_6G/1e9:.2f} bi", f"R$ {TCO_HYB/1e9:.2f} bi",
    f"Ref: Bertsias et al. (2024)"])
rows_data.append(["Cobertura rural", "Rural/Periférica",
    "Parcial (OK)", "Inviável", "Plena — 4G LTE",
    "Motiva Ad-Hoc na Seção 6"])

tbl = axC.table(
    cellText=rows_data, colLabels=col_labels,
    loc='center', cellLoc='center', bbox=[0, 0, 1, 1]
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(9.5)

# Estilo cabeçalho
for j in range(6):
    tbl[0,j].set_facecolor('#1A252F')
    tbl[0,j].set_text_props(color='white', fontweight='bold')

# Estilo linhas
CORES_COL = [None, None, COR_4G, COR_6G, COR_HYB, None]
for i in range(1, len(rows_data)+1):
    bg = '#EBF5FB' if i%2==0 else '#FDFEFE'
    for j in range(6):
        tbl[i,j].set_facecolor(bg)
        if j in [2,3,4]:
            tbl[i,j].set_text_props(color=CORES_COL[j], fontweight='bold')
    tbl[i,5].set_facecolor('#FEF9E7')

tbl.auto_set_column_width([0,1,2,3,4,5])
axC.set_title("Comparativo completo de métricas por zona e solução",
              fontsize=11, fontweight='bold', pad=10)

plt.tight_layout()
fC = os.path.join(OUTPUT_DIR, 'fig4c_tabela_comparativa.png')
figC.savefig(fC, dpi=120, bbox_inches='tight', facecolor=COR_FUNDO)
print(f"✔ Figura 4.3c salva: {fC}")
plt.close(figC)

print(f"\n✔ Simulação da Seção 4.3 concluída.")
print(f"  Arquivos em: {OUTPUT_DIR}")

# ── Exportar DataFrame para uso no texto ──────────────────────
print("\n" + "="*65)
print("RESUMO NUMÉRICO PARA CITAÇÃO NO TEXTO")
print("="*65)
print(f"""
Composição híbrida:
  Small cells 6G:  {int(N_SC_HYB)} (alta: {int(n_alta*HYB_SC_ALTA)}, média: {int(n_media*HYB_SC_MEDIA)})
  Âncoras 6G:     {int(N_ANC_HYB)}
  ERBs 4G rural:  {int(N_ERB_HYB_RUR)}

Energia:
  4G puro:   {E_4G:.1f} kW
  6G puro:   {E_6G:.1f} kW
  Híbrida:   {E_HYB:.1f} kW  (−{eco_hyb_vs_6g:.0f}% vs 6G; +{eco_hyb_vs_4g:.0f}% vs 4G)

CAPEX:
  4G:    R$ {CAPEX_4G/1e9:.3f} bi
  6G:    R$ {CAPEX_6G/1e9:.3f} bi
  HYB:   R$ {CAPEX_HYB/1e9:.3f} bi  (−{(1-CAPEX_HYB/CAPEX_6G)*100:.0f}% vs 6G)

TCO 10 anos:
  4G:    R$ {TCO_4G/1e9:.2f} bi
  6G:    R$ {TCO_6G/1e9:.2f} bi
  HYB:   R$ {TCO_HYB/1e9:.2f} bi

BER zona alta (híbrida 6G): {ber_qpsk(zonas_metricas[0]['sinr_h']):.2e}
BER zona rural (híbrida 4G): {ber_qpsk(zonas_metricas[2]['sinr_h']):.2e}
""")
