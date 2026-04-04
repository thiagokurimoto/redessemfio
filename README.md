# Análise do Compromisso entre Cobertura e Eficiência Energética em Redes Ad-Hoc Rurais
### Um Modelo Auto-Organizável com Mitigação de Interferência via Seleção Ótima de Relays

**Disciplina:** Redes Sem Fio — Universidade Federal do ABC (UFABC)  
**Autores:** Henrique Lima Santana · Thiago Tadao Alves Kurimoto · Tiago Barbosa Veiga Reis  
**Núcleo de Tecnologia da Informação — UFABC — Santo André/SP**

---

## 📋 Sobre o trabalho

Este repositório contém os simuladores computacionais desenvolvidos para o artigo científico submetido no formato SBC (Sociedade Brasileira de Computação). O trabalho analisa comparativamente as tecnologias **4G/LTE** e **6G/Sub-THz** para implantação de telefonia celular em uma cidade de **1 milhão de habitantes** distribuídos em **500 km²**, avaliando as métricas de retardo, jitter, taxa de transmissão, BER, CAPEX, OPEX e consumo energético.

Diante das limitações identificadas nas soluções puras, propõe-se uma terceira via: uma **arquitetura híbrida Ad-Hoc cooperativa** com seleção ótima de relays para extensão de cobertura nas zonas de sombra.

---

## 📁 Estrutura do repositório

```
rede-celular-1M-habitantes-UFABC/
│
├── README.md                          # Este arquivo
├── requirements.txt                   # Dependências Python
├── .gitignore                         # Arquivos ignorados pelo Git
│
├── simuladores/
│   ├── simulador_secao4.py            # Seção 4 — Dimensionamento 4G e 6G
│   ├── simulador_secao43_hibrida.py   # Seção 4.3 — Solução Híbrida 4G+6G
│   └── simulador_secao6_adhoc.py      # Seção 6 — Redes Ad-Hoc com Relay
│
├── figuras/                           # Figuras geradas pelos simuladores (PNG)
│   └── [geradas automaticamente ao rodar os simuladores]
│
└── docs/
    └── PARAMETROS.md                  # Tabela de parâmetros fixos e referências
```

---

## ⚙️ Requisitos

- **Python:** 3.10 ou superior (testado em 3.12)
- **Ambiente recomendado:** Google Colaboratory (Colab) ou Jupyter Notebook
- **Sistema operacional:** Windows, macOS ou Linux

### Dependências

```bash
pip install numpy matplotlib pandas scipy
```

Ou instale a partir do arquivo de requisitos:

```bash
pip install -r requirements.txt
```

---

## 🚀 Como executar — passo a passo

### Opção A — Google Colab (recomendado)

1. Acesse [colab.research.google.com](https://colab.research.google.com)
2. Crie um novo notebook
3. Na primeira célula, instale as dependências:
```python
!pip install numpy matplotlib pandas scipy
```
4. Copie o conteúdo do simulador desejado para uma nova célula
5. Execute com **Shift + Enter**

### Opção B — Execução local

```bash
# Clone o repositório
git clone https://github.com/[SEU_USUARIO]/rede-celular-1M-habitantes-UFABC.git
cd rede-celular-1M-habitantes-UFABC

# Instale as dependências
pip install -r requirements.txt

# Execute os simuladores na ordem correta
python simuladores/simulador_secao4.py
python simuladores/simulador_secao43_hibrida.py
python simuladores/simulador_secao6_adhoc.py
```

---

## 🔬 Descrição dos simuladores

### `simulador_secao4.py` — Dimensionamento 4G e 6G

Modela a cidade como uma grade de **500 quadrantes de 1 km²** (25×20 km), classifica cada quadrante em zonas de densidade e calcula o número de antenas necessárias para cada tecnologia.

**Saídas:**
- Mapa de zonas territoriais
- Mapa de calor de densidade populacional (cenário diurno)
- Mapa de distribuição de ERBs 4G
- Mapa de distribuição de Small Cells 6G
- Comparativo de CAPEX, OPEX, TCO e energia

**Parâmetros principais:**

| Parâmetro | 4G/LTE | 6G/Sub-THz |
|-----------|--------|-----------|
| Banda (BW) | 20 MHz | 2 GHz |
| Eficiência espectral | 5 bits/s/Hz | 30 bits/s/Hz |
| ERBs / SCs por km² (alta dens.) | 1 ERB | 25 SCs |
| ERBs / SCs por km² (méd. dens.) | 0,5 ERB | 6 SCs |
| ERBs por km² (rural) | 0,2 ERB | Inviável |
| Total de sítios | 305 ERBs | 5.225 SCs + 62 âncoras |
| CAPEX total | R$ 0,15 bi | R$ 0,86 bi |
| Consumo energético | 457,5 kW | 1.700 kW |

---

### `simulador_secao43_hibrida.py` — Solução Híbrida 4G+6G

Implementa a solução híbrida: **6G exclusivamente na zona de alta densidade** (ROI favorável) e **4G nas zonas de média densidade e rural**.

**Saídas:**
- Mapa de cobertura tecnológica por zona
- Comparativo de métricas por zona (retardo, jitter, BER, vazão)
- Comparativo de custos e energia entre as 3 soluções

**Resultados obtidos:**

| Zona | Tecnologia | Retardo | BER | Vazão |
|------|-----------|---------|-----|-------|
| Alta densidade | 6G | 0,28 ms | ≈ 10⁻⁹ | 60 Gbps |
| Urbana média | 4G | 50,3 ms | 1,72×10⁻² | 100 Mbps |
| Rural | 4G | 52,7 ms | 1,72×10⁻² | 100 Mbps |
| **CAPEX híbrida** | | | | **R$ 0,63 bi** |

---

### `simulador_secao6_adhoc.py` — Redes Ad-Hoc com Seleção Ótima de Relays

Simula a terceira solução em uma zona de sombra de **6×6 km** com 150 usuários, 85 relays candidatos e 4 ERBs âncora. Implementa o algoritmo de seleção de relay baseado em SINR e nível de bateria.

**Saídas:**
- Mapa de cobertura antes e após a seleção de relay
- Mapa de ganho de área
- Curvas BER vs. SNR (enlace direto vs. relay-assistido)
- Consumo energético comparativo
- Distribuição de SINR antes e após o relay

**Resultados obtidos:**

| Métrica | Sem relay | Com relay | Ganho |
|---------|-----------|-----------|-------|
| Cobertura | 39,3% | 100% | +60,7 p.p. |
| SINR média (sombra) | −1,3 dB | +14,0 dB | +15,3 dB |
| BER (zona de sombra) | 1,16×10⁻¹ | 4,39×10⁻⁶ | 26.400× |
| Relays ativados | — | 40 de 85 | — |

---

## 🔁 Reprodutibilidade

**Todos os simuladores utilizam `np.random.seed(42)`**, garantindo que qualquer execução produz resultados numericamente idênticos aos publicados no artigo. Para reproduzir exatamente os resultados:

1. Use Python 3.12
2. Instale as versões especificadas em `requirements.txt`
3. Execute os simuladores sem modificar os parâmetros
4. As figuras salvas serão idênticas às do artigo

---

## 📐 Modelo de propagação

O canal de rádio é modelado pelo **modelo log-distância com shadowing gaussiano** (ITU-R P.1411):

```
PL(d) = PL₀ + 10·n·log₁₀(d/d₀) + X_σ
```

| Enlace | Frequência | Expoente n | Shadowing σ | Referência |
|--------|-----------|-----------|-------------|-----------|
| Macro (ERB→relay) | 700 MHz | 3,5 | 8 dB | ITU-R P.1411 |
| D2D (relay→usuário) | 2,4 GHz | 2,5 | 4 dB | Jamshed et al. (2024) |

**Modelo de BER:** QPSK em canal AWGN — `BER = 0,5 × erfc(√SNR)` [Proakis, 2008]

---

## 📚 Referências principais

| Ref. | Fonte |
|------|-------|
| [1] | Bertsias et al. (2024) — IEEE Access — CAPEX 6G |
| [2] | ITU-R (2023) — IMT-2030 Framework — arquitetura 6G |
| [3] | Jamshed et al. (2024) — IEEE — fundamentos D2D |
| [4] | Khan et al. (2019) — MDPI Sensors — seleção de relay |
| [5] | Proakis & Salehi (2008) — Digital Communications — modelo BER |
| [9] | 3GPP TR 36.814 — densidades de ERBs |
| [11] | ITU-R P.1411 — modelo de propagação |

---

## ⚠️ Limitações declaradas

1. **Vazão teórica:** valores calculados pelo limite de Shannon (BW × η), sem overhead de protocolo. A vazão real é tipicamente 60–80% do valor teórico.
2. **Modelo AWGN:** simplificação do canal real. Modelos de ray-tracing produziriam maior precisão, mas requerem mapas urbanos detalhados.
3. **Frequência do enlace 6G:** o simulador usa 6 GHz para o enlace de ancoragem em vez dos 100+ GHz reais do Sub-THz, pois o modelo de absorção molecular (ITU-R P.676) exige dados atmosféricos específicos indisponíveis neste estudo. A simplificação é conservadora — reforça, não enfraquece, as conclusões sobre a inviabilidade rural do 6G.
4. **Cenário estático:** mobilidade de usuários e relays não é modelada.

---

## 📄 Artigo

O artigo completo está disponível em: **[INSERIR LINK DO PDF]**

---

## 📧 Contato

- henrique.l@ufabc.edu.br
- thiago.kurimoto@ufabc.edu.br
- tiagoveigareis@gmail.com

**UFABC — Núcleo de Tecnologia da Informação — Santo André/SP — 2026**
