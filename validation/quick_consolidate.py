"""
Consolidar arquivos anuais existentes em cache
"""

import pandas as pd
from pathlib import Path
from loguru import logger

CACHE_DIR = Path("validation/results/brasil/cache")

# Consolidar Alvorada 1991-2020
logger.info("Consolidando Alvorada_do_Gurgueia_PI 1991-2020...")

files = sorted(CACHE_DIR.glob("Alvorada_do_Gurgueia_PI_19*.csv"))
files += sorted(CACHE_DIR.glob("Alvorada_do_Gurgueia_PI_200*.csv"))
files += sorted(CACHE_DIR.glob("Alvorada_do_Gurgueia_PI_201*.csv"))
files += sorted(CACHE_DIR.glob("Alvorada_do_Gurgueia_PI_2020.csv"))

# Filtrar apenas arquivos de ano único
files = [f for f in files if len(f.stem.split("_")) == 5]

logger.info(f"Encontrados {len(files)} arquivos anuais")

dfs = []
for f in files:
    df = pd.read_csv(f)
    logger.info(f"  {f.name}: {len(df)} dias")
    dfs.append(df)

df_complete = pd.concat(dfs, ignore_index=True)
df_complete["date"] = pd.to_datetime(df_complete["date"])
df_complete = df_complete.sort_values("date").drop_duplicates(subset=["date"])

output = CACHE_DIR / "Alvorada_do_Gurgueia_PI_1991_2020.csv"
df_complete.to_csv(output, index=False)

logger.info(f"✅ Consolidado: {output.name} ({len(df_complete)} dias)")
