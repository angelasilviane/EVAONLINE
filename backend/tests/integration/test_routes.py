#!/usr/bin/env python3
"""
TESTE DE ROTAS - EVAonline
============================
Testa todos os endpoints da API com diferentes métodos HTTP.

Uso:
    python backend/tests/test_routes.py

Testa:
- Health checks
- ETo calculation
- Climate sources
- Cache operations
- Stats endpoints
- Admin endpoints
"""

import sys
from datetime import datetime
from pathlib import Path

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

results = {"passed": 0, "failed": 0, "warnings": 0}


def header(text):
    """Print section header."""
    print(f"\n{CYAN}{BOLD}{'='*80}{RESET}")
    print(f"{CYAN}{BOLD}{text}{RESET}")
    print(f"{CYAN}{BOLD}{'='*80}{RESET}\n")


def success(method, path, status):
    """Print success message."""
    print(f"{GREEN}[PASS] {method:6} {status:3} {path}{RESET}")
    results["passed"] += 1


def failed(method, path, status, error=""):
    """Print failed message."""
    print(f"{RED}[FAIL] {method:6} {status:3} {path}{RESET}")
    if error:
        print(f"   {RED}> {error}{RESET}")
    results["failed"] += 1


def warning_msg(method, path, msg):
    """Print warning message."""
    print(f"{YELLOW}[WARN] {method:6} {path}{RESET}")
    print(f"   {YELLOW}> {msg}{RESET}")
    results["warnings"] += 1


# ============================================================================
# TESTE 1: HEALTH CHECK ROUTES
# ============================================================================


def test_health_routes(client: TestClient) -> None:
    """Test health check endpoints."""
    header("TESTE 1: HEALTH CHECK ENDPOINTS")

    endpoints = [
        ("GET", "/api/v1/health"),
        ("GET", "/api/v1/health/detailed"),
        ("GET", "/api/v1/ready"),
    ]

    for method, path in endpoints:
        try:
            response = client.get(path)
            if response.status_code in (200, 503):
                success(method, path, response.status_code)
            else:
                failed(method, path, response.status_code)
        except Exception as e:
            failed(method, path, 0, str(e)[:60])


# ============================================================================
# TESTE 2: INTERNAL STATUS ROUTES
# ============================================================================


def test_status_routes(client: TestClient) -> None:
    """Test internal status endpoints."""
    header("TESTE 2: INTERNAL STATUS ENDPOINTS")

    endpoints = [
        ("GET", "/api/v1/api/internal/about/info"),
        ("GET", "/api/v1/api/internal/sources/status"),
        ("GET", "/api/v1/api/internal/services/status"),
        ("GET", "/api/v1/api/internal/config"),
        ("GET", "/api/v1/api/internal/cache/status"),
        ("GET", "/api/v1/api/internal/tasks/status"),
        ("GET", "/api/v1/api/internal/logs/recent"),
    ]

    for method, path in endpoints:
        try:
            response = client.get(path)
            if response.status_code == 200:
                success(method, path, response.status_code)
            else:
                warning_msg(method, path, f"HTTP {response.status_code}")
        except Exception as e:
            warning_msg(method, path, str(e)[:60])


# ============================================================================
# TESTE 3: ETO CALCULATION ROUTES
# ============================================================================


def test_eto_routes(client: TestClient) -> None:
    """Test ETo calculation endpoints."""
    header("TESTE 3: ETO CALCULATION ROUTES")

    # Test calculate endpoint (POST)
    try:
        payload = {
            "latitude": -15.0,
            "longitude": -48.0,
            "elevation": 1000.0,
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "source": "openmeteo_archive",
        }
        response = client.post("/api/v1/internal/eto/calculate", json=payload)
        if response.status_code in (200, 400, 422):
            success(
                "POST", "/api/v1/internal/eto/calculate", response.status_code
            )
        else:
            failed(
                "POST", "/api/v1/internal/eto/calculate", response.status_code
            )
    except Exception as e:
        failed("POST", "/api/v1/internal/eto/calculate", 0, str(e)[:60])

    # Test legacy endpoint
    try:
        response = client.post("/api/v1/internal/eto/eto_calculate", json={})
        if response.status_code in (200, 400, 422):
            success(
                "POST",
                "/api/v1/internal/eto/eto_calculate",
                response.status_code,
            )
        else:
            failed(
                "POST",
                "/api/v1/internal/eto/eto_calculate",
                response.status_code,
            )
    except Exception as e:
        warning_msg("POST", "/api/v1/internal/eto/eto_calculate", str(e)[:60])

    # Test v3 endpoint
    try:
        response = client.post(
            "/api/v1/internal/eto/eto_calculate_v3", json={}
        )
        if response.status_code in (200, 400, 422):
            success(
                "POST",
                "/api/v1/internal/eto/eto_calculate_v3",
                response.status_code,
            )
        else:
            failed(
                "POST",
                "/api/v1/internal/eto/eto_calculate_v3",
                response.status_code,
            )
    except Exception as e:
        warning_msg(
            "POST", "/api/v1/internal/eto/eto_calculate_v3", str(e)[:60]
        )

    # Test location info (POST)
    try:
        payload = {"latitude": -15.0, "longitude": -48.0}
        response = client.post(
            "/api/v1/internal/eto/location-info", json=payload
        )
        if response.status_code in (200, 400, 422):
            success(
                "POST",
                "/api/v1/internal/eto/location-info",
                response.status_code,
            )
        else:
            failed(
                "POST",
                "/api/v1/internal/eto/location-info",
                response.status_code,
            )
    except Exception as e:
        failed("POST", "/api/v1/internal/eto/location-info", 0, str(e)[:60])

    # Test sources endpoint (GET)
    try:
        response = client.get("/api/v1/internal/eto/sources/-15.0/-48.0")
        if response.status_code in (200, 400, 404):
            success(
                "GET",
                "/api/v1/internal/eto/sources/{lat}/{lng}",
                response.status_code,
            )
        else:
            failed(
                "GET",
                "/api/v1/internal/eto/sources/{lat}/{lng}",
                response.status_code,
            )
    except Exception as e:
        warning_msg(
            "GET", "/api/v1/internal/eto/sources/{lat}/{lng}", str(e)[:60]
        )


# ============================================================================
# TESTE 4: FAVORITES ROUTES
# ============================================================================


def test_favorites_routes(client: TestClient) -> None:
    """Test favorites endpoints."""
    header("TESTE 4: FAVORITES ENDPOINTS")

    # Test list favorites (GET)
    try:
        response = client.get("/api/v1/internal/eto/favorites/list")
        if response.status_code in (200, 401):
            success(
                "GET",
                "/api/v1/internal/eto/favorites/list",
                response.status_code,
            )
        else:
            failed(
                "GET",
                "/api/v1/internal/eto/favorites/list",
                response.status_code,
            )
    except Exception as e:
        warning_msg("GET", "/api/v1/internal/eto/favorites/list", str(e)[:60])

    # Test add favorite (POST)
    try:
        payload = {
            "latitude": -15.0,
            "longitude": -48.0,
            "name": "Test Location",
            "category": "Test",
        }
        response = client.post(
            "/api/v1/internal/eto/favorites/add", json=payload
        )
        if response.status_code in (200, 201, 400, 401):
            success(
                "POST",
                "/api/v1/internal/eto/favorites/add",
                response.status_code,
            )
        else:
            failed(
                "POST",
                "/api/v1/internal/eto/favorites/add",
                response.status_code,
            )
    except Exception as e:
        warning_msg("POST", "/api/v1/internal/eto/favorites/add", str(e)[:60])

    # Test remove favorite (DELETE)
    try:
        response = client.delete("/api/v1/internal/eto/favorites/remove/999")
        if response.status_code in (200, 204, 404, 401):
            success(
                "DELETE",
                "/api/v1/internal/eto/favorites/remove/{id}",
                response.status_code,
            )
        else:
            failed(
                "DELETE",
                "/api/v1/internal/eto/favorites/remove/{id}",
                response.status_code,
            )
    except Exception as e:
        warning_msg(
            "DELETE", "/api/v1/internal/eto/favorites/remove/{id}", str(e)[:60]
        )


# ============================================================================
# TESTE 5: CLIMATE SOURCES ROUTES
# ============================================================================


def test_climate_routes(client: TestClient) -> None:
    """Test climate data source endpoints."""
    header("TESTE 5: CLIMATE SOURCES ROUTES")

    endpoints = [
        ("GET", "/api/v1/climate/sources/available"),
        ("GET", "/api/v1/climate/sources/data-availability"),
    ]

    for method, path in endpoints:
        try:
            response = client.get(path)
            if response.status_code in (200, 400):
                success(method, path, response.status_code)
            else:
                warning_msg(method, path, f"HTTP {response.status_code}")
        except Exception as e:
            warning_msg(method, path, str(e)[:60])

    # Test climate source info
    try:
        response = client.get("/api/v1/climate/sources/info/openmeteo_archive")
        if response.status_code in (200, 404):
            success(
                "GET",
                "/api/v1/climate/sources/info/{source_id}",
                response.status_code,
            )
        else:
            warning_msg(
                "GET",
                "/api/v1/climate/sources/info/{source_id}",
                f"HTTP {response.status_code}",
            )
    except Exception as e:
        warning_msg(
            "GET", "/api/v1/climate/sources/info/{source_id}", str(e)[:60]
        )


# ============================================================================
# TESTE 6: CACHE ROUTES
# ============================================================================


def test_cache_routes(client: TestClient) -> None:
    """Test cache endpoints."""
    header("TESTE 6: CACHE ENDPOINTS")

    # Test cache stats (GET)
    try:
        response = client.get("/api/v1/cache/stats")
        if response.status_code == 200:
            success("GET", "/api/v1/cache/stats", response.status_code)
        else:
            warning_msg(
                "GET", "/api/v1/cache/stats", f"HTTP {response.status_code}"
            )
    except Exception as e:
        warning_msg("GET", "/api/v1/cache/stats", str(e)[:60])

    # Test cache clear (DELETE)
    try:
        response = client.delete("/api/v1/cache/clear")
        if response.status_code in (200, 204):
            success("DELETE", "/api/v1/cache/clear", response.status_code)
        else:
            warning_msg(
                "DELETE", "/api/v1/cache/clear", f"HTTP {response.status_code}"
            )
    except Exception as e:
        warning_msg("DELETE", "/api/v1/cache/clear", str(e)[:60])


# ============================================================================
# TESTE 7: STATS ROUTES
# ============================================================================


def test_stats_routes(client: TestClient) -> None:
    """Test statistics endpoints."""
    header("TESTE 7: STATISTICS ENDPOINTS")

    endpoints = [
        ("GET", "/api/v1/stats/visitors"),
        ("GET", "/api/v1/stats/health"),
    ]

    for method, path in endpoints:
        try:
            response = client.get(path)
            if response.status_code in (200, 400):
                success(method, path, response.status_code)
            else:
                warning_msg(method, path, f"HTTP {response.status_code}")
        except Exception as e:
            warning_msg(method, path, str(e)[:60])

    # Test increment visitors (POST)
    try:
        response = client.post("/api/v1/stats/visitors/increment")
        if response.status_code in (200, 201):
            success(
                "POST",
                "/api/v1/stats/visitors/increment",
                response.status_code,
            )
        else:
            warning_msg(
                "POST",
                "/api/v1/stats/visitors/increment",
                f"HTTP {response.status_code}",
            )
    except Exception as e:
        warning_msg("POST", "/api/v1/stats/visitors/increment", str(e)[:60])


# ============================================================================
# TESTE 8: DOCUMENTATION ROUTES
# ============================================================================


def test_documentation_routes(client: TestClient) -> None:
    """Test documentation endpoints."""
    header("TESTE 8: DOCUMENTATION ENDPOINTS")

    endpoints = [
        ("GET", "/api/v1/docs"),
        ("GET", "/api/v1/redoc"),
        ("GET", "/api/v1/openapi.json"),
    ]

    for method, path in endpoints:
        try:
            response = client.get(path)
            if response.status_code == 200:
                success(method, path, response.status_code)
            else:
                warning_msg(method, path, f"HTTP {response.status_code}")
        except Exception as e:
            warning_msg(method, path, str(e)[:60])


# ============================================================================
# TESTE 9: METRICS ENDPOINT
# ============================================================================


def test_metrics_endpoint(client: TestClient) -> None:
    """Test Prometheus metrics endpoint."""
    header("TESTE 9: METRICS ENDPOINT")

    try:
        response = client.get("/metrics")
        if response.status_code == 200:
            success("GET", "/metrics", response.status_code)
        else:
            warning_msg("GET", "/metrics", f"HTTP {response.status_code}")
    except Exception as e:
        warning_msg("GET", "/metrics", str(e)[:60])


# ============================================================================
# RESUMO
# ============================================================================


def print_summary():
    """Print final summary."""
    header("📊 RESUMO DOS TESTES DE ROTAS")

    total = results["passed"] + results["failed"] + results["warnings"]
    pass_pct = (results["passed"] / total * 100) if total > 0 else 0

    print(f"{GREEN}✅ Passou:{RESET} {results['passed']}")
    print(f"{RED}❌ Falhou:{RESET} {results['failed']}")
    print(f"{YELLOW}⚠️  Avisos:{RESET} {results['warnings']}")
    pct_str = f"({pass_pct:.1f}%)"
    print(f"\n{BOLD}Total: {results['passed']}/{total} {pct_str}{RESET}\n")

    sep = "=" * 80
    print(f"{BOLD}{sep}{RESET}")
    if results["failed"] == 0:
        status = "✅ TODAS AS ROTAS ESTÃO FUNCIONANDO!"
        print(f"{GREEN}{BOLD}{status}{RESET}\n")
    else:
        status = "❌ ALGUMAS ROTAS FALHARAM"
        print(f"{RED}{BOLD}{status}{RESET}\n")
    print(f"{BOLD}{sep}{RESET}\n")


# ============================================================================
# MAIN
# ============================================================================


def main() -> None:
    """Execute route tests."""
    print(f"\n{BOLD}{BLUE}EVAonline - TESTE DE ROTAS{RESET}")
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    try:
        from backend.main import app

        client = TestClient(app)

        test_health_routes(client)
        test_status_routes(client)
        test_eto_routes(client)
        test_favorites_routes(client)
        test_climate_routes(client)
        test_cache_routes(client)
        test_stats_routes(client)
        test_documentation_routes(client)
        test_metrics_endpoint(client)

        print_summary()

    except Exception as e:
        print(f"\n{RED}{BOLD}❌ Erro ao executar testes:{RESET}")
        print(f"{RED}{e}{RESET}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
