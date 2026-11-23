# Arquitetura — MVP de recomendação de itens

Elaborada a partir das propostas da [Sabor na Mesa](mexicano/proposta.md) e da [Casa Masala](indiano/proposta.md). O mesmo código atende mais de uma loja: cada loja tem a sua pasta de dados, e o pipeline, as regras e a avaliação são executados para todas.

## 1. Visão geral

```
pedidos.csv → pipeline de dados → pedidos_limpos.csv → cestas → regras de associação → recomendador → explicação → tela
```

| Componente | Responsabilidade | Requisitos atendidos |
|---|---|---|
| `lojas` | lista das lojas e caminho dos arquivos de cada uma | RNF-05 |
| `pipeline` | carregar `pedidos.csv`, tratar nulos, vazios, duplicados e outliers, explorar e salvar a base limpa | RF-01, RN-01, RNF-05 |
| `regras` | montar uma cesta por pedido e calcular as regras de associação com suporte, confiança e lift | RF-03, RN-04 |
| `recomendador` | escolher e ordenar as sugestões para um carrinho | RF-04, RF-05, RN-02, RN-03, RN-05, RN-06 |
| `avaliacao` | medir o acerto das versões do recomendador e da referência dos mais pedidos | RF-08 |
| `explicacao` | montar a frase de cada sugestão a partir da regra que a gerou | RF-06, RN-07, RN-08, RNF-02, RNF-03, RNF-04 |
| `app` | tela de demonstração e página “Como funciona” | RF-01, RF-02, RF-07, RF-08 |

O recomendador não depende da tela nem da explicação. Assim, ele pode ser testado sozinho, e a forma de explicar pode mudar sem afetar as sugestões.

## 2. Tecnologias

| Parte | Escolha | Motivo |
|---|---|---|
| Linguagem | Python | bibliotecas prontas para dados e regras de associação |
| Dados | pandas | leitura e agrupamento dos pedidos |
| Regras | mlxtend (Apriori) | implementação conhecida, que já calcula suporte, confiança e lift |
| Explicação | frase montada em Python | exata, instantânea e sem custo, porque usa os números da própria regra |
| Tela | Streamlit | demonstração em Python, sem front-end separado |
| Testes | pytest | testes das regras de negócio |

## 3. Organização do código

```
mvp-recomendacao/
├── dados/
│   ├── mexicano/
│   │   ├── pedidos.csv          # histórico enviado pela Sabor na Mesa
│   │   ├── pedidos_limpos.csv   # gerado pelo pipeline
│   │   └── regras.csv           # gerado por gerar_regras.py
│   └── indiano/                 # mesma estrutura, para a Casa Masala
├── docs/
│   ├── arquitetura.md
│   ├── mexicano/                # solicitação, proposta e relatório da Sabor na Mesa
│   └── indiano/                 # solicitação, proposta e relatório da Casa Masala
├── pipeline/                    # uma etapa por módulo
│   ├── etapa1_carregamento.py
│   ├── etapa2_nulos_vazios.py
│   ├── etapa3_duplicados.py
│   ├── etapa4_outliers.py
│   └── etapa5_exploracao.py
├── modelo/
│   ├── regras.py                # cestas e regras de associação
│   ├── recomendador.py          # sugestões para um carrinho
│   ├── avaliacao.py             # versões, divisões de teste e taxa de acerto
│   └── explicacao.py            # frase de cada sugestão
├── lojas.py                     # lojas e caminhos dos arquivos
├── analise_dados.py             # executa o pipeline
├── gerar_regras.py              # calcula e compara as regras
├── avaliar.py                   # executa a avaliação offline
├── app.py                       # tela em Streamlit
├── pytest.ini
└── tests/                       # testes das regras de negócio
```

## 4. Funcionamento dos componentes

### Cestas de itens

As linhas de `pedidos.csv` são agrupadas por `id_pedido`. Cada pedido vira um conjunto, então um item repetido no mesmo pedido conta uma vez só (RN-01). As cestas são convertidas em uma tabela de verdadeiro/falso (pedido × item), que é o formato esperado pelo Apriori.

### Regras de associação

O Apriori encontra os conjuntos de itens frequentes, ou seja, com suporte acima do mínimo. A partir deles, são geradas as regras A → B com confiança acima do mínimo (RN-04). Só ficam as regras em que B é um único item, e cada regra guarda suporte, confiança e lift.

Não há um valor padrão para os limites. `gerar_regras.py` compara 12 combinações pela quantidade de regras, pela cobertura dos pedidos, pela confiança média e pelo lift médio, e a escolha final veio da avaliação offline (seção 5):

- **suporte mínimo de 1%**, para que a regra tenha evidência suficiente. Na Sabor na Mesa, sem esse limite, 88% das regras viriam de apenas 1 ou 2 pedidos;
- **confiança mínima de 10%**, ou seja, pelo menos 1 em cada 10 pedidos com o antecedente também tem o consequente;
- **sem filtro de lift**. A primeira versão mantinha só as regras com lift maior que 1, mas isso deixava carrinhos sem regra e diminuía o acerto.

### Recomendador

Para um carrinho:

1. seleciona as regras cujo lado A está contido no carrinho;
2. descarta as regras cujo item B já está no carrinho (RN-02);
3. ordena por confiança e, em caso de empate, por lift (RN-05);
4. quando um mesmo item B vem de mais de uma regra, mantém a de maior confiança;
5. devolve até 3 sugestões (RN-03);
6. se sobrarem menos de 3, completa as vagas com os itens mais pedidos que não estão no carrinho (RN-06).

As regras ficam em uma lista, com o antecedente como conjunto de itens, para que a busca seja rápida mesmo com centenas de regras. Cada sugestão carrega a regra que a gerou, para que a explicação e a página “Como funciona” possam mostrá-la. Os parâmetros `criterio="lift"` e `completar=False` reproduzem as primeiras versões, usadas só na avaliação.

### Explicação

A frase de cada sugestão é montada com os dados da regra que a gerou (RN-07). A confiança vira uma contagem fácil de entender: confiança de 0,42 para a regra Água Mineral → Bowl de Frango vira “42 de cada 100 pedidos com Água Mineral também têm Bowl de Frango”. Quando a regra tem mais de um item no lado A, os itens são citados juntos (“Bowl de Frango e Água Mineral”). As sugestões que vêm dos mais vendidos recebem a frase “Um dos itens mais pedidos da casa” (RN-08).

A explicação não usa modelo de linguagem: como a frase só repete números que o sistema já calculou, um modelo de linguagem acrescentaria custo, demora e risco de citar algo fora da regra, sem acrescentar informação.

## 5. Avaliação

1. As regras e os mais pedidos são calculados só com os pedidos de treino.
2. Em cada pedido de teste com dois itens ou mais, cada item é escondido uma vez, e os demais formam o carrinho.
3. A taxa de acerto no top 3 (Hit Rate@3) é a parte dos casos em que o item escondido aparece entre as sugestões.
4. São comparadas três versões do recomendador e a referência de sugerir sempre os 3 itens mais pedidos.
5. A avaliação é feita em duas formas, ambas com semente fixa: uma divisão única (80% treino, 20% teste) e uma validação cruzada de 5 dobras, em que todos os pedidos passam pelo teste uma vez.

| Versão | Limites | Ordenação | Vagas sem regra |
|---|---|---|---|
| 1 | confiança 20%, lift > 1 | lift | vazias |
| 2 | confiança 20%, lift > 1 | lift | mais pedidos |
| 3 (MVP) | confiança 10%, sem filtro de lift | confiança | mais pedidos |

`avaliar.py` salva o resultado de cada loja em `dados/<loja>/avaliacao.csv`, que a página “Como funciona” lê sem precisar repetir a avaliação.

Os resultados de cada loja estão nos relatórios: [Sabor na Mesa](mexicano/relatorio.md) e [Casa Masala](indiano/relatorio.md).

## 6. Testes

Os testes usam pytest (`python -m pytest`) e regras pequenas montadas no próprio teste, para não depender dos dados das lojas. A exceção é o teste do tamanho das frases, que confere todas as regras geradas de cada loja.

| Arquivo | Teste | Regra verificada |
|---|---|---|
| `test_dados_e_avaliacao.py` | item repetido no mesmo pedido conta uma vez | RN-01 |
| `test_dados_e_avaliacao.py` | cada item de um pedido de teste é escondido uma vez; nenhum pedido fica no treino e no teste | avaliação |
| `test_recomendador.py` | item do carrinho nunca aparece nas sugestões | RN-02 |
| `test_recomendador.py` | no máximo 3 sugestões | RN-03 |
| `test_recomendador.py` | sugestões em ordem de confiança, com desempate pelo lift; cada item sugerido uma vez | RN-05 |
| `test_recomendador.py` | vagas sem regra são completadas com os mais pedidos | RN-06 |
| `test_explicacao.py` | frase montada com a confiança e os itens da regra | RN-07 |
| `test_explicacao.py` | sugestão dos mais vendidos recebe a frase dos mais pedidos | RN-08 |
| `test_explicacao.py` | todas as frases das regras reais têm até 20 palavras | RNF-04 |
