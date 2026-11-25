# Relatório — Garfo Certo

Olá, Lucas! Este relatório mostra os dados que usamos, como o sistema monta o top 10 e o que a avaliação mostrou. Os detalhes técnicos estão na [proposta](proposta.md) e na [arquitetura](../arquitetura.md).

## Os dados que usamos

Usamos o catálogo que você enviou, só com as três capitais atendidas e só com as colunas necessárias. Links, logotipos, formas de pagamento e códigos internos de campanha ficaram de fora.

| | Belo Horizonte | São Paulo | Rio de Janeiro |
|---|---|---|---|
| Restaurantes | 11.194 | 31.590 | 14.598 |
| Sem avaliação | 48,8% | 41,0% | 43,2% |
| Nota mediana dos avaliados | 4,67 | 4,68 | 4,65 |
| Frete mediano | R$ 7,49 | R$ 8,00 | R$ 5,99 |
| Tempo mediano de entrega | 47 min | 45 min | 45 min |

Antes de usar o catálogo, fizemos quatro ajustes:

- **nota 0 virou “sem avaliação”**, porque o catálogo usa o zero para quem ainda não foi avaliado;
- **33 restaurantes saíram** por terem tempo de entrega impossível (zero, negativo ou acima de 2 horas);
- **10 pedidos mínimos absurdos**, como R$ 99.999.999,99, deixaram de ser exibidos;
- **a distância ficou de fora**, porque foi medida a partir de um endereço fixo, e não da casa de cada cliente.

## Como o sistema monta o top 10

A pessoa escolhe a cidade e, se quiser, a culinária e um texto livre, como “sushi” ou “vegetariano”. Cada restaurante recebe quatro notas de 0 a 1:

- **conteúdo:** o quanto o restaurante combina com o texto livre;
- **avaliação:** a nota do restaurante;
- **frete:** quanto mais barato, melhor;
- **entrega:** quanto mais rápida, melhor.

A pontuação final soma as quatro notas com pesos. Os pesos padrão são 40% para o conteúdo, 30% para a avaliação e 15% para cada um dos outros. Quando não há texto livre, o peso do conteúdo é dividido entre os outros três.

Cada restaurante aparece com uma frase que explica a escolha. Exemplos em Belo Horizonte:

| Busca | 1º lugar |
|---|---|
| Japonesa | Art Sushi — sem avaliação · frete grátis · entrega em cerca de 30 min |
| Japonesa + “sushi” | Art Sushi — sem avaliação · frete grátis · entrega em cerca de 30 min · combina com “sushi” |
| Pizza | Bellita Pizzaria — nota 4,8 · frete grátis · entrega em cerca de 20 min |

## A recomendação funciona?

O catálogo não diz quais restaurantes as pessoas escolheram, então não dá para medir “acerto” antes de publicar. Por isso, comparamos o top 10 do sistema com a lista atual do aplicativo, em ordem alfabética, e com ordenações por um critério só. Usamos as 5 culinárias mais comuns de cada cidade, 15 buscas ao todo.

| Forma de ordenar | Nota média | Sem avaliação | Frete médio | Tempo médio |
|---|---|---|---|---|
| Ordem alfabética (lista atual) | 4,47 | 45% | R$ 7,60 | 47 min |
| Só a nota | 5,00 | 0% | R$ 8,00 | 45 min |
| Só o frete | 4,94 | 2% | R$ 0,00 | 42 min |
| Só o tempo | 4,83 | 2% | R$ 4,45 | 19 min |
| **Sistema de recomendação** | **4,83** | **8%** | **R$ 0,32** | **23 min** |

Comparado com a lista atual, o top 10 do sistema tem nota maior (4,83 contra 4,47), frete quase sempre grátis (R$ 0,32 contra R$ 7,60) e entrega na metade do tempo (23 contra 47 minutos). Ordenar por um critério só melhora esse critério e piora os outros. “Só a nota”, por exemplo, traz frete de R$ 8,00 e entrega de 45 minutos.

**O texto livre funciona.** Em 8 buscas como “sushi”, “vegetariano” e “poke”, 87% do top 10 combina com o que foi escrito, contra 5% quando a ordem é só pela nota. Os termos que ficaram abaixo de 100% são raros em algumas cidades: Belo Horizonte não tem nenhum restaurante com “temaki”, e o Rio tem 5. Nesses casos, o sistema mostra os que combinam e completa com os melhores da cidade.

**Os pesos mudam a lista na medida certa.** Ao dobrar o peso da avaliação, 3 dos 10 restaurantes mudam. Ao dobrar o da entrega, 2 ou 3 mudam. Ao dobrar o do frete, quase nada muda, porque o top 10 já é quase todo de frete grátis.

## O que aprendemos

**A primeira versão tinha dois problemas**, encontrados ao conferir as listas antes da avaliação.

1. **Premiava quem repete a culinária no nome.** Na busca por “Japonesa”, ela comparava a palavra “Japonesa” com o texto de cada restaurante, e “Yama Gastronomia Japonesa” ganhava pontos só pelo nome. Como a culinária já é um filtro, o conteúdo passou a comparar só o texto livre.
2. **Colocava restaurantes sem avaliação na frente dos bem avaliados.** Eles recebiam a nota mediana da cidade, 4,67, que é alta porque a maioria das notas é boa. Passaram a receber a nota do primeiro quartil, cerca de 4,3.

**Os limites desta versão** vêm do catálogo:

- não há histórico de pedidos por cliente, então a recomendação ainda não é personalizada;
- não há o número de avaliações, então uma nota 5,0 com poucos votos pesa o mesmo que uma 5,0 com milhares;
- o catálogo é de fevereiro de 2021; a versão real usaria o catálogo atual, no mesmo formato.

Para as próximas fases, ajudariam o histórico de pedidos de cada cliente, a localização dele e um teste no aplicativo comparando a lista atual com a recomendação.
