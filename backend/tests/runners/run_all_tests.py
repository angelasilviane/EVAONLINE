#!/usr/bin/env python3
"""
EXECUTOR DE TODOS OS TESTES - EVAonline
==========================================
Executa todos os scripts de teste em sequência.

Uso:
    python backend/tests/run_all_tests.py

Testes executados:
1. test_backend_audit.py - Auditoria completa do backend
2. test_routes.py - Teste de todas as rotas API
3. test_database.py - Teste de operações do banco de dados
4. test_performance.py - Teste de performance e carga
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Cores
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_header(text):
    """Print main header."""
    print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
    print(f"{BOLD}{CYAN}{text}{RESET}")
    print(f"{BOLD}{CYAN}{'='*80}{RESET}\n")


def print_subheader(text):
    """Print sub header."""
    print(f"\n{BOLD}{BLUE}{text}{RESET}\n")


def run_test(script_name, description):
    """Run a single test script."""
    print_subheader(f">> Executando: {description}")
    print(f"   {CYAN}Arquivo: {script_name}{RESET}\n")

    script_path = Path(__file__).parent / script_name

    if not script_path.exists():
        print(f"{RED}[FAIL] Arquivo nao encontrado: {script_path}{RESET}\n")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=Path(__file__).parent.parent.parent,
            capture_output=False,
            timeout=300,  # 5 min timeout
        )

        if result.returncode == 0:
            print(f"\n{GREEN}[PASS] {description} - CONCLUIDO{RESET}\n")
            return True
        else:
            print(
                f"\n{RED}[FAIL] {description} - FALHOU (codigo: "
                f"{result.returncode}){RESET}\n"
            )
            return False

    except subprocess.TimeoutExpired:
        print(f"\n{RED}[FAIL] {description} - TIMEOUT (>5 min){RESET}\n")
        return False
    except Exception as e:
        print(f"\n{RED}[FAIL] {description} - ERRO: {e}{RESET}\n")
        return False


def main():
    """Execute all tests."""
    print_header("EXECUTOR DE TESTES - EVAonline")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    tests = [
        ("test_backend_audit.py", "Auditoria Backend (14 testes)"),
        ("test_routes.py", "Teste de Rotas (9 endpoints)"),
        ("test_database.py", "Teste do Banco (7 testes)"),
        ("test_performance.py", "Teste de Performance (5 testes)"),
    ]

    results = []
    start_time = datetime.now()

    print(f"{BOLD}Testes a executar:{RESET}")
    for i, (script, desc) in enumerate(tests, 1):
        print(f"   {i}. {desc}")
    print()

    # Execute tests
    for script, description in tests:
        success = run_test(script, description)
        results.append((description, success))

    # Print summary
    print_header("RESUMO DOS TESTES")

    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    duration = (datetime.now() - start_time).total_seconds()

    print(f"{BOLD}Resultados:{RESET}\n")
    for description, success in results:
        status = f"{GREEN}[PASS]{RESET}" if success else f"{RED}[FAIL]{RESET}"
        print(f"   {description:<50} {status}")

    print(f"\n{BOLD}Estatisticas:{RESET}")
    print(f"   Total: {len(results)} testes")
    print(f"   {GREEN}Aprovados: {passed}{RESET}")
    print(f"   {RED}Falhados: {failed}{RESET}")
    print(f"   Duracao: {duration:.1f}s")

    # Final status
    sep = "=" * 80
    print(f"\n{BOLD}{sep}{RESET}")

    if failed == 0:
        print(f"{GREEN}{BOLD}TODOS OS TESTES PASSARAM!{RESET}")
        print(f"{GREEN}Backend esta operacional e pronto para uso.{RESET}\n")
        print(f"{BOLD}{sep}{RESET}\n")
        return 0
    else:
        print(f"{RED}{BOLD}{failed} TESTE(S) FALHARAM{RESET}")
        print(f"{RED}Verifique os erros acima.{RESET}\n")
        print(f"{BOLD}{sep}{RESET}\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
