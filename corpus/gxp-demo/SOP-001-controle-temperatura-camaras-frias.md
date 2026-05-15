---
doc_id: SOP-001
titulo: Controle de Temperatura em Camaras Frias
versao: 3.2
status: Vigente
data_emissao: 2025-01-10
data_revisao: 2027-01-10
elaborado_por: Ana Paula Rocha - Analista de Qualidade
aprovado_por: Dr. Renato Figueiredo - Gerente de Garantia da Qualidade
referencia: RDC 301/2019 | ICH Q10 | PIC/S PE 010-4
departamento: Garantia da Qualidade
tags: [temperatura, camaras-frias, monitoramento, GMP, armazenamento]
---

# SOP-001 - Controle de Temperatura em Camaras Frias

## 1. Objetivo
Estabelecer os procedimentos para monitoramento, registro e controle das condicoes de temperatura nas camaras frias da BioNexus Farmaceutica Ltda., garantindo a integridade dos produtos armazenados e a conformidade com os requisitos regulatorios GMP.

## 2. Escopo
Aplica-se a todas as camaras frias classificadas nas faixas:
- **Refrigeracao:** +2C a +8C (camaras CF-01, CF-02, CF-03)
- **Congelamento:** -20C +/- 5C (camaras CG-01, CG-02)
- **Ultra-baixa temperatura:** -80C +/- 10C (camaras UBT-01)

## 3. Responsabilidades
| Funcao | Responsabilidade |
|---|---|
| Operador de Armazem | Leitura e registro de temperatura a cada 4 horas |
| Analista de Qualidade | Revisao diaria dos registros e emissao de alertas |
| Gerente de GQ | Aprovacao de desvios e acoes corretivas |
| Manutencao | Resposta a alarmes e manutencao preventiva |

## 4. Definicoes
- **Desvio de temperatura:** Qualquer leitura fora dos limites operacionais por periodo superior a 15 minutos.
- **Limite de acao (LA):** Temperatura que aciona resposta imediata da equipe.
- **Limite de alerta (LAL):** Temperatura que aciona notificacao preventiva.

## 5. Limites Operacionais
| Camara | Faixa Normal | Limite de Alerta | Limite de Acao |
|---|---|---|---|
| CF-01, CF-02, CF-03 | +2C a +8C | +1C / +9C | 0C / +10C |
| CG-01, CG-02 | -25C a -15C | -26C / -14C | -30C / -10C |
| UBT-01 | -90C a -70C | -91C / -69C | -95C / -65C |

## 6. Procedimento

### 6.1 Monitoramento Continuo
1. O sistema DataTemp-Pro registra temperatura a cada 5 minutos via sensores PT100 calibrados.
2. Em caso de falha do sistema automatico, realizar leitura manual a cada 4 horas com termometro calibrado (CAL-TERM-007).
3. Registrar leituras manuais no formulario FOR-SOP-001-A.

### 6.2 Rotina Diaria
1. As 07h00, verificar o painel de controle central (Sala de Monitoramento, Bloco B).
2. Confirmar que todos os sensores estao operacionais (indicador verde).
3. Verificar historico das ultimas 24 horas em busca de desvios.
4. Assinar o Registro Diario de Temperatura (FOR-SOP-001-B).

### 6.3 Resposta a Desvio de Temperatura
1. Ao identificar desvio, notificar imediatamente o Analista de Qualidade de plantao.
2. O Analista avalia a causa (falha de equipamento, abertura indevida de porta, falta de energia).
3. Se desvio exceder o Limite de Acao, acionar protocolo de transferencia emergencial (PROT-EMER-003).
4. Abrir Relatorio de Desvio conforme SOP-005.
5. Avaliar impacto sobre os produtos armazenados com suporte do Controle de Qualidade.

### 6.4 Abertura e Fechamento de Camaras
1. Minimizar o tempo de porta aberta (maximo 3 minutos por acesso).
2. Verificar vedacao da porta apos cada acesso.
3. Nunca sobrecarregar camaras alem de 80% da capacidade volumetrica.

## 7. Manutencao Preventiva
- Verificacao de vedacoes de porta: mensal
- Limpeza de evaporadores: trimestral
- Calibracao de sensores: semestral (conforme SOP-002)
- Mapeamento termico completo: anual (conforme PROT-004)

## 8. Documentacao
| Formulario | Descricao | Retencao |
|---|---|---|
| FOR-SOP-001-A | Registro Manual de Temperatura | 5 anos |
| FOR-SOP-001-B | Registro Diario de Temperatura | 5 anos |
| FOR-SOP-001-C | Relatorio de Desvio de Temperatura | 10 anos |

## 9. Referencias
- RDC 301/2019 - ANVISA (Boas Praticas de Fabricacao)
- ICH Q10 - Pharmaceutical Quality System
- PIC/S PE 010-4 - Guide to GMP for Medicinal Products

## 10. Historico de Revisoes
| Versao | Data | Descricao | Autor |
|---|---|---|---|
| 1.0 | 2020-03-01 | Emissao inicial | M. Santos |
| 2.0 | 2022-06-15 | Inclusao camara UBT-01 | A. Rocha |
| 3.0 | 2024-01-10 | Adequacao RDC 301/2019 | A. Rocha |
| 3.2 | 2025-01-10 | Atualizacao limites alerta CG | A. Rocha |
