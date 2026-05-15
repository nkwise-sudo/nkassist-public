---
title: "SOP-010 - Controle de Temperatura na Cadeia Fria"
version: "1.0"
effective_date: "2025-01-10"
author: "Eduardo Nakahara"
department: "Logística e Armazenamento"
document_type: "SOP"
tags: ["cadeia fria", "temperatura", "GDP", "monitoramento", "transporte"]
---

# SOP-010 - Controle de Temperatura na Cadeia Fria

## Objetivo

Definir procedimentos para controle, monitoramento e manutenção de temperatura na cadeia fria durante armazenamento, transporte e distribuição de produtos termosensíveis, assegurando conformidade com Boas Práticas de Distribuição (GDP).

## Escopo

Aplica-se a todos os colaboradores envolvidos em atividades de recebimento, armazenamento, transporte e distribuição de produtos que requerem controle de temperatura (medicamentos, vacinas, amostras biológicas, reagentes).

## Responsabilidades

- **Gerente de Logística**: Aprovação do SOP e supervisão da cadeia fria
- **Técnicos de Armazenamento**: Operação e monitoramento diário dos equipamentos
- **Coordenador de Qualidade**: Verificação de conformidade e investigação de excursões de temperatura
- **Responsável Técnico**: Avaliação de impacto em caso de desvio

## Equipamentos e Materiais

- Câmaras frias, freezers e refrigeradores qualificados
- Data loggers e sensores de temperatura calibrados
- Sistemas de monitoramento contínuo (SCADA/BMS)
- Caixas térmicas validadas para transporte
- Termômetros de referência calibrados
- Geradores de backup e sistemas de alarme
- Registradores gráficos e termômetros de máxima/mínima

## Procedimento

### 4.1 Faixas de Temperatura por Produto

| Categoria | Faixa de Temperatura | Produtos Exemplos |
|-----------|---------------------|-------------------|
| Ambiente controlado | 15°C a 25°C | Medicamentos estáveis, dispositivos médicos |
| Refrigerado | 2°C a 8°C | Vacinas, insulinas, alguns biológicos |
| Congelado | -25°C a -15°C | Reagentes, amostras biológicas |
| Ultra-congelado | -80°C a -60°C | Vacinas específicas, material genético |
| Criogênico | < -150°C | Células-tronco, embriões |

### 4.2 Monitoramento de Temperatura

#### Monitoramento Contínuo
1. Instalar sensores de temperatura em pontos críticos dos equipamentos
2. Configurar sistema de monitoramento contínuo com:
   - Registro de dados a cada 15 minutos (mínimo)
   - Alarmes automáticos para desvios de temperatura
   - Notificações vía SMS/e-mail para equipe de plantao
3. Validar posicionamento de sensores durante qualificação (mapeamento térmico)

#### Monitoramento Manual
1. Realizar leituras manuais 2x ao dia (manhã e tarde) como backup
2. Registrar leituras em planilha física ou eletrônica
3. Incluir temperatura atual, máxima e mínima desde última verificação
4. Assinar e datar cada registro

### 4.3 Calibração de Equipamentos

1. Calibrar termômetros e sensores anualmente ou conforme recomendação do fabricante
2. Utilizar padrões rastreados a organismos acreditados (RBC/INMETRO)
3. Manter certificados de calibração arquivados
4. Identificar equipamentos com etiquetas indicando próxima calibração

### 4.4 Qualificação de Equipamentos de Armazenamento

Todos os equipamentos de cadeia fria devem ser qualificados conforme SOP-012:

- **IQ (Instalação)**: Verificação de instalação correta
- **OQ (Operação)**: Teste de performance e alarmes
- **PQ (Performance)**: Mapeamento térmico sob condições carregadas

Mapeamento térmico deve:
- Identificar pontos quentes e frios
- Validar uniformidade de temperatura
- Ser realizado anualmente ou após manutenções significativas

### 4.5 Transporte e Distribuição

#### Preparação para Transporte
1. Utilizar caixas térmicas validadas para a faixa de temperatura requerida
2. Pré-condicionar caixas e elementos refrigerantes
3. Incluir data logger para registro de temperatura durante transporte
4. Documentar temperatura no momento de embalagem

#### Validação de Caixas Térmicas
- Realizar estudos de estabilidade térmica (perfil térmico)
- Validar para piores condições (verão/inverno)
- Definir tempo máximo de transito
- Documentar configuração de gelo seco ou elementos refrigerantes

#### Recebimento de Produtos
1. Verificar temperatura imediatamente ao receber
2. Conferir integridade de embalagem e lacres
3. Avaliar dados de data logger
4. Rejeitar produtos com evidência de excursão de temperatura
5. Transferir imediatamente para armazenamento adequado

### 4.6 Manutenção Preventiva

1. Realizar manutenção preventiva semestral em todos os equipamentos
2. Incluir:
   - Limpeza de condensadores e filtros
   - Verificação de vedacao de portas
   - Teste de sistemas de alarme e backup
   - Inspeção de cabos e sensores
3. Documentar todas as atividades de manutenção
4. Requalificar equipamento após manutenções críticas

### 4.7 Gestão de Excursões de Temperatura

#### Detecção e Resposta Imediata
1. Ao receber alarme de temperatura:
   - Verificar alarme no local imediatamente
   - Confirmar excursão com termômetro de backup
   - Notificar supervisor e Garantia da Qualidade
2. Implementar ações corretivas imediatas:
   - Transferir produtos para equipamento backup (se disponível)
   - Acionar manutenção para reparo emergencial
   - Segregar produtos afetados

#### Avaliação de Impacto
1. Registrar todas as informações:
   - Temperatura máxima/mínima atingida
   - Duração da excursão
   - Produtos e lotes afetados
2. Avaliar impacto na qualidade do produto:
   - Consultar dados de estabilidade
   - Avaliar cálculo de energia cinética (MKT - Mean Kinetic Temperature)
   - Solicitar análises adicionais se necessário
3. Documentar investigação conforme SOP-014 (Desvios e CAPA)

#### Liberação ou Rejeição
- Responsavel Técnico deve aprovar liberação de produtos afetados
- Produtos rejeitados devem ser segregados e descartados
- Notificar clientes se produtos já distribuídos foram afetados

## Sistemas de Backup e Contingência

- Manter equipamentos de backup disponíveis
- Geradores elétricos com partida automática
- Contratos com fornecedores de gelo seco/nitrogênio para emergências
- Plano de transferência para instalações alternativas
- Lista de contatos de emergência 24/7

## Registros e Documentação

- Registros de temperatura (automáticos e manuais)
- Relatórios de excursão de temperatura
- Certificados de calibração
- Protocolos de qualificação (IQ/OQ/PQ)
- Registros de manutenção preventiva e corretiva
- Estudos de validação de transporte

## Treinamento

Todos os colaboradores devem ser treinados em:
- Importância da cadeia fria
- Procedimentos de monitoramento
- Resposta a alarmes e emergências
- Preenchimento correto de registros

## Referências

- WHO Technical Report Series 961 - Annex 9: Model guidance for the storage and transport of time- and temperature-sensitive pharmaceutical products
- EU Guidelines on Good Distribution Practice (GDP) - Chapter 3: Premises and Equipment
- PIC/S Guide PE 011-1: Good Practices for Temperature Controlled Medicinal Products
- RDC 430/2020 ANVISA - Boas Práticas de Distribuição de Medicamentos

## Histórico de Revisões

| Versão | Data       | Descrição                           | Autor               |
|--------|------------|-------------------------------------|---------------------|
| 1.0    | 2025-01-10 | Emissão inicial do documento        | Eduardo Nakahara    |
