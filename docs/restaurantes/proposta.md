# Proposta — MVP de recomendação de restaurantes

**Cliente:** Garfo Certo
**Fornecedor:** PratoTech
**Referência:** [solicitação de 24/11/2026](solicitacao-cliente.md)
**Resultado:** [relatório do MVP](relatorio.md)

## 1. Propósito

Este documento apresenta a proposta da PratoTech para o MVP de recomendação de restaurantes do Garfo Certo. Depois que a pessoa escolhe a cidade e a culinária, o sistema mostra os 10 restaurantes mais indicados, equilibrando o que ela procura, a avaliação, o frete e o tempo de entrega.

O objetivo de negócio é reduzir as desistências na escolha do restaurante e o tempo até o pedido.

## 2. Escopo

**O sistema faz:**

- lista as cidades atendidas e as culinárias de cada uma;
- recebe a cidade, a culinária (opcional) e um texto livre com o que a pessoa procura (opcional);
- mostra os 10 restaurantes recomendados, com nota, frete, tempo de entrega e faixa de preço;
- explica cada recomendação em uma frase curta;
- permite ajustar o peso de cada critério.

**O sistema não faz:**

- recomendação personalizada pelo histórico de cada cliente;
- uso da localização real do cliente ou do horário de funcionamento dos restaurantes;
- integração com o aplicativo, o pagamento ou a entrega;
- publicação em produção.

## 3. Descrição do sistema

O Garfo Certo enviou o catálogo `restaurants.csv`, com 406.399 restaurantes de 1.478 cidades. O MVP usa as três capitais atendidas:

| Indicador | Valor |
|---|---|
| Restaurantes nas três capitais | 57.416 (São Paulo 31.608, Rio de Janeiro 14.609, Belo Horizonte 11.199) |
| Culinárias | 60 (as mais comuns: Lanches, Brasileira, Doces & Bolos, Pizza e Japonesa) |
| Restaurantes sem avaliação | 43,1% (aparecem com nota 0) |
| Nota dos avaliados | média 4,51 e mediana 4,67, de 1 a 5 |
| Frete | mediana de R$ 7,00; 10% com frete grátis; 95% até R$ 15,49 |
| Tempo de entrega | mediana de 46 minutos; 95% até 70 minutos |
| Mesmo nome na mesma cidade | 2.023 restaurantes (unidades de redes) |

A primeira leitura também mostrou dados que precisam de tratamento antes do uso:

- **Nota 0 significa “sem avaliação”**, e não nota ruim. Tratar como nota ruim puniria quase metade dos restaurantes, em geral os mais novos.
- **Valores impossíveis:** 10 tempos de entrega iguais ou menores que zero, 23 acima de 2 horas e 10 pedidos mínimos acima de R$ 500 (o maior é R$ 99.999.999,99).
- **A distância foi medida a partir de um endereço fixo**, e não da casa de cada cliente. Por isso, ela não entra na recomendação.
- **As etiquetas são códigos internos de campanhas**, como `CPGN_1811_BLK_NOV`. Só três viram texto útil: pratos vegetarianos, comida saudável e “bom e barato”.

A partir do catálogo tratado, o sistema dá a cada restaurante quatro notas de 0 a 1 e as soma com pesos:

| Critério | Como é calculado |
|---|---|
| Conteúdo | semelhança entre o texto livre da pessoa e o texto do restaurante (nome, culinária, faixa de preço e etiquetas), com TF-IDF e cosseno; a culinária escolhida já é um filtro |
| Avaliação | nota do restaurante dividida por 5; sem avaliação, a nota do primeiro quartil da cidade |
| Frete | quanto mais barato, melhor: R$ 0 vale 1 e R$ 15 ou mais vale 0 |
| Entrega | quanto mais rápido, melhor: 20 minutos ou menos vale 1 e 70 minutos ou mais vale 0 |

Cada recomendação vem com uma frase montada a partir dos dados, por exemplo: “Nota 4,9, frete grátis e entrega em cerca de 30 minutos”.

## 4. Requisitos funcionais

| RF | Descrição | Prioridade |
|---|---|---|
| RF-R01 | O sistema deve listar as cidades atendidas e as culinárias de cada cidade. | Alta |
| RF-R02 | O sistema deve recomendar até 10 restaurantes para a cidade e a culinária escolhidas. | Alta |
| RF-R03 | O sistema deve considerar o texto livre da pessoa na recomendação, quando informado. | Alta |
| RF-R04 | O sistema deve combinar conteúdo, avaliação, frete e tempo de entrega com pesos ajustáveis. | Alta |
| RF-R05 | O sistema deve mostrar, para cada restaurante, a nota, o frete, o tempo de entrega e a faixa de preço. | Alta |
| RF-R06 | O sistema deve apresentar uma explicação para cada recomendação. | Alta |

## 5. Requisitos não funcionais

| RNF | Tipo | Descrição |
|---|---|---|
| RNF-R01 | Desempenho | A recomendação deve sair em até 1 segundo, na demonstração executada localmente. |
| RNF-R02 | Confiabilidade | A recomendação não depende de serviços de IA externos: o cálculo é feito no próprio sistema. |
| RNF-R03 | Manutenibilidade | O catálogo tratado deve poder ser gerado de novo a partir de um arquivo no mesmo formato, sem alterar o sistema. |
| RNF-R04 | Manutenibilidade | As regras de negócio RN-R01 a RN-R07 devem ter testes automatizados. |
| RNF-R05 | Privacidade | O catálogo publicado não traz links, logotipos, formas de pagamento nem códigos internos das campanhas. |

## 6. Regras de negócio

| RN | Descrição | RF relacionado |
|---|---|---|
| RN-R01 | Só entram restaurantes da cidade escolhida, identificada pelo código IBGE. | RF-R02 |
| RN-R02 | Quando a culinária é informada, só entram restaurantes dessa culinária. | RF-R02 |
| RN-R03 | Restaurante sem avaliação entra com a nota do primeiro quartil da cidade (cerca de 4,3) e aparece como “sem avaliação”. Assim, ele não vai para o fim da lista, mas também não passa na frente de quem já foi bem avaliado. | RF-R04 |
| RN-R04 | Os pesos padrão são: conteúdo 40%, avaliação 30%, frete 15% e entrega 15%. Pesos enviados pela pessoa são normalizados para somar 100%, e o critério não enviado vale 0. Sem texto livre, o conteúdo não diferencia os restaurantes, e o peso dele é dividido entre os outros critérios. | RF-R04 |
| RN-R05 | Restaurantes com o mesmo nome na mesma cidade aparecem uma vez só, a unidade com a maior pontuação. | RF-R02 |
| RN-R06 | São exibidos no máximo 10 restaurantes, da maior para a menor pontuação. Em caso de empate, vem primeiro o de maior nota. | RF-R02 |
| RN-R07 | A entrada é validada antes da recomendação: cidade atendida, culinária existente na cidade, texto de até 200 caracteres e pesos numéricos, finitos e não negativos, com pelo menos um maior que zero. Uma entrada inválida recebe a lista de erros, sem recomendações. | RF-R01, RF-R04 |
| RN-R08 | A explicação é montada a partir dos dados do restaurante: nota (ou “sem avaliação”), frete e tempo de entrega e, quando o texto livre ajudou na escolha, a menção ao que a pessoa procurou. | RF-R06 |

## 7. Abordagem

É uma **recomendação baseada em conteúdo combinada com critérios de qualidade e conveniência** (sistema híbrido com pesos).

- **Conteúdo (TF-IDF e cosseno).** O texto de cada restaurante (nome, culinária, faixa de preço e etiquetas úteis) vira um vetor em que cada palavra pesa mais quanto mais rara ela é na cidade. O que a pessoa procura vira um vetor do mesmo jeito, e o cosseno entre os dois mede a semelhança. Assim, “sushi” favorece restaurantes com “sushi” no nome, e “vegetariano” favorece os que têm pratos vegetarianos.
- **Avaliação, frete e entrega.** Cada um vira uma nota de 0 a 1 em escala fixa, para que um restaurante tenha a mesma nota de frete em qualquer busca.
- **Pontuação final.** É a soma das quatro notas, cada uma multiplicada pelo seu peso.

**Por que essa abordagem.** O catálogo não tem o histórico de pedidos por cliente, então ainda não dá para usar filtragem colaborativa (“quem pediu aqui também pediu ali”). A recomendação por conteúdo funciona sem histórico, é explicável e fica pronta para receber o histórico numa próxima fase.

Os detalhes de construção estão no documento de [arquitetura](../arquitetura.md).

## 8. Critérios de avaliação

O catálogo não registra quais restaurantes as pessoas escolheram, então não existe um “acerto” para medir antes de publicar. A avaliação offline compara o sistema híbrido com formas simples de ordenar, em buscas de exemplo nas três cidades:

- **Qualidade e conveniência do top 10:** nota média, parte sem avaliação, frete médio e tempo médio, comparados com ordenar só pela nota, só pelo frete e só pelo tempo.
- **Aderência ao texto:** para buscas como “sushi” ou “vegetariano”, quantos dos 10 restaurantes têm o termo no nome ou nas etiquetas.
- **Efeito dos pesos:** quanto o top 10 muda quando cada peso é aumentado.

**Depois de publicar (fase futura).** Taxa de clique na lista, taxa de pedido a partir da recomendação e tempo até o pedido, com teste A/B contra a lista atual.

## 9. Prazo estimado

Uma semana e meia (8 dias úteis):

| Etapa | Dias | Resultado para o Garfo Certo |
|---|---|---|
| Análise e tratamento do catálogo | 2 | catálogo das três capitais tratado |
| Pontuação e recomendação | 2 | top 10 funcionando para qualquer busca |
| Avaliação offline | 1 | comparação com as ordenações simples |
| API e explicações | 1 | rota de recomendação com frase para cada restaurante |
| Tela de demonstração | 1 | escolha da cidade, da culinária e dos pesos |
| Revisão com o cliente | 1 | ajustes e apresentação final |

## 10. Riscos

| Risco | Como tratar |
|---|---|
| Quase metade dos restaurantes sem avaliação | nota mediana da cidade (RN-R03) e indicação “sem avaliação” na tela |
| Nota 5,0 de restaurante com poucas avaliações | o catálogo não traz o número de avaliações; a nota pesa 30% e divide espaço com frete e tempo; pedir esse dado para a próxima fase |
| Catálogo de fevereiro de 2021 | o MVP demonstra o método; a recomendação real usaria o catálogo atualizado, no mesmo formato (RNF-R03) |
| Redes com várias unidades ocupando a lista | uma unidade por nome em cada cidade (RN-R05) |
| Texto livre sem relação com o catálogo | o conteúdo fica zerado e a ordem segue avaliação, frete e entrega |

## 11. Próximas fases

- Filtragem colaborativa a partir do histórico de pedidos de cada cliente.
- Distância real até o endereço do cliente e horário de funcionamento.
- Número de avaliações, para dar menos peso a notas com poucos votos.
- Teste A/B no aplicativo, medindo cliques e pedidos.
