# 🔍 Scripts de Validação - EVAonline

Scripts para **verificação de qualidade e integridade** dos dados e configurações do projeto EVAonline.

## 📁 Arquivos nesta pasta

### `check_api_coverage.py`
**Verifica cobertura de limites físicos por API específica**

**Uso:**
```bash
python scripts/validation/check_api_coverage.py
```

**Funcionalidades:**
- ✅ Análise de variáveis retornadas por cada API
- ✅ Verificação de limites físicos definidos em `data_preprocessing.py`
- ✅ Cobertura por API individual (NASA POWER, Open-Meteo, MET Norway, NWS)
- ✅ Identificação de variáveis sem limites definidos
- ✅ Relatório detalhado de cobertura

**Verifica APIs:**
- 🌐 NASA POWER (7 variáveis)
- 🌤️ Open-Meteo (13 variáveis)
- 🇳🇴 MET Norway Locationforecast (9 variáveis)
- 🏔️ MET Norway FROST (2 variáveis)
- 🇺🇸 NWS Stations (4 variáveis)

---

### `check_complete_coverage.py`
**Verificação completa de cobertura de limites**

**Uso:**
```bash
python scripts/validation/check_complete_coverage.py
```

**Funcionalidades:**
- ✅ Análise de TODAS as variáveis climáticas possíveis
- ✅ Comparação com limites definidos em `data_preprocessing.py`
- ✅ Cobertura total do sistema
- ✅ Identificação de limites não utilizados
- ✅ Relatório de cobertura percentual

**Métricas:**
- 📊 Total de variáveis teóricas possíveis
- 🛡️ Variáveis com limites definidos
- ✅ Taxa de cobertura (%)
- ❌ Variáveis faltando limites
- ⚠️ Limites para variáveis não utilizadas

---

## 🔧 Como funcionam

Estes scripts analisam o arquivo `backend/core/data_processing/data_preprocessing.py` e:

1. **Extraem** todas as variáveis retornadas por cada API
2. **Compararem** com os limites físicos definidos
3. **Calculam** cobertura por API e total
4. **Identificam** lacunas e inconsistências
5. **Geram** relatórios detalhados

---

## 📋 Quando usar

- ✅ **Após mudanças** em `data_preprocessing.py`
- ✅ **Antes de deploy** para produção
- ✅ **Durante desenvolvimento** de novas APIs
- ✅ **Para auditoria** de qualidade de dados
- ✅ **Troubleshooting** de validações que falham

---

## 📊 Exemplo de saída

```
🔍 VERIFICAÇÃO POR API: TODAS AS VARIÁVEIS RETORNADAS
================================================================================

📊 NASA POWER: 7 variáveis retornadas
  ✅ T2M_MAX
  ✅ T2M_MIN
  ✅ T2M
  ✅ RH2M
  ✅ WS2M
  ✅ ALLSKY_SFC_SW_DWN
  ✅ PRECTOTCORR

🔍 NASA POWER:
  📊 Retornadas: 7 | Cobertas: 7 | Faltando: 0
  ✅ TODAS as variáveis têm limites!

================================================================================
📋 RESUMO FINAL:
  ✅ Variáveis retornadas pelas APIs: 35
  🛡️ Variáveis com limites definidos: 35
  ❌ Variáveis faltando limites: 0
  ⚠️ Limites para variáveis não retornadas: 0

🎉 SUCESSO: TODAS as variáveis retornadas pelas APIs têm limites!
```

---

## 🚨 Alertas importantes

- **❌ Se houver variáveis sem limites:** Dados inválidos podem passar despercebidos
- **⚠️ Se houver limites não utilizados:** Código pode estar obsoleto
- **🔍 Sempre executar após mudanças:** Garante consistência do sistema

---

## 📁 Dependências

- ✅ Arquivo `backend/core/data_processing/data_preprocessing.py` deve existir
- ✅ Função `data_initial_validate` deve estar disponível
- ✅ Backend do EVAonline no PYTHONPATH

---

**Última atualização**: 29/10/2025</content>
<parameter name="filePath">c:\Users\User\OneDrive\Documentos\GitHub\EVAonline_SoftwareX\scripts\validation\README.md
