# 💡 Scripts de Exemplo - EVAonline

Scripts de **demonstração e exemplos** de uso das funcionalidades do projeto EVAonline.

## 📁 Arquivos nesta pasta

### `exemplo_nws_stations.py`
**Exemplo completo de uso da API NWS Stations**

**Uso:**
```bash
python scripts/examples/exemplo_nws_stations.py
```

**Funcionalidades demonstradas:**
- ✅ Conexão com cliente NWS
- ✅ Busca de estações meteorológicas próximas a uma coordenada
- ✅ Filtragem por distância máxima
- ✅ Limitação de número de resultados
- ✅ Obtenção de observações históricas de uma estação
- ✅ Tratamento de erros e cleanup adequado

**Exemplo de saída:**
```
🌤️ Exemplo: Dados de estações NWS
📍 Coordenadas: 38.8977, -77.0365

🔍 Buscando estações próximas...
✅ Encontradas 5 estações:
  1. KDCA: Washington Dulles International Airport
     Provedor: NOAA
  2. KIAD: Washington Dulles International Airport
     Provedor: NOAA
  ...

📊 Obtendo observações da estação KDCA...
✅ 10 observações encontradas:
   Timestamp              Temp(°C)  Umid(%)  Vento(m/s)
   --------------------  --------  -------  ----------
   2023-10-29 12:00:00    22.2      45.0      2.1
   2023-10-29 11:00:00    21.7      48.0      2.3
   ...
```

---

## 🎯 Propósito

Estes scripts servem para:

- 📚 **Aprendizado**: Como usar as APIs do projeto
- 🔧 **Teste**: Validar que as integrações funcionam
- 📖 **Documentação**: Exemplos práticos de uso
- 🐛 **Debugging**: Testar funcionalidades específicas
- 🚀 **Onboarding**: Novos desenvolvedores entenderem o código

---

## 📋 Como usar os exemplos

1. **Configure o ambiente:**
   ```bash
   # Ative o virtual environment
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

2. **Execute o exemplo:**
   ```bash
   python scripts/examples/exemplo_nws_stations.py
   ```

3. **Analise a saída** e o código fonte para entender como funciona

4. **Adapte** para suas necessidades específicas

---

## 🔧 Estrutura típica dos exemplos

```python
#!/usr/bin/env python3
"""
Descrição do exemplo
Uso: python scripts/examples/exemplo_nome.py
"""

import asyncio
import sys
from pathlib import Path

# Adiciona backend ao path
backend_path = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

async def exemplo_principal():
    """Função principal do exemplo."""
    print("🌟 Exemplo: Descrição do que faz")

    try:
        # Código do exemplo aqui
        print("✅ Exemplo executado com sucesso!")

    except Exception as e:
        print(f"❌ Erro: {e}")

    finally:
        # Cleanup se necessário
        pass

if __name__ == "__main__":
    asyncio.run(exemplo_principal())
```

---

## 📚 Criando novos exemplos

### Template recomendado:

1. **Nome descritivo:** `exemplo_[funcionalidade].py`
2. **Docstring completa:** Explique o que o exemplo demonstra
3. **Comentários:** Cada seção importante comentada
4. **Tratamento de erros:** Try/except com mensagens claras
5. **Cleanup:** Sempre fechar conexões/recursos
6. **Output formatado:** Use emojis e formatação clara

### Exemplo de novo arquivo:

```python
Uso: python scripts/examples/exemplo_openmeteo.py
"""

import asyncio
from backend.api.services.openmeteo_archive_client import (
    OpenMeteoArchiveClient,
)

async def exemplo_openmeteo():
    """Demonstra busca de dados históricos."""
    client = OpenMeteoArchiveClient()

    try:
        # Coordenadas de São Paulo
        lat, lon = -23.5505, -46.6333

        print("🌤️ Exemplo: Dados históricos Open-Meteo Archive")
        print(f"📍 Local: São Paulo ({lat}, {lon})")

        # Buscar dados históricos
        data = await client.get_climate_data(
            lat=lat, 
            lng=lon, 
            start_date="2023-01-01", 
            end_date="2023-01-31"
        )

        print(f"✅ Dados obtidos: {len(data['climate_data']['dates'])} registros")
        print("📊 Primeiras 3 linhas:")
        for i in range(min(3, len(data['climate_data']['dates']))):
            date = data['climate_data']['dates'][i]
            temp = data['climate_data'].get('temperature_2m_max', [])[i]
            print(f"  {date}: Temp={temp}°C")

    except Exception as e:
        print(f"❌ Erro: {e}")

    # Archive client doesn't require close() (uses requests_cache)

```
```

---

## 🚀 Contribuindo

Para contribuir com novos exemplos:

1. **Siga o padrão** de nomenclatura e estrutura
2. **Teste o exemplo** antes de commitar
3. **Adicione ao README** da pasta se criar novo arquivo
4. **Documente** casos de uso e pré-requisitos
5. **Use dados de teste** que não dependam de APIs externas quando possível

---

## 📞 Suporte

- **Documentação da API**: Ver `backend/api/services/`
- **Issues**: Abra issue para exemplos que não funcionam
- **Logs**: Ver `logs/` para detalhes de execução

---

**Última atualização**: 29/10/2025</content>
<parameter name="filePath">c:\Users\User\OneDrive\Documentos\GitHub\EVAonline_SoftwareX\scripts\examples\README.md
