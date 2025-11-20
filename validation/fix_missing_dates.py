"""
Corrigir Arquivos Sem Coluna Date
Adiciona coluna 'date' aos arquivos anuais que não têm essa coluna.
"""

from pathlib import Path
import pandas as pd
from loguru import logger


BASE_DIR = Path(__file__).parent
CACHE_DIR = BASE_DIR / "results/brasil/cache"


def fix_file_add_date(file_path: Path):
    """
    Adiciona coluna 'date' a um arquivo CSV baseado no ano do nome do arquivo.

    Formato esperado do nome: CityName_YYYY.csv
    Ex: Alvorada_do_Gurgueia_PI_1991.csv
    """
    try:
        # Ler arquivo
        df = pd.read_csv(file_path)

        # Verificar se já tem date
        if "date" in df.columns:
            logger.info(f"✅ {file_path.name} - Já tem coluna 'date'")
            return True

        # Extrair ano do nome do arquivo
        # Formato: CityName_YYYY.csv
        parts = file_path.stem.split("_")
        year = parts[-1]  # Último elemento é o ano

        if not year.isdigit() or len(year) != 4:
            logger.error(
                f"❌ {file_path.name} - Não consegui extrair ano válido: '{year}'"
            )
            return False

        # Criar datas para o ano
        num_days = len(df)
        start_date = f"{year}-01-01"
        dates = pd.date_range(start=start_date, periods=num_days, freq="D")

        # Adicionar coluna date no INÍCIO
        df.insert(0, "date", dates)

        # Salvar de volta
        df.to_csv(file_path, index=False)

        logger.info(
            f"✅ {file_path.name} - Adicionada coluna 'date' ({num_days} dias de {year})"
        )
        return True

    except Exception as e:
        logger.error(f"❌ {file_path.name} - Erro: {e}")
        return False


def main():
    """
    Processa todos os arquivos anuais no cache.
    """
    logger.info("🔧 Corrigindo arquivos sem coluna 'date'")
    logger.info(f"   Diretório: {CACHE_DIR}\n")

    # Buscar arquivos no formato: CityName_YYYY.csv (4 dígitos = ano)
    all_files = list(CACHE_DIR.glob("*.csv"))

    # Filtrar apenas arquivos anuais (terminam com _YYYY.csv)
    annual_files = []
    for file in all_files:
        parts = file.stem.split("_")
        if len(parts) > 0 and parts[-1].isdigit() and len(parts[-1]) == 4:
            annual_files.append(file)

    logger.info(f"📁 Encontrados {len(annual_files)} arquivos anuais\n")

    success = 0
    failed = 0

    for file in sorted(annual_files):
        if fix_file_add_date(file):
            success += 1
        else:
            failed += 1

    logger.info(f"\n{'='*70}")
    logger.info(f"✅ Correção completa!")
    logger.info(f"   Sucesso: {success} arquivos")
    logger.info(f"   Falhas: {failed} arquivos")
    logger.info(f"{'='*70}")


if __name__ == "__main__":
    main()
