# Change Request — CR-003: Visão Consolidada de Parcelas Futuras

**Versão:** 1.0  
**Data:** 2026-03-14  
**Status:** Concluído  
**Autor:** Rafael Peixoto  
**Prioridade:** Crítica

---

## 1. Resumo da Mudança

Evoluir a aba "Parcelas" existente de uma lista estática de passivos para uma central de inteligência sobre compromissos parcelados. A mudança adiciona três camadas sobre a tela atual: cards de resumo no topo, projeção visual de comprometimento futuro no meio, e melhorias na tabela de parcelas existente. O objetivo é responder perguntas que o app hoje não consegue: "quanto estarei comprometido nos próximos meses?", "quando cada parcela termina?", e "quanto dinheiro será liberado quando parcelas encerrarem?".

---

## 2. Classificação

| Campo            | Valor                                                                 |
|------------------|-----------------------------------------------------------------------|
| Tipo             | Nova Feature (evolução de tela existente)                             |
| Origem           | Benchmark competitivo + Evolução do produto (Roadmap F03)             |
| Urgência         | Próxima sprint                                                        |
| Complexidade     | Média                                                                 |

---

## 3. Contexto e Motivação

### Situação Atual (AS-IS)

A aba "Parcelas" exibe uma tabela com as parcelas ativas do usuário contendo: descrição, valor da parcela mensal, parcela atual/total (formato "X de Y"), data de vencimento e valor total restante. A tela é uma lista estática sem resumo, sem projeção temporal e sem indicadores visuais de tendência.

Exemplo com dados reais (Fev/2026):
- 11 parcelas ativas simultâneas
- Total comprometido mensalmente em parcelas: ~R$ 7.330
- Total restante em passivos futuros: R$ 248.010,51
- Parcelas que encerram em 1-3 meses: 4 (liberando ~R$ 1.228/mês)
- Parcelas pendentes (não iniciadas): 2 (Empr. Itaú 60x ~R$ 2.726/mês, Receita Federal 55x ~R$ 143/mês)

Nenhuma dessas informações derivadas é visível na tela atual. O usuário precisa calcular mentalmente.

### Problema ou Necessidade

1. **Sem visão temporal**: o usuário não sabe quando seu comprometimento com parcelas vai diminuir ou aumentar. Não há projeção de fluxo de caixa futuro baseada em parcelas.
2. **Sem indicadores de resumo**: não existe totalização rápida (quantas parcelas, quanto comprometido, quanto será liberado).
3. **Parcelas pendentes invisíveis**: parcelas com "0 de Y" (ainda não iniciadas) aparecem na lista mas sem destaque sobre o impacto que terão quando começarem.
4. **Sem ordenação estratégica**: a tabela não prioriza parcelas por data de encerramento, dificultando identificar quais terminam primeiro.
5. **Oportunidades perdidas**: quando uma parcela termina, o dinheiro liberado não é destacado como oportunidade de realocação.

### Situação Desejada (TO-BE)

A aba "Parcelas" será reorganizada em 3 seções com progressive disclosure:

**Seção 1 — Cards de resumo (topo da tela)**
- Total comprometido este mês (R$)
- Total restante em todas as parcelas (R$)
- Quantidade de parcelas ativas
- Próxima parcela a encerrar (nome + mês)
- Dinheiro a ser liberado nos próximos 3 meses (R$/mês)
- % da renda comprometida com parcelas (com indicador visual: verde < 30%, amarelo 30-50%, vermelho > 50%)

**Seção 2 — Projeção visual (centro da tela)**
- Gráfico de barras empilhadas: eixo X = meses (próximos 12 meses), eixo Y = valor total de parcelas. Cada parcela é um segmento colorido. Linha horizontal marca 50% da renda como limite saudável.
- Timeline horizontal (alternável): cada parcela como barra de Gantt simplificada mostrando início e fim. Parcelas pendentes (não iniciadas) em estilo diferenciado (tracejado/cinza).
- Toggle entre as duas visualizações.

**Seção 3 — Tabela de parcelas aprimorada (parte inferior)**
- Mantém todas as colunas existentes (descrição, valor, parcela atual/total, vencimento, valor restante)
- Adiciona coluna "Termina em" (mês/ano calculado)
- Adiciona badge de status: "Encerrando" (últimas 2 parcelas), "Ativa", "Pendente" (não iniciada)
- Ordenação padrão por data de encerramento (quem termina primeiro no topo)
- Destaque visual para parcelas pendentes (Empr. Itaú, Receita Federal 55x) com indicador de impacto futuro

---

## 4. Detalhamento da Mudança

### 4.1 O que muda

| #  | Item                              | Antes (AS-IS)                                        | Depois (TO-BE)                                                                      |
|----|-----------------------------------|------------------------------------------------------|-------------------------------------------------------------------------------------|
| 1  | Estrutura da aba Parcelas         | Tabela única de parcelas                             | 3 seções: cards resumo + projeção visual + tabela aprimorada                        |
| 2  | Informações de resumo             | Inexistente                                          | 6 cards com indicadores-chave no topo                                               |
| 3  | Projeção temporal                 | Inexistente                                          | Gráfico de barras empilhadas 12 meses + timeline Gantt (alternáveis)                |
| 4  | Colunas da tabela                 | Descrição, valor, parcela, vencimento, valor restante| Adiciona "Termina em" e badge de status                                             |
| 5  | Ordenação da tabela               | Ordem de cadastro (ou não especificada)              | Padrão por data de encerramento (ascendente)                                        |
| 6  | Parcelas pendentes (0 de Y)       | Aparecem na lista sem destaque                       | Badge "Pendente" + estilo visual diferenciado + indicador de impacto futuro na renda|
| 7  | Parcelas encerrando (X-1 de X, X de X) | Sem destaque                                  | Badge "Encerrando" + destaque de valor mensal que será liberado                     |
| 8  | Indicador de comprometimento      | Inexistente                                          | % da renda comprometida com parcelas, com cor semafórica                            |

### 4.2 O que NÃO muda

- Modelo de dados da entidade parcela (campos existentes permanecem iguais)
- Regra de avanço automático de parcela ao virar o mês ("X de Y" → "X+1 de Y")
- Regra de não replicar despesa na última parcela
- Lógica de criação, edição e exclusão de parcelas
- Integração das parcelas com as despesas planejadas mensais
- Demais abas do aplicativo (Despesas Planejadas, Gastos Diários)

---

## 5. Impacto nos Documentos

| Documento                          | Impactado? | Seções Afetadas                        | Ação Necessária                                   |
|------------------------------------|------------|----------------------------------------|---------------------------------------------------|
| `/docs/PRD.md`                     | Sim        | Requisitos Funcionais, Roadmap         | Adicionar RF para projeção de parcelas             |
| `/docs/ARCHITECTURE.md`            | Sim        | Estrutura de Pastas, Integrações       | Adicionar módulo/componentes de projeção           |
| `/docs/SPEC.md`                    | Sim        | Feature de Parcelas                    | Detalhar nova seção de projeção, endpoints, UI     |
| `/docs/IMPLEMENTATION_PLAN.md`     | Sim        | Adicionar novo grupo de tarefas        | Inserir tarefas da F03 com dependências            |

---

## 6. Impacto no Código

### 6.1 Arquivos Afetados

| Ação      | Caminho do Arquivo (estimado)                        | Descrição da Mudança                                          |
|-----------|------------------------------------------------------|---------------------------------------------------------------|
| Criar     | `backend/services/installment_projection.py`         | Serviço de projeção: recebe parcelas ativas, retorna projeção mês a mês para 12-24 meses |
| Criar     | `backend/routes/installment_projection.py`           | Endpoint GET /api/installments/projection?months=12            |
| Criar     | `backend/schemas/installment_projection.py`          | Schemas Pydantic para request/response da projeção            |
| Modificar | `backend/routes/__init__.py` (ou equivalente)        | Registrar nova rota                                           |
| Criar     | `frontend/src/components/installments/SummaryCards.tsx` | Componente de cards de resumo (6 indicadores)               |
| Criar     | `frontend/src/components/installments/ProjectionChart.tsx` | Gráfico de barras empilhadas (Recharts ou Chart.js)      |
| Criar     | `frontend/src/components/installments/TimelineGantt.tsx` | Timeline horizontal tipo Gantt simplificado                |
| Modificar | `frontend/src/pages/Installments.tsx` (ou equivalente) | Reorganizar layout: cards + gráfico + tabela               |
| Modificar | `frontend/src/components/installments/InstallmentTable.tsx` (ou equivalente) | Adicionar colunas "Termina em" e badge status, nova ordenação |
| Criar     | `frontend/src/hooks/useInstallmentProjection.ts`     | Hook para consumir endpoint de projeção                       |
| Criar     | `frontend/src/types/installmentProjection.ts`        | Types TypeScript para projeção                                |
| Criar     | `backend/tests/test_installment_projection.py`       | Testes unitários do serviço de projeção                       |

### 6.2 Banco de Dados

| Ação      | Descrição                                          | Migration Necessária? |
|-----------|----------------------------------------------------|-----------------------|
| Nenhuma   | Usa dados existentes das parcelas. Sem nova tabela, sem novos campos. A projeção é calculada em runtime. | Não |

---

## 7. Tarefas de Implementação

| ID      | Tarefa                                                          | Depende de | Done When                                                        |
|---------|-----------------------------------------------------------------|------------|------------------------------------------------------------------|
| CR3-T01 | Criar serviço de projeção no backend (`installment_projection.py`) | —          | Função recebe lista de parcelas e retorna array de projeção mês a mês com: mês, total_comprometido, parcelas_ativas (lista), parcelas_encerrando (lista), valor_liberado |
| CR3-T02 | Criar schemas Pydantic para projeção                            | CR3-T01    | Request aceita `months` (int, default 12). Response retorna array tipado |
| CR3-T03 | Criar endpoint GET `/api/installments/projection`               | CR3-T02    | Endpoint funcional retornando JSON da projeção para os próximos N meses |
| CR3-T04 | Testes unitários do serviço de projeção                         | CR3-T01    | Cenários cobertos: parcelas terminando, parcelas pendentes (0 de Y), mês sem mudança, todas terminando, nenhuma parcela |
| CR3-T05 | Criar types TypeScript para projeção                            | CR3-T03    | Types refletem o schema do backend                                |
| CR3-T06 | Criar hook `useInstallmentProjection`                           | CR3-T05    | Hook consome endpoint e retorna dados + loading + error           |
| CR3-T07 | Criar componente `SummaryCards`                                 | CR3-T06    | 6 cards renderizados: total mensal, total restante, qtd parcelas, próxima a encerrar, liberação 3 meses, % comprometimento com cor semafórica |
| CR3-T08 | Criar componente `ProjectionChart` (barras empilhadas)          | CR3-T06    | Gráfico de barras empilhadas com 12 meses, cada parcela como segmento, linha de 50% da renda visível |
| CR3-T09 | Criar componente `TimelineGantt`                                | CR3-T06    | Timeline horizontal com barras por parcela, estilo diferenciado para pendentes (tracejado) |
| CR3-T10 | Adicionar colunas e badges na tabela existente                  | —          | Coluna "Termina em" calculada, badges "Encerrando"/"Ativa"/"Pendente", ordenação por encerramento |
| CR3-T11 | Reorganizar layout da aba Parcelas                              | CR3-T07, CR3-T08, CR3-T09, CR3-T10 | Aba renderiza 3 seções na ordem: cards → gráfico (com toggle para Gantt) → tabela |
| CR3-T12 | Testes de integração frontend                                   | CR3-T11    | Componentes renderizam corretamente com dados mock e cenários de borda |
| CR3-T13 | Atualizar documentação (SPEC.md, PRD.md)                        | CR3-T11    | Documentos refletem nova estrutura da aba Parcelas                |

---

## 8. Critérios de Aceite

| #  | Critério                                                                                  | Tipo       |
|----|-------------------------------------------------------------------------------------------|------------|
| 1  | DADO que existem parcelas ativas QUANDO o usuário acessa a aba Parcelas ENTÃO os 6 cards de resumo são exibidos no topo com valores calculados corretamente | Funcional  |
| 2  | DADO que existem parcelas ativas QUANDO o usuário visualiza o gráfico ENTÃO cada mês dos próximos 12 meses mostra uma barra empilhada com o total de parcelas, e barras diminuem quando parcelas terminam | Funcional  |
| 3  | DADO que existe uma parcela com "9 de 10" QUANDO o gráfico é renderizado ENTÃO a barra do mês seguinte não inclui essa parcela e o card de "liberação nos próximos 3 meses" reflete o valor | Funcional  |
| 4  | DADO que existe uma parcela pendente (0 de Y) QUANDO a tabela é renderizada ENTÃO a parcela aparece com badge "Pendente" e estilo visual diferenciado (tracejado/cinza) | Funcional  |
| 5  | DADO que existe uma parcela nas últimas 2 prestações QUANDO a tabela é renderizada ENTÃO a parcela aparece com badge "Encerrando" | Funcional  |
| 6  | DADO que existem parcelas com datas de encerramento diferentes QUANDO a tabela é renderizada ENTÃO a ordenação padrão é por data de encerramento ascendente (mais próxima primeiro) | Funcional  |
| 7  | DADO que o % de comprometimento com parcelas é > 50% da renda QUANDO os cards são renderizados ENTÃO o indicador de % aparece em vermelho | Funcional  |
| 8  | DADO que o usuário está no gráfico de barras QUANDO clica no toggle ENTÃO alterna para a visualização de timeline Gantt e vice-versa | Funcional  |
| 9  | DADO que não existem parcelas cadastradas QUANDO o usuário acessa a aba Parcelas ENTÃO exibe estado vazio com mensagem orientativa | Edge case  |
| 10 | DADO que todas as parcelas terminam no mês atual QUANDO a projeção é calculada ENTÃO os meses seguintes mostram R$ 0 de comprometimento | Edge case  |
| 11 | O endpoint de projeção responde em menos de 500ms para até 50 parcelas ativas            | Performance|
| 12 | Os componentes visuais são responsivos e funcionam em telas de 320px a 1920px             | UI         |

---

## 9. Riscos e Efeitos Colaterais

| #  | Risco / Efeito Colateral                                        | Probabilidade | Mitigação                                                       |
|----|-----------------------------------------------------------------|---------------|-----------------------------------------------------------------|
| 1  | Parcelas pendentes (0 de Y) não têm valor mensal definido       | Alta          | Estimar valor mensal como (valor_total / total_parcelas). Marcar como "estimativa" na UI |
| 2  | Renda do usuário pode variar mês a mês, afetando % de comprometimento | Média     | Usar a renda do mês atual como referência. Quando multi-fonte de receita for implementado (F10), recalcular |
| 3  | Performance do gráfico com muitas parcelas (> 20) em mobile     | Baixa         | Limitar visualização a top 10 parcelas por valor no gráfico, com "ver todas" na tabela |
| 4  | Biblioteca de gráficos pode ser pesada para o bundle            | Média         | Usar Recharts (já comum em projetos React) com lazy loading do componente |

---

## 10. Notas de Implementação

### Lógica de Projeção (pseudocódigo)

```python
def calcular_projecao(parcelas: list, meses: int = 12, renda_mensal: float = 0) -> list:
    projecao = []
    
    for mes_offset in range(meses):
        mes_data = {
            "mes": data_atual + mes_offset,
            "parcelas_ativas": [],
            "parcelas_encerrando": [],
            "total_comprometido": 0,
            "valor_liberado": 0,  # vs mês anterior
        }
        
        for parcela in parcelas:
            parcela_projetada = parcela.atual + mes_offset
            
            if parcela.atual == 0:  # pendente
                # incluir como impacto potencial (estilo diferente)
                mes_data["parcelas_pendentes"].append(parcela)
                continue
            
            if parcela_projetada <= parcela.total:
                mes_data["parcelas_ativas"].append(parcela)
                mes_data["total_comprometido"] += parcela.valor
                
                if parcela_projetada == parcela.total:
                    mes_data["parcelas_encerrando"].append(parcela)
        
        if mes_offset > 0:
            mes_data["valor_liberado"] = (
                projecao[mes_offset - 1]["total_comprometido"] 
                - mes_data["total_comprometido"]
            )
        
        if renda_mensal > 0:
            mes_data["percentual_comprometimento"] = (
                mes_data["total_comprometido"] / renda_mensal * 100
            )
        
        projecao.append(mes_data)
    
    return projecao
```

### Cálculo do campo "Termina em"

```python
def calcular_data_termino(parcela_atual: int, parcela_total: int, mes_referencia: date) -> date:
    if parcela_atual == 0:  # pendente, data desconhecida
        return None
    meses_restantes = parcela_total - parcela_atual
    return mes_referencia + relativedelta(months=meses_restantes)
```

### Estrutura de resposta do endpoint

```json
{
  "resumo": {
    "total_comprometido_mes_atual": 7330.00,
    "total_restante_todas_parcelas": 248010.51,
    "quantidade_parcelas_ativas": 11,
    "proxima_a_encerrar": {
      "descricao": "Parc. Koin 1",
      "termina_em": "2026-02"
    },
    "liberacao_proximos_3_meses": 1228.46,
    "percentual_comprometimento": 41.6,
    "renda_referencia": 17619.55
  },
  "projecao_mensal": [
    {
      "mes": "2026-03",
      "total_comprometido": 6224.07,
      "parcelas_ativas": 8,
      "parcelas_encerrando": ["Seguro do Carro", "Empr. Sonia"],
      "valor_liberado": 1105.73,
      "percentual_comprometimento": 35.3
    }
  ],
  "parcelas_pendentes": [
    {
      "descricao": "Empr. Itaú",
      "valor_estimado_mensal": 2726.52,
      "total_parcelas": 60,
      "impacto_percentual": 15.5
    }
  ]
}
```

---

## 11. Changelog

| Versão | Data       | Autor           | Descrição           |
|--------|------------|-----------------|---------------------|
| 1.0    | 2026-03-14 | Rafael Peixoto  | Criação do CR-003   |
| 1.1    | 2026-03-14 | Claude | Implementação concluída |
