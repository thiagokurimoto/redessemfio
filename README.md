# Análise do Compromisso entre Cobertura e Eficiência Energética em Redes Móveis Metropolitanas
### Uma Abordagem Híbrida 4G/6G com Seleção Ótima de Relays Ad-Hoc

**Disciplina:** Redes Sem Fio — Universidade Federal do ABC (UFABC)  
**Integrantes:**
- Henrique Lima Santana — henrique.l@ufabc.edu.br
- Thiago Tadao Alves Kurimoto — thiago.kurimoto@ufabc.edu.br
- Tiago Barbosa Veiga Reis — tiago.barbosa@ufabc.edu.br

**Núcleo de Tecnologia da Informação — UFABC — Santo André/SP — 2026**

---

## 📋 Resumo do trabalho

Este repositório contém os simuladores computacionais desenvolvidos para o artigo científico no formato SBC. O trabalho analisa comparativamente as tecnologias **4G/LTE** e **6G/Sub-THz** para implantação de telefonia celular em uma cidade de **1 milhão de habitantes** em **500 km²**, avaliando retardo, jitter, taxa de transmissão, BER, CAPEX, OPEX e consumo energético.

Diante das limitações das soluções puras, propõe-se uma terceira via: uma **arquitetura híbrida Ad-Hoc cooperativa** com seleção ótima de relays para extensão de cobertura nas zonas de sombra.

---

## 📁 Estrutura do repositório

```
redessemfio/
│
├── README.md                              ← Este arquivo
├── requirements.txt                       ← Dependências Python
├── .gitignore                             ← Arquivos ignorados
│
├── simuladores/
│   ├── simulador_secao4.py                ← Seção 4 — Dimensionamento 4G e 6G
│   ├── simulador_secao43_hibrida.py       ← Seção 4.3 — Coexistência 4G+6G
│   └── simulador_secao6_adhoc.py          ← Seção 6 — Ad-Hoc com relay ótimo
│
├── docs/
│   ├── APENDICE_TECNICO.md                ← Apêndice técnico completo
│   └── PARAMETROS.md                      ← Tabela de parâmetros fixos (seed=42)
│
└── figuras/
    └── [geradas automaticamente pelos simuladores]
```

---

## ⚙️ Requisitos

- **Python:** 3.10 ou superior (testado em 3.12)
- **Ambiente recomendado:** Google Colaboratory
- **Dependências:**

```bash
pip install -r requirements.txt
```

ou diretamente:

```bash
pip install numpy matplotlib pandas scipy
```

---

## 🚀 Como executar no Google Colab

```python
# Célula 1 — Instalar dependências
!pip install numpy matplotlib pandas scipy

# Célula 2 — Clonar o repositório
!git clone https://github.com/thiagokurimoto/redessemfio.git
%cd redessemfio

# Célula 3 — Rodar os simuladores na ordem correta
!python simuladores/simulador_secao4.py
!python simuladores/simulador_secao43_hibrida.py
!python simuladores/simulador_secao6_adhoc.py
```

As figuras são salvas automaticamente na pasta `figuras/`.

---

## 🔬 Descrição dos simuladores

### `simulador_secao4.py` — Dimensionamento 4G e 6G

Modela a cidade como grade de **500 quadrantes de 1 km²** (25×20 km), classifica por zonas e calcula o dimensionamento de antenas para 4G e 6G.

| Saída | Descrição |
|-------|-----------|
| Figura 1 | Mapa de zonas e densidade populacional (cenário diurno) |
| Figura 2 | Mapa de infraestrutura 4G vs. 6G com resumo comparativo |
| Figura 3 | Comparativo CAPEX, OPEX, TCO e consumo energético |

**Resultados principais:**

| Parâmetro | 4G / LTE | 6G / Sub-THz |
|-----------|----------|--------------|
| Total de sítios | 305 ERBs | 5.225 SCs + 62 âncoras |
| CAPEX | R$ 0,15 bi | R$ 0,86 bi |
| TCO (10 anos) | R$ 0,40 bi | R$ 2,28 bi |
| Energia total | 457,5 kW | 1.700 kW |
| Razão de sítios | — | 17× mais que o 4G |

---

### `simulador_secao43_hibrida.py` — Coexistência 4G+6G

Implementa a solução de coexistência: **6G na zona de alta densidade** (ROI favorável) e **4G nas zonas de média densidade e rural**.

| Saída | Descrição |
|-------|-----------|
| Figura 4.3a | Mapa de cobertura tecnológica por zona |
| Figura 4.3b | Comparativo de métricas por zona |
| Figura 4.3c | Comparativo de custos e energia |

**Resultados principais:**

| Zona | Tecnologia | Retardo | BER | Vazão |
|------|-----------|---------|-----|-------|
| Alta densidade | 6G | 0,28 ms | ≈10⁻⁹ | 60 Gbps |
| Urbana média | 4G | 50,31 ms | 1,72×10⁻² | 100 Mbps |
| Rural | 4G (fallback) | 52,73 ms | 1,72×10⁻² | 100 Mbps |
| **CAPEX total** | | | | **R$ 0,63 bi** |

---

### `simulador_secao6_adhoc.py` — Redes Ad-Hoc com Seleção Ótima de Relays

Simula a terceira solução em zona de sombra de **6×6 km** com 150 usuários, 85 relays candidatos e 4 ERBs âncora.

| Saída | Descrição |
|-------|-----------|
| Figura 4 | Mapas de cobertura antes/depois + mapa de ganho |
| Figura 5 | Curvas BER vs. SNR (direto vs. relay-assistido) |
| Figura 6 | Consumo energético e distribuição de SINR |

**Resultados principais:**

| Métrica | Sem relay | Com relay | Melhora |
|---------|-----------|-----------|---------|
| Cobertura | 39,3% | **100%** | +60,7 p.p. |
| SINR média (sombra) | −1,3 dB | **+14,0 dB** | +15,3 dB |
| BER (sombra) | 1,16×10⁻¹ | **4,39×10⁻⁶** | 26.400× |
| Relays ativados | — | **40 de 85** | — |
| Energia | — | **1.291,5 kW** | −24% vs 6G |

---

## 🔁 Reprodutibilidade

**Todos os simuladores usam `np.random.seed(42)`**, garantindo resultados idênticos em qualquer execução. Para reproduzir exatamente:

1. Use Python 3.12
2. Instale as versões em `requirements.txt`
3. Execute os simuladores sem modificar parâmetros

---

## 📐 Modelos utilizados

**Propagação:** Modelo log-distância com shadowing gaussiano (ITU-R P.1411)
```
PL(d) = PL₀ + 10·n·log₁₀(d/d₀) + X_σ
```

| Enlace | Frequência | n | σ |
|--------|-----------|---|---|
| Macro (ERB→relay) | 700 MHz | 3,5 | 8 dB |
| D2D (relay→usuário) | 2,4 GHz | 2,5 | 4 dB |

**BER:** QPSK em canal AWGN (Proakis & Salehi, 2008)
```
BER = 0,5 × erfc(√SNR)
```

**Seleção de relay:**
```
k* = arg max { min(SINR_h1,k , SINR_h2,k) + 4·log₁₀(B_k) }
     sujeito a: B_k ≥ 0,20
```

---

## 📚 Referências principais

| Fonte | Uso no trabalho |
|-------|----------------|
| Bertsias et al. (2024) — IEEE Access | CAPEX 6G, modelo econômico |
| ITU-R (2023) — IMT-2030 Framework | Arquitetura 6G, densidades |
| Jamshed et al. (2024) — IEEE | Fundamentos D2D, Sidelink |
| Khan et al. (2019) — MDPI Sensors | Algoritmo de seleção de relay |
| Proakis & Salehi (2008) — Digital Comm. | Modelo BER QPSK/AWGN |
| 3GPP TR 36.814 | Densidades ERB 4G |
| ITU-R P.1411 | Modelo de propagação |

---

## 📄 Documentação técnica

- **[Apêndice Técnico](docs/APENDICE_TECNICO.md)** — premissas, modelos e limitações dos simuladores
- **[Tabela de Parâmetros](docs/PARAMETROS.md)** — todos os valores fixos com referências bibliográficas
