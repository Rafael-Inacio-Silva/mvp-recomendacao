# Proposta — MVP de recomendação de itens

**Cliente:** Sabor na Mesa Cozinha Mexicana
**Fornecedor:** PratoTech
**Referência:** [solicitação de 22/11/2026](solicitacao-cliente.md)
**Resultado:** [relatório do MVP](relatorio.md)

## 1. Propósito

Este documento apresenta a proposta da PratoTech para o MVP de recomendação de itens do delivery da Sabor na Mesa. O sistema sugere acompanhamentos, bebidas ou outros pratos enquanto o cliente monta o carrinho, com base nos itens que costumam ser pedidos juntos.

O objetivo de negócio é reduzir os pedidos fechados só com o prato principal e aumentar o número de itens por pedido.

## 2. Escopo

**O sistema faz:**

- exibe o cardápio com os itens do histórico de pedidos;
- permite montar um carrinho de demonstração;
- sugere até 3 itens relacionados ao carrinho, ordenados pela força da associação;
- explica cada sugestão em uma frase curta;
- apresenta os dados usados, as regras calculadas e os resultados da avaliação.

**O sistema não faz:**

- integração com o site, o pagamento ou a entrega;
- recomendação personalizada por cliente;
- uso de preços, promoções, estoque, horário ou dia da semana;
- publicação em produção.

## 3. Descrição do sistema

O restaurante enviou o histórico do delivery no arquivo `pedidos.csv`, com o número de cada pedido e os itens pedidos. Uma primeira leitura mostra:

| Indicador | Valor |
|---|---|
| Pedidos | 1.834 |
| Itens distintos | 45 |
| Média de itens distintos por pedido | 2,3 |
| Pedidos com um único item | 194 (10,6%) |
| Itens mais presentes | Bowl de Frango (33,5% dos pedidos), Burrito de Frango (26,7%), Nachos com Guacamole (25,8%) |

A partir desse histórico, o sistema identifica regras do tipo “quem pede A também costuma pedir B”. Quando o cliente coloca itens no carrinho, o sistema procura as regras que se aplicam a eles e mostra os itens sugeridos, cada um com uma frase explicando a relação. A frase é montada a partir da própria regra, sem IA, por exemplo: “Já que você escolheu Água Mineral, que tal incluir Bowl de Frango no pedido?”.

Uma página separada mostra ao restaurante como o sistema chegou às sugestões: o resumo dos dados, a lista de regras e os resultados da avaliação.

## 4. Requisitos funcionais

| RF | Descrição | Prioridade |
|---|---|---|
| RF-01 | O sistema deve exibir o cardápio com os itens do histórico de pedidos. | Alta |
| RF-02 | O sistema deve permitir montar o carrinho, adicionando e removendo itens. | Alta |
| RF-03 | O sistema deve calcular regras de associação a partir do histórico de pedidos. | Alta |
| RF-04 | O sistema deve sugerir itens relacionados aos itens do carrinho. | Alta |
| RF-05 | O sistema deve ordenar as sugestões pela força da associação. | Alta |
| RF-06 | O sistema deve apresentar uma explicação para cada sugestão. | Alta |
| RF-07 | O sistema deve apresentar os dados utilizados e as regras calculadas. | Média |
| RF-08 | O sistema deve apresentar os resultados da avaliação das recomendações. | Média |

## 5. Requisitos não funcionais

| RNF | Tipo | Descrição |
|---|---|---|
| RNF-01 | Desempenho | As sugestões devem aparecer em até 1 segundo após uma alteração no carrinho, na demonstração executada localmente. |
| RNF-02 | Desempenho | A explicação deve aparecer junto com a sugestão, sem depender de serviços externos. |
| RNF-03 | Confiabilidade | A demonstração deve funcionar sem acesso à internet. |
| RNF-04 | Usabilidade | Cada explicação deve estar em português. |
| RNF-05 | Manutenibilidade | As regras devem poder ser recalculadas a partir de um novo arquivo de pedidos no mesmo formato, sem alterar o sistema. |
| RNF-06 | Manutenibilidade | As regras de negócio RN-02 a RN-06 devem ter testes automatizados. |

## 6. Regras de negócio

| RN | Descrição | RF relacionado |
|---|---|---|
| RN-01 | Um pedido é o conjunto de itens com o mesmo número. A quantidade de vezes que um item aparece no pedido não é considerada. | RF-03 |
| RN-02 | Um item que já está no carrinho não é sugerido. | RF-04 |
| RN-03 | São exibidas no máximo 3 sugestões. | RF-04 |
| RN-04 | Só são usadas as regras com suporte de pelo menos 1% e confiança de pelo menos 10%, limites definidos na avaliação offline. | RF-03 |
| RN-05 | As sugestões são ordenadas pela confiança da regra. Em caso de empate, vale o maior lift. | RF-05 |
| RN-06 | Quando as regras geram menos de 3 sugestões, as vagas restantes são completadas com os itens mais pedidos que ainda não estão no carrinho. | RF-04 |
| RN-07 | A explicação é montada a partir da regra que gerou a sugestão: “Já que você escolheu {itens do carrinho}, que tal incluir {item sugerido} no pedido?”. | RF-06 |
| RN-08 | Quando a sugestão vem dos mais vendidos, e não de uma regra, a explicação é “Um dos itens mais pedidos da casa”. | RF-06 |

## 7. Abordagem

As sugestões vêm de **regras de associação**, uma técnica usada em análise de cesta de compras. Para cada regra “quem pede A também pede B”, o sistema calcula três medidas:

- **Suporte:** em que parte dos pedidos A e B aparecem juntos.
- **Confiança:** entre os pedidos que têm A, em quantos também aparece B.
- **Lift:** quanto ter A no carrinho aumenta a chance de B, comparado com a frequência normal de B. Lift acima de 1 indica uma associação real.

A ordenação usa a confiança (RN-05): entre os itens ligados ao carrinho por alguma regra, vem primeiro o que mais aparece junto com ele. A ordenação pelo lift foi a primeira escolha, para evitar que itens populares aparecessem em todas as sugestões, mas a avaliação offline mostrou que, nesta base, ela favorece itens raros e acerta menos que a referência dos mais pedidos. A comparação está no [relatório](relatorio.md).

Os detalhes de construção estão no documento de [arquitetura](../arquitetura.md).

## 8. Critérios de avaliação

**Antes da entrega.** Parte dos pedidos fica separada e não é usada no cálculo das regras. Em cada um desses pedidos, um item é escondido e o sistema recebe os demais como carrinho. A avaliação mede:

- **Taxa de acerto:** em quantos casos o item escondido aparece entre as 3 sugestões.
- **Cobertura:** em quantos carrinhos existe pelo menos uma regra aplicável.
- **Força das sugestões:** lift médio das regras usadas.

O resultado é comparado com uma referência simples: sugerir sempre os 3 itens mais pedidos. O MVP só agrega valor se acertar mais do que essa referência. Além disso, as 10 regras mais fortes serão revisadas com a equipe do restaurante.

**Depois de publicar (fase futura).** Taxa de aceitação das sugestões, itens por pedido e ticket médio, com teste A/B entre clientes que veem e que não veem as sugestões.

## 9. Prazo estimado

Duas semanas (10 dias úteis):

| Etapa | Dias | Resultado para o restaurante |
|---|---|---|
| Análise dos dados | 2 | resumo do histórico e limites das regras definidos |
| Cálculo das regras e das sugestões | 3 | sugestões funcionando para qualquer carrinho |
| Avaliação | 1 | taxa de acerto e comparação com a referência |
| Explicações | 1 | frase para cada sugestão |
| Tela de demonstração | 2 | páginas “Monte seu pedido” e “Como funciona” |
| Revisão com o restaurante | 1 | ajustes e apresentação final |

## 10. Riscos

| Risco | Como tratar |
|---|---|
| Base pequena, com itens que aparecem em poucos pedidos | limites mínimos nas regras (RN-04) e sugestão dos mais pedidos (RN-06) |
| Itens populares dominarem as sugestões | as sugestões vêm de regras ligadas ao carrinho, e a avaliação compara o resultado com a referência dos mais pedidos |
| Explicação prometer algo que os dados não mostram | a frase é montada com os números da própria regra (RN-07) |
| Histórico sem data e sem identificação do cliente | o MVP não usa horário nem perfil; isso fica para fases futuras |

## 11. Próximas fases

- Recomendação personalizada pelo histórico de cada cliente.
- Uso de horário, dia da semana e preço nas sugestões.
- Atualização periódica das regras com os pedidos novos.
- Integração ao site de delivery e medição com teste A/B.
