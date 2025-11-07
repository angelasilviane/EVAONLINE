# Testes de Performance - EVAonline

Testes de carga, stress, latência e throughput do backend.

## Arquivo

- **test_performance.py** - 5 seções de testes

### Seções Cobertas

1. **Health Check Load (100 requisições)**
   - Testa latência com múltiplas requisições sequenciais
   - Coleta: média, mín, máx, mediana de tempo de resposta

2. **Concurrent Requests (50 simultâneas)**
   - Testa comportamento com múltiplas requisições simultâneas
   - Calcula throughput (requisições/segundo)

3. **Endpoint Comparison**
   - Compara performance de diferentes endpoints
   - Identifica gargalos

4. **Error Rate Analysis (100 requisições)**
   - Testa requisições inválidas
   - Analisa códigos HTTP de erro

5. **Stress Test (10 segundos)**
   - Requisições contínuas por período prolongado
   - Verifica estabilidade e degradação

## Como Rodar

Todos os testes:
```bash
pytest test_performance.py -v
```

Teste específico:
```bash
pytest test_performance.py::test_health_check_load -v
```

Com output em tempo real:
```bash
pytest test_performance.py -v -s
```

## Métricas Coletadas

- Latência: média, mínima, máxima, mediana (ms)
- Throughput: requisições/segundo
- Taxa de sucesso: percentual
- Códigos de erro: distribuição de status codes

## Resultados Esperados (Última Execução)

| Teste | Resultado |
|-------|-----------|
| Health Check (100 req) | 2.93ms avg |
| Concurrent (50 req) | 371.72 req/s |
| Endpoints Comparison | 2.76ms - 3.69ms |
| Error Rate | 0.0% taxa de erro |
| Stress Test (10s) | 345.27 req/s, 99.4% sucesso |

**Conclusão:** ✅ Performance está excelente
