# OpenTopoData Integration Guide

## 📍 O Que é OpenTopoData?

**OpenTopoData** fornece dados de **elevação** e **topografia** essenciais para cálculos precisos de **ETo FAO-56**.

### Por Que Usar?

A **elevação** afeta diretamente 3 componentes críticos da ETo:

1. **Pressão Atmosférica** (P)
   - Diminui com altitude
   - Afeta a constante psicrométrica (γ)
   
2. **Radiação Solar**
   - Aumenta ~10% por 1000m
   - Menos absorção atmosférica em altitudes elevadas
   
3. **Temperatura**
   - Lapse rate: -6.5°C/1000m (aproximado)

## 🌍 Cobertura

| Dataset | Cobertura | Resolução | Melhor Para |
|---------|-----------|-----------|-------------|
| **srtm30m** | 60°S - 60°N | 30m | Áreas agrícolas (padrão) |
| **aster30m** | Global | 30m | Regiões polares |
| **mapzen** | Global | Variável | Backup geral |

## 🚀 Uso Básico

### 1. Obter Elevação de um Ponto

```python
from backend.api.services import OpenTopoClient

# Inicializar cliente
client = OpenTopoClient()

# Obter elevação (Brasília)
location = await client.get_elevation(-15.7801, -47.9292)

print(f"Elevação: {location.elevation:.1f}m")
# Output: Elevação: 1172.0m

await client.close()
```

### 2. Obter Elevações em Lote (Batch)

```python
# Até 100 pontos por request
locations = [
    (-15.7801, -47.9292),  # Brasília
    (-23.5505, -46.6333),  # São Paulo
    (-22.9068, -43.1729),  # Rio de Janeiro
]

results = await client.get_elevations_batch(locations)

for loc in results:
    print(f"({loc.lat}, {loc.lon}): {loc.elevation}m")
```

### 3. Cálculos FAO-56 com Elevação

```python
from backend.api.services import ElevationUtils

# Obter elevação
location = await client.get_elevation(-15.7801, -47.9292)
elevation = location.elevation  # 1172m

# Calcular pressão atmosférica (FAO-56 Eq. 7)
pressure = ElevationUtils.calculate_atmospheric_pressure(elevation)
print(f"Pressão: {pressure:.2f} kPa")
# Output: Pressão: 87.78 kPa

# Calcular constante psicrométrica (FAO-56 Eq. 8)
gamma = ElevationUtils.calculate_psychrometric_constant(elevation)
print(f"Gamma: {gamma:.5f} kPa/°C")
# Output: Gamma: 0.05840 kPa/°C

# Ajustar radiação solar
radiation_sea_level = 20.0  # MJ/m²/dia
radiation_adjusted = ElevationUtils.adjust_solar_radiation_for_elevation(
    radiation_sea_level, elevation
)
print(f"Radiação ajustada: {radiation_adjusted:.2f} MJ/m²/dia")
# Output: Radiação ajustada: 22.34 MJ/m²/dia (+11.7%)
```

### 4. Obter Todos os Fatores de Correção

```python
# Retorna pressão, gamma, e fator solar em um único dict
factors = ElevationUtils.get_elevation_correction_factor(1172)

print(factors)
# Output: {
#   'pressure': 87.78,
#   'gamma': 0.05840,
#   'solar_factor': 1.1172,
#   'elevation': 1172
# }
```

## 🔄 Integração com Open-Meteo

O **Open-Meteo** já retorna elevação, mas o **OpenTopoData** oferece:

✅ **Maior precisão** (SRTM 30m vs interpolado)  
✅ **Validação cruzada**  
✅ **Backup** se Open-Meteo falhar  

### Exemplo: Comparar Elevações

```python
# Open-Meteo
from backend.api.services import OpenMeteoForecastClient

meteo_client = OpenMeteoForecastClient()
meteo_data = await meteo_client.get_daily_forecast(-15.7801, -47.9292, ...)
meteo_elevation = meteo_data['location']['elevation']

# OpenTopoData
topo_client = OpenTopoClient()
topo_location = await topo_client.get_elevation(-15.7801, -47.9292)
topo_elevation = topo_location.elevation

# Comparar
diff = abs(meteo_elevation - topo_elevation)
print(f"Open-Meteo: {meteo_elevation}m")
print(f"OpenTopo: {topo_elevation}m")
print(f"Diferença: {diff}m")

# Usar a mais precisa (OpenTopo SRTM 30m)
elevation_to_use = topo_elevation
```

## 📊 Impacto da Elevação no ETo

### Exemplo Prático: Brasília (1172m)

| Variável | Nível do Mar | 1172m | Diferença |
|----------|--------------|-------|-----------|
| Pressão (P) | 101.3 kPa | 87.8 kPa | -13.3% |
| Gamma (γ) | 0.0673 kPa/°C | 0.0584 kPa/°C | -13.2% |
| Radiação Solar | 20.0 MJ/m² | 22.3 MJ/m² | +11.7% |
| **ETo Estimado** | **4.5 mm/dia** | **5.1 mm/dia** | **+13.3%** |

⚠️ **Ignorar elevação pode subestimar ETo em >10% em regiões altas!**

## 🔧 Configuração Avançada

### Mudar Dataset Padrão

```python
from backend.api.services.opentopo import OpenTopoConfig

# Usar ASTER30m (regiões polares)
config = OpenTopoConfig(
    default_dataset="aster30m",
    cache_ttl=3600 * 24 * 30,  # 30 dias
)

client = OpenTopoClient(config=config)
```

### Usar Cache Redis

```python
from backend.infrastructure.cache import ClimateCache

# Inicializar cache
cache = ClimateCache()

# Cliente com cache
client = OpenTopoClient(cache=cache)

# Primeira chamada: API request
location1 = await client.get_elevation(-15.7801, -47.9292)

# Segunda chamada: cache hit (instantâneo)
location2 = await client.get_elevation(-15.7801, -47.9292)
```

## 🎯 Casos de Uso

### 1. Validar Elevação do Open-Meteo

```python
async def validate_elevation(lat: float, lon: float) -> dict:
    """Compara elevação de duas fontes."""
    meteo = OpenMeteoForecastClient()
    topo = OpenTopoClient()
    
    meteo_data = await meteo.get_daily_forecast(lat, lon, ...)
    topo_data = await topo.get_elevation(lat, lon)
    
    return {
        "open_meteo": meteo_data['location']['elevation'],
        "opentopo": topo_data.elevation,
        "source": "opentopo",  # Mais preciso
        "difference": abs(
            meteo_data['location']['elevation'] - topo_data.elevation
        ),
    }
```

### 2. Corrigir ETo para Elevação

```python
async def calculate_eto_with_elevation(
    lat: float, 
    lon: float, 
    date: datetime
) -> dict:
    """Calcula ETo considerando elevação."""
    # Obter dados climáticos
    meteo = OpenMeteoForecastClient()
    climate = await meteo.get_daily_forecast(lat, lon, date, date)
    
    # Obter elevação precisa
    topo = OpenTopoClient()
    location = await topo.get_elevation(lat, lon)
    
    # Calcular fatores de correção
    factors = ElevationUtils.get_elevation_correction_factor(
        location.elevation
    )
    
    # Ajustar radiação solar
    radiation_adjusted = (
        climate[0].solar_radiation * factors['solar_factor']
    )
    
    # TODO: Usar gamma e pressure no cálculo de ETo FAO-56
    
    return {
        "elevation": location.elevation,
        "pressure": factors['pressure'],
        "gamma": factors['gamma'],
        "radiation_original": climate[0].solar_radiation,
        "radiation_adjusted": radiation_adjusted,
    }
```

### 3. Pré-calcular Elevações para Grid

```python
async def precalculate_elevations_grid(
    lat_min: float,
    lat_max: float,
    lon_min: float,
    lon_max: float,
    resolution: float = 0.1,
) -> list[dict]:
    """Pré-calcula elevações para um grid."""
    import numpy as np
    
    lats = np.arange(lat_min, lat_max, resolution)
    lons = np.arange(lon_min, lon_max, resolution)
    
    locations = []
    for lat in lats:
        for lon in lons:
            locations.append((lat, lon))
    
    client = OpenTopoClient()
    results = await client.get_elevations_batch(locations)
    
    return [
        {
            "lat": loc.lat,
            "lon": loc.lon,
            "elevation": loc.elevation,
            "pressure": ElevationUtils.calculate_atmospheric_pressure(
                loc.elevation
            ),
            "gamma": ElevationUtils.calculate_psychrometric_constant(
                loc.elevation
            ),
        }
        for loc in results
    ]
```

## 📚 Referências FAO-56

- **Equação 7** (Pressão): P = 101.3 × [(293 - 0.0065 × z) / 293]^5.26
- **Equação 8** (Gamma): γ = 0.665 × 10^-3 × P

**Fonte**: Allen et al. (1998). Crop evapotranspiration - Guidelines for computing crop water requirements. FAO Irrigation and Drainage Paper 56.

## ⚡ Performance

| Operação | Tempo | Cache |
|----------|-------|-------|
| Single request | ~500ms | ✅ 30 dias |
| Batch (100 pts) | ~800ms | ✅ Individual |
| Cache hit | <1ms | ✅ Redis |

## 🔒 Rate Limits

- **Public API**: 100 requests/minuto
- **Batch**: Até 100 pontos/request
- **Recomendado**: Usar cache + batch para otimizar

## 🐛 Troubleshooting

### Elevação fora da cobertura SRTM (>60°N or <60°S)

```python
# Automaticamente tenta ASTER30m
location = await client.get_elevation(70, 25)  # Noruega
# Retorna com dataset='aster30m'
```

### Rate limit excedido

```python
# Usar batch em vez de múltiplos requests
locations = [(lat, lon) for lat, lon in coordinates]
results = await client.get_elevations_batch(locations)
```

### Elevação None retornada

```python
location = await client.get_elevation(lat, lon)
if location is None:
    # Fallback para Open-Meteo
    meteo_data = await meteo_client.get_daily_forecast(...)
    elevation = meteo_data['location']['elevation']
```

## 🎓 Conclusão

O **OpenTopoData** é essencial para cálculos precisos de ETo em regiões com elevação significativa (>500m). A integração com Open-Meteo fornece **redundância** e **validação cruzada** dos dados de elevação.

**Recomendação**: Sempre use OpenTopoData para obter elevação ao calcular ETo FAO-56, especialmente em:
- Regiões montanhosas
- Planaltos (ex: Cerrado brasileiro)
- Áreas acima de 500m
