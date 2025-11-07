# Resumo dos Testes de APIs Climáticas - EVAonline

## Status Geral dos Testes

**Data:** 2025
**Período de Forecast Padronizado:** Máximo de 5 dias para todas as APIs

---

## 📊 Resumo de Cobertura

| API                              | Testes | Passou | Falhou | Taxa de Sucesso | Cobertura |
|----------------------------------|--------|--------|--------|-----------------|-----------|
| NASA POWER                       | 16     | 16     | 0      | 100%            | ✅        |
| NWS Forecast                     | 10     | 10     | 0      | 100%            | ✅        |
| NWS Stations                     | 11     | 11     | 0      | 100%            | ✅        |
| Met Norway LocationForecast      | 16     | 16     | 0      | 100%            | ✅        |
| Open-Meteo Forecast              | 18     | 18     | 0      | 100%            | ✅        |
| Met Norway Frost                 | 17     | 17     | 0      | 100%            | ✅        |
| Open-Meteo Archive               | -      | -      | -      | Pendente        | ⏳        |
| **TOTAL**                        | **88** | **88** | **0**  | **100%**        | **✅**    |

---

## 🌍 APIs Testadas em Detalhes

### 1. NASA POWER (16 testes ✅)

**Arquivo:** `tests/unit/api/test_nasa_power_api.py`

**Descrição:** API da NASA para dados de radiação solar e variáveis climáticas globais

**Cobertura Geográfica:** GLOBAL

**Período de Dados:** 1981 - presente (-30 dias)

**Classes de Teste:**
- `TestNASAPowerBasic`: 6 testes - Download de dados, múltiplas localizações, período multi-anual
- `TestNASAPowerDataQuality`: 4 testes - Validação de estrutura de dados, variáveis ETo, radiação solar
- `TestNASAPowerEdgeCases`: 3 testes - Coordenadas inválidas, dia único, latitudes extremas
- `TestNASAPowerHealthCheck`: 2 testes - Health check e informações da API
- `TestNASAPowerCoverage`: 1 teste - Informações de cobertura geográfica

**Principais Variáveis Testadas:**
- T2M (Temperatura 2m)
- RH2M (Umidade Relativa)
- WS2M (Velocidade do Vento)
- PRECTOTCORR (Precipitação)
- ALLSKY_SFC_SW_DWN (Radiação Solar)

**Status:** ✅ Todos os testes passando

---

### 2. NWS Forecast (10 testes ✅)

**Arquivo:** `tests/unit/api/test_nws_forecast.py`

**Descrição:** National Weather Service - Previsão meteorológica para Estados Unidos

**Cobertura Geográfica:** USA apenas

**Período de Dados:** Forecast de até 7 dias (testes limitados a 5 dias)

**Classes de Teste:**
- `TestNWSForecastBasic`: 4 testes - Download de previsões para múltiplas cidades dos EUA
- `TestNWSForecastDataStructure`: 3 testes - Estrutura de dados, validação de campos essenciais
- `TestNWSForecastEdgeCases`: 2 testes - Coordenadas fora dos EUA, dia único
- `TestNWSForecastHealthCheck`: 1 teste - Health check

**Localizações Testadas:**
- Washington, DC (38.9072, -77.0369)
- Los Angeles, CA (34.0522, -118.2437)
- Miami, FL (25.7617, -80.1918)
- Chicago, IL (41.8781, -87.6298)

**Status:** ✅ Todos os testes passando

---

### 3. NWS Stations (11 testes ✅)

**Arquivo:** `tests/unit/api/test_nws_stations.py`

**Descrição:** National Weather Service Stations - Dados históricos de estações meteorológicas

**Cobertura Geográfica:** USA apenas

**Período de Dados:** Últimos 7 dias (limite da API)

**Classes de Teste:**
- `TestNWSStationsBasic`: 5 testes - Download de dados, múltiplas estações, período de 7 dias
- `TestNWSStationsDataQuality`: 2 testes - Estrutura de dados, validação de temperatura
- `TestNWSStationsEdgeCases`: 2 testes - Coordenadas sem estações próximas, dia único
- `TestNWSStationsHealthCheck`: 2 testes - Health check e informações da API

**Estações Testadas:**
- KDCA (Washington Reagan)
- KLAX (Los Angeles)
- KMIA (Miami)
- KORD (Chicago O'Hare)

**Status:** ✅ Todos os testes passando

---

### 4. Met Norway LocationForecast (16 testes ✅)

**Arquivo:** `tests/unit/api/test_met_norway_locationforecast.py`

**Descrição:** Met Norway LocationForecast 2.0 - Previsão meteorológica global de alta qualidade

**Cobertura Geográfica:** GLOBAL

**Período de Dados:** Forecast de até 5 dias (padronizado)

**Classes de Teste:**
- `TestMETNorwayLocationForecastBasic`: 6 testes - Download global, período estendido, hemisfério sul
- `TestMETNorwayDataQuality`: 4 testes - Validação de temperatura, umidade, vento, precipitação
- `TestMETNorwayEToVariables`: 1 teste - Validação de variáveis para cálculo de ETo FAO-56
- `TestMETNorwayEdgeCases`: 3 testes - Coordenadas inválidas, dia único, latitudes extremas
- `TestMETNorwayHealthCheck`: 1 teste - Health check
- `TestMETNorwayCoverage`: 1 teste - Informações de cobertura

**Localizações Testadas:**
- Brasília, Brasil (-15.7801, -47.9292)
- Oslo, Noruega (59.9139, 10.7522)
- Tóquio, Japão (35.6762, 139.6503)
- Nova York, EUA (40.7128, -74.0060)

**Variáveis ETo Testadas:**
- temperature_2m (Temperatura)
- relative_humidity_2m (Umidade)
- wind_speed_10m (Vento)
- precipitation (Precipitação)
- shortwave_radiation (Radiação Solar)

**Status:** ✅ Todos os testes passando (após padronização para 5 dias)

---

### 5. Open-Meteo Forecast (18 testes ✅)

**Arquivo:** `tests/unit/api/test_openmeteo_forecast.py`

**Descrição:** Open-Meteo Forecast API - Previsão meteorológica global gratuita

**Cobertura Geográfica:** GLOBAL

**Período de Dados:** -90 dias até +5 dias (padronizado)

**Classes de Teste:**
- `TestOpenMeteoForecastBasic`: 7 testes - Download global, período estendido, dados recentes
- `TestOpenMeteoForecastDataQuality`: 3 testes - Estrutura de dados, temperatura, datas válidas
- `TestOpenMeteoForecastEdgeCases`: 4 testes - Dia único, ajuste de datas, latitudes extremas
- `TestOpenMeteoForecastHealth`: 3 testes - Health check, informações, método get_forecast
- `TestOpenMeteoForecastMultiLocation`: 1 teste - Múltiplas localizações sequenciais

**Localizações Testadas:**
- Brasília, Brasil (-15.7801, -47.9292)
- Paris, França (48.8566, 2.3522)
- Pequim, China (39.9042, 116.4074)
- Toronto, Canadá (43.6532, -79.3832)

**Variáveis Testadas:**
- temperature_2m_max/min
- relative_humidity_2m
- wind_speed_10m_max
- precipitation_sum
- shortwave_radiation_sum

**Status:** ✅ Todos os testes passando (após padronização para 5 dias)

---

### 6. Met Norway Frost (17 testes ✅)

**Arquivo:** `tests/unit/api/test_met_norway_frost.py`

**Descrição:** Met Norway Frost API - Dados históricos de estações meteorológicas norueguesas

**Cobertura Geográfica:** Noruega (estações meteorológicas)

**Período de Dados:** 1937 - presente

**Autenticação:** OAuth2 ou Basic Auth (Client ID + Client Secret)

**Classes de Teste:**
- `TestFrostBasic`: 6 testes - Health check, observações de 3 estações, período de 30 dias, séries temporais
- `TestFrostDataQuality`: 3 testes - Estrutura de observações, validação de temperatura, agregação diária
- `TestFrostEdgeCases`: 4 testes - Station ID inválido, validações de período (7-30 dias), ordem de datas
- `TestFrostMetadata`: 2 testes - Disponibilidade de dados, múltiplos elementos
- `TestFrostIntegration`: 2 testes - Múltiplas estações sequenciais, dados históricos

**Estações Testadas:**
- SN18700: Oslo - Blindern (59.9423, 10.7211)
- SN50540: Bergen - Florida (60.3832, 5.3314)
- SN90450: Tromsø (69.6533, 18.9561)

**Elementos Testados:**
- mean(air_temperature P1D) - Temperatura média diária
- sum(precipitation_amount P1D) - Precipitação diária acumulada
- mean(wind_speed P1D) - Velocidade média do vento

**Limitações:**
- Requer credenciais válidas (FROST_CLIENT_ID e FROST_CLIENT_SECRET)
- Cobertura limitada à Noruega
- Requer station IDs (não aceita coordenadas diretas)
- Período mínimo: 7 dias
- Período máximo: 30 dias por requisição

**Status:** ✅ Todos os testes passando

---

### 7. Open-Meteo Archive ⏳

**Descrição:** Dados históricos de reanálise global

**Motivo:** Ainda não testada

**Prioridade:** Média

---

## 🚧 APIs Pendentes de Teste

### Open-Meteo Archive ⏳

## 📋 Padronização Implementada

### Período de Forecast

**Decisão:** Padronizar todas as APIs de forecast para máximo de **5 dias**

**Motivo:**
- NWS já possui limite de 7 dias
- Margem de segurança de 2 dias
- Evita erros de requisição além dos limites das APIs
- Mantém consistência entre todas as fontes

**APIs Afetadas:**
- NWS Forecast: Mantido em 7 dias (limite da API), testes usam 5 dias
- Met Norway LocationForecast: Reduzido de 14 → 5 dias
- Open-Meteo Forecast: Reduzido de 16 → 5 dias

**Mudanças Implementadas:**
1. `met_norway_locationforecast_client.py`: `forecast_horizon_days = 5`
2. `openmeteo_forecast_sync_adapter.py`: `max_date = current + timedelta(days=5)`
3. Todos os testes atualizados para usar máximo de 5 dias
4. Met Norway Frost: Validação de 7-30 dias por requisição (apenas dados históricos)

---

## 🧪 Metodologia de Testes

### Estrutura Padrão

Cada arquivo de teste segue a estrutura:

```python
class TestAPINameBasic:
    """Testes básicos de funcionalidade"""
    - test_download_data_global[location]  # Parametrizado
    - test_multi_day_period
    - test_hemisphere_coverage

class TestAPINameDataQuality:
    """Validação de qualidade e estrutura dos dados"""
    - test_data_structure
    - test_variable_ranges
    - test_eto_variables_presence

class TestAPINameEdgeCases:
    """Casos extremos e validação de erros"""
    - test_invalid_coordinates
    - test_single_day
    - test_extreme_latitudes

class TestAPINameHealthCheck:
    """Health checks e informações da API"""
    - test_health_check
    - test_get_info
```

### Validações Implementadas

1. **Estrutura de Dados:**
   - Lista não vazia
   - Dicionários com chaves esperadas
   - Tipos de dados corretos

2. **Valores Físicos:**
   - Temperatura: -90°C a 60°C
   - Umidade: 0% a 100%
   - Vento: 0 a 150 m/s
   - Precipitação: ≥ 0 mm
   - Radiação solar: ≥ 0 W/m²

3. **Variáveis ETo FAO-56:**
   - Temperatura
   - Umidade relativa
   - Velocidade do vento
   - Radiação solar
   - Precipitação (opcional)

4. **Cobertura Geográfica:**
   - Múltiplos continentes
   - Ambos hemisférios
   - Latitudes extremas (±70°)

5. **Casos Extremos:**
   - Coordenadas inválidas (além de ±90°/±180°)
   - Períodos de 1 dia
   - Localizações sem cobertura

---

## 📈 Métricas de Execução

### Tempo de Execução (exemplo recente)

```
34 testes executados em 20.69 segundos
Média: ~0.6 segundos por teste
Testes mais lentos:
- test_extreme_latitudes: 1.78s (Met Norway)
- test_southern_hemisphere: 1.66s (Met Norway)
- test_recent_data_past_week: 0.94s (Open-Meteo)
```

### Cobertura de Código

```
met_norway_locationforecast_client.py: 67%
met_norway_locationforecast_sync_adapter.py: 54%
openmeteo_forecast_client.py: 62%
openmeteo_forecast_sync_adapter.py: 65%
```

---

## ✅ Conclusões

### Pontos Fortes

1. **Alta Taxa de Sucesso:** 100% dos testes passando (88/88)
2. **Cobertura Global:** APIs testadas funcionam em todos os continentes
3. **Padronização:** Período de forecast consistente entre todas as fontes
4. **Robustez:** Validação de casos extremos e erros
5. **Autenticação:** Suporte para OAuth2 e Basic Auth (Frost API)

### Recomendações

1. **Completar Testes:**
   - Open-Meteo Archive (dados históricos globais)

2. **Aumentar Cobertura de Código:**
   - Adicionar testes para branches não cobertas
   - Testar cenários de erro e timeout

3. **Monitoramento:**
   - Implementar testes de performance
   - Adicionar testes de rate limiting

4. **Documentação:**
   - Manter este documento atualizado
   - Adicionar exemplos de uso para cada API

5. **Credenciais:**
   - Documentar processo de obtenção de credenciais Frost
   - Adicionar instruções de configuração de ambiente

---

## 📝 Comandos de Teste

### Executar Todos os Testes de APIs

```bash
pytest tests/unit/api/ -v
```

### Executar Testes de API Específica

```bash
# NASA POWER
pytest tests/unit/api/test_nasa_power_api.py -v

# NWS
pytest tests/unit/api/test_nws_forecast.py -v
pytest tests/unit/api/test_nws_stations.py -v

# Met Norway
pytest tests/unit/api/test_met_norway_locationforecast.py -v

# Open-Meteo
pytest tests/unit/api/test_openmeteo_forecast.py -v
```

### Executar com Cobertura

```bash
pytest tests/unit/api/ -v --cov=backend/api/services --cov-report=html
```

### Executar Teste Específico

```bash
pytest tests/unit/api/test_nasa_power_api.py::TestNASAPowerBasic::test_download_global -v
```

### Executar Frost API (requer credenciais)

```bash
# Definir credenciais
$env:FROST_CLIENT_ID="your-client-id"
$env:FROST_CLIENT_SECRET="your-client-secret"

# Executar testes
pytest tests/unit/api/test_met_norway_frost.py -v
```

---

## 🔗 Referências

- [NASA POWER API Docs](https://power.larc.nasa.gov/docs/)
- [NWS API Documentation](https://www.weather.gov/documentation/services-web-api)
- [Met Norway API](https://api.met.no/)
- [Open-Meteo API](https://open-meteo.com/)
- [FAO-56 ETo Method](http://www.fao.org/3/x0490e/x0490e00.htm)

---

**Última Atualização:** 2025-01-XX

**Mantido por:** Equipe EVAonline
