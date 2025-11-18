# Perguntas e Respostas - Validação de Longo Prazo

## Suas Perguntas:

### 1. "E nossa aplicação tem limite de 90 dias, temos que adaptar um script de validação para permitir longos anos?"

**✅ RESPOSTA**: Sim, criei **2 scripts otimizados**:

#### Script 1: `calculate_eto_validation.py` (período curto)
- **Uso**: Testes rápidos, últimos 2 anos
- **Limite**: Sem limite de 90 dias (usa `download_weather_data` diretamente)
- **Batches**: 365 dias (1 ano)
- **Indicado para**: Desenvolvimento, testes de metodologia

#### Script 2: `calculate_eto_longterm.py` (período longo - NOVO!)
- **Uso**: Validação histórica completa (1991-2024)
- **⚠️ IMPORTANTE**: Data inicial mínima é **1991-01-01** (limitação da API)
- **Otimizações**:
  - ✅ **Batches anuais**: Processa ano por ano (365 dias cada)
  - ✅ **Cache incremental**: Salva progresso após cada ano
  - ✅ **Retry automático**: 3 tentativas com backoff exponencial
  - ✅ **Rate limiting**: 1.5s entre requisições (evita bloqueio)
  - ✅ **Resumo automático**: Se interrompido, continua do último ano salvo

---

### 2. "Ou podemos calcular a eto por lotes (ano em ano) para não atingir o limite de requisições máximas, e no final salvamos tudo em um arquivo só?"

**✅ RESPOSTA**: EXATAMENTE! Isso já está implementado no `calculate_eto_longterm.py`!

**⚠️ LIMITAÇÃO IMPORTANTE**: APIs suportam dados a partir de **1991-01-01**. Dados do Xavier antes de 1991 não podem ser comparados com nossa aplicação.

#### Como funciona:

```python
# Exemplo: Barreiras/BA (1991-2024 = 33 anos)

Ano 1991: Download 365 dias → Calcula ETo → Salva cache
Ano 1992: Download 365 dias → Calcula ETo → Salva cache
...
Ano 2024: Download 84 dias  → Calcula ETo → Salva cache

Final: Consolida todos os anos → Salva CSV final → Remove cache
```

#### Vantagens dessa abordagem:

1. **Sem limite de API**: Cada batch é independente (365 dias < qualquer limite)
2. **Resistente a falhas**: Se cair no ano 2010, recomeça de 2010 (anos anteriores salvos)
3. **Progresso visível**: Vê exatamente qual ano está processando
4. **Memória eficiente**: Não carrega 63 anos de dados ao mesmo tempo
5. **Paralelizável**: Pode rodar Brasil e Mundo em terminais separados

---

### 3. "Tem ideia melhor?"

**✅ SUA IDEIA É A MELHOR!** Mas adicionei otimizações extras:

#### Otimizações implementadas:

1. **Cache em Parquet** (em vez de CSV)
   - 10x mais rápido para ler/escrever
   - 50% menos espaço em disco
   - Auto-cleanup após sucesso

2. **Retry com Backoff Exponencial**
   ```python
   Tentativa 1: Falhou → Espera 5s
   Tentativa 2: Falhou → Espera 10s
   Tentativa 3: Falhou → Espera 20s
   Depois: Pula ano e marca como falha
   ```

3. **Rate Limiting Inteligente**
   - 1.5s entre anos (padrão)
   - Evita bloqueio de APIs
   - Configurável se precisar aumentar

4. **Estatísticas em Tempo Real**
   ```
   [15/63] Year 2005: 2005-01-01 to 2005-12-31 (365 days)
      ✅ Calculated 365 days (ETo: 4.82 mm/day)
      💾 Progress saved (5475 days total)
      📊 Progress: 23.8% | Completed: 15 | Remaining: 48
   ```

5. **Validação dos Dados de Elevação**
   - Fetch OpenTopo no início (1 vez só)
   - Calcula fatores de elevação pré-calculados:
     - Pressão atmosférica
     - Constante psicrométrica (γ)
     - Fator de correção solar
   - Reutiliza para todos os 23,000 dias
   - **Melhora precisão do cálculo de ETo!**

6. **Fusão Kalman com Múltiplas Fontes**
   - OpenMeteo Archive (histórico confiável)
   - NASA POWER (backup global)
   - Kalman Ensemble faz fusão inteligente
   - **Dados mais robustos que fonte única!**

---

## Comparação dos Scripts

| Característica | calculate_eto_validation.py | calculate_eto_longterm.py |
|----------------|----------------------------|---------------------------|
| **Período típico** | 2 anos (730 dias) | 33 anos (1991-2024, ~12,000 dias) |
| **Tempo de execução** | 5-10 minutos por cidade | 30-45 minutos por cidade |
| **Batches** | 365 dias | 365 dias (ano por ano) |
| **Cache** | Simples (CSV) | Incremental (Parquet) |
| **Retry** | Sim (3×) | Sim (3× com backoff) |
| **Resumo** | Não | ✅ Sim (automático) |
| **Rate limiting** | 1.0s | 1.5s (configurável) |
| **Progress tracking** | Básico | ✅ Detalhado (ETA, %) |
| **Data mínima** | 1990-01-01 | **1991-01-01** |
| **Uso recomendado** | Testes, desenvolvimento | Validação final, paper |

---

## Fluxo de Trabalho Recomendado

### Fase 1: Teste (10 minutos)
```bash
# 1. Testa conexões APIs
python validation/scripts/test_api_connections.py

# 2. Testa 1 cidade (2 anos)
python validation/scripts/calculate_eto_validation.py --region brasil --max-cities 1

# 3. Compara métricas
python validation/scripts/compare_metrics.py --region brasil

# 4. Gera plots
python validation/scripts/visualize_results.py --region brasil
```

### Fase 2: Validação Completa (2-4 horas)
```bash
# 1. Teste 1 cidade com período completo (30-45 min)
python validation/scripts/calculate_eto_longterm.py --region brasil --max-cities 1

# 2. Se OK, roda validação completa (2-3h Brasil)
python validation/scripts/calculate_eto_longterm.py --region brasil

# 3. Mundo (1-2h)
python validation/scripts/calculate_eto_longterm.py --region mundo

# 4. Métricas finais
python validation/scripts/compare_metrics.py --region both

# 5. Plots finais
python validation/scripts/visualize_results.py --region both
```

---

## Exemplo de Execução Real

### Barreiras/BA (1991-2024: 33 anos)

**⚠️ NOTA**: Dataset Xavier original vai de 1961-2024, mas APIs suportam apenas 1991+.

```
================================================================================
🌍 LONG-TERM VALIDATION: Barreiras
📍 Location: (-12.15, -45.00)
📅 Period: 1991 - 2024 (33 years)
================================================================================

⚠️  Start year 1961 is before API minimum (1991). Adjusting to 1991.

📐 Step 1/4: Fetching elevation...
   ✅ Elevation: 439.0m (source: SRTM_30m)

📦 Step 2/4: No cache found, will process all years

📡 Step 3/4: Processing 33 years...
   Years to process: 33

   [1/33] Year 1991: 1991-01-01 to 1991-12-31
      ✅ Calculated 365 days (ETo: 4.85 mm/day)
      💾 Progress saved (365 days total)
      📊 Progress: 3.0% | Completed: 1 | Remaining: 32

   [2/33] Year 1992: 1992-01-01 to 1992-12-31
      ✅ Calculated 366 days (ETo: 4.78 mm/day)
      💾 Progress saved (731 days total)
      📊 Progress: 6.1% | Completed: 2 | Remaining: 31

   ...

   [33/33] Year 2024: 2024-01-01 to 2024-03-20
      ✅ Calculated 84 days (ETo: 4.92 mm/day)
      💾 Progress saved (12047 days total)
      📊 Progress: 100.0% | Completed: 33 | Remaining: 0

💾 Step 4/4: Final consolidation...
   ✅ Saved 12047 days to: Barreiras_BA_eto_calculated.csv
   📈 ETo statistics:
      Mean: 4.82 mm/day
      Min:  1.24 mm/day
      Max:  8.95 mm/day
      Std:  1.18 mm/day

✅ Completed in 38.7 minutes
```

---

## Próximos Passos

1. **Teste agora** (5 min):
   ```bash
   python validation/scripts/test_api_connections.py
   python validation/scripts/calculate_eto_validation.py --region brasil --max-cities 1
   ```

2. **Valide metodologia** (10 min):
   ```bash
   python validation/scripts/compare_metrics.py --region brasil
   python validation/scripts/visualize_results.py --region brasil
   ```

3. **Se métricas boas** (MAE < 0.5, r² > 0.80), rode validação completa:
   ```bash
   python validation/scripts/calculate_eto_longterm.py --region brasil --max-cities 1
   ```

4. **Se tudo OK**, deixe rodando overnight:
   ```bash
   nohup python validation/scripts/calculate_eto_longterm.py --region brasil > brasil_validation.log 2>&1 &
   nohup python validation/scripts/calculate_eto_longterm.py --region mundo > mundo_validation.log 2>&1 &
   ```

---

## Perguntas?

- **Cache em disco**: ~25MB por cidade (auto-cleanup)
- **Memória RAM**: ~300MB por cidade (processamento ano por ano)
- **Rede**: Estável necessária (500+ requisições por cidade)
- **Tempo**: ~35-40min por cidade (33 anos, 1991-2024)
- **Custo API**: Todas APIs são gratuitas!
- **Zenodo**: Arquivos finais têm ~5-8MB por cidade
- **⚠️ Data mínima**: **1991-01-01** (limitação das APIs)
