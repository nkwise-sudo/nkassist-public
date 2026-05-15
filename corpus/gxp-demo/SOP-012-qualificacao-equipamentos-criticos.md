---
title: "SOP-012 - Qualificação de Equipamentos Críticos"
version: "1.0"
effective_date: "2025-01-10"
author: "Eduardo Nakahara"
department: "Engenharia e Validação"
document_type: "SOP"
tags: ["qualificação", "IQ/OQ/PQ", "GMP", "equipamentos", "validação"]
---

# SOP-012 - Qualificação de Equipamentos Críticos

## Objetivo

Estabelecer metodologia para qualificação de equipamentos, instrumentos e sistemas críticos utilizados em processos farmacêuticos, biotecnológicos e laboratoriais, assegurando que funcionam conforme especificado e atendem aos requisitos de Boas Práticas de Fabricação (GMP).

## Escopo

Aplica-se a todos os equipamentos críticos novos, relocados ou que sofram modificações significativas, incluindo:
- Equipamentos de produção (biorreatores, misturadores, liofilizadores)
- Sistemas de armazenamento (câmaras frias, freezers, incubadoras)
- Equipamentos analíticos (HPLC, GC, espectrofotômetros)
- Sistemas de água purificada e água para injeção
- Autoclaves e estufas de esterilização

## Responsabilidades

- **Gerente de Engenharia**: Aprovação do plano de qualificação e supervisão
- **Especialista em Validação**: Elaboração de protocolos IQ/OQ/PQ e execução dos testes
- **Garantia da Qualidade**: Revisão e aprovação de protocolos e relatórios
- **Usuário Final**: Participação em PQ e aceitação final
- **Fornecedor**: Suporte técnico, documentação e FAT (Factory Acceptance Test)

## Definições

- **Qualificação**: Evidência documentada de que equipamentos, utilidades e sistemas funcionam conforme especificado
- **IQ (Installation Qualification)**: Verificação de que o equipamento foi instalado conforme especificações
- **OQ (Operational Qualification)**: Verificação de que o equipamento opera dentro dos limites operacionais
- **PQ (Performance Qualification)**: Demonstração de que o equipamento desempenha consistentemente sob condições reais de uso
- **DQ (Design Qualification)**: Verificação de que o design atende aos requisitos do usuário (URS)
- **FAT (Factory Acceptance Test)**: Testes realizados na fábrica do fornecedor
- **SAT (Site Acceptance Test)**: Testes realizados após instalação no local

## Procedimento

### 4.1 Fases da Qualificação

#### Fase 0: Planejamento e Requisitos

1. **URS (User Requirements Specification)**:
   - Documentar requisitos do usuário (processo, segurança, qualidade)
   - Definir parâmetros críticos de operação
   - Especificar faixas aceitáveis e critérios de aceitação
   - Identificar requisitos regulatórios aplicáveis

2. **Classificação de Risco**:
   - Avaliar impacto do equipamento na qualidade do produto
   - Classificar como crítico, importante ou não crítico
   - Definir nível de qualificação necessário

3. **Plano Mestre de Qualificação**:
   - Definir escopo, cronograma e recursos
   - Identificar protocolos necessários (IQ, OQ, PQ)
   - Estabelecer responsabilidades

#### Fase 1: DQ (Design Qualification)

1. Revisar especificações técnicas do fornecedor vs. URS
2. Verificar conformidade com normas e regulamentos
3. Avaliar:
   - Capacidade técnica
   - Materiais de construção
   - Sistemas de controle e automação
   - Segurança e ergonomia
4. Documentar desvios e requerer alterações se necessário

#### Fase 2: FAT (Factory Acceptance Test)

1. Testes na fábrica do fornecedor antes do envio
2. Verificar:
   - Funcionalidade básica
   - Calibração de instrumentos
   - Sistemas de alarme
   - Interfaces de comunicação
3. Aprovar envio somente após aceitação

#### Fase 3: IQ (Installation Qualification)

**Objetivo**: Verificar que o equipamento foi instalado corretamente.

**Atividades**:

1. **Documentação**:
   - Verificar recebimento de manuais (operação, manutenção)
   - Conferir desenhos (P&ID, elétricos, mecânicos)
   - Validar certificados de calibração de instrumentos
   - Confirmar lista de peças de reposição

2. **Inspeção Física**:
   - Verificar modelo, número de série, identificação
   - Conferir integridade (sem danos de transporte)
   - Validar materiais de construção
   - Verificar acabamento de superfícies (polimento para áreas de contato com produto)

3. **Instalação**:
   - Verificar localização conforme especificado
   - Confirmar conexões (elétricas, hidráulicas, vapor, ar comprimido)
   - Validar sistemas de dreno e ventilação
   - Verificar nivelamento

4. **Utilidades**:
   - Confirmar tensão, frequência, potência elétrica
   - Validar qualidade de utilidades (ar comprimido, água, vapor)
   - Verificar sistemas de backup (geradores, no-breaks)

5. **Segurança**:
   - Testar dispositivos de proteção
   - Verificar botões de emergência
   - Validar sinalizadores e alarmes

#### Fase 4: OQ (Operational Qualification)

**Objetivo**: Demonstrar que o equipamento opera conforme especificações em toda faixa operacional.

**Atividades**:

1. **Testes de Funcionalidade**:
   - Testar todas as funções do equipamento
   - Verificar modos de operação (automático, manual, emergência)
   - Validar sequência de operação

2. **Testes de Parâmetros Críticos**:
   - **Temperatura**: Mapear perfil térmico, testar uniformidade
   - **Velocidade**: Verificar RPM, velocidade de agitação
   - **Pressão**: Testar controle de pressão, vedação
   - **Vazão**: Validar bombas e sistemas de transferência
   - **Tempo**: Verificar precisão de timers

3. **Sistemas de Controle**:
   - Testar setpoints em toda faixa operacional
   - Verificar precisão de sensores e transmissores
   - Validar algoritmos de controle (PID)
   - Testar integração com sistemas supervisores (SCADA, DCS)

4. **Alarmes e Intertravamentos**:
   - Forçar condições de alarme
   - Verificar ações de segurança (shutdown)
   - Testar todos os alarmes (alto, baixo, crítico)
   - Validar notificações (sonoras, visuais, remotas)

5. **Calibração**:
   - Calibrar todos os instrumentos críticos
   - Documentar certificados rastreados a padrões nacionais
   - Estabelecer frequência de recalibração

6. **Testes de Pior Caso (Worst Case)**:
   - Testar nas condições extremas de operação
   - Avaliar desempenho em situações críticas

#### Fase 5: PQ (Performance Qualification)

**Objetivo**: Demonstrar que o equipamento desempenha consistentemente sob condições normais de uso com produto/material real ou simulado.

**Atividades**:

1. **Testes com Processo Real**:
   - Executar processo completo (3 lotes mínimo)
   - Utilizar produto real ou simulado (placebo)
   - Monitorar parâmetros críticos de qualidade

2. **Consistência**:
   - Avaliar reprodutibilidade entre lotes
   - Verificar uniformidade do produto
   - Validar estabilidade do processo ao longo do tempo

3. **Capacidade de Processo**:
   - Calcular índices Cp e Cpk
   - Avaliar capabilidade estatística
   - Confirmar atendimento a especificações

4. **Condições Desafiadoras**:
   - Testar com volumes mínimo e máximo
   - Avaliar diferentes formulações/lotes
   - Simular variações de matéria-prima

5. **Integração com Processo**:
   - Verificar interface com equipamentos adjacentes
   - Validar transferência de dados
   - Testar sincronização de etapas

6. **Limpeza**:
   - Executar procedimento de limpeza completo
   - Validar eficácia (swab test, rinse test)
   - Confirmar facilidade de limpeza e acesso

### 4.2 Documentação da Qualificação

#### Protocolo de Qualificação

Deve conter:
- Objetivo e escopo
- Referências (URS, desenhos, SOPs)
- Descrição do equipamento
- Critérios de aceitação
- Procedimentos de teste detalhados
- Formulários de registro de dados
- Responsabilidades e assinaturas

#### Relatório de Qualificação

Deve incluir:
- Resumo executivo
- Resultados de todos os testes
- Desvios e investigações
- Análise estatística (quando aplicável)
- Conclusão e recomendações
- Aprovações finais

### 4.3 Critérios de Aceitação

- Todos os testes devem passar conforme critérios predefinidos
- Desvios devem ser justificados e aprovados pela Qualidade
- Não conformidades críticas devem ser corrigidas e retestadas
- Documentação deve estar completa e aprovada

### 4.4 Requalificação

Requalificação periódica é necessária:
- Após modificações significativas (hardware, software)
- Após manutenções críticas
- Em caso de desvios recorrentes de performance
- Periodicamente (geralmente a cada 3-5 anos)
- Após realocação do equipamento

Requalificação pode ser parcial (somente áreas afetadas) ou completa conforme avaliação de risco.

## Gestão de Desvios

- Documentar todos os desvios durante qualificação
- Classificar severidade (crítico, maior, menor)
- Investigar causa raiz
- Implementar CAPA quando necessário
- Avaliar impacto na aprovação do equipamento

## Treinamento

- Treinar operadores após aprovação da qualificação
- Incluir operação, manutenção e limpeza
- Documentar competência antes de liberar uso

## Registros e Documentação

- URS (User Requirements Specification)
- Plano Mestre de Qualificação
- Protocolos IQ/OQ/PQ
- Relatórios de qualificação
- Certificados de calibração
- Registros de treinamento
- Relatórios de desvio e CAPA
- Manuais do fabricante

Todos os documentos devem ser arquivados por toda vida útil do equipamento + 1 ano após descarte.

## Referências

- ISPE Baseline Guide Vol. 5: Commissioning and Qualification
- WHO TRS 996 Annex 4: Guidelines on qualification
- EU GMP Annex 15: Qualification and Validation
- FDA Guidance: Process Validation
- ABNT NBR ISO/IEC 17025: Competência de laboratórios

## Histórico de Revisões

| Versão | Data       | Descrição                           | Autor               |
|--------|------------|-------------------------------------|---------------------|
| 1.0    | 2025-01-10 | Emissão inicial do documento        | Eduardo Nakahara    |
