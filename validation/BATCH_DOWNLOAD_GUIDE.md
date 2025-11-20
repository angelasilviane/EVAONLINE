# Batch Download e Validação - Guia Completo

## 📋 Visão Geral

Sistema para download em lote de dados históricos (1991-2020) de todas as cidades brasileiras e comparação com dados Xavier.

## 🔧 Scripts Disponíveis

### 1. `batch_download_yearly.py` - Download por Ano
Download incremental ano por ano para evitar timeouts.

**Uso:**
```bash
# Todas as cidades, 1991-2020
python validation/batch_download_yearly.py

# Período específico
python validation/batch_download_yearly.py --start-year 1991 --end-year 2020

# Cidades específicas
python validation/batch_download_yearly.py --cities Alvorada_do_Gurgueia_PI Piracicaba_SP

# Uma cidade, um ano
python validation/batch_download_yearly.py --cities Alvorada_do_Gurgueia_PI --start-year 1991 --end-year 1991
```

**Saída:**
- Arquivos em `results/brasil/cache/`
- `{cidade}_{ano}.csv` - Dados anuais
- `{cidade}_{start_year}_{end_year}.csv` - Dados consolidados

### 2. `batch_validate_xavier.py` - Validação com Xavier
Compara dados baixados com Xavier e gera métricas + gráficos.

**Uso:**
```bash
# Validar todas as cidades
python validation/batch_validate_xavier.py

# Período específico
python validation/batch_validate_xavier.py --start-year 1991 --end-year 2020

# Cidades específicas
python validation/batch_validate_xavier.py --cities Alvorada_do_Gurgueia_PI Piracicaba_SP

# Sem gráficos (mais rápido)
python validation/batch_validate_xavier.py --no-plots
```

**Saída:**
- `results/brasil/validation/validation_summary_{timestamp}.csv` - Métricas consolidadas
- `results/brasil/validation/plots/{cidade}.png` - Gráficos de dispersão e série temporal

### 3. `batch_download_and_validate.py` - Tudo Junto
Download completo + validação em um único comando (mais lento).

**Uso:**
```bash
# Processo completo
python validation/batch_download_and_validate.py --start-date 1991-01-01 --end-date 2020-12-31
```

## 📊 Métricas Geradas

Para cada cidade:
- **R²** - Coeficiente de determinação
- **NSE** - Nash-Sutcliffe Efficiency
- **MAE** - Mean Absolute Error (mm/dia)
- **RMSE** - Root Mean Squared Error (mm/dia)
- **PBIAS** - Percent Bias (%)
- **Slope/Intercept** - Parâmetros da regressão linear

## 🗂️ Estrutura de Arquivos

```
validation/
├── batch_download_yearly.py       # Download incremental
├── batch_validate_xavier.py       # Validação
├── batch_download_and_validate.py # Tudo junto
├── data_validation/data/
│   ├── info_cities.csv            # Lista de cidades (input)
│   └── csv/BRASIL/ETo/            # Dados Xavier (referência)
│       ├── Alvorada_do_Gurgueia_PI.csv
│       ├── Piracicaba_SP.csv
│       └── ...
└── results/brasil/
    ├── cache/                      # Dados baixados (intermediário)
    │   ├── Alvorada_do_Gurgueia_PI_1991.csv
    │   ├── Alvorada_do_Gurgueia_PI_1991_2020.csv
    │   └── ...
    └── validation/                 # Resultados finais
        ├── validation_summary_{timestamp}.csv
        └── plots/
            ├── Alvorada_do_Gurgueia_PI_1991_2020.png
            └── ...
```

## 🚀 Fluxo Recomendado

### Opção 1: Processo Incremental (Recomendado)

```bash
# 1. Download incremental (pode pausar/retomar)
python validation/batch_download_yearly.py --start-year 1991 --end-year 2020

# 2. Validação após download completo
python validation/batch_validate_xavier.py --start-year 1991 --end-year 2020
```

### Opção 2: Teste Rápido

```bash
# Testar com 1 cidade, 1 ano
python validation/batch_download_yearly.py \
    --cities Alvorada_do_Gurgueia_PI \
    --start-year 1991 \
    --end-year 1991

python validation/batch_validate_xavier.py \
    --cities Alvorada_do_Gurgueia_PI \
    --start-year 1991 \
    --end-year 1991
```

### Opção 3: Tudo de Uma Vez (Mais Lento)

```bash
python validation/batch_download_and_validate.py \
    --start-date 1991-01-01 \
    --end-date 2020-12-31
```

## 📈 Interpretação dos Resultados

### Critérios de Qualidade (baseados em literatura científica)

| Métrica | Excelente | Bom | Aceitável | Fraco |
|---------|-----------|-----|-----------|-------|
| **R²** | > 0.90 | 0.80-0.90 | 0.65-0.80 | < 0.65 |
| **NSE** | > 0.75 | 0.65-0.75 | 0.50-0.65 | < 0.50 |
| **PBIAS** | ±5% | ±10% | ±15% | > ±15% |
| **RMSE** | < 0.5 mm | 0.5-1.0 mm | 1.0-1.5 mm | > 1.5 mm |

### Exemplo de Saída

```
📈 ESTATÍSTICAS GERAIS:
  Cidades validadas: 17
  R² médio: 0.892
  NSE médio: 0.875
  MAE médio: 0.487 mm/dia
  RMSE médio: 0.623 mm/dia
  PBIAS médio: -2.3%

🏆 Melhor R²: Piracicaba_SP (R²=0.945)
⚠️  Pior R²: Campos_Lindos_TO (R²=0.812)
```

## ⚙️ Sistema de Cache

O sistema usa cache inteligente para evitar re-downloads:

1. **Cache por Ano**: `{cidade}_{ano}.csv`
   - Permite retomar downloads interrompidos
   - Cada ano é salvo independentemente

2. **Cache Consolidado**: `{cidade}_{start_year}_{end_year}.csv`
   - União de todos os anos baixados
   - Usado para validação

3. **Validação de Cache**:
   ```bash
   # Se já existe cache, pula o download
   # Para forçar re-download, delete os arquivos em cache/
   rm results/brasil/cache/*
   ```

## 🐛 Solução de Problemas

### Timeout nos Downloads
```bash
# Use batch_download_yearly.py em vez de batch_download_and_validate.py
# Processa ano por ano, mais resistente a timeouts
python validation/batch_download_yearly.py
```

### Falta de Dados Xavier
```bash
# Verifique se o arquivo existe em data_validation/data/csv/BRASIL/ETo/
ls validation/data_validation/data/csv/BRASIL/ETo/
```

### Erro "et0_mm não encontrado"
```bash
# Re-baixe os dados com o script atualizado
rm results/brasil/cache/{cidade}_*.csv
python validation/batch_download_yearly.py --cities {cidade}
```

## 📝 Cidades Disponíveis

As 17 cidades em `info_cities.csv`:
- Alvorada_do_Gurgueia_PI
- Araguaina_TO
- Balsas_MA
- Barreiras_BA
- Bom_Jesus_PI
- Campos_Lindos_TO
- Carolina_MA
- Corrente_PI
- Formosa_do_Rio_Preto_BA
- Imperatriz_MA
- Luiz_Eduardo_Magalhaes_BA
- Pedro_Afonso_TO
- Piracicaba_SP
- Porto_Nacional_TO
- Sao_Desiderio_BA
- Tasso_Fragoso_MA
- Urucui_PI

## 🔬 Metodologia

### Download
1. **Fontes**: NASA POWER + OpenMeteo Archive
2. **Fusão**: Kalman Adaptativo com referência climática
3. **Período**: 1991-01-01 a 2020-12-31 (30 anos)

### Cálculo ETo
1. **Método Primário**: Penman-Monteith ASCE
2. **Fallback**: Hargreaves-Samani
3. **Variáveis**: T_max, T_min, RH, U2, Rs

### Validação
1. **Referência**: Xavier et al. (2015) gridded dataset
2. **Métricas**: R², NSE, MAE, RMSE, PBIAS
3. **Outputs**: CSV + gráficos PNG

## 📚 Referências

- Xavier, A.C., et al. (2015). Daily gridded meteorological variables in Brazil (1980-2013). International Journal of Climatology.
- Allen, R.G., et al. (1998). Crop evapotranspiration - FAO Irrigation and drainage paper 56.
- ASCE-EWRI (2005). The ASCE standardized reference evapotranspiration equation.
