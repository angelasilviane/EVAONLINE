"""
Script de teste para validação de email e processamento de downloads históricos.

Este script permite testar:
1. Validação de emails
2. Processamento local (sem Celery)
3. Processamento via Celery worker
4. Geração de arquivos CSV/Excel
5. Workflow completo de emails

USAGE:
    # Teste de validação de email
    python test_historical_download.py --test-email user@example.com

    # Teste processamento local (síncrono)
    python test_historical_download.py --test-local

    # Teste via Celery worker (assíncrono)
    python test_historical_download.py --test-celery

    # Teste workflow completo
    python test_historical_download.py --test-all
"""

import argparse
import sys
from pathlib import Path

# Adiciona raiz do projeto ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


def test_email_validation():
    """Testa validação de emails."""
    from backend.core.utils.email_utils import validate_email

    print("\n" + "=" * 60)
    print("TESTE 1: VALIDAÇÃO DE EMAILS")
    print("=" * 60)

    test_cases = [
        ("user@example.com", True),
        ("test.user+tag@domain.co.uk", True),
        ("invalid.email", False),
        ("@domain.com", False),
        ("user@", False),
        ("", False),
        (None, False),
        ("user name@domain.com", False),
        ("user@domain", False),
        ("valid.email@test-domain.com", True),
    ]

    passed = 0
    failed = 0

    for email, expected in test_cases:
        result = validate_email(email) if email else False
        status = "✅ PASS" if result == expected else "❌ FAIL"

        if result == expected:
            passed += 1
        else:
            failed += 1

        print(f"{status} | '{email}' → {result} (esperado: {expected})")

    print(f"\nResultado: {passed} passed, {failed} failed")
    return failed == 0


def test_local_processing():
    """Testa processamento local (sem Celery)."""
    print("\n" + "=" * 60)
    print("TESTE 2: PROCESSAMENTO LOCAL")
    print("=" * 60)

    from backend.core.data_processing.data_download import (
        download_weather_data,
    )
    from backend.core.data_processing.data_preprocessing import (
        preprocessing,
    )
    from backend.core.eto_calculation.eto_calculation import calculate_eto

    # Parâmetros de teste: São Paulo, últimos 10 dias
    from datetime import datetime, timedelta

    end_date = datetime.now()
    start_date = end_date - timedelta(days=10)

    params = {
        "lat": -23.5505,
        "lon": -46.6333,
        "source": "data fusion",
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
    }

    print(f"\nParâmetros:")
    print(f"  Localização: São Paulo ({params['lat']}, {params['lon']})")
    print(f"  Período: {params['start_date']} a {params['end_date']}")
    print(f"  Fonte: {params['source']}")

    try:
        # 1. Download
        print(f"\n[1/3] Baixando dados...")
        weather_df, warnings = download_weather_data(
            data_source=params["source"],
            data_inicial=params["start_date"],
            data_final=params["end_date"],
            longitude=params["lon"],
            latitude=params["lat"],
        )

        if weather_df is None or weather_df.empty:
            print("❌ FAIL: Nenhum dado obtido")
            return False

        print(f"✅ Dados obtidos: {len(weather_df)} registros")
        print(f"   Avisos: {len(warnings)}")

        # 2. Preprocessing
        print(f"\n[2/3] Processando dados...")
        df_processed, prep_warnings = preprocessing(
            weather_df, latitude=params["lat"]
        )
        print(f"✅ Dados processados: {len(df_processed)} registros")
        print(f"   Avisos: {len(prep_warnings)}")

        # 3. Cálculo ETo
        print(f"\n[3/3] Calculando ETo...")
        df_eto, eto_warnings = calculate_eto(
            weather_df=df_processed, elevation=0.0, latitude=params["lat"]
        )
        print(f"✅ ETo calculado: {len(df_eto)} registros")
        print(f"   Avisos: {len(eto_warnings)}")

        # Estatísticas
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   Colunas: {list(df_eto.columns)}")
        print(
            f"   Total de avisos: {len(warnings) + len(prep_warnings) + len(eto_warnings)}"
        )

        # Gerar arquivo de teste
        test_file = f"/tmp/test_EVAonline_{params['start_date']}.csv"
        df_eto.to_csv(test_file, index=True)
        print(f"\n✅ Arquivo gerado: {test_file}")

        return True

    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def test_celery_task():
    """Testa task Celery (requer worker rodando)."""
    print("\n" + "=" * 60)
    print("TESTE 3: TASK CELERY")
    print("=" * 60)

    from datetime import datetime, timedelta

    from backend.infrastructure.celery.tasks.historical_download import (
        process_historical_download,
    )

    # Parâmetros de teste
    end_date = datetime.now()
    start_date = end_date - timedelta(days=10)

    params = {
        "email": "test@example.com",
        "lat": -23.5505,
        "lon": -46.6333,
        "source": "data fusion",
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "file_format": "csv",
    }

    print(f"\nParâmetros:")
    for key, value in params.items():
        print(f"  {key}: {value}")

    try:
        print(f"\n⏳ Enviando task para Celery worker...")
        result = process_historical_download.delay(**params)

        print(f"✅ Task enviada: {result.id}")
        print(f"   Status: {result.status}")
        print(
            f"\n💡 Use 'celery -A backend.infrastructure.celery.celery_config "
            f"inspect active' para monitorar"
        )

        return True

    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
        print("\n⚠️  Certifique-se de que o Celery worker está rodando:")
        print(
            "   celery -A backend.infrastructure.celery.celery_config worker "
            "--loglevel=info"
        )
        return False


def test_email_workflow():
    """Testa workflow completo de emails (simulado)."""
    print("\n" + "=" * 60)
    print("TESTE 4: WORKFLOW DE EMAILS")
    print("=" * 60)

    from backend.core.utils.email_utils import (
        send_email,
        send_email_with_attachment,
    )

    test_email = "test@example.com"

    # Teste 1: Email inicial
    print(f"\n[1/3] Enviando email inicial...")
    result1 = send_email(
        to=test_email,
        subject="EVAonline: Processamento iniciado",
        body="Seus dados estão sendo processados...",
    )
    print(f"{'✅' if result1 else '❌'} Email inicial")

    # Teste 2: Email com anexo (simulado)
    print(f"\n[2/3] Enviando email com anexo...")
    result2 = send_email_with_attachment(
        to=test_email,
        subject="EVAonline: Dados prontos!",
        body="Seus dados estão anexados.",
        attachment_path="/tmp/test_file.csv",
    )
    print(f"{'✅' if result2 else '❌'} Email com anexo")

    # Teste 3: Email de erro
    print(f"\n[3/3] Enviando email de erro...")
    result3 = send_email(
        to=test_email,
        subject="EVAonline: Erro no processamento",
        body="Erro: Teste de simulação",
    )
    print(f"{'✅' if result3 else '❌'} Email de erro")

    all_passed = result1 and result2 and result3
    print(
        f"\n{'✅ TODOS OS EMAILS OK' if all_passed else '❌ ALGUNS EMAILS FALHARAM'}"
    )
    print("\n💡 NOTA: Emails estão em modo simulado (logs apenas)")
    print("   Configure SMTP real para produção")

    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Testa validação de email e download histórico"
    )
    parser.add_argument(
        "--test-email",
        type=str,
        help="Testa validação de um email específico",
    )
    parser.add_argument(
        "--test-local",
        action="store_true",
        help="Testa processamento local (síncrono)",
    )
    parser.add_argument(
        "--test-celery",
        action="store_true",
        help="Testa task Celery (requer worker)",
    )
    parser.add_argument(
        "--test-all", action="store_true", help="Executa todos os testes"
    )

    args = parser.parse_args()

    results = {}

    # Teste individual de email
    if args.test_email:
        from backend.core.utils.email_utils import validate_email

        is_valid = validate_email(args.test_email)
        print(f"\nEmail: {args.test_email}")
        print(f"Válido: {'✅ SIM' if is_valid else '❌ NÃO'}")
        return 0 if is_valid else 1

    # Testes completos
    if args.test_all or not any(
        [args.test_local, args.test_celery, args.test_email]
    ):
        results["email_validation"] = test_email_validation()
        results["local_processing"] = test_local_processing()
        results["email_workflow"] = test_email_workflow()
        results["celery_task"] = test_celery_task()

    else:
        if args.test_local:
            results["local_processing"] = test_local_processing()
        if args.test_celery:
            results["celery_task"] = test_celery_task()

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")

    all_passed = all(results.values())
    print(
        f"\n{'🎉 TODOS OS TESTES PASSARAM!' if all_passed else '⚠️ ALGUNS TESTES FALHARAM'}"
    )

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
