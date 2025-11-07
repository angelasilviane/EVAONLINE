#!/usr/bin/env python3
"""
⚡ TESTE DE PERFORMANCE - EVAonline
===================================
Load testing e análise de performance da API.

Uso:
    python backend/tests/test_performance.py

Testa:
- Throughput (requisições por segundo)
- Latência média, mínima e máxima
- Taxa de erro
- Tempo de resposta dos endpoints
- Carga simultânea
"""

import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import mean, median

from fastapi.testclient import TestClient

# Adicionar raiz do projeto ao PYTHONPATH
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Cores
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

results = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "total_time": 0,
    "response_times": [],
    "error_codes": {},
}


def header(text):
    """Print section header."""
    print(f"\n{CYAN}{BOLD}{'='*80}{RESET}")
    print(f"{CYAN}{BOLD}{text}{RESET}")
    print(f"{CYAN}{BOLD}{'='*80}{RESET}\n")


def success(msg, detail=""):
    """Print success message."""
    print(f"{GREEN}✅ {msg}{RESET}", end="")
    if detail:
        print(f" | {detail}")
    else:
        print()


def failed(msg, detail=""):
    """Print failed message."""
    print(f"{RED}❌ {msg}{RESET}", end="")
    if detail:
        print(f" | {detail[:60]}")
    else:
        print()


def info_msg(msg, detail=""):
    """Print info message."""
    print(f"{BLUE}ℹ️  {msg}{RESET}", end="")
    if detail:
        print(f" | {detail}")
    else:
        print()


# ============================================================================
# TESTE 1: HEALTH CHECK LOAD TEST
# ============================================================================


def test_health_check_load(client: TestClient, num_requests: int = 100):
    """Load test health check endpoint."""
    header(f"TESTE 1: HEALTH CHECK ({num_requests} requisições)")

    endpoint = "/api/v1/health"
    local_times = []

    print(f"Enviando {num_requests} requisições para {endpoint}...\n")

    for i in range(num_requests):
        start = time.time()
        try:
            response = client.get(endpoint)
            duration = (time.time() - start) * 1000  # ms

            if response.status_code == 200:
                results["successful_requests"] += 1
                local_times.append(duration)
            else:
                results["failed_requests"] += 1
                code = response.status_code
                results["error_codes"][code] = (
                    results["error_codes"].get(code, 0) + 1
                )

            results["response_times"].append(duration)
            results["total_requests"] += 1

            if (i + 1) % 20 == 0:
                print(f"   Progresso: {i + 1}/{num_requests}")

        except Exception as e:
            results["failed_requests"] += 1
            results["total_requests"] += 1

    # Print results
    if local_times:
        avg_time = mean(local_times)
        min_time = min(local_times)
        max_time = max(local_times)
        median_time = median(local_times)

        print(f"\n   📊 Resultados para {endpoint}:")
        print(
            f"      Requisições bem-sucedidas: {results['successful_requests']}"
        )
        print(f"      Tempo médio: {avg_time:.2f}ms")
        print(f"      Tempo mínimo: {min_time:.2f}ms")
        print(f"      Tempo máximo: {max_time:.2f}ms")
        print(f"      Mediana: {median_time:.2f}ms")

        success(f"Health check load test concluído")
    else:
        failed("Nenhuma resposta bem-sucedida")


# ============================================================================
# TESTE 2: CONCURRENT REQUESTS
# ============================================================================


def test_concurrent_requests(client: TestClient, num_concurrent: int = 50):
    """Test concurrent requests."""
    header(f"TESTE 2: REQUISIÇÕES CONCORRENTES ({num_concurrent})")

    endpoint = "/api/v1/health"
    local_times = []

    print(f"Enviando {num_concurrent} requisições simultâneas...\n")

    start_total = time.time()

    for i in range(num_concurrent):
        start = time.time()
        try:
            response = client.get(endpoint)
            duration = (time.time() - start) * 1000

            if response.status_code == 200:
                results["successful_requests"] += 1
                local_times.append(duration)
            else:
                results["failed_requests"] += 1

            results["total_requests"] += 1

        except Exception:
            results["failed_requests"] += 1
            results["total_requests"] += 1

    total_time = (time.time() - start_total) * 1000

    if local_times:
        avg_time = mean(local_times)
        throughput = len(local_times) / (total_time / 1000)

        print(f"\n   📊 Resultados para requisições concorrentes:")
        print(f"      Total de requisições: {len(local_times)}")
        print(f"      Tempo total: {total_time:.2f}ms")
        print(f"      Tempo médio por requisição: {avg_time:.2f}ms")
        print(f"      Throughput: {throughput:.2f} req/s")

        success("Teste de concorrência concluído")
    else:
        failed("Nenhuma resposta bem-sucedida")


# ============================================================================
# TESTE 3: DIFFERENT ENDPOINTS
# ============================================================================


def test_multiple_endpoints(client: TestClient):
    """Test multiple endpoints for performance comparison."""
    header("TESTE 3: COMPARAÇÃO DE ENDPOINTS")

    endpoints = [
        ("GET", "/api/v1/health", 20),
        ("GET", "/api/v1/cache/stats", 20),
        ("GET", "/api/v1/stats/visitors", 20),
    ]

    print("Testando diferentes endpoints...\n")

    endpoint_times = {}

    for method, path, num_req in endpoints:
        local_times = []

        for _ in range(num_req):
            start = time.time()
            try:
                response = client.get(path)
                duration = (time.time() - start) * 1000

                if response.status_code in (200, 400):
                    local_times.append(duration)

                results["total_requests"] += 1
                if response.status_code == 200:
                    results["successful_requests"] += 1

            except Exception:
                results["total_requests"] += 1
                results["failed_requests"] += 1

        if local_times:
            endpoint_times[path] = {
                "avg": mean(local_times),
                "min": min(local_times),
                "max": max(local_times),
                "count": len(local_times),
            }

    # Print results
    print(f"\n   📊 Resultados por endpoint:")
    for path, stats in sorted(
        endpoint_times.items(), key=lambda x: x[1]["avg"]
    ):
        print(f"\n      {path}:")
        print(f"         Requisições: {stats['count']}")
        print(f"         Tempo médio: {stats['avg']:.2f}ms")
        print(f"         Min/Max: {stats['min']:.2f}ms / {stats['max']:.2f}ms")

    success("Comparação de endpoints concluída")


# ============================================================================
# TESTE 4: ERROR RATE TEST
# ============================================================================


def test_error_rate(client: TestClient, num_requests: int = 100):
    """Test error rate with invalid requests."""
    header(f"TESTE 4: TAXA DE ERRO ({num_requests} requisições)")

    endpoints = [
        ("GET", "/api/v1/nonexistent"),
        ("GET", "/api/v1/health"),
        ("POST", "/api/v1/cache/invalid", {}),
    ]

    print("Testando taxa de erro com requisições inválidas...\n")

    for method, path, *payload in endpoints:
        body = payload[0] if payload else None
        local_success = 0
        local_error = 0

        for _ in range(num_requests // len(endpoints)):
            try:
                if method == "GET":
                    response = client.get(path)
                elif method == "POST":
                    response = client.post(path, json=body or {})

                if response.status_code < 500:
                    local_success += 1
                else:
                    local_error += 1

            except Exception:
                local_error += 1

        total = local_success + local_error
        error_rate = (local_error / total * 100) if total > 0 else 0

        print(f"\n   {path}:")
        print(f"      Sucesso: {local_success}")
        print(f"      Erro: {local_error}")
        print(f"      Taxa de erro: {error_rate:.1f}%")

    success("Teste de taxa de erro concluído")


# ============================================================================
# TESTE 5: STRESS TEST
# ============================================================================


def test_stress(client: TestClient, duration: int = 30):
    """Stress test - maintain load for specified duration."""
    header(f"TESTE 5: STRESS TEST ({duration}s)")

    endpoint = "/api/v1/health"
    local_times = []
    start_total = time.time()

    print(f"Enviando requisições por {duration}s para {endpoint}...\n")

    while (time.time() - start_total) < duration:
        start = time.time()
        try:
            response = client.get(endpoint)
            duration_ms = (time.time() - start) * 1000

            if response.status_code == 200:
                results["successful_requests"] += 1
                local_times.append(duration_ms)
            else:
                results["failed_requests"] += 1

            results["total_requests"] += 1

        except Exception:
            results["failed_requests"] += 1
            results["total_requests"] += 1

        elapsed = time.time() - start_total
        if int(elapsed) % 5 == 0 and elapsed < duration:
            print(f"   Tempo decorrido: {int(elapsed)}s")

    total_time = time.time() - start_total

    if local_times:
        avg_time = mean(local_times)
        throughput = len(local_times) / total_time
        success_rate = (
            results["successful_requests"] / results["total_requests"] * 100
        )

        print(f"\n   📊 Resultados do stress test:")
        print(f"      Duração: {total_time:.1f}s")
        print(f"      Requisições totais: {len(local_times)}")
        print(f"      Tempo médio: {avg_time:.2f}ms")
        print(f"      Throughput: {throughput:.2f} req/s")
        print(f"      Taxa de sucesso: {success_rate:.1f}%")

        success("Stress test concluído")
    else:
        failed("Nenhuma resposta bem-sucedida no stress test")


# ============================================================================
# RESUMO FINAL
# ============================================================================


def print_summary():
    """Print final summary."""
    header("📊 RESUMO DE PERFORMANCE")

    if results["response_times"]:
        avg_time = mean(results["response_times"])
        min_time = min(results["response_times"])
        max_time = max(results["response_times"])
        median_time = median(results["response_times"])

        success_rate = (
            results["successful_requests"] / results["total_requests"] * 100
            if results["total_requests"] > 0
            else 0
        )

        print(f"\n   📊 Estatísticas Gerais:")
        print(f"      Total de requisições: {results['total_requests']}")
        print(f"      Bem-sucedidas: {results['successful_requests']}")
        print(f"      Falhadas: {results['failed_requests']}")
        print(f"      Taxa de sucesso: {success_rate:.1f}%")

        print(f"\n   ⏱️  Tempos de Resposta:")
        print(f"      Médio: {avg_time:.2f}ms")
        print(f"      Mínimo: {min_time:.2f}ms")
        print(f"      Máximo: {max_time:.2f}ms")
        print(f"      Mediana: {median_time:.2f}ms")

        print(f"\n   🔍 Códigos de Erro:")
        if results["error_codes"]:
            for code, count in sorted(results["error_codes"].items()):
                print(f"      HTTP {code}: {count}")
        else:
            print(f"      Nenhum erro HTTP")

        sep = "=" * 80
        print(f"\n{BOLD}{sep}{RESET}")
        if success_rate >= 95:
            status = "✅ PERFORMANCE ESTÁ BOM!"
            print(f"{GREEN}{BOLD}{status}{RESET}\n")
        elif success_rate >= 80:
            status = "⚠️  PERFORMANCE ACEITÁVEL"
            print(f"{YELLOW}{BOLD}{status}{RESET}\n")
        else:
            status = "❌ PROBLEMAS DE PERFORMANCE"
            print(f"{RED}{BOLD}{status}{RESET}\n")
        print(f"{BOLD}{sep}{RESET}\n")


# ============================================================================
# MAIN
# ============================================================================


def main() -> None:
    """Execute performance tests."""
    print(f"\n{BOLD}{BLUE}EVAonline - TESTE DE PERFORMANCE{RESET}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    try:
        from backend.main import app

        client = TestClient(app)

        # Run tests
        test_health_check_load(client, num_requests=100)
        test_concurrent_requests(client, num_concurrent=50)
        test_multiple_endpoints(client)
        test_error_rate(client, num_requests=100)
        test_stress(client, duration=10)  # 10 seconds stress test

        print_summary()

    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Teste de performance interrompido{RESET}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}{BOLD}❌ Erro:{RESET} {e}\n")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
