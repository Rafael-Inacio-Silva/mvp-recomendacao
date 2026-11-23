# Relatório — Sabor na Mesa Cozinha Mexicana

Resultado do MVP de recomendação de itens para o delivery da Sabor na Mesa, a partir da [solicitação](solicitacao-cliente.md) e da [proposta](../proposta.md).

## Dados

| Indicador | Valor |
|---|---|
| Pedidos recebidos | 1.834 |
| Pedidos após a limpeza | 1.789 |
| Itens distintos | 45 |
| Itens por pedido (média) | 2,3 |
| Item mais presente | Bowl de Frango, em 33% dos pedidos |

## Resultado

Taxa de acerto no top 3: em cada pedido de teste, um item é escondido e o recomendador recebe os demais como carrinho. A validação cruzada testa todos os pedidos, por isso é a medida mais confiável.

| Versão | Divisão única (771 casos) | Validação cruzada (3.840 casos) |
|---|---|---|
| 1: regras por lift, sem completar as vagas | 36,8% | 32,6% |
| 2: regras por lift + mais pedidos completando | 45,5% | 45,2% |
| **3: regras por confiança + mais pedidos completando** | **48,4%** | **47,3%** |
| Referência: sempre os 3 mais pedidos | 45,8% | 43,6% |

A versão 3 é a usada no MVP. Ela acerta 3,7 pontos a mais que a referência, e as regras se aplicam a 91% dos carrinhos.

## Dificuldade: poucos dados

A primeira versão acertou menos que a referência dos mais pedidos. Com poucos pedidos, só 23 regras passavam nos limites iniciais (confiança de 20% e lift maior que 1), e isso causou dois problemas.

**1. Vagas vazias.** Muitos carrinhos recebiam só 1 ou 2 sugestões. Com o Bowl de Frango no carrinho, por exemplo, a versão 1 sugeria apenas o Refrigerante em Lata. A versão 2 passou a completar as vagas com os mais pedidos (RN-06).

**2. O lift favorece itens raros.** Com a Água Mineral no carrinho:

| Regra | Confiança | Lift |
|---|---|---|
| Água Mineral → Bowl de Frango | 42% | 1,28 |
| Água Mineral → Nachos | 23% | 2,12 |

Ordenando pelo lift, o Nachos vem primeiro, porque a Água Mineral dobra a chance de pedir Nachos. Mas quem pede Água Mineral leva o Bowl de Frango em 42% dos pedidos, contra 23% do Nachos. A confiança coloca primeiro o item mais provável, e é isso que aumenta o acerto.

O filtro de lift também deixava carrinhos sem regra. Com o Burrito de Frango, por exemplo, a versão 1 caía nos mais pedidos e sugeria o Bowl de Frango, um segundo prato principal. Na versão 3, as regras sugerem Nachos com Guacamole, Refrigerante em Lata e Burrito de Carne.

**Mudanças da versão 3:** confiança mínima de 10%, sem filtro de lift, sugestões ordenadas pela confiança e vagas restantes completadas com os mais pedidos.

## Conclusão

As regras de associação superam a referência dos mais pedidos, mas por pouco. A causa é a base: são poucos pedidos, eles são curtos e há pouca variedade, com 45 itens e três deles presentes em um quarto dos pedidos ou mais. Por isso, as regras são poucas e fracas (lift máximo de 3,96).

Para melhorar, o restaurante precisaria de:

- **mais pedidos**, com um histórico mais longo;
- **mais variedade** de itens e pedidos maiores, com entrada, prato, acompanhamento e bebida;
- **dados do cliente e do horário**, para sugestões personalizadas;
- um **teste A/B** no site, para medir o efeito no ticket médio, que a avaliação offline não mede.

Outra abordagem testada, sugerir itens com o nome parecido com os do carrinho, acertou 7,8%, porque indica substitutos (um burrito para quem já tem um burrito) e não complementos.
