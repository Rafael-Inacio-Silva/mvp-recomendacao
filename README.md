# MVP de recomendação de itens — Sabor na Mesa

Projeto preparado para a entrevista a partir de um cenário fictício. A Sabor na Mesa, um restaurante de culinária mexicana em São Paulo, pede à PratoTech um MVP que recomende itens com base no carrinho do delivery, usando regras de associação calculadas a partir dos pedidos.

- [Solicitação do cliente](docs/solicitacao-cliente.md): e-mail com o escopo do MVP.

## Dados

[pedidos.csv](dados/pedidos.csv) é o histórico de pedidos enviado pelo restaurante: 4.622 linhas, 1.834 pedidos e 45 itens distintos.

| Coluna | Descrição |
|---|---|
| `id_pedido` | número do pedido; as linhas com o mesmo número formam um carrinho |
| `item` | nome do item do cardápio |

Um mesmo item pode aparecer em mais de uma linha do mesmo pedido. Para as regras de associação, interessa apenas se o item está ou não no pedido, então cada pedido é tratado como um conjunto de itens.
