#!/usr/bin/env python3
"""
🚀 START DOCKER - Inicia ambiente completo com testes
"""
import subprocess
import sys
import time


def run(cmd, description=""):
    """Execute command with status"""
    if description:
        print(f"\n[*] {description}")
    print(f"    $ {cmd}\n")
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0


def main():
    print("\n" + "=" * 80)
    print("🚀 DOCKER SETUP - EVAonline Backend Complete")
    print("=" * 80)

    # 1. Stop old containers
    print("\n[1] Parando containers antigos...")
    subprocess.run("docker-compose down", shell=True, capture_output=True)

    # 2. Start PostgreSQL and Redis only
    print("\n[2] Iniciando PostgreSQL e Redis...")
    if not run(
        "docker-compose up -d postgres redis", "Subindo postgres e redis"
    ):
        print("ERRO ao iniciar postgres/redis")
        return 1

    # 3. Wait for services
    print("\n[3] Aguardando services ficarem prontos...")
    time.sleep(5)

    # 4. Check health
    print("\n[4] Verificando saude dos services...")

    # PostgreSQL
    pg_check = subprocess.run(
        "docker exec evaonline-postgres pg_isready -U evaonline -q",
        shell=True,
        capture_output=True,
    )
    if pg_check.returncode == 0:
        print("    ✅ PostgreSQL pronto")
    else:
        print("    ❌ PostgreSQL nao pronto")
        return 1

    # Redis
    redis_check = subprocess.run(
        "docker exec evaonline-redis redis-cli -a $(grep REDIS_PASSWORD .env | cut -d= -f2) ping",
        shell=True,
        capture_output=True,
        text=True,
    )
    if "PONG" in redis_check.stdout or redis_check.returncode == 0:
        print("    ✅ Redis pronto")
    else:
        print("    ❌ Redis nao pronto")

    # 5. Start test runner
    print("\n[5] Iniciando test-runner...")
    print("    Executando: docker-compose run --rm test-runner\n")

    result = subprocess.run("docker-compose run --rm test-runner", shell=True)

    print("\n" + "=" * 80)
    if result.returncode == 0:
        print("✅ TESTES PASSARAM - Ambiente pronto!")
        print("=" * 80)

        print("\n[6] Opcoes de continuacao:")
        print("    • Rodar API:           docker-compose up -d api")
        print("    • Rodar API (dev):     docker-compose up -d api-dev")
        print(
            "    • Rodar Celery:        docker-compose up -d celery-worker celery-beat"
        )
        print("    • Ver Logs API:        docker logs -f evaonline-api")
        print("    • Parar tudo:          docker-compose down")
        print()
        return 0
    else:
        print("❌ TESTES FALHARAM")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
