# Relatório — Casa Masala Cozinha Indiana

Olá, Rodrigo! Este relatório mostra os dados que usamos, como o sistema escolhe as sugestões e se elas funcionam com os pedidos da Casa Masala. Os detalhes técnicos estão na [proposta](proposta.md) e na [arquitetura](../arquitetura.md).

## Os dados que usamos

Usamos só o histórico que você enviou: o número de cada pedido e os itens que ele tinha. Não usamos dados dos clientes, preços nem datas.

| | |
|---|---|
| Pedidos analisados | 13.006 |
| Itens no cardápio | 243 |
| Itens por pedido, em média | 5,3 |
| Item mais pedido | Arroz Pilau, presente em 1 de cada 3 pedidos |

Antes de começar, deixamos de fora 391 pedidos com 12 itens ou mais. Eles costumam ser pedidos de grupo e misturam escolhas de várias pessoas. Um item pedido duas vezes no mesmo pedido contou uma vez só.

## Como o sistema escolhe as sugestões

O sistema olha os pedidos antigos e aprende quais itens costumam sair juntos. Quando o cliente coloca um item no carrinho, ele sugere o que mais acompanhou esse item no passado.

Por exemplo, de cada 100 pedidos com Frango Tikka Masala, 52 também tinham Arroz Pilau e 39 tinham Naan Simples. Então, para quem pôs Frango Tikka Masala no carrinho, o Arroz Pilau aparece primeiro.

Quando o histórico não traz uma combinação suficiente, o sistema completa com os itens mais vendidos que ainda não estão no carrinho. Assim, o cliente sempre vê 3 sugestões.

| No carrinho | O sistema sugere |
|---|---|
| Frango Tikka Masala | Arroz Pilau, Naan Simples, Papadum Simples |
| Korma de Frango | Arroz Pilau, Naan Simples, Papadum Simples |
| Papadum Simples | Arroz Pilau, Chutney de Manga, Naan Simples |
| Naan de Alho | Arroz Pilau, Papadum Simples, Frango Tikka Masala |

## As sugestões funcionam?

Para testar, pegamos pedidos antigos, tiramos um item de cada um e pedimos ao sistema 3 sugestões para o que sobrou. Depois, contamos quantas vezes o item tirado estava entre as sugestões. Repetimos o teste com todos os pedidos.

| Forma de sugerir | Acertos a cada 100 carrinhos |
|---|---|
| **Sistema de sugestões** | **23** |
| Mostrar sempre os 3 itens mais vendidos | 20 |

O sistema acerta 16% mais do que simplesmente mostrar os mais vendidos. O número parece baixo porque o cardápio tem 243 itens: acertar exatamente o item que o cliente vai pedir, entre tantas opções, é difícil. O que importa é a comparação. Além disso, as sugestões combinam com o carrinho: quem pede papadum recebe chutney de manga, que os mais vendidos não mostrariam.

## Conclusão

**O histórico da Casa Masala é muito bom para sugestões.** São muitos pedidos, com vários itens cada, e a refeição costuma seguir um padrão (curry, arroz, pão e entrada). O sistema encontrou combinações para 95% dos carrinhos testados.

Para os próximos passos, sugerimos:

- um teste no site, com parte dos clientes vendo as sugestões, para medir se o ticket médio aumenta;
- o número do cliente e a data de cada pedido, para personalizar as sugestões;
- atualizar as sugestões periodicamente com os pedidos novos.
