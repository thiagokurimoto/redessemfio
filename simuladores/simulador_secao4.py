"""
============================================================
SEÇÃO 4 — DIMENSIONAMENTO DE REDES 4G e 6G
Projeto de Comunicação: Cidade de 1 Milhão de Habitantes
Autores: Henrique Lima Santana, Thiago Tadao Kurimoto, Tiago Barbosa Veiga Reis
UFABC — Núcleo de Tecnologia da Informação
============================================================
Fundamentação metodológica:
  - Grid: 500 quadrantes de 1 km² (25 km × 20 km)
  - Densidade 4G: ITU-R M.2370, 3GPP TR 36.814
  - Densidade 6G: Bertsias et al. (2024), ITU-R IMT-2030
  - CAPEX/OPEX: referências de mercado (Anatel, Bertsias et al. 2024)
============================================================
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 1. PARÂMETROS GLOBAIS — REPRODUTIBILIDADE GARANTIDA
# ============================================================
np.random.seed(42)  # Semente fixa: resultados 100% reprodutíveis

# --- Grade Espacial ---
GRID_COLS = 25   # 25 km de largura
GRID_ROWS = 20   # 20 km de altura
# Resultado: 25 × 20 = 500 quadrantes de 1 km²

# --- Dados Populacionais Brutos ---
POP_TOTAL         = 1_000_000
POP_URBANA_FRAC   = 0.95                       # 95% em zona urbana
POP_URBANA        = int(POP_TOTAL * POP_URBANA_FRAC)  # 950.000
POP_RURAL         = POP_TOTAL - POP_URBANA           # 50.000

# PEA + estudantes (60% + 5% = 65% → migra para zonas de alta demanda)
PEA_FRAC          = 0.65
POP_ALTA_BRUTA    = int(POP_URBANA * PEA_FRAC)       # ~617.500
POP_BAIXA_BRUTA   = POP_URBANA - POP_ALTA_BRUTA       # ~332.500

# --- Projeção 10 anos (juros compostos 1% a.a. → 10,46% total) ---
TAXA_CRESCIMENTO  = (1.01 ** 10)                 # ≈ 1.1046
POP_ALTA_PROJ     = round(POP_ALTA_BRUTA  * TAXA_CRESCIMENTO)  # ≈ 682.000
POP_BAIXA_PROJ    = round(POP_BAIXA_BRUTA * TAXA_CRESCIMENTO)  # ≈ 367.000
POP_TOTAL_PROJ    = POP_ALTA_PROJ + POP_BAIXA_PROJ

# --- Zonas de Área ---
# Alta densidade: 25% de 500 km² = 125 km²   (comercial + industrial)
# Urbana média:   70% de 500 km² = 350 km²   (residencial)
# Rural/periférica: 5% de 500 km² = 25 km²
AREA_ALTA   = 125  # km²
AREA_MEDIA  = 350  # km²
AREA_RURAL  = 25   # km²

# ============================================================
# 2. CONSTRUÇÃO DO MAPA DE ZONAS (25 × 20 = 500 quadrantes)
# ============================================================
# Legenda de zonas:  0 = Rural | 1 = Urbana Média | 2 = Alta Densidade

zone_map = np.ones((GRID_ROWS, GRID_COLS), dtype=int)  # inicia tudo como médio (1)

# ZONA RURAL — 25 km²: faixa externa (bordas do mapa)
# Bordas norte/sul (primeiras e últimas 1 linha)
zone_map[0, :]  = 0   # linha norte (25 km²)
# Isso dá 25 células → total rural = 25 km² ✓
# OBS: zona rural concentrada na periferia norte (simula acesso a fazendas/sítios)

# ZONA ALTA DENSIDADE — 125 km²: centro comercial + polo industrial
# Bloco comercial central: linhas 4-13, colunas 6-15 → 10×10 = 100 km²
zone_map[4:14, 6:16] = 2

# Polo industrial (SW): linhas 14-17, colunas 3-7 → 4×5 = 20 km²
zone_map[14:18, 3:8]  = 2

# Polo tech/startup (NE): linhas 2-3, colunas 18-20 → 2×3 = 6 km²
zone_map[2:4, 18:21]  = 2

# Ajuste fino: -1 km² (retirar 1 célula de sobreposição)
zone_map[14, 3] = 1  # desfaz sobreposição → 100+19+6 = 125 km² ✓

# Contar zonas reais
n_alta  = int(np.sum(zone_map == 2))
n_media = int(np.sum(zone_map == 1))
n_rural = int(np.sum(zone_map == 0))

print(f"Verificação de áreas:")
print(f"  Alta densidade: {n_alta} km²  (meta: {AREA_ALTA})")
print(f"  Urbana média:   {n_media} km²  (meta: {AREA_MEDIA})")
print(f"  Rural:          {n_rural} km²  (meta: {AREA_RURAL})")
print(f"  Total:          {n_alta+n_media+n_rural} km²\n")

# ============================================================
# 3. MAPA DE DENSIDADE POPULACIONAL — CENÁRIO DIURNO
# ============================================================
# Cenário diurno: PEA migra para zonas alta → cria picos de demanda

pop_map = np.zeros((GRID_ROWS, GRID_COLS))

dens_alta  = POP_ALTA_PROJ  / n_alta    # hab/km² na zona alta
dens_media = (POP_BAIXA_PROJ * 0.90) / n_media   # 90% dos baixa demanda em zona média
dens_rural = (POP_BAIXA_PROJ * 0.10) / n_rural   # 10% em rural

for r in range(GRID_ROWS):
    for c in range(GRID_COLS):
        z = zone_map[r, c]
        if z == 2:
            # Alta densidade: variação ±20% (heterogeneidade urbana real)
            pop_map[r, c] = dens_alta * np.random.uniform(0.80, 1.20)
        elif z == 1:
            # Urbana média: variação ±30% (bairros diferentes)
            pop_map[r, c] = dens_media * np.random.uniform(0.70, 1.30)
        else:
            # Rural: variação ±50%
            pop_map[r, c] = dens_rural * np.random.uniform(0.50, 1.50)

# ============================================================
# 4. DIMENSIONAMENTO DE BASE STATIONS
# ============================================================

# --- 4G (LTE / LTE-Advanced) ---
# Referência: 3GPP TR 36.814, ITU-R M.2370
# Alta densidade (>3000 hab/km²): 1 BS/km² (raio ~560m)
# Média densidade (500-3000 hab/km²): 1 BS/2 km² (raio ~800m)
# Baixa/rural (<500 hab/km²): 1 BS/5 km² (raio ~1.26 km)

bs_4g_map = np.zeros((GRID_ROWS, GRID_COLS))
for r in range(GRID_ROWS):
    for c in range(GRID_COLS):
        z = zone_map[r, c]
        if z == 2:
            bs_4g_map[r, c] = 1.0
        elif z == 1:
            bs_4g_map[r, c] = 0.5
        else:
            bs_4g_map[r, c] = 0.2

total_bs_4g = bs_4g_map.sum()
bs_4g_alta  = bs_4g_map[zone_map == 2].sum()
bs_4g_media = bs_4g_map[zone_map == 1].sum()
bs_4g_rural = bs_4g_map[zone_map == 0].sum()

# --- 6G (Sub-THz, 100GHz–1THz) ---
# Referência: Bertsias et al. (2024), Tariq et al. (2020)
# Sub-THz: alcance ~150-200m em ambientes externos → necessita densificação extrema
# Alta densidade: ~25 small cells/km² (1 a cada ~200m)
# Média densidade: ~6 small cells/km² (1 a cada ~400m)
# Rural: inviável → fallback 4G (conforme proposta da Seção 6)
# + Macrocélulas âncora 6G: 1 a cada ~2 km² nas zonas de alta demanda (ancoragem de core)

bs_6g_sc_map     = np.zeros((GRID_ROWS, GRID_COLS))  # small cells
bs_6g_ancora_map = np.zeros((GRID_ROWS, GRID_COLS))  # âncoras macro

for r in range(GRID_ROWS):
    for c in range(GRID_COLS):
        z = zone_map[r, c]
        if z == 2:
            bs_6g_sc_map[r, c]     = 25
            bs_6g_ancora_map[r, c] = 0.5  # 1 âncora a cada 2 km²
        elif z == 1:
            bs_6g_sc_map[r, c]     = 6
            bs_6g_ancora_map[r, c] = 0.0
        else:
            bs_6g_sc_map[r, c]     = 0    # fallback 4G (Seção 6)
            bs_6g_ancora_map[r, c] = 0

total_sc_6g     = bs_6g_sc_map.sum()
total_ancora_6g = bs_6g_ancora_map.sum()
bs_6g_rural_fallback = n_rural * 0.2   # mesma densidade 4G rural como fallback

sc_alta  = bs_6g_sc_map[zone_map == 2].sum()
sc_media = bs_6g_sc_map[zone_map == 1].sum()

# ============================================================
# 5. MODELO FINANCEIRO — CAPEX / OPEX / TCO
# ============================================================
# Referências de valores:
#   4G macro: Anatel (2023), média mercado brasileiro
#   6G: Bertsias et al. (2024) — CAPEX 6G pode ser até 840% > legadas
#   Energia: ANEEL tarifa industrial ~R$0,70/kWh

# --- 4G ---
CAPEX_4G_MACRO   = 500_000     # R$/site (torre + equipamento + civil)
OPEX_4G_MACRO_A  = 80_000      # R$/site/ano (energia + manutenção + backhaul)
ENERGIA_4G_KW    = 1.5         # kW/site (consumo contínuo)

# --- 6G ---
CAPEX_6G_SC      = 150_000     # R$/small cell
OPEX_6G_SC_A     = 25_000      # R$/SC/ano
ENERGIA_6G_SC_KW = 0.3         # kW/SC

CAPEX_6G_ANCORA  = 1_200_000   # R$/âncora macro
OPEX_6G_ANCORA_A = 180_000     # R$/âncora/ano
ENERGIA_6G_ANC_KW= 2.0         # kW/âncora

ANOS_TCO = 10

# Cálculos
capex_4g   = total_bs_4g * CAPEX_4G_MACRO
opex_4g    = total_bs_4g * OPEX_4G_MACRO_A * ANOS_TCO
tco_4g     = capex_4g + opex_4g
energia_4g_mw = total_bs_4g * ENERGIA_4G_KW / 1000

capex_6g_sc    = total_sc_6g     * CAPEX_6G_SC
capex_6g_anc   = total_ancora_6g * CAPEX_6G_ANCORA
capex_6g_rural = bs_6g_rural_fallback * CAPEX_4G_MACRO  # fallback 4G
capex_6g       = capex_6g_sc + capex_6g_anc + capex_6g_rural

opex_6g_sc     = total_sc_6g     * OPEX_6G_SC_A    * ANOS_TCO
opex_6g_anc    = total_ancora_6g * OPEX_6G_ANCORA_A * ANOS_TCO
opex_6g_rural  = bs_6g_rural_fallback * OPEX_4G_MACRO_A * ANOS_TCO
opex_6g        = opex_6g_sc + opex_6g_anc + opex_6g_rural

tco_6g         = capex_6g + opex_6g

energia_6g_mw  = (total_sc_6g * ENERGIA_6G_SC_KW + total_ancora_6g * ENERGIA_6G_ANC_KW) / 1000

razao_capex    = capex_6g / capex_4g
razao_tco      = tco_6g  / tco_4g

# ============================================================
# 6. GERAÇÃO DOS GRÁFICOS — VERSÃO APRESENTAÇÃO
#    3 figuras independentes, grandes e autoexplicativas
# ============================================================

import os
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'figuras') if not os.path.exists('/content') else ('/content/drive/MyDrive' if os.path.exists('/content/drive/MyDrive') else '/content')

energia_4g_total     = total_bs_4g   * ENERGIA_4G_KW
energia_6g_sc_total  = total_sc_6g   * ENERGIA_6G_SC_KW
energia_6g_anc_total = total_ancora_6g * ENERGIA_6G_ANC_KW
energia_6g_total     = energia_6g_sc_total + energia_6g_anc_total

ESTILO_CAIXA   = dict(boxstyle='round,pad=0.4', linewidth=1.5)
COR_4G         = '#1A6BAF'
COR_6G         = '#7B2D8B'
COR_RURAL      = '#4A7C4E'
COR_FUNDO_FIG  = '#F7F7F2'

# ══════════════════════════════════════════════════════════════
# FIGURA 1 — MAPA DE ZONAS E MAPA DE CALOR POPULACIONAL
# ══════════════════════════════════════════════════════════════
fig1, (ax_z, ax_p) = plt.subplots(1, 2, figsize=(18, 9), dpi=110,
                                   facecolor=COR_FUNDO_FIG)
fig1.suptitle(
    "Figura 1 — Estrutura Territorial e Densidade Populacional\n"
    "Cidade de 1.000.000 habitantes  |  500 km²  (grade de 25 × 20 quadrantes de 1 km²)",
    fontsize=15, fontweight='bold', y=1.01
)

# ── Painel esquerdo: Mapa de Zonas ──────────────────────────
cmap_zone = LinearSegmentedColormap.from_list(
    "zona", [COR_RURAL, '#D4A017', '#C0392B'], N=3)

ax_z.imshow(zone_map, cmap=cmap_zone, vmin=0, vmax=2,
            origin='upper', aspect='equal', extent=[0, 25, 20, 0])
ax_z.set_title("Mapa de Zonas Urbanas", fontsize=14, fontweight='bold', pad=12)
ax_z.set_xlabel("Distância Leste–Oeste (km)", fontsize=12)
ax_z.set_ylabel("Distância Norte–Sul (km)", fontsize=12)
ax_z.tick_params(labelsize=11)

# Rótulos diretos sobre as regiões
ax_z.text(10.5, 9.0, "ZONA COMERCIAL\nE INDUSTRIAL\n125 km²",
          ha='center', va='center', fontsize=11, fontweight='bold', color='white',
          bbox={**ESTILO_CAIXA, 'facecolor': '#922B21', 'alpha': 0.85})
ax_z.text(20.5, 13.0, "ZONA\nRESIDENCIAL\n350 km²",
          ha='center', va='center', fontsize=10, fontweight='bold', color='#2C3E50',
          bbox={**ESTILO_CAIXA, 'facecolor': '#F9E79F', 'alpha': 0.90})
ax_z.text(12.5, 0.7, "ZONA RURAL / PERIFÉRICA  —  25 km²",
          ha='center', va='center', fontsize=10, fontweight='bold', color='white',
          bbox={**ESTILO_CAIXA, 'facecolor': '#1E8449', 'alpha': 0.80})

# Seta Norte
ax_z.annotate('N', xy=(0.96, 0.97), xycoords='axes fraction',
              fontsize=16, fontweight='bold', ha='center', va='top',
              xytext=(0.96, 0.88), textcoords='axes fraction',
              arrowprops=dict(arrowstyle='->', lw=2.5, color='black'))

# Barra de escala
ax_z.plot([1, 6], [19.3, 19.3], 'k-', lw=3)
ax_z.text(3.5, 18.9, '5 km', ha='center', fontsize=10, fontweight='bold')

# Legenda
leg_z = [mpatches.Patch(color='#C0392B', label=f'Alta Densidade — {n_alta} km²  (Comercial + Industrial)'),
         mpatches.Patch(color='#D4A017', label=f'Urbana Média   — {n_media} km²  (Residencial)'),
         mpatches.Patch(color=COR_RURAL,  label=f'Rural/Periférica — {n_rural} km²')]
ax_z.legend(handles=leg_z, loc='lower left', fontsize=10, framealpha=0.92,
            edgecolor='gray', title='Classificação das Zonas', title_fontsize=10)

# ── Painel direito: Mapa de Calor Populacional ───────────────
im_p = ax_p.imshow(pop_map, cmap='YlOrRd', origin='upper',
                   aspect='equal', extent=[0, 25, 20, 0])
cb_p = plt.colorbar(im_p, ax=ax_p, shrink=0.88, pad=0.02)
cb_p.set_label('Habitantes por km²', fontsize=12)
cb_p.ax.tick_params(labelsize=11)

ax_p.set_title("Mapa de Calor — Concentração Populacional (Cenário Diurno)",
               fontsize=14, fontweight='bold', pad=12)
ax_p.set_xlabel("Distância Leste–Oeste (km)", fontsize=12)
ax_p.set_ylabel("Distância Norte–Sul (km)", fontsize=12)
ax_p.tick_params(labelsize=11)

# Anotações explicativas
ax_p.annotate(
    f"PICO DE DEMANDA\n~{int(dens_alta):,} hab/km²\n(PEA + Estudantes\nmigram para cá)",
    xy=(10.5, 9.0), xytext=(16.5, 5.5),
    fontsize=10, fontweight='bold', ha='center', color='white',
    bbox={**ESTILO_CAIXA, 'facecolor': '#922B21', 'alpha': 0.85},
    arrowprops=dict(arrowstyle='->', color='white', lw=2))

ax_p.annotate(
    f"DEMANDA MODERADA\n~{int(dens_media):,} hab/km²\n(Residencial)",
    xy=(3.0, 13.0), xytext=(3.0, 17.0),
    fontsize=10, fontweight='bold', ha='center', color='#2C3E50',
    bbox={**ESTILO_CAIXA, 'facecolor': '#FAD7A0', 'alpha': 0.92},
    arrowprops=dict(arrowstyle='->', color='#784212', lw=2))

# Caixa de resumo populacional
resumo_txt = (
    f"  Projeção para 10 anos (1% a.a.)  \n"
    f"  ▲ Alta demanda:  {POP_ALTA_PROJ:>9,} hab.  \n"
    f"  ▼ Baixa demanda: {POP_BAIXA_PROJ:>9,} hab.  \n"
    f"  ━ Total projetado:{POP_TOTAL_PROJ:>9,} hab.  "
)
ax_p.text(0.02, 0.02, resumo_txt, transform=ax_p.transAxes,
          fontsize=10, va='bottom', ha='left', family='monospace',
          bbox=dict(facecolor='white', alpha=0.92, edgecolor='gray',
                    boxstyle='round,pad=0.5', linewidth=1.2))

plt.tight_layout()
f1_path = os.path.join(OUTPUT_DIR, 'fig1_mapa_zonas_populacao.png')
fig1.savefig(f1_path, dpi=120, bbox_inches='tight', facecolor=COR_FUNDO_FIG)
print(f"✔ Figura 1 salva: {f1_path}")

# ══════════════════════════════════════════════════════════════
# FIGURA 2 — INFRAESTRUTURA 4G vs 6G (MAPAS LADO A LADO)
# ══════════════════════════════════════════════════════════════
fig2, (ax_4g, ax_6g) = plt.subplots(1, 2, figsize=(18, 9), dpi=110,
                                     facecolor=COR_FUNDO_FIG)
fig2.suptitle(
    "Figura 2 — Planejamento de Infraestrutura: 4G vs 6G\n"
    "Quantidade e localização de antenas por zona — Fundamentação para CAPEX",
    fontsize=15, fontweight='bold', y=1.01
)

# ── Painel 4G ────────────────────────────────────────────────
im_4g = ax_4g.imshow(bs_4g_map, cmap='Blues', origin='upper',
                     aspect='equal', extent=[0, 25, 20, 0], vmin=0, vmax=1.2)
cb_4g = plt.colorbar(im_4g, ax=ax_4g, shrink=0.88, pad=0.02)
cb_4g.set_label('ERBs (antenas macro) por km²', fontsize=11)
cb_4g.ax.tick_params(labelsize=10)

ax_4g.set_facecolor('#E8F4FD')
ax_4g.set_title(f"Rede 4G / LTE  —  Total: {int(total_bs_4g)} ERBs",
                fontsize=14, fontweight='bold', color=COR_4G, pad=12)
ax_4g.set_xlabel("Distância Leste–Oeste (km)", fontsize=12)
ax_4g.set_ylabel("Distância Norte–Sul (km)", fontsize=12)
ax_4g.tick_params(labelsize=11)

# Anotações 4G
ax_4g.annotate(
    "1 ERB por km²\n(raio de cobertura ≈ 560m)\n→ 125 ERBs nesta zona",
    xy=(10.5, 8.0), xytext=(15.5, 4.0),
    fontsize=10, ha='center', color='white',
    bbox={**ESTILO_CAIXA, 'facecolor': COR_4G, 'alpha': 0.88},
    arrowprops=dict(arrowstyle='->', color=COR_4G, lw=2))

ax_4g.annotate(
    "1 ERB a cada 2 km²\n(raio ≈ 800m)\n→ 175 ERBs nesta zona",
    xy=(21.0, 12.0), xytext=(21.0, 17.5),
    fontsize=10, ha='center', color='#1A252F',
    bbox={**ESTILO_CAIXA, 'facecolor': '#AED6F1', 'alpha': 0.95},
    arrowprops=dict(arrowstyle='->', color=COR_4G, lw=2))

ax_4g.annotate(
    "1 ERB a cada 5 km²\n(raio ≈ 1,26 km)\n→ 5 ERBs  (zona rural)",
    xy=(12.5, 0.7), xytext=(5.0, 3.5),
    fontsize=10, ha='center', color='#1A252F',
    bbox={**ESTILO_CAIXA, 'facecolor': '#D6EAF8', 'alpha': 0.95},
    arrowprops=dict(arrowstyle='->', color=COR_4G, lw=2))

# Caixa de totais 4G
tot_4g_txt = (
    f"  RESUMO 4G  \n"
    f"  Alta dens.: {int(bs_4g_alta):>5} ERBs  \n"
    f"  Méd. dens.: {int(bs_4g_media):>5} ERBs  \n"
    f"  Rural:      {int(bs_4g_rural):>5} ERBs  \n"
    f"  ─────────────────  \n"
    f"  TOTAL:      {int(total_bs_4g):>5} ERBs  "
)
ax_4g.text(0.02, 0.98, tot_4g_txt, transform=ax_4g.transAxes,
           fontsize=10, va='top', ha='left', family='monospace',
           bbox=dict(facecolor='white', alpha=0.95, edgecolor=COR_4G,
                     boxstyle='round,pad=0.5', linewidth=2))

# Ref. 3GPP
ax_4g.text(0.98, 0.02, "Ref: 3GPP TR 36.814\nITU-R M.2370",
           transform=ax_4g.transAxes, fontsize=8.5, va='bottom', ha='right',
           color='gray', style='italic')

# ── Painel 6G ────────────────────────────────────────────────
im_6g = ax_6g.imshow(bs_6g_sc_map, cmap='Purples', origin='upper',
                     aspect='equal', extent=[0, 25, 20, 0], vmin=0, vmax=30)
cb_6g = plt.colorbar(im_6g, ax=ax_6g, shrink=0.88, pad=0.02)
cb_6g.set_label('Small Cells 6G por km²', fontsize=11)
cb_6g.ax.tick_params(labelsize=10)

ax_6g.set_facecolor('#F5EEF8')
ax_6g.set_title(
    f"Rede 6G / Sub-THz  —  {int(total_sc_6g)} Small Cells  +  {int(total_ancora_6g)} Âncoras",
    fontsize=14, fontweight='bold', color=COR_6G, pad=12)
ax_6g.set_xlabel("Distância Leste–Oeste (km)", fontsize=12)
ax_6g.set_ylabel("Distância Norte–Sul (km)", fontsize=12)
ax_6g.tick_params(labelsize=11)

ax_6g.annotate(
    "25 Small Cells por km²\n(raio ≈ 200m — Sub-THz\nexige visada direta)",
    xy=(10.5, 8.0), xytext=(15.5, 4.0),
    fontsize=10, ha='center', color='white',
    bbox={**ESTILO_CAIXA, 'facecolor': COR_6G, 'alpha': 0.88},
    arrowprops=dict(arrowstyle='->', color=COR_6G, lw=2))

ax_6g.annotate(
    "6 Small Cells por km²\n(raio ≈ 400m)\n→ 2.100 SCs nesta zona",
    xy=(21.0, 12.0), xytext=(21.0, 17.5),
    fontsize=10, ha='center', color='#1A252F',
    bbox={**ESTILO_CAIXA, 'facecolor': '#E8DAEF', 'alpha': 0.95},
    arrowprops=dict(arrowstyle='->', color=COR_6G, lw=2))

ax_6g.annotate(
    "ZERO cobertura 6G\nSub-THz inviável em rural\n→ Fallback 4G (motiva Seção 6)",
    xy=(12.5, 0.7), xytext=(3.5, 4.5),
    fontsize=10, ha='center', color='#555',
    bbox={**ESTILO_CAIXA, 'facecolor': '#FDFEFE', 'alpha': 0.95},
    arrowprops=dict(arrowstyle='->', color='gray', lw=2))

# Caixa de totais 6G
tot_6g_txt = (
    f"  RESUMO 6G  \n"
    f"  Alta dens.: {int(sc_alta):>5} SCs  \n"
    f"  Méd. dens.: {int(sc_media):>5} SCs  \n"
    f"  Âncoras:    {int(total_ancora_6g):>5} macro  \n"
    f"  ─────────────────  \n"
    f"  TOTAL SCs:  {int(total_sc_6g):>5}  \n"
    f"  Razão 6G/4G: {total_sc_6g/total_bs_4g:.0f}× mais sites  "
)
ax_6g.text(0.02, 0.98, tot_6g_txt, transform=ax_6g.transAxes,
           fontsize=10, va='top', ha='left', family='monospace',
           bbox=dict(facecolor='white', alpha=0.95, edgecolor=COR_6G,
                     boxstyle='round,pad=0.5', linewidth=2))

ax_6g.text(0.98, 0.02, "Ref: Bertsias et al. (2024)\nITU-R IMT-2030 | Tariq et al. (2020)",
           transform=ax_6g.transAxes, fontsize=8.5, va='bottom', ha='right',
           color='gray', style='italic')

plt.tight_layout()
f2_path = os.path.join(OUTPUT_DIR, 'fig2_infraestrutura_4G_vs_6G.png')
fig2.savefig(f2_path, dpi=120, bbox_inches='tight', facecolor=COR_FUNDO_FIG)
print(f"✔ Figura 2 salva: {f2_path}")

# ══════════════════════════════════════════════════════════════
# FIGURA 3 — DASHBOARD DE CUSTOS E ENERGIA
# ══════════════════════════════════════════════════════════════
fig3 = plt.figure(figsize=(18, 11), dpi=110, facecolor=COR_FUNDO_FIG)
fig3.suptitle(
    "Figura 3 — Análise Econômica e Energética: 4G vs 6G\n"
    f"Horizonte de planejamento: {ANOS_TCO} anos  |  Ref: Bertsias et al. (2024), Anatel (2023)",
    fontsize=15, fontweight='bold', y=1.01
)
gs3 = gridspec.GridSpec(2, 3, figure=fig3, hspace=0.50, wspace=0.38)

# ── KPI Cards (linha 0) ──────────────────────────────────────
kpis = [
    ("Total de Sites\n4G vs 6G",
     f"{int(total_bs_4g)} ERBs", f"{int(total_sc_6g)} Small Cells",
     "6G exige mais antenas\nporque o sinal Sub-THz\nnão penetra obstáculos",
     COR_4G, COR_6G),
    ("Custo de Implantação\n(CAPEX)",
     f"R$ {capex_4g/1e9:.2f} bi", f"R$ {capex_6g/1e9:.2f} bi",
     f"6G custa {razao_capex:.1f}× mais\npara implantar\n(Bertsias: até 8,4×)",
     COR_4G, COR_6G),
    ("Custo Total em 10 anos\n(TCO = CAPEX + OPEX)",
     f"R$ {tco_4g/1e9:.2f} bi", f"R$ {tco_6g/1e9:.2f} bi",
     f"TCO do 6G é {razao_tco:.1f}×\nmais alto que o 4G\nem 10 anos",
     COR_4G, COR_6G),
]

for col, (titulo_kpi, val4, val6, obs, c4, c6) in enumerate(kpis):
    ax_k = fig3.add_subplot(gs3[0, col])
    ax_k.set_facecolor('white')
    ax_k.set_xlim(0, 1); ax_k.set_ylim(0, 1)
    ax_k.axis('off')

    # Título do card
    ax_k.text(0.5, 0.96, titulo_kpi, ha='center', va='top',
              fontsize=12, fontweight='bold', color='#2C3E50',
              transform=ax_k.transAxes)
    ax_k.plot([0, 1], [0.82, 0.82], color='lightgray', lw=1.2, transform=ax_k.transAxes, clip_on=False)

    # Valor 4G
    ax_k.text(0.25, 0.68, "4G / LTE", ha='center', va='center',
              fontsize=10, color=c4, fontweight='bold', transform=ax_k.transAxes)
    ax_k.text(0.25, 0.52, val4, ha='center', va='center',
              fontsize=16, color=c4, fontweight='bold', transform=ax_k.transAxes,
              bbox=dict(facecolor='#EBF5FB', edgecolor=c4, boxstyle='round,pad=0.4', lw=1.5))

    # Divisor
    ax_k.plot([0.5, 0.5], [0.35, 0.85], color='lightgray', lw=1.5, transform=ax_k.transAxes, clip_on=False)

    # Valor 6G
    ax_k.text(0.75, 0.68, "6G / Sub-THz", ha='center', va='center',
              fontsize=10, color=c6, fontweight='bold', transform=ax_k.transAxes)
    ax_k.text(0.75, 0.52, val6, ha='center', va='center',
              fontsize=16, color=c6, fontweight='bold', transform=ax_k.transAxes,
              bbox=dict(facecolor='#F4ECF7', edgecolor=c6, boxstyle='round,pad=0.4', lw=1.5))

    # Observação
    ax_k.plot([0, 1], [0.34, 0.34], color='lightgray', lw=1.2, transform=ax_k.transAxes, clip_on=False)
    ax_k.text(0.5, 0.17, obs, ha='center', va='center',
              fontsize=9.5, color='#555', style='italic', transform=ax_k.transAxes)

    # Borda do card
    for spine in ax_k.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor('lightgray')
        spine.set_linewidth(1.5)

# ── Gráfico de Barras: CAPEX / OPEX / TCO ────────────────────
ax_custo = fig3.add_subplot(gs3[1, 0:2])
cats  = ['CAPEX\n(Implantação)', f'OPEX\n({ANOS_TCO} anos)', f'TCO Total\n({ANOS_TCO} anos)']
v4g_c = [capex_4g/1e9, opex_4g/1e9, tco_4g/1e9]
v6g_c = [capex_6g/1e9, opex_6g/1e9, tco_6g/1e9]
x_c   = np.arange(len(cats))

b4 = ax_custo.bar(x_c - 0.22, v4g_c, 0.40, color=COR_4G,
                  edgecolor='white', linewidth=1.2, label='4G / LTE', zorder=3)
b6 = ax_custo.bar(x_c + 0.22, v6g_c, 0.40, color=COR_6G,
                  edgecolor='white', linewidth=1.2, label='6G / Sub-THz', zorder=3)

for bar, val, cor in zip(list(b4)+list(b6), v4g_c+v6g_c, [COR_4G]*3+[COR_6G]*3):
    ax_custo.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.015,
                  f'R$ {val:.2f} bi', ha='center', va='bottom',
                  fontsize=10.5, fontweight='bold', color=cor)

ax_custo.set_title("Comparativo de Custos — 4G vs 6G",
                   fontsize=13, fontweight='bold', pad=10)
ax_custo.set_ylabel("R$ Bilhões", fontsize=12)
ax_custo.set_xticks(x_c); ax_custo.set_xticklabels(cats, fontsize=12)
ax_custo.legend(fontsize=11, loc='upper left')
ax_custo.set_facecolor('#FAFAFA')
ax_custo.grid(axis='y', alpha=0.35, zorder=0)
ax_custo.set_ylim(0, max(v6g_c) * 1.22)
ax_custo.spines[['top','right']].set_visible(False)
# Linha de razão TCO
ax_custo.annotate(
    f"→ TCO do 6G é {razao_tco:.1f}× maior",
    xy=(2 + 0.22, tco_6g/1e9), xytext=(1.5, tco_6g/1e9 * 0.82),
    fontsize=10.5, color=COR_6G, fontweight='bold',
    arrowprops=dict(arrowstyle='->', color=COR_6G, lw=1.8))

# ── Gráfico de Energia ────────────────────────────────────────
ax_en = fig3.add_subplot(gs3[1, 2])

cats_e  = ['4G\n(305 ERBs)', '6G Small\nCells', '6G\nÂncoras']
vals_e  = [energia_4g_total/1000, energia_6g_sc_total/1000, energia_6g_anc_total/1000]
cores_e = [COR_4G, COR_6G, '#5B2C6F']

bars_e = ax_en.bar(cats_e, vals_e, color=cores_e, edgecolor='white',
                   linewidth=1.2, zorder=3, width=0.55)
for bar, val in zip(bars_e, vals_e):
    ax_en.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.008,
               f'{val:.2f} MW', ha='center', va='bottom',
               fontsize=11, fontweight='bold', color=bar.get_facecolor())

ax_en.set_title("Consumo Energético Total\nda Rede (contínuo)",
                fontsize=13, fontweight='bold', pad=10)
ax_en.set_ylabel("Megawatts (MW)", fontsize=12)
ax_en.set_facecolor('#FAFAFA')
ax_en.grid(axis='y', alpha=0.35, zorder=0)
ax_en.set_ylim(0, max(vals_e) * 1.28)
ax_en.spines[['top','right']].set_visible(False)
ax_en.tick_params(labelsize=11)

# Anotação total 6G
ax_en.annotate(
    f"6G total: {energia_6g_total/1000:.2f} MW\n({energia_6g_total/energia_4g_total:.1f}× mais que 4G)",
    xy=(1, energia_6g_sc_total/1000), xytext=(1.55, energia_6g_sc_total/1000 * 0.60),
    fontsize=9.5, ha='center', color=COR_6G, fontweight='bold',
    bbox=dict(facecolor='#F4ECF7', edgecolor=COR_6G, boxstyle='round,pad=0.3'),
    arrowprops=dict(arrowstyle='->', color=COR_6G, lw=1.5))

plt.tight_layout()
f3_path = os.path.join(OUTPUT_DIR, 'fig3_custos_energia.png')
fig3.savefig(f3_path, dpi=120, bbox_inches='tight', facecolor=COR_FUNDO_FIG)
print(f"✔ Figura 3 salva: {f3_path}")

print("\n✔ Todas as figuras geradas com sucesso!")
print("\n" + "="*90)
print("RELATÓRIO DE DIMENSIONAMENTO — SEÇÃO 4")
print("="*90)
print(f"""
PARÂMETROS POPULACIONAIS:
  Pop. total atual:             {POP_TOTAL:>12,}
  Pop. urbana (95%):            {POP_URBANA:>12,}
  Pop. rural (5%):              {POP_RURAL:>12,}
  Pop. alta demanda atual:      {POP_ALTA_BRUTA:>12,}   (PEA 60% + estudantes 5%)
  Pop. baixa demanda atual:     {POP_BAIXA_BRUTA:>12,}
  Taxa de crescimento 10 anos:  {'10,46%':>12}   (1% a.a., juros compostos)
  Pop. alta demanda (projeção): {POP_ALTA_PROJ:>12,}
  Pop. baixa demanda (projeção):{POP_BAIXA_PROJ:>12,}
  Pop. total projetada:         {POP_TOTAL_PROJ:>12,}

DISTRIBUIÇÃO DE ÁREA:
  Alta densidade (comerc./indust.): {n_alta:>5} km²
  Urbana média (residencial):       {n_media:>5} km²
  Rural/periférica:                 {n_rural:>5} km²

DENSIDADE MÉDIA POR ZONA:
  Alta densidade: {dens_alta:>8,.0f} hab/km²
  Urbana média:   {dens_media:>8,.0f} hab/km²
  Rural:          {dens_rural:>8,.0f} hab/km²

BASE STATIONS — 4G:
  Alta dens. (1 BS/km²):   {bs_4g_alta:>8.0f} ERBs
  Média dens. (0.5 BS/km²):{bs_4g_media:>8.0f} ERBs
  Rural (0.2 BS/km²):      {bs_4g_rural:>8.1f} ERBs
  TOTAL:                   {total_bs_4g:>8.0f} ERBs

BASE STATIONS — 6G:
  Small Cells (alta, 25/km²):  {sc_alta:>8.0f} SCs
  Small Cells (média, 6/km²):  {sc_media:>8.0f} SCs
  Âncoras macro (0.5/km²):     {total_ancora_6g:>8.0f} âncoras
  Rural fallback 4G:           {bs_6g_rural_fallback:>8.1f} ERBs
  TOTAL SCs:                   {total_sc_6g:>8.0f} SCs
  Razão 6G/4G em sites:        {total_sc_6g/total_bs_4g:>8.0f}×

CUSTOS FINANCEIROS:
  4G  CAPEX:           R$ {capex_4g/1e9:>8.2f} bi
  4G  OPEX (10 anos):  R$ {opex_4g/1e9:>8.2f} bi
  4G  TCO  (10 anos):  R$ {tco_4g/1e9:>8.2f} bi
  ─────────────────────────────────────
  6G  CAPEX:           R$ {capex_6g/1e9:>8.2f} bi
  6G  OPEX (10 anos):  R$ {opex_6g/1e9:>8.2f} bi
  6G  TCO  (10 anos):  R$ {tco_6g/1e9:>8.2f} bi
  ─────────────────────────────────────
  Razão CAPEX  6G/4G:  {razao_capex:>8.1f}×
  Razão TCO    6G/4G:  {razao_tco:>8.1f}×
  (Bertsias et al. 2024 reportam até 840% = 8.4× → resultado compatível)

CONSUMO ENERGÉTICO:
  4G total:            {energia_4g_total/1000:>8.1f} MW
  6G SCs:              {energia_6g_sc_total/1000:>8.1f} MW
  6G Âncoras:          {energia_6g_anc_total/1000:>8.1f} MW
  6G TOTAL:            {energia_6g_total/1000:>8.1f} MW
""")
print("="*90)
print(f"\nArquivos gerados em: {OUTPUT_DIR}")
