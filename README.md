# MVP de recomendação de itens — Sabor na Mesa

Projeto preparado para a entrevista a partir de um cenário fictício. A Sabor na Mesa, um restaurante de culinária mexicana em São Paulo, pede à PratoTech um MVP que recomende itens com base no carrinho do delivery, usando regras de associação calculadas a partir dos pedidos.

- [Solicitação do cliente](docs/solicitacao-cliente.md): e-mail com o escopo do MVP.
- [Proposta](docs/proposta.md): propósito, escopo, requisitos (RF, RNF e regras de negócio), critérios de avaliação, prazo e riscos.
- [Arquitetura](docs/arquitetura.md): componentes, tecnologias, organização do código e funcionamento do recomendador.

## Dados

[pedidos.csv](dados/pedidos.csv) é o histórico de pedidos enviado pelo restaurante: 4.622 linhas, 1.834 pedidos e 45 itens distintos.

| Coluna | Descrição |
|---|---|
| `id_pedido` | número do pedido; as linhas com o mesmo número formam um carrinho |
| `item` | nome do item do cardápio |

Um mesmo item pode aparecer em mais de uma linha do mesmo pedido. Para as regras de associação, interessa apenas se o item está ou não no pedido, então cada pedido é tratado como um conjunto de itens.

## Pipeline de dados

Cada etapa da preparação dos dados fica em um módulo da pasta `pipeline/`, e o arquivo `analise_dados.py` executa as etapas em sequência.

| Etapa | Módulo | O que faz |
|---|---|---|
| 1 | [etapa1_carregamento.py](pipeline/etapa1_carregamento.py) | lê `pedidos.csv` em um DataFrame e mostra tamanho, estrutura, primeiras linhas e contagens |
| 2 | [etapa2_nulos_vazios.py](pipeline/etapa2_nulos_vazios.py) | conta nulos, vazios e espaços extras; remove espaços e descarta linhas sem pedido ou sem item |
| 3 | [etapa3_duplicados.py](pipeline/etapa3_duplicados.py) | conta itens repetidos no mesmo pedido e mantém uma linha por item em cada pedido (RN-01) |
| 4 | [etapa4_outliers.py](pipeline/etapa4_outliers.py) | identifica pedidos com quantidade atípica de itens (IQR) e itens raros; remove os pedidos acima do limite superior |

## Como executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python analise_dados.py
```

No PyCharm, selecione o interpretador `.venv` do projeto e execute `analise_dados.py`.
