# 📚 Scripts de Automação - EVAonline

## 📖 Índice

- [Visão Geral](#visão-geral)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Scripts Essenciais](#scripts-essenciais)
- [Como Executar](#como-executar)

---

## 🎯 Visão Geral

Esta pasta contém **scripts de automação e manutenção** para o projeto EVAonline, organizados em subpastas temáticas:

- ✅ **Scripts de dados**: Importação e manipulação de dados
- ✅ **Scripts de validação**: Verificação de qualidade e integridade
- ✅ **Scripts de teste**: Testes não-pytest e validações manuais
- ✅ **Scripts de exemplo**: Demonstrações e exemplos de uso

---

## 📁 Estrutura de Pastas

```
scripts/
├── data/                    # Scripts essenciais de manipulação de dados
│   ├── load_climate_reports_to_postgres.py
│   └── validate_data_load.py
├── validation/              # Scripts de validação e verificação
│   ├── check_api_coverage.py
│   └── check_complete_coverage.py
├── testing/                 # Testes não-pytest
│   └── test_api_limits.py
├── examples/                # Exemplos e demonstrações
│   └── exemplo_nws_stations.py
└── README.md               # Esta documentação
```

---

## 🔧 Scripts Essenciais

### 📊 Scripts de Dados (`data/`)

#### 1. `load_climate_reports_to_postgres.py` ⭐
**Importa dados climáticos para o PostgreSQL**

```bash
python scripts/data/load_climate_reports_to_postgres.py
```

**O que faz:**
- Lê dados de relatórios climáticos em `reports/`
- Carrega resumos, normais anuais e análises de extremos
- Trata erros e duplicatas com upsert
- Gera relatório detalhado de importação

**Configuração:**
- Banco de dados: Variáveis de ambiente PostgreSQL
- Arquivos de entrada: `reports/summary/` (CSVs) e `reports/cities/` (JSONs)

#### 2. `validate_data_load.py`
**Valida dados carregados no PostgreSQL**

```bash
python scripts/data/validate_data_load.py
```

**O que faz:**
- Verifica integridade dos dados após importação
- Conta registros por tabela
- Valida geometrias GIS
- Verifica chaves estrangeiras
- Gera relatório detalhado de validação

### � Scripts de Validação (`validation/`)

#### 3. `check_api_coverage.py`
**Verifica cobertura de limites físicos por API**

```bash
python scripts/validation/check_api_coverage.py
```

**O que faz:**
- Verifica se todas as variáveis retornadas por cada API têm limites definidos
- Analisa cobertura por API individualmente
- Identifica variáveis faltando limites

#### 4. `check_complete_coverage.py`
**Verificação completa de cobertura de limites**

```bash
python scripts/validation/check_complete_coverage.py
```

**O que faz:**
- Verifica cobertura completa de todas as variáveis climáticas possíveis
- Compara com limites definidos em `data_preprocessing.py`
- Gera relatório de cobertura total

### 🧪 Scripts de Teste (`testing/`)

#### 5. `test_api_limits.py`
**Testa aplicação de limites físicos**

```bash
python scripts/testing/test_api_limits.py
```

**O que faz:**
- Testa se os limites físicos estão sendo aplicados corretamente
- Usa dados extremos para validar cada API
- Gera relatório de testes com taxa de sucesso

### 💡 Scripts de Exemplo (`examples/`)

#### 6. `exemplo_nws_stations.py`
**Exemplo de uso da API NWS Stations**

```bash
python scripts/examples/exemplo_nws_stations.py
```

**O que faz:**
- Demonstra como buscar estações meteorológicas próximas
- Mostra como obter observações históricas
- Exemplo completo de uso da API NWS

---

## 🚀 Como Executar

### Opção 1: Python direto
```bash
cd /caminho/para/Evaonline_Temp

# Scripts de dados
python scripts/data/load_climate_reports_to_postgres.py
python scripts/data/validate_data_load.py

# Scripts de validação
python scripts/validation/check_api_coverage.py
python scripts/validation/check_complete_coverage.py

# Scripts de teste
python scripts/testing/test_api_limits.py

# Exemplos
python scripts/examples/exemplo_nws_stations.py
```

### Opção 2: Com virtual environment
```bash
source .venv/bin/activate          # Linux/Mac
.venv\Scripts\activate             # Windows

python scripts/data/load_climate_reports_to_postgres.py
```

### Opção 3: Com Docker
```bash
docker-compose exec api python scripts/data/load_climate_reports_to_postgres.py
```

---

## 📋 Checklist antes de executar

- [ ] `.env` está configurado com credenciais corretas
- [ ] PostgreSQL está rodando (`docker-compose ps`)
- [ ] Redis está rodando
- [ ] Arquivos de entrada estão em `reports/summary/` e `reports/cities/`

---

## 📊 Auditoria Completa do Projeto

Execute a auditoria para verificar integridade geral:

```bash
python scripts/maintenance/full_project_audit.py
```

**Verifica:**
- ✅ Arquivos na raiz do projeto
- ✅ Estrutura de pastas
- ✅ Configuração Docker
- ✅ Assets estáticos
- ✅ Settings da aplicação
- ✅ Frontend (Dash)
- ✅ Backend (FastAPI)
- ✅ Traduções
- ✅ Dependências Python

**Gera relatório:** `FULL_PROJECT_AUDIT_REPORT.json`

---

## 🐛 Troubleshooting

### Erro: `ModuleNotFoundError: No module named 'backend'`
```bash
# Adicione o caminho do projeto ao PYTHONPATH
export PYTHONPATH=/caminho/para/Evaonline_Temp:$PYTHONPATH
python scripts/data/load_climate_reports_to_postgres.py
```

### Erro: Conexão PostgreSQL recusada
```bash
# Verifique se PostgreSQL está rodando
docker-compose ps

# Verifique credenciais no .env
cat .env | grep POSTGRES
```

### Erro: Arquivo de entrada não encontrado
```bash
# Verifique arquivos em reports/
ls -la reports/summary/
ls -la reports/cities/
```

---

## 📝 Criando novos scripts

### Template para novo script

```python
#!/usr/bin/env python3
"""
Descrição do script
Uso: python scripts/novo_script.py
"""

import sys
from pathlib import Path
from loguru import logger

# Configuração de logging
logger.add(
    "logs/novo_script_{time}.log",
    rotation="500 MB",
    retention="7 days"
)

def main():
    """Função principal."""
    logger.info("Iniciando novo script...")
    
    try:
        # Seu código aqui
        logger.success("Script executado com sucesso!")
    except Exception as e:
        logger.error(f"Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 📂 Onde colocar novos scripts?

- **`data/`**: Scripts essenciais de manipulação de dados
- **`validation/`**: Scripts de verificação e validação
- **`testing/`**: Testes não-pytest e validações manuais
- **`examples/`**: Exemplos e demonstrações de uso

---

## 📞 Suporte

- **Documentação**: Ver `docs/`
- **Issues**: Abra um issue no GitHub
- **Logs**: Ver `logs/` para detalhes de execução

---

**Última atualização**: 29/10/2025
**Reorganização**: Scripts organizados em subpastas temáticas
