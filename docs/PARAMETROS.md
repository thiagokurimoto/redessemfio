# Tabela de Parâmetros Fixos — Referência de Reprodutibilidade

> ⚠️ **Não altere estes valores.** Qualquer modificação produz resultados diferentes
> dos publicados no artigo. Para experimentos alternativos, crie uma cópia do simulador.

---

## Parâmetros globais

| Parâmetro | Valor | Justificativa |
|-----------|-------|---------------|
| Semente aleatória | `42` | Reprodutibilidade científica |
| Grade da cidade | 25×20 km = 500 km² | Enunciado do problema |
| Número de quadrantes | 500 (1 km² cada) | Resolução da simulação |
| População total | 1.000.000 habitantes | Enunciado do problema |
| % zona urbana | 95% → 950.000 hab. | Hipótese demográfica |
| PEA + estudantes | 65% → alta demanda | Khodabandelou et al. (2016) |
| Taxa de crescimento | 1% a.a. (juros compostos) | Flanagan et al. (2005) |
| Horizonte de projeto | 10 anos | Savunen et al. (2025) |
| Horizonte de TCO | 10 anos | Padrão de mercado |

---

## Zonas territoriais

| Zona | Área | Densidade hab/km² | Classificação |
|------|------|--------------------|---------------|
| Alta densidade | 125 km² | ≈ 5.457 hab/km² | Comercial + Industrial |
| Urbana média | 350 km² | ≈ 944 hab/km² | Residencial |
| Rural/periférica | 25 km² | ≈ 1.469 hab/km² | Periferia + Zona rural |

---

## Parâmetros 4G / LTE

| Parâmetro | Valor | Referência |
|-----------|-------|-----------|
| Largura de banda (BW) | 20 MHz | 3GPP TR 36.814 |
| Eficiência espectral (η) | 5 bits/s/Hz | LTE-A, Releases 10–17 |
| **Vazão teórica por célula** | **100 Mbps** | BW × η |
| Frequência de propagação | 700 MHz | ITU-R P.1411 |
| Expoente de perda (n) | 3,5 (urbano-sub.) | ITU-R P.1411 |
| Shadowing (σ) | 8 dB | ITU-R P.1411 |
| Potência TX (ERB) | 46 dBm | Típico LTE macro |
| Consumo por ERB | 1,5 kW | Anatel (2023) |
| CAPEX por ERB | R$ 500.000 | Anatel (2023) |
| OPEX por ERB/ano | R$ 80.000 | Anatel (2023) |
| Densidade — alta dens. | 1 ERB/km² → raio ≈ 560 m | ITU-R M.2370 |
| Densidade — urb. média | 0,5 ERB/km² → raio ≈ 800 m | ITU-R M.2370 |
| Densidade — rural | 0,2 ERB/km² → raio ≈ 1,26 km | ITU-R M.2370 |
| **Total ERBs** | **305** | Simulação (seed=42) |

---

## Parâmetros 6G / Sub-THz

| Parâmetro | Valor | Referência |
|-----------|-------|-----------|
| Largura de banda (BW) | 2 GHz | ITU-R IMT-2030 |
| Eficiência espectral (η) | 30 bits/s/Hz | Tariq et al. (2020) |
| **Vazão teórica por SC** | **60 Gbps** | BW × η |
| Frequência enlace âncora | 6 GHz (simplificação) | Ver Apêndice A.8 — L3 |
| Consumo por small cell (SC) | 0,3 kW | Bertsias et al. (2024) |
| Consumo por âncora | 2,0 kW | Bertsias et al. (2024) |
| CAPEX por SC | R$ 150.000 | Bertsias et al. (2024) |
| CAPEX por âncora | R$ 1.200.000 | Bertsias et al. (2024) |
| OPEX por SC/ano | R$ 25.000 | Bertsias et al. (2024) |
| OPEX por âncora/ano | R$ 180.000 | Bertsias et al. (2024) |
| Densidade — alta dens. | 25 SCs/km² → raio ≈ 200 m | ITU-R IMT-2030 |
| Densidade — urb. média | 6 SCs/km² → raio ≈ 400 m | ITU-R IMT-2030 |
| Densidade — rural | **INVIÁVEL** | Física Sub-THz |
| **Total SCs** | **5.225 + 62 âncoras** | Simulação (seed=42) |

---

## Parâmetros do modelo de propagação

| Parâmetro | Enlace Macro | Enlace D2D | Referência |
|-----------|-------------|-----------|-----------|
| Frequência | 700 MHz | 2,4 GHz | ITU-R P.1411 |
| PL₀ (@ d₀=1m) | 29,3 dB | 40,1 dB | Calculado |
| Expoente n | 3,5 | 2,5 | ITU-R P.1411 |
| Shadowing σ | 8 dB | 4 dB | ITU-R P.1411 |
| Ruído N₀ | −174 dBm/Hz | −174 dBm/Hz | Físico |
| BW do ruído | 20 MHz | 20 MHz | LTE |
| Ruído total | ≈ −101 dBm | ≈ −101 dBm | N₀ × BW |
| **SINR mínima (limiar)** | **3,0 dB** | **3,0 dB** | QPSK, BER ≈ 5×10⁻³ |

---

## Parâmetros do algoritmo de relay (Seção 6)

| Parâmetro | Valor | Referência |
|-----------|-------|-----------|
| Potência TX relay móvel | 23 dBm | 3GPP Sidelink |
| Potência TX relay fixo | 30 dBm | — |
| Bateria relay móvel | Beta(2,5; 1,5) | Modelagem realista |
| Bateria relay fixo | ∞ (rede elétrica) | — |
| **Limiar de bateria (B_min)** | **20%** | Khan et al. (2019) |
| Fator de ponderação bateria | 4 × log₁₀(B_k) | Khan et al. (2019) |
| Critério de seleção | max { min(SINR_h1,k, SINR_h2,k) + 4·log₁₀(B_k) } | Khan et al. (2019) |
| Usuários simulados | 150 | — |
| Relays móveis | 60 | — |
| Relays fixos | 25 | — |
| **Total relays candidatos** | **85** | — |
| ERBs âncora | 4 | — |
| Área do cenário | 6×6 km | Zona de sombra periférica |
| Resolução da grade de cobertura | 120×120 pontos | — |

---

## Modelo de BER

```
BER = 0,5 × erfc(√SNR)

Onde:
  erfc = função erro complementar
  SNR  = 10^(SINR_dB / 10)   [linear]
```

**Modulação:** QPSK  
**Canal:** AWGN  
**Referência:** Proakis & Salehi (2008) — *Digital Communications*, 5ª ed.

---

## Resultados consolidados — NÃO ALTERAR

Estes são os valores gerados pela simulação com `seed = 42` e devem ser reproduzidos
integralmente ao executar os simuladores sem modificações:

| Solução | CAPEX | Energia | BER alta dens. | BER zona sombra | Cobertura |
|---------|-------|---------|----------------|-----------------|-----------|
| 4G puro | R$ 0,15 bi | 457,5 kW | 6,81×10⁻¹³ | 1,16×10⁻¹ | Parcial |
| 6G puro | R$ 0,86 bi | 1.700 kW | ≈10⁻⁹ | N/A | ~98% (urb.) |
| Coexistência | R$ 0,63 bi | 1.332,5 kW | ≈10⁻⁹ | 1,72×10⁻² | Parcial |
| Ad-Hoc | R$ 0,61 bi | 1.291,5 kW | — | **4,39×10⁻⁶** | **100%** |

**Ganhos da solução Ad-Hoc vs. enlace direto:**

| Métrica | Antes (sem relay) | Depois (com relay) | Ganho |
|---------|------------------|--------------------|-------|
| Cobertura | 39,3% | 100% | +60,7 p.p. |
| SINR (sombra) | −1,3 dB | +14,0 dB | +15,3 dB |
| BER (sombra) | 1,16×10⁻¹ | 4,39×10⁻⁶ | 26.400× |
| Relays ativados | — | 40 de 85 | — |

---

*Última atualização: Abril 2026*
