# MVP de recomendação de itens — PratoTech

Projeto preparado para a entrevista a partir de um cenário fictício. Restaurantes de São Paulo pedem à PratoTech um MVP que recomende itens com base no carrinho do delivery, usando regras de associação calculadas a partir dos pedidos.

- [Proposta](docs/proposta.md): propósito, escopo, requisitos (RF, RNF e regras de negócio), critérios de avaliação, prazo e riscos.
- [Arquitetura](docs/arquitetura.md): componentes, tecnologias, organização do código e funcionamento do recomendador.

## Lojas

| Loja | Solicitação | Relatório | Pedidos | Itens | Itens por pedido |
|---|---|---|---|---|---|
| Sabor na Mesa Cozinha Mexicana | [e-mail](docs/mexicano/solicitacao-cliente.md) | [relatório](docs/mexicano/relatorio.md) | 1.834 | 45 | 2,3 |
| Casa Masala Cozinha Indiana | [e-mail](docs/indiano/solicitacao-cliente.md) | [relatório e conclusão](docs/indiano/relatorio.md) | 13.397 | 244 | 5,6 |

Cada loja tem a sua pasta em `dados/`, com o arquivo `pedidos.csv` no mesmo formato:

| Coluna | Descrição |
|---|---|
| `id_pedido` | número do pedido; as linhas com o mesmo número formam um carrinho |
| `item` | nome do item do cardápio |

Um mesmo item pode aparecer em mais de uma linha do mesmo pedido. Para as regras de associação, interessa apenas se o item está ou não no pedido, então cada pedido é tratado como um conjunto de itens.

A base da Casa Masala vem da exportação do caixa, em inglês, e não fica no repositório, porque a licença do conjunto original (“Data files © Original Authors”) não permite redistribuí-lo. Para gerá-la:

1. baixe `restaurant-1-orders.csv` do conjunto [Takeaway Food Orders](https://www.kaggle.com/datasets/henslersoftware/19560-indian-takeaway-orders), no Kaggle;
2. coloque o arquivo em `dados/indiano/`;
3. execute `python preparar_indiano.py`, que traduz os nomes com [traducao_itens.csv](dados/indiano/traducao_itens.csv) e gera `dados/indiano/pedidos.csv`.

Sem esse arquivo, os scripts avisam e executam só a loja mexicana.

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

O arquivo `avaliar.py` compara três versões do recomendador com a referência de sugerir sempre os 3 itens mais pedidos, em uma divisão única 80/20 e em uma validação cruzada de 5 dobras. Acerto no top 3 na validação cruzada:

| Versão | Sabor na Mesa | Casa Masala |
|---|---|---|
| 1: regras por lift, sem completar as vagas | 32,6% | 20,5% |
| 2: regras por lift + mais pedidos | 45,2% | 20,6% |
| **3: regras por confiança + mais pedidos (MVP)** | **47,3%** | **23,4%** |
| Referência: só mais pedidos | 43,6% | 20,2% |

Nas duas lojas, a versão 3 supera a referência. Na Casa Masala, com sete vezes mais pedidos, o ganho relativo dobra (de 8% para 16%). A explicação de cada versão e a comparação entre as lojas estão nos relatórios.

## Como executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python preparar_indiano.py   # só depois de baixar a base da Casa Masala
python analise_dados.py
python gerar_regras.py
python avaliar.py
```

No PyCharm, selecione o interpretador `.venv` do projeto e execute, nesta ordem, `preparar_indiano.py` (se tiver a base da Casa Masala), `analise_dados.py`, `gerar_regras.py` e `avaliar.py`. Cada script processa as duas lojas.
