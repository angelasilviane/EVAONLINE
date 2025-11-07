#!/usr/bin/env python3
"""
Teste de Integração EVAonline
- Conexão com banco de dados
- Funcionalidade dos módulos StationFinder e KalmanEnsemble
"""

import sys
from pathlib import Path

# Adicionar backend ao path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))


def test_integration():
    print("🔍 Testando integração EVAonline...")
    print("=" * 50)

    # 1. Testar importação dos módulos
    print("\n1️⃣ Testando importações...")
    try:
        from backend.core.data_processing.kalman_ensemble import KalmanEnsembleStrategy
        from backend.core.data_processing.station_finder import StationFinder
        from backend.database.connection import get_db_context

        print("✅ Todos os módulos importados com sucesso")
    except Exception as e:
        print(f"❌ Erro na importação: {e}")
        return False

    # 2. Testar conexão com banco
    print("\n2️⃣ Testando conexão com PostgreSQL...")
    try:
        from sqlalchemy import text

        with get_db_context() as db:
            # Query simples para testar conexão
            result = db.execute(text("SELECT 1 as test")).first()
            if result and result[0] == 1:
                print("✅ Conexão com PostgreSQL estabelecida")

                # Testar se tabelas existem
                tables_result = db.execute(
                    text(
                        """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'climate_history'
                    LIMIT 5
                """
                    )
                ).fetchall()

                if tables_result:
                    table_names = [row[0] for row in tables_result]
                    print(
                        f"✅ Schema 'climate_history' encontrado com " f"{len(table_names)} tabelas"
                    )
                    print(
                        f"   📋 Tabelas encontradas: "
                        f"{', '.join(table_names[:3])}"
                        f"{'...' if len(table_names) > 3 else ''}"
                    )
                else:
                    print("⚠️  Schema 'climate_history' vazio ou não encontrado")

            else:
                print("❌ Conexão falhou - resultado inesperado")
                return False
    except Exception as e:
        print(f"❌ Erro na conexão com banco: {e}")
        print("💡 Verifique se:")
        print("   - PostgreSQL está rodando")
        print("   - Variáveis de ambiente estão configuradas (.env)")
        print("   - Banco de dados 'evaonline' existe")
        print("   - Schema 'climate_history' foi criado")
        return False

    # 3. Testar StationFinder
    print("\n3️⃣ Testando StationFinder...")
    try:
        finder = StationFinder(db_session=None)  # Sem sessão para teste básico
        print("✅ StationFinder instanciado")

        # Testar método sem DB (deve retornar lista vazia)
        import asyncio

        result = asyncio.run(finder.find_studied_city(-15.8, -47.9, 50))
        if result is None:
            print("✅ StationFinder.find_studied_city funciona (sem DB)")
        else:
            print("❌ StationFinder retornou dados inesperados sem DB")

    except Exception as e:
        print(f"❌ Erro no StationFinder: {e}")
        return False

    # 4. Testar KalmanEnsembleStrategy
    print("\n4️⃣ Testando KalmanEnsembleStrategy...")
    try:
        kalman = KalmanEnsembleStrategy(db_session=None, redis_client=None)
        print("✅ KalmanEnsembleStrategy instanciado")

        # Testar método sem DB (modo simples)
        result = kalman.auto_fuse_sync(
            latitude=-15.8,
            longitude=-47.9,
            current_measurements={"temperature": 25.0, "humidity": 65.0},
        )
        if "temperature" in result and "humidity" in result:
            print("✅ KalmanEnsembleStrategy.auto_fuse_sync funciona (modo simples)")
            print(f"   📊 Temperatura fusionada: {result['temperature']:.1f}°C")
            print(f"   📊 Umidade fusionada: {result['humidity']:.1f}%")
            print(f"   🎯 Estratégia usada: {result.get('fusion_strategy', 'unknown')}")
        else:
            print("❌ KalmanEnsembleStrategy não retornou dados esperados")
            return False

    except Exception as e:
        print(f"❌ Erro no KalmanEnsembleStrategy: {e}")
        return False

    # 5. Testar integração completa (simulação do fluxo da aplicação)
    print("\n5️⃣ Testando fluxo completo da aplicação...")
    try:
        # Simular clique no mapa em Brasília
        lat, lon = -15.7942, -47.8822  # Brasília
        print(f"🗺️  Simulando clique no mapa: ({lat}, {lon})")

        # 1. StationFinder busca estações próximas
        with get_db_context() as db:
            finder_with_db = StationFinder(db_session=db)

            # Buscar cidade estudada próxima
            city_data = finder_with_db.find_studied_city_sync(lat, lon, 20)
            if city_data:
                print("✅ Cidade estudada encontrada:")
                print(f"   🏙️  {city_data['city_name']} - {city_data['distance_km']:.1f}km")
                print(f"   📅 Dados históricos: {len(city_data.get('monthly_data', {}))} meses")
            else:
                print("ℹ️  Nenhuma cidade estudada próxima encontrada")

            # Buscar estações meteorológicas
            stations = finder_with_db.find_stations_in_radius_sync(lat, lon, 100, 3)
            print(f"✅ {len(stations)} estações encontradas dentro de 100km")

            # 2. KalmanEnsembleStrategy faz fusão inteligente
            kalman_with_db = KalmanEnsembleStrategy(db_session=db, redis_client=None)

            # Simular dados das APIs
            api_data = {
                "temperature_max": 28.5,
                "temperature_min": 18.2,
                "precipitation": 5.2,
                "humidity": 65.0,
                "wind_speed": 12.5,
            }

            result = kalman_with_db.auto_fuse_sync(lat, lon, api_data)

            print("✅ Fusão Kalman concluída:")
            print(f"   🌡️  Temperatura: {result.get('temperature_max', 'N/A')}")
            print(f"   💧 Precipitação: {result.get('precipitation', 'N/A')}")
            print(f"   🎯 Estratégia: {result.get('fusion_strategy', 'unknown')}")

    except Exception as e:
        print(f"❌ Erro no fluxo completo: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 INTEGRAÇÃO EVAONLINE FUNCIONANDO PERFEITAMENTE!")
    print("✅ Banco de dados conectado")
    print("✅ Módulos funcionando")
    print("✅ Fluxo da aplicação validado")
    return True


if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
