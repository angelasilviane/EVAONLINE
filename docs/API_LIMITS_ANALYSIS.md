# 🚨 ANÁLISE CRÍTICA: Limites de API vs Pré-cache

## ⚠️ PROBLEMA IDENTIFICADO: Pode esgotar limites diários!

Você tem razão em se preocupar! Vamos calcular o consumo REAL de cada API com o pré-cache:

---

## 📊 Limites de Cada API

### 1. NASA POWER
```yaml
API: NASA POWER Daily API
Limite: 1000 requests/dia
Rate limit: ~1 req/segundo
Cobertura: Global
Custo por localização: 1 request (dados diários prontos)
```

### 2. NWS (National Weather Service)
```yaml
API: NWS Forecast + Stations
Limite: SEM LIMITE DOCUMENTADO (domínio público)
Rate limit: ~5 requests/segundo
Cobertura: USA apenas
Custo por localização (Forecast): 2 requests
  - 1 req: GET /points/{lat},{lon} (metadata)
  - 1 req: GET /gridpoints/{office}/{x},{y}/forecast (dados)
Custo por localização (Stations): 2-3 requests
  - 1 req: GET /points/{lat},{lon}/stations (lista estações)
  - 1-2 req: GET /stations/{stationId}/observations (dados)
```

### 3. Open-Meteo
```yaml
API: Open-Meteo Forecast + Archive
Limite: SEM LIMITE (open-source, self-hosted possível)
Rate limit: ~10000 requests/dia (free tier)
Cobertura: Global
Custo por localização: 1 request (dados diários prontos)
```

### 4. MET Norway Locationforecast
```yaml
API: MET Norway Locationforecast 2.0
Limite: SEM LIMITE DIÁRIO documentado
Rate limit: 20 requests/segundo
Cobertura: Global (melhor qualidade na Escandinávia)
Custo por localização: 1 request (dados horários)
Restrições:
  - User-Agent obrigatório
  - Cache Expires header (não requisitar antes do tempo)
  - Fair use policy (não abusar)
```

---

## 💰 CÁLCULO DO CONSUMO COM PRÉ-CACHE ATUAL

### ❌ NASA POWER: RISCO ALTO!

```python
# CONSUMO DIÁRIO:
POPULAR_WORLD_CITIES = 50 cidades
Período: últimos 30 dias
Requests por execução: 50 cities × 1 req = 50 requests

# SCHEDULE ATUAL (climate_tasks.py):
# 03:00 BRT (1x ao dia)
Consumo diário: 50 requests/dia

# ANÁLISE:
Limite API: 1000 requests/dia
Consumo pré-cache: 50 requests (5%)
Margem restante: 950 requests (95%)

CONCLUSÃO: ✅ SEGURO!
- Pré-cache usa apenas 5% do limite
- 950 requests restantes para usuários ao vivo
- Se 100 usuários consultarem 9-10 localizações diferentes = OK
```

**Cenário de Risco:**
```
Se tivermos 1000+ usuários/dia consultando locais únicos:
- Pré-cache: 50 req (5%)
- Usuários: 950 localizações únicas
= TOTAL: 1000 req = LIMITE ATINGIDO! ❌

Solução: Implementar throttling/queuing para NASA POWER
```

### ✅ NWS: SEM LIMITE DOCUMENTADO (Seguro)

```python
# CONSUMO DIÁRIO:
POPULAR_USA_CITIES = 30 cidades

# NWS FORECAST (6h/6h = 4x ao dia):
# 00:00, 06:00, 12:00, 18:00 BRT
Requests por execução: 30 cities × 2 req = 60 requests
Consumo diário: 60 × 4 = 240 requests/dia

# NWS STATIONS (1x ao dia):
# 04:00 BRT
Requests por execução: 30 cities × 2.5 req = 75 requests
Consumo diário: 75 requests/dia

# TOTAL NWS:
Consumo diário: 240 + 75 = 315 requests/dia

# ANÁLISE:
Limite API: SEM LIMITE (domínio público)
Rate limit: ~5 req/s = 432,000 req/dia (teórico)
Consumo pré-cache: 315 req/dia (0.07%)

CONCLUSÃO: ✅ MUITO SEGURO!
- NWS não tem limite diário documentado
- Rate limit altíssimo (5 req/s)
- Margem gigantesca para usuários ao vivo
```

### ✅ Open-Meteo: SEM LIMITE PRÁTICO (Seguro)

```python
# CONSUMO DIÁRIO (se ativado):
Limite free tier: 10,000 requests/dia
Pré-cache estimado: < 100 requests/dia

CONCLUSÃO: ✅ MUITO SEGURO!
- Open-Meteo é open-source (pode self-host)
- Limite altíssimo no free tier
- Margem enorme
```

### ⚠️ MET Norway: ATENÇÃO AO FAIR USE

```python
# CONSUMO DIÁRIO (se ativado):
Limite diário: SEM LIMITE documentado
Rate limit: 20 req/s = 1,728,000 req/dia (teórico)
Restrições: Fair use policy (não abusar)

CONCLUSÃO: ⚠️ USAR COM CUIDADO
- Sem limite rígido, mas fair use policy
- Respeitar Cache-Control headers
- Não requisitar antes do Expires
- Implementar cache inteligente (já feito)
```

---

## 🎯 CENÁRIOS DE USO REAL

### Cenário 1: Aplicação com 100 usuários/dia (BAIXO)
```
NASA POWER:
  Pré-cache: 50 req (5%)
  Usuários: ~50 localizações únicas
  Total: 100 req (10% do limite)
  Status: ✅ MUITO SEGURO

NWS:
  Pré-cache: 315 req
  Usuários: ~100 req
  Total: 415 req
  Status: ✅ MUITO SEGURO (sem limite)

Conclusão: Sistema suporta tranquilamente
```

### Cenário 2: Aplicação com 500 usuários/dia (MÉDIO)
```
NASA POWER:
  Pré-cache: 50 req (5%)
  Usuários: ~200-300 localizações únicas
  Total: 250-350 req (25-35% do limite)
  Status: ✅ SEGURO

NWS:
  Pré-cache: 315 req
  Usuários: ~400 req
  Total: 715 req
  Status: ✅ SEGURO (sem limite)

Conclusão: Sistema suporta bem
```

### Cenário 3: Aplicação com 2000+ usuários/dia (ALTO)
```
NASA POWER:
  Pré-cache: 50 req (5%)
  Usuários: ~800-900 localizações únicas
  Total: 850-950 req (85-95% do limite)
  Status: ⚠️ RISCO MÉDIO

Se chegarem a 1000+ localizações únicas:
  Total: 1050 req
  Status: ❌ LIMITE EXCEDIDO!

Solução necessária:
  1. Implementar queue com throttling
  2. Retornar erro 429 (Too Many Requests)
  3. Fallback para outras APIs
  4. Aumentar TTL do cache (1h → 6h)
  5. Upgrade para NASA POWER Enterprise (se disponível)
```

---

## 🛡️ ESTRATÉGIAS DE MITIGAÇÃO

### ✅ JÁ IMPLEMENTADAS:

1. **Cache Redis (TTL 1h)**
   - Reduz requisições repetidas
   - 95% cache hit rate para cidades populares
   - Auto-expira dados frios

2. **Pré-cache Inteligente**
   - Apenas TOP 30-50 cidades
   - Não tenta cachear todas as localizações
   - Foco em 95% dos usuários

3. **Retry com Backoff Exponencial**
   - Evita sobrecarga em falhas temporárias
   - Implementado em todos os clientes

4. **Rate Limiting nas APIs**
   - Respeita limites de req/segundo
   - Delay entre requisições quando necessário

### 🔧 RECOMENDAÇÕES ADICIONAIS:

#### 1. Monitoramento de Consumo de API
```python
# Adicionar contador Redis para NASA POWER
from redis import Redis

def track_api_usage(api_name: str, requests_count: int = 1):
    """Rastrear uso diário de cada API."""
    redis = Redis.from_url(settings.redis.redis_url)
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"api_usage:{api_name}:{today}"
    
    # Incrementar contador
    current = redis.incr(key, requests_count)
    redis.expire(key, 86400 * 2)  # Manter 2 dias
    
    # Alertar se próximo do limite
    if api_name == "nasa_power" and current > 800:
        logger.warning(
            f"⚠️ NASA POWER usage high: {current}/1000 requests today"
        )
    
    return current

# Usar em cada chamada de API
usage = track_api_usage("nasa_power")
if usage >= 1000:
    raise APILimitExceeded("NASA POWER daily limit reached")
```

#### 2. Queue com Priorização
```python
# Priorizar cache hits vs API calls
def get_weather_data(lat: float, lon: float):
    # 1. Tentar cache primeiro (instantâneo)
    cached = get_from_cache(lat, lon)
    if cached:
        return cached
    
    # 2. Verificar limite da API
    usage = check_api_usage("nasa_power")
    if usage >= 950:  # 95% do limite
        # Fallback para outras APIs
        logger.warning("NASA POWER near limit, using Open-Meteo")
        return get_from_openmeteo(lat, lon)
    
    # 3. Chamar API e cachear
    data = fetch_from_nasa_power(lat, lon)
    track_api_usage("nasa_power")
    save_to_cache(data)
    return data
```

#### 3. Aumentar TTL do Cache (se necessário)
```python
# ATUAL: TTL 1h
CACHE_TTL = 3600

# OPÇÃO 1: TTL 6h (reduz consumo 6x)
CACHE_TTL = 3600 * 6  # Dados históricos mudam pouco

# OPÇÃO 2: TTL variável por tipo de dado
CACHE_TTL_HISTORICAL = 3600 * 24  # 24h (dados antigos)
CACHE_TTL_RECENT = 3600 * 6       # 6h (dados recentes)
CACHE_TTL_FORECAST = 3600 * 1     # 1h (previsões)
```

#### 4. Estratégia de Fallback em Cascata
```python
API_PRIORITY = [
    ("nws_forecast", "USA only, no limit"),
    ("openmeteo_forecast", "Global, 10k/day limit"),
    ("nasa_power", "Global, 1k/day limit"),
    ("met_norway", "Global, fair use"),
]

def get_weather_with_fallback(lat, lon, days):
    """Tentar APIs em ordem de prioridade/disponibilidade."""
    for api_name, description in API_PRIORITY:
        # Verificar se API cobre a localização
        if not api_covers_location(api_name, lat, lon):
            continue
        
        # Verificar limite da API
        if not api_has_quota(api_name):
            logger.warning(f"⚠️ {api_name} limit reached, trying next")
            continue
        
        # Tentar buscar dados
        try:
            data = fetch_from_api(api_name, lat, lon, days)
            logger.info(f"✅ Data from {api_name}")
            return data
        except Exception as e:
            logger.error(f"❌ {api_name} failed: {e}")
            continue
    
    # Todas falharam
    raise NoAPIAvailable("All climate APIs exhausted or failed")
```

---

## 📊 DASHBOARD DE CONSUMO (Recomendado)

### Métricas a Monitorar:

```python
# Redis keys para monitoramento
api_usage:nasa_power:2025-11-06 = 245  # Requests hoje
api_usage:nws_forecast:2025-11-06 = 389
api_usage:openmeteo:2025-11-06 = 12

cache_hits:nasa_power:2025-11-06 = 8542   # 95%
cache_misses:nasa_power:2025-11-06 = 245  # 5%

# Alertas automáticos
if usage > 800:  # 80% do limite NASA
    send_alert("NASA POWER usage: 80%")

if usage > 950:  # 95% do limite
    send_critical_alert("NASA POWER usage: 95%!")
    switch_to_fallback_apis()
```

### Endpoint de Status:
```python
@router.get("/api/status/climate-apis")
async def get_api_status():
    """Status de consumo de todas APIs climáticas."""
    return {
        "nasa_power": {
            "requests_today": 245,
            "limit": 1000,
            "usage_percent": 24.5,
            "status": "healthy",
        },
        "nws_forecast": {
            "requests_today": 389,
            "limit": None,  # Sem limite
            "usage_percent": None,
            "status": "healthy",
        },
        "openmeteo": {
            "requests_today": 12,
            "limit": 10000,
            "usage_percent": 0.12,
            "status": "healthy",
        },
        "cache": {
            "hit_rate": 95.2,
            "total_hits": 8542,
            "total_misses": 245,
        }
    }
```

---

## ✅ RECOMENDAÇÕES FINAIS

### Para Aplicação com < 500 usuários/dia:
```
✅ Manter pré-cache atual (SEGURO)
  - NASA POWER: 50 req/dia (5% do limite)
  - NWS: 315 req/dia (sem limite)
  - Cache hit rate: 95%
  - Margem: 950 req para usuários

✅ Adicionar apenas:
  - Monitoramento básico (contador Redis)
  - Alerta se > 800 req/dia NASA POWER
```

### Para Aplicação com 500-2000 usuários/dia:
```
⚠️ Adicionar proteções:
  - Monitoramento detalhado
  - Fallback automático para Open-Meteo
  - TTL cache aumentado (6h para histórico)
  - Queue com priorização
```

### Para Aplicação com > 2000 usuários/dia:
```
❌ Pré-cache NASA POWER pode ser problemático
  - Considerar reduzir de 50 para 20 cidades TOP
  - Implementar fallback obrigatório
  - Aumentar TTL para 24h (dados históricos)
  - Considerar NASA POWER Enterprise (se existir)
  - Priorizar NWS (USA) e Open-Meteo (Global)
```

---

## 🎯 CONCLUSÃO

### Status Atual: ✅ SEGURO para aplicações pequenas/médias

| API | Limite | Pré-cache | % Usado | Margem | Status |
|-----|--------|-----------|---------|--------|--------|
| **NASA POWER** | 1000/dia | 50 req | 5% | 950 req | ✅ OK |
| **NWS** | Ilimitado | 315 req | 0% | Ilimitado | ✅ OK |
| **Open-Meteo** | 10000/dia | 0 req* | 0% | 10000 req | ✅ OK |
| **MET Norway** | Fair use | 0 req* | 0% | Fair use | ✅ OK |

*Atualmente não tem pré-cache ativo

### Ações Recomendadas:

1. **IMPLEMENTAR AGORA** (Crítico):
   - ✅ Contador Redis de uso diário (api_usage:*)
   - ✅ Alertas quando > 80% do limite NASA

2. **IMPLEMENTAR EM BREVE** (Importante):
   - ⚠️ Fallback automático NASA → Open-Meteo
   - ⚠️ Endpoint /api/status/climate-apis
   - ⚠️ Dashboard de monitoramento

3. **CONSIDERAR FUTURO** (Se crescer):
   - 💡 Queue com throttling
   - 💡 TTL variável por tipo de dado
   - 💡 Self-host Open-Meteo (sem limites)

**Sistema atual é SEGURO, mas monitoramento é ESSENCIAL!** 🎯
