# 📊 Monitoramento EVAonline

Guia de acesso aos dashboards e ferramentas de monitoramento.

---

## 🌐 **URLs de Acesso Direto**

Após iniciar os containers com `docker-compose up -d`, acesse:

### **1. Grafana - Dashboards Visuais**
- **URL**: http://localhost:3000
- **Usuário**: `admin` (configurado em `.env`)
- **Senha**: Definida em `GRAFANA_ADMIN_PASSWORD` no `.env`
- **Descrição**: Interface visual com dashboards personalizados

### **2. Prometheus - Métricas Brutas**
- **URL**: http://localhost:9090
- **Autenticação**: Nenhuma (acesso interno)
- **Descrição**: Consultas PromQL e exploração de métricas

### **3. Flower - Monitor Celery**
- **URL**: http://localhost:5555
- **Usuário**: `admin` (configurado em `.env`)
- **Senha**: Definida em `FLOWER_PASSWORD` no `.env`
- **Descrição**: Monitoramento de tasks e workers Celery

### **4. API Backend**
- **URL**: http://localhost:8000
- **Health Check**: http://localhost:8000/health
- **Docs**: http://localhost:8000/docs (Swagger)

---

## 📋 **Endpoints de Health Check**

### **Básico**
```bash
curl http://localhost:8000/health
```

**Resposta**:
```json
{
  "status": "ok",
  "service": "evaonline-api",
  "version": "1.0.0",
  "timestamp": 1699308000.0
}
```

### **Detalhado**
```bash
curl http://localhost:8000/health/detailed
```

**Resposta**:
```json
{
  "overall_status": "healthy",
  "postgres": {
    "status": "healthy",
    "response_time_ms": 5.2
  },
  "redis": {
    "status": "healthy",
    "response_time_ms": 2.1
  },
  "celery": {
    "status": "healthy",
    "active_workers": 2
  },
  "api": {
    "status": "healthy",
    "version": "1.0.0",
    "environment": "production",
    "debug": false
  }
}
```

### **Readiness (Docker Health Check)**
```bash
curl http://localhost:8000/ready
```

---

## 🔒 **Segurança**

### **Produção**
- ✅ Grafana: Autenticação obrigatória (usuário/senha)
- ✅ Flower: HTTP Basic Auth (usuário/senha)
- ⚠️ Prometheus: **Sem autenticação** (apenas rede interna Docker)

### **Configuração de Senhas**

Edite o arquivo `.env`:

```bash
# Grafana Admin
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=SuaSenhaSegura123!

# Flower (Celery)
FLOWER_USER=admin
FLOWER_PASSWORD=OutraSenhaSegura456!
```

**⚠️ IMPORTANTE**: 
- **NÃO versione** o arquivo `.env` com senhas reais
- Use `.env.example` como template
- Troque as senhas padrão em produção

---

## 🚀 **Iniciando Monitoramento**

### **Docker Compose**

```bash
# Iniciar todos os serviços (incluindo monitoramento)
docker-compose up -d

# Verificar status
docker-compose ps

# Logs do Grafana
docker-compose logs -f grafana

# Logs do Prometheus
docker-compose logs -f prometheus

# Parar tudo
docker-compose down
```

### **Desenvolvimento (opcional)**

Para desenvolvimento, você pode desabilitar monitoramento:

```bash
# Iniciar apenas backend essencial
docker-compose up -d postgres redis api celery-worker

# Verificar
docker-compose ps
```

---

## 📈 **Dashboards Grafana**

Os dashboards estão pré-configurados em:
- `docker/monitoring/grafana/dashboards/evaonline-metrics.json`
- `docker/monitoring/grafana/dashboards/evaonline-user-dashboard.json`

### **Importar Dashboard Manualmente**

1. Acesse http://localhost:3000
2. Login com usuário/senha do `.env`
3. Menu: **Dashboards** → **Import**
4. Upload do arquivo `.json` ou cole o conteúdo
5. Selecione datasource: **Prometheus**

---

## 🔍 **Prometheus - Consultas Úteis**

Acesse http://localhost:9090 e experimente:

### **API Response Time (p95)**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### **Taxa de Erros 5xx**
```promql
rate(http_requests_total{status=~"5.."}[5m])
```

### **Uso de Memória da API**
```promql
process_resident_memory_bytes{job="evaonline-api"}
```

### **Tasks Celery Ativas**
```promql
celery_tasks_active_total
```

---

## 🛠️ **Troubleshooting**

### **Grafana não carrega dashboards**

```bash
# Verificar logs
docker-compose logs grafana

# Verificar se Prometheus está respondendo
curl http://localhost:9090/api/v1/status/config

# Reiniciar Grafana
docker-compose restart grafana
```

### **Prometheus não coleta métricas**

```bash
# Verificar targets
curl http://localhost:9090/api/v1/targets

# Ver configuração
docker exec evaonline-prometheus cat /etc/prometheus/prometheus.yml

# Reiniciar Prometheus
docker-compose restart prometheus
```

### **Flower não autentica**

Verifique se as variáveis estão corretas no `.env`:

```bash
docker-compose exec flower env | grep FLOWER
```

---

## 📦 **Arquivos de Configuração**

```
docker/monitoring/
├── prometheus.yml              # Config Prometheus
├── grafana/
│   ├── provisioning/
│   │   ├── dashboards/
│   │   │   └── dashboard.yml   # Auto-provisioning dashboards
│   │   └── datasources/
│   │       └── prometheus.yml  # Config datasource Prometheus
│   └── dashboards/
│       ├── evaonline-metrics.json          # Dashboard principal
│       └── evaonline-user-dashboard.json   # Dashboard usuário
└── README.md                   # Este arquivo
```

---

## 🔗 **Links Úteis**

- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)
- [Flower Docs](https://flower.readthedocs.io/)
- [FastAPI Metrics](https://fastapi.tiangolo.com/advanced/middleware/)

---

## 📝 **Notas**

- **Sem Nginx**: Monitoramento acessado **diretamente** (sem proxy)
- **Docker Network**: Todos os serviços na rede `evaonline-network`
- **Dados Persistentes**: Volumes Docker mantêm dados históricos
- **Portas Expostas**: 3000 (Grafana), 9090 (Prometheus), 5555 (Flower)

---

**Última atualização**: 2024-11-06
