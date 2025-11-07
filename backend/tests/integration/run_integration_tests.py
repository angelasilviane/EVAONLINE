#!/usr/bin/env python3
"""
Runner para testes de validacao e fluxo de dados.
Executa testes de integracao sem criar documentos, apenas verificando funcionalidade.
"""
import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
scripts_dir = project_root / "backend" / "tests" / "integration"

print("\n" + "=" * 80)
print("RUNNER DE TESTES DE INTEGRACAO - EVAonline")
print("=" * 80)

tests = [
    ("Validacao do Backend", scripts_dir / "validate_backend.py"),
    ("Fluxo de Dados", scripts_dir / "test_data_flow.py"),
]

results = []

for test_name, test_file in tests:
    print("\n[EXECUTANDO] {}".format(test_name))
    print("-" * 80)
    try:
        result = subprocess.run(
            [sys.executable, str(test_file)], capture_output=False, text=True
        )
        results.append(
            (test_name, "PASSOU" if result.returncode == 0 else "FALHOU")
        )
    except Exception as e:
        print("ERRO ao executar {}: {}".format(test_name, str(e)[:100]))
        results.append((test_name, "ERRO"))

print("\n" + "=" * 80)
print("RESUMO DOS TESTES")
print("=" * 80)
for test_name, status in results:
    print("{}: {}".format(test_name, status))
print("=" * 80 + "\n")
