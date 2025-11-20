"""
Consolidar Arquivos Anuais em Cache
Consolida arquivos anuais (YYYY.csv) em um único arquivo período completo.
"""

from pathlib import Path
import pandas as pd
from loguru import logger


BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / "results/brasil/cache"


def consolidate_annual_files(city_name: str):
    """
    Consolida todos os arquivos anuais de uma cidade em um único arquivo.

    Busca arquivos: {city_name}_YYYY.csv
    Cria arquivo: {city_name}_{start_year}_{end_year}.csv
    """
    logger.info(f"🔄 Consolidando {city_name}...")

    # Buscar arquivos anuais
    pattern = f"{city_name}_*.csv"
    all_files = list(CACHE_DIR.glob(pattern))

    # Filtrar apenas arquivos anuais (terminam com _YYYY.csv, 4 dígitos)
    annual_files = []
    for file in all_files:
        parts = file.stem.split("_")
        last_part = parts[-1]
        if last_part.isdigit() and len(last_part) == 4:
            annual_files.append(file)

    if not annual_files:
        logger.warning(f"  ⚠️  Nenhum arquivo anual encontrado")
        return None

    annual_files.sort()
    logger.info(f"  📁 Encontrados {len(annual_files)} arquivos anuais")

    all_data = []
    years = []

    for file in annual_files:
        try:
            # Extrair ano
            year = file.stem.split("_")[-1]

            df = pd.read_csv(file)

            if "date" not in df.columns:
                logger.warning(f"  ⚠️  {file.name} sem coluna 'date'")
                continue

            df["date"] = pd.to_datetime(df["date"])
            all_data.append(df)
            years.append(int(year))

            logger.info(f"  ✅ {year}: {len(df)} dias")

        except Exception as e:
            logger.error(f"  ❌ Erro em {file.name}: {e}")
            continue

    if not all_data:
        logger.error(f"  ❌ Nenhum dado válido")
        return None

    # Concatenar
    df_complete = pd.concat(all_data, ignore_index=True)
    df_complete = df_complete.sort_values("date").drop_duplicates(
        subset=["date"]
    )

    # Nome do arquivo consolidado
    start_year = min(years)
    end_year = max(years)
    output_file = CACHE_DIR / f"{city_name}_{start_year}_{end_year}.csv"

    df_complete.to_csv(output_file, index=False)

    logger.info(f"  💾 {output_file.name}")
    logger.info(f"     {len(df_complete)} dias ({start_year}-{end_year})")

    return df_complete


def main():
    """Consolida Alvorada do Gurguéia."""
    logger.info("🚀 Consolidando arquivos anuais\n")

    city = "Alvorada_do_Gurgueia_PI"
    result = consolidate_annual_files(city)

    if result is not None:
        logger.info(f"\n✅ Consolidação completa!")
    else:
        logger.error(f"\n❌ Falha na consolidação")


if __name__ == "__main__":
    main()
