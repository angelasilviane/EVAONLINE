#!/usr/bin/env python3
"""
Script para testar se os limites físicos estão sendo aplicados corretamente
para cada variável de cada API, de forma independente.
"""

import sys
from pathlib import Path

import pandas as pd

# Adicionar backend ao path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))


def test_api_validation():
    """Testa validação independente por API."""

    print("🧪 TESTE DE VALIDAÇÃO POR API")
    print("=" * 60)

    # Importar função de validação
    from backend.core.data_processing.data_preprocessing import data_initial_validate

    # Dados de teste para cada API (com valores extremos)
    test_data = {
        "NASA POWER": {
            "T2M_MAX": [-50, 25, 60],  # Fora: -50, 60
            "T2M_MIN": [-50, 15, 60],  # Fora: -50, 60
            "T2M": [-50, 20, 60],  # Fora: -50, 60
            "RH2M": [-10, 50, 110],  # Fora: -10, 110
            "WS2M": [-5, 2, 120],  # Fora: -5, 120
            "ALLSKY_SFC_SW_DWN": [-5, 20, 50],  # Fora: -5, 50
            "PRECTOTCORR": [-10, 5, 500],  # Fora: -10, 500
        },
        "Open-Meteo": {
            "temperature_2m_max": [-50, 25, 60],  # Fora: -50, 60
            "temperature_2m_min": [-50, 15, 60],  # Fora: -50, 60
            "temperature_2m_mean": [-50, 20, 60],  # Fora: -50, 60
            "relative_humidity_2m_max": [-10, 50, 110],  # Fora: -10, 110
            "relative_humidity_2m_mean": [-10, 50, 110],  # Fora: -10, 110
            "relative_humidity_2m_min": [-10, 50, 110],  # Fora: -10, 110
            "wind_speed_10m_max": [-5, 2, 120],  # Fora: -5, 120
            "wind_speed_10m_mean": [-5, 2, 120],  # Fora: -5, 120
            "shortwave_radiation_sum": [-5, 20, 50],  # Fora: -5, 50
            "daylight_duration": [-5, 12, 30],  # Fora: -5, 30
            "sunshine_duration": [-5, 8, 30],  # Fora: -5, 30
            "precipitation_sum": [-10, 5, 500],  # Fora: -10, 500
            "et0_fao_evapotranspiration": [-5, 5, 20],  # Fora: -5, 20
        },
        "MET Norway": {
            "temperature_2m_max": [-50, 25, 60],  # Fora: -50, 60
            "temperature_2m_min": [-50, 15, 60],  # Fora: -50, 60
            "temperature_2m_mean": [-50, 20, 60],  # Fora: -50, 60
            "relative_humidity_2m_mean": [-10, 50, 110],  # Fora: -10, 110
            "wind_speed_10m_max": [-5, 2, 120],  # Fora: -5, 120
            "wind_speed_10m_mean": [-5, 2, 120],  # Fora: -5, 120
            "shortwave_radiation_sum": [-5, 20, 50],  # Fora: -5, 50
            "precipitation_sum": [-10, 5, 500],  # Fora: -10, 500
            "pressure_mean_sea_level": [800, 1000, 1200],  # Fora: 800, 1200
        },
        "NWS Stations": {
            "temp_celsius": [-50, 20, 60],  # Fora: -50, 60
            "humidity_percent": [-10, 50, 110],  # Fora: -10, 110
            "wind_speed_ms": [-5, 2, 120],  # Fora: -5, 120
            "precipitation_mm": [-10, 5, 500],  # Fora: -10, 500
        },
    }

    total_tests = 0
    passed_tests = 0

    for api_name, variables in test_data.items():
        print(f"\n🌐 Testando {api_name}")
        print("-" * 40)

        # Criar DataFrame de teste
        df = pd.DataFrame(variables)
        df.index = pd.date_range("2023-01-01", periods=3)

        # Executar validação
        validated_df, warnings = data_initial_validate(df, latitude=-15.0)

        # Verificar cada variável
        for var_name, original_values in variables.items():
            total_tests += 1

            if var_name in validated_df.columns:
                validated_values = validated_df[var_name].values

                # Verificar se valores inválidos foram convertidos para NaN
                expected_nans = []
                if var_name.startswith(("temperature", "temp_celsius", "T2M")):
                    # Temperaturas: fora [-30, 50] → NaN
                    expected_nans = [i for i, v in enumerate(original_values) if v < -30 or v > 50]
                elif var_name.startswith(
                    ("relative_humidity", "humidity", "RH2M")
                ) or var_name.startswith(("wind_speed", "WS2M", "wind_speed")):
                    # Umidade/Vento: fora [0, 100] → NaN
                    expected_nans = [i for i, v in enumerate(original_values) if v < 0 or v > 100]
                elif var_name.startswith(("precipitation", "PRECTOTCORR", "precipitation")):
                    # Precipitação: fora [0, 450] → NaN
                    expected_nans = [i for i, v in enumerate(original_values) if v < 0 or v > 450]
                elif var_name.startswith(("shortwave_radiation", "ALLSKY_SFC_SW_DWN")):
                    # Radiação: fora [0, 40] → NaN
                    expected_nans = [i for i, v in enumerate(original_values) if v < 0 or v > 40]
                elif var_name in ["daylight_duration", "sunshine_duration"]:
                    # Durações: fora [0, 24] → NaN
                    expected_nans = [i for i, v in enumerate(original_values) if v < 0 or v > 24]
                elif var_name == "et0_fao_evapotranspiration":
                    # ETo: fora [0, 15] → NaN
                    expected_nans = [i for i, v in enumerate(original_values) if v < 0 or v > 15]
                elif var_name == "pressure_mean_sea_level":
                    # Pressão: fora [900, 1100] → NaN
                    expected_nans = [
                        i for i, v in enumerate(original_values) if v < 900 or v > 1100
                    ]

                # Verificar se NaNs estão nas posições esperadas
                actual_nans = [i for i, v in enumerate(validated_values) if pd.isna(v)]

                if set(expected_nans) == set(actual_nans):
                    print(f"  ✅ {var_name}: validação correta")
                    passed_tests += 1
                else:
                    print(f"  ❌ {var_name}: validação INCORRETA")
                    print(f"     Esperado NaN em: {expected_nans}")
                    print(f"     NaN encontrado em: {actual_nans}")
            else:
                print(f"  ⚠️  {var_name}: variável não encontrada")

    # Resumo final
    print(f"\n{'='*60}")
    print("📊 RESULTADO DOS TESTES")
    print(f"  ✅ Testes passados: {passed_tests}/{total_tests}")
    success_rate = (passed_tests / total_tests) * 100
    print(f"  📊 Taxa de sucesso: {success_rate:.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 SUCESSO: Todas as validações estão funcionando!")
        print("   Cada API tem seus limites físicos aplicados\n" "   independentemente.")
    else:
        print(f"\n❌ FALHA: {total_tests - passed_tests} testes falharam!")

    return passed_tests == total_tests


if __name__ == "__main__":
    success = test_api_validation()
    sys.exit(0 if success else 1)
