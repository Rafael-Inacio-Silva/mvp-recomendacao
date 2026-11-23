# Relatório — Casa Masala Cozinha Indiana

Resultado do mesmo MVP aplicado ao delivery da Casa Masala, a partir da [solicitação](solicitacao-cliente.md). O código, as regras de negócio e a avaliação são os mesmos usados na [Sabor na Mesa](../mexicano/relatorio.md).

## Dados

A exportação do caixa veio em inglês. O script `preparar_indiano.py` mantém o número do pedido e o nome do item e traduz os nomes com a tabela `dados/indiano/traducao_itens.csv`. Grafias diferentes do mesmo item, como “Onion Bhajee” e “Onion Bhaji”, recebem a mesma tradução.

| Indicador | Valor |
|---|---|
| Pedidos recebidos | 13.397 |
| Pedidos após a limpeza | 13.006 |
| Itens distintos | 243 |
| Itens por pedido (média) | 5,3 |
| Item mais presente | Arroz Pilau, em 34% dos pedidos |

Na limpeza, o pipeline removeu 144 linhas repetidas (o mesmo item duas vezes no pedido) e 391 pedidos com mais de 11,5 itens (2,9%), que são pedidos de grupo.

## Resultado

| Versão | Divisão única (13.754 casos) | Validação cruzada (68.771 casos) |
|---|---|---|
| 1: regras por lift, sem completar as vagas | 20,7% | 20,5% |
| 2: regras por lift + mais pedidos completando | 21,0% | 20,6% |
| **3: regras por confiança + mais pedidos completando** | **23,3%** | **23,4%** |
| Referência: sempre os 3 mais pedidos | 20,3% | 20,2% |

A versão 3 acerta 3,2 pontos a mais que a referência, ou seja, 16% a mais, e as regras se aplicam a 95% dos carrinhos.

## O que mudou com mais dados

**Mais regras e mais fortes.** São 637 regras, contra 61 na Sabor na Mesa; 294 delas têm lift acima de 1,5, e o lift máximo é 6,35.

**Quase não sobram vagas vazias.** Mesmo a versão 1 encontra regra para 95% dos carrinhos, por isso as versões 1 e 2 ficam praticamente iguais. O problema das vagas vazias era consequência da base pequena.

**O lift continua acertando menos.** Com o Papadum Simples no carrinho:

| Versão | Sugestões |
|---|---|
| 1 (lift) | Chutney de Manga (39%, lift 2,78), Molho de Hortelã (27%, lift 2,77), Arroz Pilau (48%, lift 1,40) |
| 3 (confiança) | Arroz Pilau (48%), Chutney de Manga (39%), Naan Simples (31%) |
| Referência | Arroz Pilau, Naan Simples, Naan de Alho |

Os molhos são os itens mais “ligados” ao papadum, mas o Arroz Pilau é o mais provável. A versão 3 junta os dois: o item mais provável e o complemento típico, que a referência não sugere.

**O acerto absoluto é menor que no mexicano** (23% contra 47%) porque o cardápio tem 243 itens, contra 45. Por isso, a comparação justa é o ganho sobre a referência de cada loja.

## Conclusão dos dois cenários

| Indicador | Sabor na Mesa | Casa Masala |
|---|---|---|
| Pedidos (após a limpeza) | 1.789 | 13.006 |
| Itens / itens por pedido | 45 / 2,3 | 243 / 5,3 |
| Regras (suporte 1%, confiança 10%) | 61 | 637 |
| Lift máximo | 3,96 | 6,35 |
| Carrinhos com regra na versão 1 | 63% | 95% |
| Versão 3 × referência (validação cruzada) | 47,3% × 43,6% | 23,4% × 20,2% |
| Ganho relativo sobre a referência | 8% | 16% |

- Na **Sabor na Mesa**, a dificuldade foi a pouca quantidade de dados: poucas regras, vagas vazias e o lift favorecendo itens raros. Completar as vagas com os mais pedidos e ordenar pela confiança fez as regras superarem a referência.
- Na **Casa Masala**, com sete vezes mais pedidos e pedidos maiores, as regras cobrem quase todos os carrinhos e o ganho relativo dobra. A ordenação pela confiança continua sendo a escolha que faz a diferença.
- Nas duas lojas, o próximo passo é um **teste A/B** no site, para medir o efeito das sugestões no ticket médio, e o uso de **dados do cliente e do horário** para personalizar as sugestões.
