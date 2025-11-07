# 🧪 Scripts de Teste - EVAonline

Scripts de **teste não-pytest** para validações manuais e testes de qualidade específicos.

> **Nota:** Estes não são testes unitários automatizados (pytest), mas sim scripts utilitários de validação manual.

## 📁 Arquivos nesta pasta

### `test_api_limits.py`
**Testa aplicação de limites físicos das APIs**

**Uso:**
```bash
python scripts/testing/test_api_limits.py
```

**Funcionalidades:**
- ✅ Testa validação independente por API
- ✅ Usa dados extremos para validar limites
- ✅ Verifica se valores inválidos são convertidos para NaN
- ✅ Gera relatório detalhado de testes
- ✅ Calcula taxa de sucesso

**APIs testadas:**
- 🌐 NASA POWER (7 variáveis)
- 🌤️ Open-Meteo (13 variáveis)
- 🇳🇴 MET Norway (9 variáveis)
- 🇺🇸 NWS Stations (4 variáveis)

**Limites testados:**
- **Temperatura:** -30°C a 50°C
- **Umidade:** 0% a 100%
- **Velocidade do vento:** 0 m/s a 100 m/s
- **Precipitação:** 0 mm a 450 mm
- **Radiação:** 0 W/m² a 40 W/m²
- **Duração:** 0h a 24h
- **ETo:** 0 mm a 15 mm
- **Pressão:** 900 hPa a 1100 hPa

---

## 🔧 Como funciona

O script cria DataFrames de teste com **valores extremos** para cada variável:

```python
test_data = {
    "NASA POWER": {
        "T2M_MAX": [-50, 25, 60],  # Fora: -50, 60 (limite: -30, 50)
        "T2M_MIN": [-50, 15, 60],  # Fora: -50, 60
        # ... mais variáveis
    }
}
```

1. **Cria** dados de teste com valores dentro e fora dos limites
2. **Executa** `data_initial_validate()` do preprocessing
3. **Verifica** se valores inválidos foram convertidos para NaN
4. **Calcula** taxa de sucesso dos testes
5. **Gera** relatório detalhado

---

## 📊 Exemplo de saída

```
🧪 TESTE DE VALIDAÇÃO POR API
============================================================

🌐 Testando NASA POWER
----------------------------------------
  ✅ T2M_MAX: validação correta
  ✅ T2M_MIN: validação correta
  ✅ T2M: validação correta
  ✅ RH2M: validação correta
  ✅ WS2M: validação correta
  ✅ ALLSKY_SFC_SW_DWN: validação correta
  ✅ PRECTOTCORR: validação correta

============================================================
📊 RESULTADO DOS TESTES
  ✅ Testes passados: 35/35
  📊 Taxa de sucesso: 100.0%

🎉 SUCESSO: Todas as validações estão funcionando!
   Cada API tem seus limites físicos aplicados
   independentemente.
```

---

## 📋 Quando usar

- ✅ **Após mudanças** em limites físicos
- ✅ **Para debugging** de validações que falham
- ✅ **Validação manual** antes de deploy
- ✅ **Teste de regressão** de qualidade de dados
- ✅ **Verificação** de que preprocessing está funcionando

---

## 🚨 Cenários de falha

**Se um teste falhar:**
```
❌ T2M_MAX: validação INCORRETA
   Esperado NaN em: [0]
   NaN encontrado em: []
```

Isso indica que:
- ❌ Valores fora dos limites **não foram** convertidos para NaN
- ❌ Função `data_initial_validate()` pode estar com bug
- ❌ Limites podem estar incorretos

---

## 📁 Dependências

- ✅ Função `data_initial_validate` em `backend.core.data_processing.data_preprocessing`
- ✅ Biblioteca `pandas` para manipulação de dados
- ✅ Backend do EVAonline no PYTHONPATH

---

## 🔄 Diferença dos testes pytest

| Característica | `scripts/testing/` | `tests/` (pytest) |
|---|---|---|
| **Framework** | Scripts manuais | pytest automatizado |
| **Execução** | Manual sob demanda | CI/CD automático |
| **Saída** | Print formatado | XML/JSON reports |
| **Propósito** | Validação específica | Testes unitários |
| **Cobertura** | Funcionalidades críticas | Todo o código |

---

**Última atualização**: 29/10/2025</content>
<parameter name="filePath">c:\Users\User\OneDrive\Documentos\GitHub\EVAonline_SoftwareX\scripts\testing\README.md
