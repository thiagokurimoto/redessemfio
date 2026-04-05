# Tabela de Parâmetros Fixos — Referência de Reprodutibilidade

Este arquivo documenta todos os parâmetros imutáveis utilizados nos três
simuladores. Qualquer alteração nestes valores produz resultados diferentes
dos publicados no artigo.

---

## Parâmetros globais

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| Semente aleatória | `42` | Reprodutibilidade científica |
| Área total | 500 km² (grade 25×20 km) | Enunciado do problema |
| População total | 1.000.000 hab. | Enunciado do problema |
| % zona urbana | 95% → 950.000 hab. | Hipótese demográfica |
| % alta demanda (PEA + estudantes) | 65% → 617.500 hab. | Hipótese de tráfego |
| Taxa de crescimento | 1% a.a. (juros compostos, 10 anos) | Hipótese de planejamento |
| Horizonte de TCO | 10 anos | Padrão de mercado |

---

## Zonas territoriais

| Zona | Área | Densidade média | Classificação |
|------|------|----------------|---------------|
| Alta densidade | 125 km² | 5.457 hab/km² | Comercial + Industrial |
| Urbana média | 350 km² | 944 hab/km² | Residencial |
| Rural/periférica | 25 km² | 1.469 hab/km² | Periferia + Fazendas |

---

## Parâmetros 4G / LTE

| Parâmetro | Valor | Referência |
|-----------|-------|-----------|
| Largura de banda | 20 MHz | 3GPP TR 36.814 |
| Eficiência espectral | 5 bits/s/Hz | LTE-A (3GPP Rel. 10–17) |
| Vazão teórica por célula | 100 Mbps | BW × η |
| Potência TX (ERB) | 46 dBm | Típico LTE macro |
| Consumo por ERB | 1,5 kW | Anatel (2023) |
| CAPEX por ERB | R$ 500.000 | Anatel (2023) |
| OPEX por ERB/ano | R$ 80.000 | Anatel (2023) |
| Densidade — alta dens. | 1 ERB/km² (raio ≈ 560 m) | 3GPP TR 36.814 |
| Densidade — urb. média | 0,5 ERB/km² (raio ≈ 800 m) | 3GPP TR 36.814 |
| Densidade — rural | 0,2 ERB/km² (raio ≈ 1,26 km) | ITU-R M.2370 |
| **Total ERBs** | **305** | Simulação |

---

## Parâmetros 6G / Sub-THz

| Parâmetro | Valor | Referência |
|-----------|-------|-----------|
| Largura de banda | 2 GHz | ITU-R IMT-2030 |
| Eficiência espectral | 30 bits/s/Hz | Tariq et al. (2020) |
| Vazão teórica por SC | 60 Gbps | BW × η |
| Consumo por small cell | 0,3 kW | Bertsias et al. (2024) |
| Consumo por âncora | 2,0 kW | Bertsias et al. (2024) |
| CAPEX por small cell | R$ 150.000 | Bertsias et al. (2024) |
| CAPEX por âncora | R$ 1.200.000 | Bertsias et al. (2024) |
| OPEX por SC/ano | R$ 25.000 | Bertsias et al. (2024) |
| OPEX por âncora/ano | R$ 180.000 | Bertsias et al. (2024) |
| Densidade — alta dens. | 25 SCs/km² (raio ≈ 200 m) | Bertsias et al. (2024) |
| Densidade — urb. média | 6 SCs/km² (raio ≈ 400 m) | ITU-R IMT-2030 |
| Densidade — rural | Inviável | Física Sub-THz |
| **Total SCs** | **5.225 + 62 âncoras** | Simulação |

---

## Parâmetros do modelo de propagação

| Parâmetro | Enlace macro | Enlace D2D | Referência |
|-----------|-------------|-----------|-----------|
| Frequência | 700 MHz | 2,4 GHz | ITU-R P.1411 |
| PL₀ (@ 1m) | 29,3 dB | 40,1 dB | Calculado |
| Expoente n | 3,5 | 2,5 | ITU-R P.1411 |
| Shadowing σ | 8 dB | 4 dB | ITU-R P.1411 |
| Ruído N₀ | −174 dBm/Hz | −174 dBm/Hz | Padrão |
| Largura de banda ruído | 20 MHz | 20 MHz | LTE |
| Ruído total | ≈ −101 dBm | ≈ −101 dBm | N₀ × BW |
| SINR mínima (limiar) | 3,0 dB | 3,0 dB | QPSK, BER ≈ 5×10⁻³ |

---

## Parâmetros do algoritmo de relay (Seção 6)

| Parâmetro | Valor | Referência |
|-----------|-------|-----------|
| Potência TX relay móvel | 23 dBm (200 mW) | 3GPP Sidelink |
| Potência TX relay fixo | 30 dBm (1 W) | — |
| Limiar de bateria (B_min) | 20% | Khan et al. (2019) |
| Fator de ponderação bateria | 4 × log₁₀(B_k) | Khan et al. (2019) |
| Critério de seleção | max { min(SINR_h1, SINR_h2) + 4·log₁₀(B_k) } | Khan et al. (2019) |
| Usuários simulados | 150 | — |
| Relays candidatos (total) | 85 (60 móveis + 25 fixos) | — |
| ERBs âncora | 4 | — |
| Área do cenário | 6×6 km | Zona de sombra periférica |
| Resolução da grade | 120×120 pontos | — |

---

## Modelo de BER

```
BER = 0,5 × erfc(√SNR)

Onde:
  erfc = função erro complementar
  SNR  = 10^(SINR_dB / 10)   [linear]
```

Modulação: QPSK | Canal: AWGN | Referência: Proakis & Salehi (2008)

---

## Resultados consolidados (não alterar)

| Solução | CAPEX | Energia | BER alta dens. | BER rural | Cobertura |
|---------|-------|---------|----------------|-----------|-----------|
| 4G puro | R$ 0,15 bi | 457,5 kW | 6,81×10⁻¹³ | 1,72×10⁻² | Parcial |
| 6G puro | R$ 0,86 bi | 1.700 kW | ≈ 10⁻⁹ | N/A | ~98% (urb.) |
| Híbrida | R$ 0,63 bi | 1.332,5 kW | ≈ 10⁻⁹ | 1,72×10⁻² | Parcial |
| Ad-Hoc | R$ 0,61 bi | 1.291,5 kW | — | 4,39×10⁻⁶ | 100% |

> ⚠️ Estes valores foram gerados com `seed=42` e não devem ser modificados
> manualmente. Para reproduzi-los, execute os simuladores sem alterar parâmetros.

---

**Última atualização:** Abril 2026  
**Semente:** `np.random.seed(42)` — fixada em todos os simuladores
