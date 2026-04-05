# Apêndice Técnico — Premissas e Metodologia dos Simuladores

**Artigo:** Análise do Compromisso entre Cobertura e Eficiência Energética em Redes Móveis Metropolitanas  
**Disciplina:** Redes Sem Fio — UFABC — 2026  


---

> Este apêndice documenta os parâmetros, modelos e decisões metodológicas adotados nos três
> simuladores. O objetivo é garantir a **reprodutibilidade integral** dos experimentos e fornecer
> base técnica suficiente para auditoria dos resultados.

---

## A.1 Reprodutibilidade

Todos os simuladores fixam a semente aleatória com a instrução:

```python
np.random.seed(42)
```

Esta instrução garante que qualquer pessoa que execute o código nas mesmas condições obtenha
resultados numericamente idênticos aos publicados no artigo. A escolha do valor `42` é arbitrária
— qualquer inteiro fixo cumpriria a mesma função. O importante é que o valor esteja documentado
e seja imutável entre execuções.

**Por que isso importa:** os simuladores usam distribuições aleatórias para modelar
variabilidades reais do canal de rádio, como o *shadowing* gaussiano que representa obstáculos
imprevisíveis no caminho do sinal. Sem semente fixa, cada execução geraria resultados diferentes,
tornando o experimento irreproduzível e, portanto, não verificável cientificamente.

---

## A.2 Ambiente de Execução

| Item | Especificação |
|------|---------------|
| Linguagem | Python 3.12 |
| Ambiente | Google Colaboratory (Colab) |
| NumPy | 1.26.4 |
| SciPy | 1.13.0 |
| Matplotlib | 3.8.4 |
| Pandas | 2.2.2 |

Para instalar as dependências:

```bash
pip install numpy==1.26.4 matplotlib==3.8.4 pandas==2.2.2 scipy==1.13.0
```

---

## A.3 Modelo de Propagação

O canal de rádio é modelado pelo **modelo log-distância com shadowing gaussiano**,
referenciado na Recomendação ITU-R P.1411:

```
PL(d) = PL₀ + 10·n·log₁₀(d/d₀) + X_σ
```

**Onde:**
- `PL₀` = perda de percurso a 1 metro: `20·log₁₀(4π/λ)` [dB]
- `n` = expoente de perda de percurso (adimensional)
- `d` = distância em metros
- `d₀` = distância de referência = 1 m
- `X_σ` = variável aleatória gaussiana: `X_σ ~ N(0, σ²)` [dB]

### Parâmetros por enlace

| Enlace | Frequência | Expoente n | Shadowing σ | Referência |
|--------|-----------|-----------|-------------|-----------|
| Macro — ERB→relay/usuário | 700 MHz | 3,5 | 8 dB | ITU-R P.1411 |
| D2D — relay→usuário | 2,4 GHz | 2,5 | 4 dB | Jamshed et al. (2024) |

### Valores de referência para o expoente n

| Ambiente | n típico |
|----------|---------|
| Espaço livre (sem obstáculos) | 2,0 |
| D2D — curta distância, obstáculos parciais | 2,5 |
| **Urbano/suburbano — cenário deste estudo** | **3,5** |
| Interior de edifícios | 4,0 |
| Corredores e ambientes muito obstruídos | 5,0 |

### Cálculo do ruído total

```
N_total = N₀ · BW
N₀ = −174 dBm/Hz (densidade espectral de ruído térmico a 290 K)
BW = 20 MHz (4G) → N_total ≈ −101 dBm
```

### Cálculo da SINR

```
SINR [dB] = P_TX [dBm] − PL(d) [dB] − N_total [dBm]
```

---

## A.4 Modelo de BER — QPSK/AWGN

A Taxa de Erro de Bit (BER) é calculada pelo modelo analítico para QPSK em canal AWGN,
conforme Proakis & Salehi (2008):

```
BER = 0,5 × erfc(√SNR)
```

**Onde:**
- `erfc(·)` = função erro complementar
- `SNR` = relação sinal-ruído linear: `SNR = 10^(SINR_dB / 10)`

### Tabela de referência BER × requisito de serviço

| BER | Interpretação | Serviço típico |
|-----|--------------|----------------|
| 10⁻¹ | 1 em 10 bits com erro | Canal inutilizável |
| 10⁻³ | 1 em 1.000 bits | **Limiar mínimo para VoIP** |
| 10⁻⁶ | 1 em 1.000.000 bits | Dados críticos |
| 10⁻⁹ | 1 em 1 bilhão de bits | Excelente (6G em zonas densas) |

### Por que QPSK e não outra modulação?

QPSK (*Quadrature Phase Shift Keying*) é a modulação de referência para análise comparativa
de sistemas de comunicação. Representa o caso base — não o melhor nem o pior. O uso de
modulações de alta ordem como 64-QAM produziria BER muito menor nas zonas boas e muito
maior nas ruins, mascarando as diferenças entre soluções. O QPSK é o padrão metodológico
correto para comparação justa entre tecnologias.

### Por que AWGN e não desvanecimento Rayleigh?

O modelo AWGN (*Additive White Gaussian Noise*) é o padrão de canal para comparação em
nível de sistema (*system-level simulation*). Modelos com desvanecimento seletivo em frequência,
como Rayleigh, exigem parâmetros de canal específicos do ambiente que não estão disponíveis para
o cenário urbano genérico modelado. O AWGN é a escolha metodologicamente correta para análise
comparativa de primeiro nível, e seu uso está documentado como limitação declarada (Seção A.8).

---

## A.5 Simulador da Seção 4 — Dimensionamento 4G e 6G

**Arquivo:** `simuladores/simulador_secao4.py`

### O que faz

1. Constrói uma grade de 500 quadrantes de 1 km² (25×20 km) representando a cidade
2. Atribui a cada quadrante uma zona de densidade (alta, média ou rural) conforme o mapa
3. Calcula o número de antenas necessárias por zona para cada tecnologia
4. Computa CAPEX, OPEX, TCO e consumo energético
5. Gera as Figuras 1, 2 e 3 do artigo

### Parâmetros principais

| Parâmetro | 4G / LTE | 6G / Sub-THz |
|-----------|----------|--------------|
| Banda (BW) | 20 MHz | 2 GHz |
| Eficiência espectral (η) | 5 bits/s/Hz | 30 bits/s/Hz |
| Densidade — alta dens. | 1 ERB/km² | 25 SCs/km² |
| Densidade — urb. média | 0,5 ERB/km² | 6 SCs/km² |
| Densidade — rural | 0,2 ERB/km² | Inviável |
| Consumo por sítio | 1,5 kW/ERB | 0,3 kW/SC; 2,0 kW/âncora |
| CAPEX por sítio | R$ 500.000/ERB | R$ 150.000/SC; R$ 1.200.000/âncora |
| OPEX anual por sítio | R$ 80.000/ERB | R$ 25.000/SC; R$ 180.000/âncora |

### Variabilidade estocástica

O mapa de densidade populacional introduz perturbações gaussianas (±20% a ±50% por zona),
reproduzindo a heterogeneidade real de distribuição urbana. O resultado é determinístico para
`seed = 42`.

---

## A.6 Simulador da Seção 4.3 — Coexistência 4G+6G

**Arquivo:** `simuladores/simulador_secao43_hibrida.py`

### O que faz

1. Reutiliza a grade da Seção 4
2. Aplica lógica de partição tecnológica: 6G em alta densidade (> 4.000 hab/km²), 4G nas demais
3. Calcula métricas de retardo, jitter e BER por zona para as três soluções (4G, 6G, coexistência)
4. Compara custos e consumo energético
5. Gera as Figuras 4.3a, 4.3b e 4.3c do artigo

### Critério de partição tecnológica

A decisão de implantar 6G apenas na zona de alta densidade é baseada em análise de
Retorno sobre Investimento (ROI). Bertsias et al. (2024) demonstram que o CAPEX do 6G
pode ser até 840% superior ao das redes legadas. Em zonas com densidade superior a
4.000 hab/km², o número de usuários por *small cell* comprime o custo unitário a ponto de
tornar o investimento economicamente justificável em horizonte de até três anos. Nas zonas
de menor densidade, esse equilíbrio não se verifica.

---

## A.7 Simulador da Seção 6 — Redes Ad-Hoc com Seleção Ótima de Relay

**Arquivo:** `simuladores/simulador_secao6_adhoc.py`

### O que faz

1. Modela zona de sombra de 6×6 km com 150 usuários, 85 relays candidatos e 4 ERBs âncora
2. Calcula SINR do enlace direto (ERB→usuário) para cada usuário
3. Para usuários com SINR < 3,0 dB, busca o melhor relay disponível
4. Aplica o algoritmo de seleção ótima
5. Calcula cobertura, SINR e BER antes e após o relay
6. Gera as Figuras 4, 5 e 6 do artigo

### Distribuição dos relays

| Tipo | Quantidade | Bateria | Potência TX |
|------|-----------|---------|-------------|
| Relay móvel (smartphone D2D) | 60 | Beta(2,5; 1,5) | 23 dBm |
| Relay fixo (poste de iluminação) | 25 | ∞ (alimentação contínua) | 30 dBm |

A distribuição Beta(2,5; 1,5) representa realisticamente a distribuição de carga de bateria
em terminais em uso ativo — assimétrica para a direita, indicando que a maioria dos
terminais está com bateria em nível médio-alto.

### Algoritmo de seleção de relay

```
k* = arg max { min(SINR_h1,k , SINR_h2,k) + 4·log₁₀(B_k) }
     sujeito a: B_k ≥ B_min = 0,20
```

**Onde:**
- `SINR_h1,k` = SINR do enlace ERB→relay k (modelo macro, 700 MHz, n=3,5, σ=8 dB)
- `SINR_h2,k` = SINR do enlace relay k→usuário (modelo D2D, 2,4 GHz, n=2,5, σ=4 dB)
- `B_k` = nível de bateria normalizado do relay k ∈ [0, 1]
- `B_min = 0,20` = limiar de exclusão (20%)
- `min(SINR_h1,k, SINR_h2,k)` captura o gargalo do enlace de dois saltos

**Por que o limiar de 20% de bateria?**  
Para proteger o usuário dono do terminal cooperante. Um smartphone com 15% de bateria
descarrega rapidamente no modo D2D, prejudicando o cooperante e eventualmente retirando
o relay da malha quando mais se precisa dele. O limiar de 20% é o ponto de equilíbrio
identificado por Khan et al. (2019) em experimentos com smartphones reais.

### Cálculo da cobertura de área

A cobertura é calculada em uma grade de 120×120 pontos. Para cada ponto, avalia-se a
SINR máxima entre o enlace direto e todos os enlaces relay-assistidos viáveis. O ponto é
considerado coberto se a SINR máxima ≥ 3,0 dB.

---

## A.8 Limitações Declaradas

As seguintes limitações são inerentes à metodologia adotada e não invalidam as conclusões
comparativas do artigo:

### L1 — Vazão teórica

Os valores de taxa de transmissão são calculados pelo limite de Shannon (`BW × η`) sem
considerar overheads de protocolo, sinalização, retransmissões ou ocupação do canal.
Na prática, a vazão efetiva é tipicamente 60–80% do valor teórico.

### L2 — Modelo de canal simplificado

O modelo AWGN é uma simplificação do canal real. Modelos de traçado de raios (*ray-tracing*)
produziriam maior precisão, mas demandariam mapas urbanos detalhados com geometria de
edificações, indisponíveis neste estudo.

### L3 — Frequência do enlace 6G

O simulador adota **6 GHz** para o enlace de ancoragem 6G em vez das frequências
Sub-THz reais (100 GHz – 1 THz). O motivo é que o modelo de absorção molecular
(ITU-R P.676) exige dados atmosféricos específicos — temperatura, pressão, umidade —
indisponíveis para o cenário genérico modelado.

Esta simplificação é **conservadora**: a 6 GHz, a atenuação já é significativa. A frequências
de 100 GHz, seria ainda maior, reforçando — e não enfraquecendo — as conclusões sobre
a inviabilidade do 6G na zona rural.

### L4 — Cenário estático

A mobilidade de usuários e relays não é modelada — trata-se de um cenário *snapshot*.
O impacto da mobilidade veicular sobre a reestruturação dinâmica da malha Ad-Hoc é
apontado como trabalho futuro.

### L5 — Interferência simplificada

A interferência entre células vizinhas é representada por um termo fixo, não por um modelo
de interferência dinâmica. Em cenários reais com alta densificação de *small cells* 6G, a
gestão de interferência é um problema ativo de pesquisa.

---

## A.9 Execução e Saídas Esperadas

### Ordem de execução recomendada

```bash
python simuladores/simulador_secao4.py        # ~30 segundos
python simuladores/simulador_secao43_hibrida.py  # ~45 segundos
python simuladores/simulador_secao6_adhoc.py  # ~60 segundos
```

### Saídas geradas

Após a execução completa, a pasta `figuras/` conterá:

| Arquivo | Seção | Descrição |
|---------|-------|-----------|
| `fig1_mapa_zonas_populacao.png` | 4 | Mapa de zonas e densidade populacional |
| `fig2_infraestrutura_redesign.png` | 4 | Infraestrutura 4G vs. 6G |
| `fig3_custos_energia.png` | 4 | CAPEX, OPEX, TCO e energia |
| `fig4a_mapa_hibrida.png` | 4.3 | Cobertura tecnológica por zona |
| `fig4b_metricas_hibrida.png` | 4.3 | Métricas por zona |
| `fig4c_tabela_comparativa.png` | 4.3 | Custos e energia comparados |
| `fig4_mapas_cobertura.png` | 6 | Antes/depois do relay + mapa de ganho |
| `fig5_ber_comparativo.png` | 6 | Curvas BER vs. SNR |
| `fig6_energia_sinr.png` | 6 | Energia e distribuição de SINR |

### Verificação dos resultados

Os seguintes valores devem ser reproduzidos exatamente com `seed = 42`:

```
Dimensionamento 4G:    305 ERBs  | CAPEX R$ 0,15 bi | Energia 457,5 kW
Dimensionamento 6G:  5.225 SCs + 62 âncoras | CAPEX R$ 0,86 bi | Energia 1.700 kW
Coexistência:        3.125 SCs + 175 ERBs + 5 ERBs | CAPEX R$ 0,63 bi | Energia 1.332,5 kW
Ad-Hoc — cobertura: 39,3% → 100% (+60,7 p.p.)
Ad-Hoc — BER:       1,16×10⁻¹ → 4,39×10⁻⁶ (redução de 26.400×)
Ad-Hoc — SINR:      −1,3 dB → +14,0 dB (+15,3 dB de ganho)
Ad-Hoc — relays:    40 ativados de 85 candidatos
```

Qualquer desvio desses valores indica que os parâmetros foram alterados ou que a semente
aleatória não foi aplicada corretamente.

---

## A.10 Referências do Apêndice

| Referência | Relevância |
|-----------|-----------|
| ITU-R P.1411 (2019) | Modelo de propagação macro e D2D |
| Proakis & Salehi (2008) — *Digital Communications* | Modelo BER QPSK/AWGN |
| Khan et al. (2019) — MDPI Sensors | Algoritmo de seleção de relay e limiar de bateria |
| Jamshed et al. (2024) — IEEE | Parâmetros do enlace D2D em 2,4 GHz |
| Bertsias et al. (2024) — IEEE Access | CAPEX e OPEX 6G, critério de ROI |
| Anatel (2023) | CAPEX e OPEX 4G no mercado brasileiro |
| 3GPP TR 36.814 | Densidades de ERBs 4G por zona |

---

*Última atualização: Abril 2026 | seed = 42 em todos os simuladores*
