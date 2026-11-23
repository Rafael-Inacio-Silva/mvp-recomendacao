# Relatório — Sabor na Mesa Cozinha Mexicana

Olá, Mariana! Este relatório mostra os dados que usamos, como o sistema escolhe as sugestões e se elas funcionam com os pedidos da Sabor na Mesa. Os detalhes técnicos estão na [proposta](proposta.md) e na [arquitetura](../arquitetura.md).

## Os dados que usamos

Usamos só o histórico que você enviou: o número de cada pedido e os itens que ele tinha. Não usamos dados dos clientes, preços nem datas.

| | |
|---|---|
| Pedidos analisados | 1.789 |
| Itens no cardápio | 45 |
| Itens por pedido, em média | 2,3 |
| Item mais pedido | Bowl de Frango, presente em 1 de cada 3 pedidos |

Antes de começar, deixamos de fora 45 pedidos com 5 itens ou mais. Eles costumam ser pedidos de grupo e misturam escolhas de várias pessoas. Um item pedido duas vezes no mesmo pedido contou uma vez só.

## Como o sistema escolhe as sugestões

O sistema olha os pedidos antigos e aprende quais itens costumam sair juntos. Quando o cliente coloca um item no carrinho, ele sugere o que mais acompanhou esse item no passado.

Por exemplo, de cada 100 pedidos com Água Mineral, 42 também tinham Bowl de Frango e 23 tinham Nachos. Então, para quem pôs Água Mineral no carrinho, o Bowl de Frango aparece primeiro.

Quando o histórico não traz uma combinação suficiente, o sistema completa com os itens mais vendidos que ainda não estão no carrinho. Assim, o cliente sempre vê 3 sugestões.

| No carrinho | O sistema sugere |
|---|---|
| Água Mineral | Bowl de Frango, Nachos, Bowl de Carne |
| Burrito de Frango | Nachos com Guacamole, Refrigerante em Lata, Burrito de Carne |
| Bowl de Frango | Nachos com Guacamole, Refrigerante em Lata, Nachos |
| Nachos | Bowl de Frango, Refrigerante em Lata, Burrito de Frango |

## As sugestões funcionam?

Para testar, pegamos pedidos antigos, tiramos um item de cada um e pedimos ao sistema 3 sugestões para o que sobrou. Depois, contamos quantas vezes o item tirado estava entre as sugestões. Repetimos o teste com todos os pedidos.

| Forma de sugerir | Acertos a cada 100 carrinhos |
|---|---|
| **Sistema de sugestões** | **47** |
| Mostrar sempre os 3 itens mais vendidos | 44 |

O sistema acerta mais do que simplesmente mostrar os mais vendidos e, além disso, adapta as sugestões ao que está no carrinho. Para quem já escolheu um Burrito de Frango, por exemplo, ele não oferece um segundo prato principal, como o Bowl de Frango, e sim um acompanhamento e uma bebida.

## O que aprendemos

**A primeira versão acertava menos que os mais vendidos.** Com poucos pedidos no histórico, ela encontrava poucas combinações e deixava espaços vazios nas sugestões. Além disso, dava preferência a combinações curiosas, porém raras. Ajustamos o sistema para completar os espaços com os mais vendidos e para priorizar o que os clientes mais levam juntos.

**A vantagem ainda é pequena, por causa do tamanho do histórico.** São poucos pedidos, com poucos itens cada, e três itens dominam as vendas. Para as sugestões ficarem melhores, ajudariam:

- um histórico maior, com mais meses de pedidos;
- o número do cliente e a data de cada pedido, para personalizar as sugestões;
- um teste no site, com parte dos clientes vendo as sugestões, para medir se o ticket médio aumenta.
