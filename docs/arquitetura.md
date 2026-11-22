# Arquitetura — MVP de recomendação de itens

Versão inicial, elaborada a partir da [proposta](proposta.md). Os limites das regras e alguns detalhes serão definidos depois da análise exploratória dos dados.

## 1. Visão geral

```
pedidos.csv → pipeline de dados → pedidos_limpos.csv → cestas → regras de associação → recomendador → explicação → tela
```

| Componente | Responsabilidade | Requisitos atendidos |
|---|---|---|
| `pipeline` | carregar `pedidos.csv`, tratar nulos, vazios, duplicados e outliers, explorar e salvar a base limpa | RF-01, RN-01, RNF-05 |
| `regras` | montar uma cesta por pedido e calcular as regras de associação com suporte, confiança e lift | RF-03, RN-04 |
| `recomendador` | escolher e ordenar as sugestões para um carrinho | RF-04, RF-05, RN-02, RN-03, RN-05, RN-06 |
| `explicacao` | gerar a frase de cada sugestão, com IA ou frase padrão | RF-06, RN-07, RN-08, RNF-02, RNF-03, RNF-04 |
| `app` | tela de demonstração e página “Como funciona” | RF-01, RF-02, RF-07, RF-08 |

O recomendador não depende da tela nem da explicação. Assim, ele pode ser testado sozinho, e a forma de explicar pode mudar sem afetar as sugestões.

## 2. Tecnologias

| Parte | Escolha | Motivo |
|---|---|---|
| Linguagem | Python | bibliotecas prontas para dados e regras de associação |
| Dados | pandas | leitura e agrupamento dos pedidos |
| Regras | mlxtend (Apriori) | implementação conhecida, que já calcula suporte, confiança e lift |
| Explicação | API de modelo de linguagem | texto natural; a frase padrão garante o funcionamento sem a API |
| Tela | Streamlit | demonstração em Python, sem front-end separado |
| Testes | pytest | testes das regras de negócio |

## 3. Organização do código

```
mvp-recomendacao/
├── dados/
│   ├── pedidos.csv              # histórico enviado pelo restaurante
│   └── pedidos_limpos.csv       # gerado pelo pipeline
├── pipeline/                    # uma etapa por módulo
│   ├── etapa1_carregamento.py
│   ├── etapa2_nulos_vazios.py
│   ├── etapa3_duplicados.py
│   ├── etapa4_outliers.py
│   └── etapa5_exploracao.py
├── modelo/
│   ├── regras.py                # cestas e regras de associação
│   ├── recomendador.py          # sugestões para um carrinho
│   └── explicacao.py            # frase da IA e frase padrão
├── analise_dados.py             # executa o pipeline
├── gerar_regras.py              # calcula e compara as regras
├── app.py                       # tela em Streamlit
└── tests/
```

## 4. Funcionamento dos componentes

### Cestas de itens

As linhas de `pedidos.csv` são agrupadas por `id_pedido`. Cada pedido vira um conjunto, então um item repetido no mesmo pedido conta uma vez só (RN-01). As cestas são convertidas em uma tabela de verdadeiro/falso (pedido × item), que é o formato esperado pelo Apriori.

### Regras de associação

O Apriori encontra os conjuntos de itens frequentes, ou seja, com suporte acima do mínimo. A partir deles, são geradas as regras A → B com confiança acima do mínimo (RN-04). Cada regra guarda suporte, confiança e lift.

Os dois limites serão escolhidos na análise exploratória, observando a quantidade de regras e a cobertura dos carrinhos. Como a base tem 1.834 pedidos, um suporte mínimo muito alto deixaria de fora os itens menos pedidos, e um muito baixo aceitaria combinações que aconteceram poucas vezes.

### Recomendador

Para um carrinho:

1. seleciona as regras cujo lado A está contido no carrinho;
2. descarta as regras cujo item B já está no carrinho (RN-02);
3. quando um mesmo item B vem de mais de uma regra, mantém a regra com maior lift;
4. ordena por lift e, em caso de empate, por confiança (RN-05);
5. devolve até 3 sugestões (RN-03);
6. se não sobrar nenhuma, devolve os itens mais pedidos que não estão no carrinho (RN-06).

Cada sugestão carrega a regra que a gerou, para que a explicação e a página “Como funciona” possam mostrá-la.

### Explicação

O modelo de linguagem recebe apenas os nomes dos itens A e B e as métricas da regra, e é instruído a escrever uma frase de até 20 palavras em português. Depois da resposta, o sistema confere se a frase cita os dois itens e respeita o tamanho (RN-07, RNF-04). Se a frase não passar na conferência, se a chamada falhar ou se demorar mais de 5 segundos, é usada a frase padrão (RN-08, RNF-02).

As frases já geradas ficam guardadas em memória durante a execução, para não repetir a chamada para a mesma regra.

## 5. Avaliação

1. Os pedidos são divididos em 80% para treino e 20% para teste, com semente fixa para que o resultado possa ser reproduzido.
2. As regras são calculadas só com os pedidos de treino.
3. Em cada pedido de teste com dois itens ou mais, cada item é escondido uma vez, e os demais formam o carrinho.
4. São calculadas a taxa de acerto no top 3 (Hit Rate@3), a cobertura e o lift médio das sugestões.
5. A mesma taxa de acerto é calculada para a referência dos 3 itens mais pedidos.

## 6. Testes planejados

| Teste | Regra verificada |
|---|---|
| item repetido no mesmo pedido conta uma vez | RN-01 |
| item do carrinho nunca aparece nas sugestões | RN-02 |
| no máximo 3 sugestões | RN-03 |
| sugestões em ordem de lift, com desempate pela confiança | RN-05 |
| carrinho sem regra aplicável recebe os mais pedidos | RN-06 |
| falha da IA resulta na frase padrão | RN-08 |
