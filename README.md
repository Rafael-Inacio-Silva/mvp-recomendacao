# MVP de recomendação de itens — PratoTech

Projeto preparado para a entrevista a partir de um cenário fictício. Restaurantes de São Paulo pedem à PratoTech um MVP que recomende itens com base no carrinho do delivery, usando regras de associação calculadas a partir dos pedidos.

- [Arquitetura](docs/arquitetura.md): componentes, tecnologias, organização do código e funcionamento do recomendador, comum às duas lojas.

## Lojas

| Loja | Solicitação | Proposta | Relatório | Pedidos | Itens | Itens por pedido |
|---|---|---|---|---|---|---|
| Sabor na Mesa Cozinha Mexicana | [e-mail](docs/mexicano/solicitacao-cliente.md) | [proposta](docs/mexicano/proposta.md) | [relatório](docs/mexicano/relatorio.md) | 1.834 | 45 | 2,3 |
| Casa Masala Cozinha Indiana | [e-mail](docs/indiano/solicitacao-cliente.md) | [proposta](docs/indiano/proposta.md) | [relatório](docs/indiano/relatorio.md) | 13.397 | 244 | 5,6 |

Cada loja tem a sua pasta em `dados/`, com o arquivo `pedidos.csv` no mesmo formato:

| Coluna | Descrição |
|---|---|
| `id_pedido` | número do pedido; as linhas com o mesmo número formam um carrinho |
| `item` | nome do item do cardápio |

Um mesmo item pode aparecer em mais de uma linha do mesmo pedido. Para as regras de associação, interessa apenas se o item está ou não no pedido, então cada pedido é tratado como um conjunto de itens.

## Pipeline de dados

Cada etapa da preparação dos dados fica em um módulo da pasta `pipeline/`, e o arquivo `analise_dados.py` executa as etapas em sequência para cada loja.

| Etapa | Módulo | O que faz |
|---|---|---|
| 1 | [etapa1_carregamento.py](pipeline/etapa1_carregamento.py) | lê `pedidos.csv` em um DataFrame e mostra tamanho, estrutura, primeiras linhas e contagens |
| 2 | [etapa2_nulos_vazios.py](pipeline/etapa2_nulos_vazios.py) | conta nulos, vazios e espaços extras; remove espaços e descarta linhas sem pedido ou sem item |
| 3 | [etapa3_duplicados.py](pipeline/etapa3_duplicados.py) | conta itens repetidos no mesmo pedido e mantém uma linha por item em cada pedido (RN-01) |
| 4 | [etapa4_outliers.py](pipeline/etapa4_outliers.py) | identifica pedidos com quantidade atípica de itens (IQR) e itens raros; remove os pedidos acima do limite superior |
| 5 | [etapa5_exploracao.py](pipeline/etapa5_exploracao.py) | mostra o resumo da base limpa e os itens e pares mais frequentes |

Ao final, a base limpa de cada loja é salva em `dados/<loja>/pedidos_limpos.csv`, que é a entrada do modelo.

## Modelo

| Módulo | O que faz |
|---|---|
| [modelo/regras.py](modelo/regras.py) | monta as cestas, calcula as regras de associação (Apriori) e compara limites de suporte e confiança |
| [modelo/recomendador.py](modelo/recomendador.py) | recebe o carrinho e devolve até 3 sugestões, ordenadas pela confiança, cada uma com a regra que a gerou; as vagas sem regra são completadas com os itens mais pedidos |
| [modelo/avaliacao.py](modelo/avaliacao.py) | separa treino e teste, esconde um item de cada pedido de teste e mede o acerto no top 3 de cada versão |

O arquivo `gerar_regras.py` compara os limites e gera as regras finais de cada loja, com suporte mínimo de 1% e confiança mínima de 10%. As regras são salvas em `dados/<loja>/regras.csv`.

## Avaliação

**Como testamos:** pegamos os pedidos antigos, tiramos um item de cada pedido e pedimos ao sistema 3 sugestões para o que sobrou. Contamos quantas vezes o item tirado estava entre as sugestões e comparamos com o jeito mais simples de sugerir: mostrar sempre os 3 itens mais vendidos.

**Acertos a cada 100 carrinhos:**

| Forma de sugerir | Sabor na Mesa | Casa Masala |
|---|---|---|
| Primeira versão: combinações mais “curiosas”, sem completar as vagas | 33 | 21 |
| Segunda versão: a primeira + mais vendidos nas vagas vazias | 45 | 21 |
| **Versão final: combinações mais frequentes + mais vendidos nas vagas** | **47** | **23** |
| Só os 3 mais vendidos | 44 | 20 |

**O que os números mostram:**

- **Sabor na Mesa:** com poucos pedidos, a primeira versão perdia para os mais vendidos, porque deixava vagas vazias e preferia combinações raras. A versão final ganha por pouco: 47 contra 44.
- **Casa Masala:** com sete vezes mais pedidos, quase todo carrinho tem combinação conhecida, e a versão final acerta 16% mais que os mais vendidos (23 contra 20). O número é menor que o do mexicano porque o cardápio tem 243 itens, contra 45.
- **Nas duas lojas,** o que fez a diferença foi priorizar o que os clientes mais levam juntos. Mais pedidos e mais variedade deixam a vantagem maior.

Os números vêm de `avaliar.py`, que também mostra uma divisão única 80/20; a validação cruzada (5 dobras) é a usada aqui. Os detalhes de cada versão estão na [arquitetura](docs/arquitetura.md#5-avaliação).

## Como executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python analise_dados.py
python gerar_regras.py
python avaliar.py
```

No PyCharm, selecione o interpretador `.venv` do projeto e execute, nesta ordem, `analise_dados.py`, `gerar_regras.py` e `avaliar.py`. Cada script processa as duas lojas.
