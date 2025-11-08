# 🔍 AUDITORIA COMPLETA - Database & Infrastructure

**Data**: 06/11/2025  
**Status**: ⚠️ **AÇÕES NECESSÁRIAS IDENTIFICADAS**

---

## 📊 **ANÁLISE DA ESTRUTURA**

### **1. Pasta `/database` (Raiz do Projeto)**

```
database/
├── config/
│   └── pg_hba_extra.conf    ✅ Configuração segura (md5)
└── init/
    └── init_alembic.py       ⚠️ Script básico, falta integração
```

#### **✅ Pontos Positivos:**
- pg_hba_extra.conf bem configurado para produção (md5, não trust)
- Suporte a redes Docker (172.16.0.0/12, 10.0.0.0/8)
- Configurações de replicação presentes

#### **⚠️ Melhorias Necessárias:**

**1.1. init_alembic.py está incompleto**
- ❌ Não cria arquivo `alembic.ini`
- ❌ Não configura `env.py`
- ❌ Não aponta para os modelos

**RECOMENDAÇÃO**: Substituir por script completo ou usar `alembic init`

---

### **2. Pasta `/backend/database`**

```
backend/database/
├── connection.py          ✅ Configuração robusta
├── data_storage.py        ⚠️ Modelo desatualizado
├── health_checks.py       ✅ Monitoramento completo
├── redis_pool.py          (não analisado ainda)
├── session_database.py    (não analisado ainda)
└── models/
    ├── admin_user.py
    ├── climate_data.py    ❌ NÃO ESTÁ SENDO USADO!
    ├── user_cache.py
    ├── user_favorites.py
    └── visitor_stats.py
```

#### **✅ Pontos Positivos:**
- `connection.py`: Excelente! Pool configurado, validações, context managers
- `health_checks.py`: Completo com métricas PostgreSQL + Redis
- Modelos bem estruturados

#### **❌ PROBLEMAS CRÍTICOS:**

**2.1. climate_data.py (EToResults) está COMENTADO no __init__.py**

```python
# backend/database/models/__init__.py
# from .climate_data import EToResults  ← COMENTADO!
```

**Impacto**:
- ❌ `data_storage.py` importa `EToResults` mas ele não está disponível
- ❌ Tabela `eto_results` não será criada por Alembic
- ❌ Função `save_eto_data()` vai falhar em runtime

**2.2. data_storage.py usa modelo antigo**

O modelo `EToResults` em `climate_data.py` usa campos NASA POWER:
```python
t2m_max, t2m_min, rh2m, ws2m, radiation, precipitation
```

Mas agora temos **6 APIs diferentes** com variáveis diferentes!

**PROBLEMA**: Como salvar dados de:
- Open-Meteo (temperature_2m_max, relative_humidity_2m_mean)
- MET Norway (diferentes variáveis por região)
- NWS Forecast/Stations (temp_celsius, humidity_percent)
- Data Fusion (variáveis mescladas)

---

### **3. Pasta `/backend/infrastructure`**

```
backend/infrastructure/
├── cache/
│   ├── celery_tasks.py        ✅ Tasks genéricas OK
│   ├── climate_tasks.py       ✅ Pre-carregamento robusto
│   ├── climate_cache.py       (precisa verificar)
│   └── ...
├── celery/
│   ├── celery_config.py       (precisa verificar)
│   └── tasks/
│       ├── visitor_sync.py
│       └── historical_download.py  ✅ NOVA task implementada
└── loaders/
    └── climate_history_loader.py  ⚠️ Usa schema climate_history
```

#### **✅ Pontos Positivos:**
- `climate_tasks.py`: 6 tasks de pré-carregamento (NASA, Open-Meteo, NWS, MET Norway)
- `historical_download.py`: Task completa para downloads históricos
- `climate_history_loader.py`: Loader completo para normais climáticas
- **`celery_config.py`**: ✅ **EXCELENTE!** 
  - 10 tasks agendadas no Beat
  - Métricas Prometheus integradas
  - Filas separadas por tipo de task
  - MonitoredProgressTask com publicação Redis
  - Timezone correto (America/Sao_Paulo)
- **`redis_pool.py`**: ✅ **MUITO BOM!**
  - Connection pool configurado (max 50 conexões)
  - Health check interval
  - Retry on timeout
  - Decode responses habilitado
- **`session_database.py`**: ✅ **OK** - Re-export limpo

#### **⚠️ Questões a Resolver:**

**3.1. Schema climate_history existe?**

`climate_history_loader.py` assume schema `climate_history`:
```sql
climate_history.studied_cities
climate_history.monthly_climate_normals
```

**PERGUNTAS**:
- ✅ Schema existe? Precisa criar?
- ✅ Tabelas existem? Precisam migration?
- ✅ Integração com Alembic?

**3.2. Celery Beat está configurado?**

`climate_tasks.py` tem tasks agendadas:
- `prefetch_nasa_popular_cities`: Diariamente às 03:00
- `cleanup_old_cache`: Diariamente às 02:00
- `prefetch_nws_forecast_usa_cities`: A cada 6 horas
- etc.

**PERGUNTAS**:
- ❓ `celery_config.py` tem configuração de Beat?
- ❓ Precisa adicionar schedule para novas tasks?

---

## 🔧 **AÇÕES NECESSÁRIAS**

### **PRIORIDADE ALTA** (Bloqueante)

#### **1. Descomentar e Atualizar EToResults**

**Problema**: Modelo comentado no `__init__.py`

**Solução**:
```python
# backend/database/models/__init__.py
from .climate_data import EToResults  # ← DESCOMENTAR

__all__ = [
    "AdminUser",
    "EToResults",  # ← ADICIONAR
    # ... resto
]
```

#### **2. Modernizar Modelo EToResults para Multi-API**

**Opção A - Modelo Flexível (JSON)**:
```python
class ClimateData(Base):
    __tablename__ = "climate_data"
    
    id = Column(Integer, primary_key=True)
    source_api = Column(String(50))  # "nasa_power", "openmeteo", etc.
    latitude = Column(Float)
    longitude = Column(Float)
    date = Column(DateTime)
    
    # Dados brutos como JSON (flexível)
    raw_data = Column(JSONB)
    
    # Dados harmonizados (mesmas unidades)
    harmonized_data = Column(JSONB)
    
    # ETo calculado
    eto_mm_day = Column(Float)
    eto_method = Column(String(20))  # "FAO-56", "Penman", etc.
```

**Opção B - Colunas Específicas por API** (mais complexo):
```python
# Colunas NASA POWER
t2m_max_nasa = Column(Float)
# Colunas Open-Meteo
temperature_2m_max_openmeteo = Column(Float)
# etc.
```

**RECOMENDAÇÃO**: **Opção A** (JSONB) por flexibilidade

#### **3. Atualizar data_storage.py**

Criar função genérica que aceita qualquer API:
```python
def save_climate_data(
    source: str,  # "nasa_power", "data_fusion", etc.
    data: pd.DataFrame,
    lat: float,
    lon: float,
):
    """Salva dados de qualquer API."""
    for idx, row in data.iterrows():
        record = ClimateData(
            source_api=source,
            latitude=lat,
            longitude=lon,
            date=idx,
            raw_data=row.to_dict(),  # Dados brutos
            harmonized_data=harmonize(row, source),  # Normalizado
            eto_mm_day=row.get('ETo') or row.get('et0_fao_evapotranspiration'),
        )
        db.add(record)
```

#### **4. Criar Migração Alembic**

```bash
# Criar migração para novos modelos
alembic revision --autogenerate -m "Add climate_data and historical tables"

# Aplicar
alembic upgrade head
```

---

### **PRIORIDADE MÉDIA**

#### **5. Configurar Celery Beat**

Verificar se `celery_config.py` tem:
```python
from celery.schedules import crontab

app.conf.beat_schedule = {
    'prefetch-nasa-daily': {
        'task': 'climate.prefetch_nasa_popular_cities',
        'schedule': crontab(hour=3, minute=0),  # 03:00 BRT
    },
    # ... resto das tasks
}
```

#### **6. Validar Schema climate_history**

Opções:
1. Criar via Alembic migration
2. Usar SQL direto (DDL em `database/init/`)
3. Integrar com `climate_history_loader.py`

#### **7. Implementar Task de Histórico no Beat** (se aplicável)

Se quiser processar downloads históricos agendados:
```python
'process-pending-historical-downloads': {
    'task': 'backend.infrastructure.celery.tasks.process_historical_download',
    'schedule': crontab(minute='*/30'),  # A cada 30 min
},
```

---

### **PRIORIDADE BAIXA**

#### **8. Adicionar Testes de Integração**

Testar:
- Salvar dados de cada API
- Recuperar dados harmonizados
- Health checks
- Celery tasks

#### **9. Documentar Schema do Banco**

Criar `database/README.md` com:
- Diagrama ER
- Descrição de tabelas
- Índices e otimizações
- Estratégia de particionamento (se aplicável)

---

## 📋 **CHECKLIST DE IMPLEMENTAÇÃO**

### **Fase 1: Corrigir Modelo de Dados** (URGENTE)

- [ ] Descomentar `EToResults` em `models/__init__.py`
- [ ] Criar novo modelo `ClimateData` (JSONB flexível)
- [ ] Atualizar `data_storage.py` para multi-API
- [ ] Criar migração Alembic
- [ ] Testar salvamento com cada API

### **Fase 2: Validar Infraestrutura**

- [ ] ✅ **celery_config.py VALIDADO** - Excelente configuração!
- [ ] ✅ **Celery Beat schedule COMPLETO** - 10 tasks agendadas
- [ ] ✅ **redis_pool.py VALIDADO** - Pool otimizado
- [ ] ✅ **session_database.py VALIDADO** - Re-export OK
- [ ] Validar schema `climate_history`
- [ ] Testar health checks
- [ ] Integrar nova task `process_historical_download` no Beat (se necessário)

### **Fase 3: Integração**

- [ ] Integrar `historical_download` task com salvamento BD
- [ ] Testar workflow completo: requisição → download → save → email
- [ ] Validar tasks de pré-carregamento
- [ ] Monitorar métricas Prometheus

### **Fase 4: Testes**

- [ ] Testes unitários para modelos
- [ ] Testes de integração para tasks
- [ ] Testes de carga (stress test)
- [ ] Validação de segurança (SQL injection, etc.)

---

## 🎯 **PRÓXIMOS PASSOS SUGERIDOS**

### **Imediato** (hoje):
1. ✅ Descomentar `EToResults` (1 linha)
2. ✅ Criar modelo `ClimateData` (novo arquivo)
3. ✅ Atualizar `data_storage.py` (função genérica)
4. ✅ Rodar migração Alembic

### **Curto Prazo** (esta semana):
5. ✅ Validar Celery Beat config
6. ✅ Testar workflow de download histórico
7. ✅ Verificar schema `climate_history`

### **Médio Prazo** (próximas 2 semanas):
8. ✅ Testes de integração
9. ✅ Documentação completa
10. ✅ Deploy em staging

---

## ⚠️ **AVISOS IMPORTANTES**

### **1. Migração de Dados**

Se já existem dados em `eto_results` (modelo antigo):
- ⚠️ Criar script de migração
- ⚠️ Backup antes de alterar schema
- ⚠️ Testar migração em ambiente de dev

### **2. Compatibilidade**

Garantir que código legado que usa `EToResults` continue funcionando:
- ✅ Manter modelo antigo (deprecated)
- ✅ Criar adapter/wrapper
- ✅ Documentar migração

### **3. Performance**

JSONB pode ter impacto:
- ✅ Criar índices GIN para queries em JSON
- ✅ Considerar particionamento por data
- ✅ Monitorar query performance

---

## 📊 **RESUMO EXECUTIVO**

| Componente | Status | Ação |
|------------|--------|------|
| **database/config** | ✅ OK | Nenhuma |
| **database/init** | ⚠️ Incompleto | Melhorar init_alembic.py |
| **backend/database/connection** | ✅ Excelente | Nenhuma |
| **backend/database/redis_pool** | ✅ Muito Bom | Nenhuma |
| **backend/database/session_database** | ✅ OK | Nenhuma |
| **backend/database/models** | ❌ Problema | Descomentar + modernizar |
| **backend/database/data_storage** | ⚠️ Desatualizado | Reescrever para multi-API |
| **backend/database/health_checks** | ✅ Completo | Nenhuma |
| **infrastructure/cache/celery_tasks** | ✅ Bom | Nenhuma |
| **infrastructure/cache/climate_tasks** | ✅ Excelente | Nenhuma |
| **infrastructure/celery/celery_config** | ✅ Excelente | Nenhuma |
| **infrastructure/celery/tasks** | ✅ Organizado | Nenhuma |
| **infrastructure/loaders** | ⚠️ Schema? | Validar climate_history |

### **Score Geral**: **8/10** ⬆️ (melhorou de 7/10)

**Crítico**: Modelo `EToResults` comentado e desatualizado  
**Excelente**: Celery config completo + Beat schedule + Redis pool  
**Muito Bom**: Health checks, connection pool, tasks de pré-carregamento  

---

## 📊 **ANÁLISE DETALHADA - NOVOS ARQUIVOS**

### **✅ celery_config.py - CONFIGURAÇÃO PERFEITA**

**Pontos Fortes**:
1. ✅ **Beat Schedule Completo**: 10 tasks agendadas
   - Limpeza de cache (02:00)
   - Pre-fetch NASA (03:00)
   - Pre-fetch NWS Forecast (a cada 6h)
   - Pre-fetch NWS Stations (04:00)
   - Pre-fetch Open-Meteo Forecast (05:00)
   - Pre-fetch Open-Meteo Archive (domingo 06:00)
   - Pre-fetch MET Norway (07:00)
   - Stats de cache (a cada hora)
   - Sync visitantes (a cada 30min)
   - Limpeza expirados (meia-noite)

2. ✅ **Filas Separadas**:
   - `general`: Tasks genéricas
   - `eto_processing`: Cálculos de ETo
   - `data_download`: Downloads climáticos
   - `data_processing`: Processamento de dados
   - `elevation`: Serviços de elevação

3. ✅ **MonitoredProgressTask**:
   - Métricas Prometheus automáticas
   - Publicação de progresso via Redis/WebSocket
   - Rastreamento de duração e status

4. ✅ **Timezone Correto**: `America/Sao_Paulo`

**Única Observação**:
- ⏳ Task `process_historical_download` **NÃO está no Beat**
- Isso está OK! Task é acionada sob demanda (`.delay()`)
- Não precisa agendamento automático

### **✅ redis_pool.py - CONNECTION POOL OTIMIZADO**

**Configurações**:
```python
max_connections=50          # Limite de conexões
socket_timeout=10           # Timeout de operações
socket_connect_timeout=5    # Timeout de conexão
retry_on_timeout=True       # Retry automático
health_check_interval=30    # Ping a cada 30s
decode_responses=True       # Strings em vez de bytes
```

**Padrão Singleton**: Garante pool único global

### **✅ session_database.py - RE-EXPORT LIMPO**

Função: Compatibilidade com código legado
- Re-exporta `get_db`, `get_db_context`, `engine`, `Base`
- Mantém imports funcionando

---

**Quer que eu comece pelas correções críticas (Fase 1)?** 🔧
