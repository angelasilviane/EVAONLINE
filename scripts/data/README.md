# 📊 Scripts de Dados - EVAonline

Scripts essenciais para **manipulação e carregamento de dados** no projeto EVAonline.

## 📁 Arquivos nesta pasta

### `load_climate_reports_to_postgres.py` ⭐
**Script principal de carregamento de dados climáticos**

**Uso:**
```bash
python scripts/data/load_climate_reports_to_postgres.py
```

**Funcionalidades:**
- ✅ Carregamento bulk de dados climáticos para PostgreSQL
- ✅ Pool de conexões configurável para produção
- ✅ Validação de integridade de dados
- ✅ Transações seguras com rollback automático
- ✅ Constraints UNIQUE para evitar duplicatas
- ✅ Logging detalhado com rotação de arquivos
- ✅ Verificação de dados antes/depois do carregamento

**Entradas:**
- `reports/summary/cities_summary.csv`
- `reports/summary/annual_normals_comparison.csv`
- `reports/summary/extremes_analysis.csv`
- `reports/cities/report_*.json`
- `reports/summary/generation_metadata.json`

**Saídas:**
- Dados carregados nas tabelas PostgreSQL
- Logs em `logs/load_data.log`
- Relatório de execução no console

---

### `validate_data_load.py`
**Validação de dados carregados no PostgreSQL**

**Uso:**
```bash
python scripts/data/validate_data_load.py
```

**Funcionalidades:**
- ✅ Contagem de registros por tabela
- ✅ Validação de geometrias GIS (PostGIS)
- ✅ Verificação de integridade de chaves estrangeiras
- ✅ Validação de qualidade geral dos dados
- ✅ Geração de relatório detalhado em JSON

**Saídas:**
- Relatório de validação no console
- Arquivo JSON: `reports/validation_report.json`
- Logs em `logs/validate_data_load.log`

---

## 🔧 Dependências

Estes scripts requerem:
- ✅ PostgreSQL/PostGIS rodando
- ✅ Variáveis de ambiente configuradas (`.env`)
- ✅ Arquivos de entrada em `reports/`
- ✅ Backend do EVAonline no PYTHONPATH

---

## 📋 Pré-requisitos

Antes de executar:

1. **Banco de dados:**
   ```bash
   docker-compose up -d postgres
   ```

2. **Variáveis de ambiente:**
   ```bash
   # Verificar .env ou .env.local
   cat .env | grep POSTGRES
   ```

3. **Arquivos de entrada:**
   ```bash
   ls -la reports/summary/
   ls -la reports/cities/
   ```

---

## 🚀 Fluxo de Execução Recomendado

```bash
# 1. Carregar dados
python scripts/data/load_climate_reports_to_postgres.py

# 2. Validar carregamento
python scripts/data/validate_data_load.py
```

---

## 📊 Monitoramento

**Logs importantes:**
- `logs/load_data.log` - Detalhes do carregamento
- `logs/validate_data_load.log` - Resultados da validação

**Métricas de sucesso:**
- ✅ Dados carregados sem erros
- ✅ Todas as validações passando
- ✅ Relatórios gerados corretamente

---

**Última atualização**: 29/10/2025</content>
<parameter name="filePath">c:\Users\User\OneDrive\Documentos\GitHub\EVAonline_SoftwareX\scripts\data\README.md
