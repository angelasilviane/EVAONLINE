# Documentação de Testes - EVAonline

Guias e referências para trabalhar com os testes.

## Índice

- [README.md](#) - Estrutura geral
- [QUICK_START.md](#) - Início rápido
- [BEST_PRACTICES.md](#) - Boas práticas
- [CI_CD.md](#) - Integração contínua

## Próximos Documentos a Criar

### QUICK_START.md
- Como rodar os testes pela primeira vez
- Configuração do ambiente
- Troubleshooting comum

### BEST_PRACTICES.md
- Padrões para escrever novos testes
- Nomes de funções e variáveis
- Estrutura de testes
- Fixtures e mocks

### CI_CD.md
- Integração com GitHub Actions
- Configuração de CI/CD
- Deployment após testes

### TROUBLESHOOTING.md
- Erros comuns e soluções
- PostgreSQL/Redis offline
- Problemas de encoding
- Timeout de testes

## Referências Rápidas

### Rodar tudo
```bash
cd backend/tests/runners
python run_all_tests.py
```

### Rodar teste específico
```bash
cd backend/tests
pytest integration/test_routes.py -v
```

### Com Docker
```bash
cd backend/tests/runners
bash run_tests_docker.sh        # Linux/Mac
./run_tests_docker.bat          # Windows
```
