# Arquitetura — MVP de recomendação de itens

Elaborada a partir das propostas da [Sabor na Mesa](mexicano/proposta.md) e da [Casa Masala](indiano/proposta.md). O mesmo código atende mais de uma loja: cada loja tem a sua pasta de dados, e o pipeline, as regras e a avaliação são executados para todas. O backend (a API em FastAPI) fica no Render, e o site, na Vercel.

## 1. Visão geral

**Preparação** (roda a cada atualização do backend):

```
pedidos.csv → pipeline (etapas 1 a 5) → pedidos_limpos.csv → gerar_regras.py → regras.csv
                     └─ etapa 6 (LLM, só para itens novos) → cardapio.csv
```

**Uso** (a cada ação do cliente no site):

```
site (Vercel) → API (Render) → validação → recomendador → explicação → sugestões com a frase
site (Vercel) → API (Render) → assistente: orquestrador → especialistas → resposta do chat
```

| Componente | Responsabilidade | Requisitos atendidos |
|---|---|---|
| `lojas` | lista das lojas e caminho dos arquivos de cada uma | RNF-05 |
| `pipeline` | carregar `pedidos.csv`, tratar nulos, vazios, duplicados e outliers, explorar, salvar a base limpa e gerar o cardápio com artigos (etapa 6) | RF-01, RN-01, RNF-05 |
| `regras` | montar uma cesta por pedido e calcular as regras de associação com suporte, confiança e lift | RF-03, RN-04 |
| `validacao` | conferir e normalizar o carrinho antes da recomendação, com um código para cada erro | RF-02, RN-01, RN-09 |
| `recomendador` | escolher e ordenar as sugestões para um carrinho | RF-04, RF-05, RN-02, RN-03, RN-05, RN-06 |
| `avaliacao` | medir o acerto das versões do recomendador e da referência dos mais pedidos | critérios de avaliação |
| `explicacao` | montar a frase de cada sugestão a partir da regra que a gerou | RF-06, RN-07, RN-08, RNF-02, RNF-04 |
| `dados_loja` | carregar uma vez os arquivos de cada loja e mantê-los em memória | RNF-01 |
| `agente` | assistente de conversa: orquestrador, especialistas, ferramentas e prompts | RF-07, RF-08, RN-10, RN-11, RNF-03 |
| `api` | rotas que o site chama: cardápio, sugestões e chat | RF-01, RF-02, RF-04, RF-06, RF-07, RF-08 |
| site | página “Monte seu pedido” e chat, na Vercel (próxima etapa) | RF-01, RF-02, RF-07 |

O recomendador não depende do site, da explicação nem do assistente. Assim, ele pode ser testado sozinho, e a forma de explicar pode mudar sem afetar as sugestões.

## 2. Tecnologias

| Parte | Escolha | Motivo |
|---|---|---|
| Linguagem | Python | bibliotecas prontas para dados e regras de associação |
| Dados | pandas | leitura e agrupamento dos pedidos |
| Regras | mlxtend (Apriori) | implementação conhecida, que já calcula suporte, confiança e lift |
| Explicação | frase montada em Python | exata, instantânea e sem custo, porque só cita itens da própria regra |
| Artigos do cardápio | OpenAI `gpt-6-luna` (Responses API, saída em JSON) | tarefa de linguagem; roda uma vez no pipeline e o resultado fica salvo |
| Assistente de conversa | OpenAI `gpt-6-luna` (Responses API, function calling) | entende a pergunta e escreve a resposta; os fatos vêm das ferramentas |
| API | FastAPI e uvicorn, no Render (plano gratuito) | rotas em Python sobre o código que já existe; o Render atualiza a cada envio ao GitHub |
| Site | React e Vite, na Vercel | interface separada do backend; a Vercel repassa as chamadas `/api` ao Render |
| Testes | pytest | testes das regras de negócio, das ferramentas e da API |

## 3. Organização do código

```
mvp-recomendacao/
├── dados/
│   ├── mexicano/
│   │   ├── pedidos.csv          # histórico enviado pela Sabor na Mesa
│   │   ├── pedidos_limpos.csv   # gerado pelo pipeline
│   │   ├── cardapio.csv         # gerado pela etapa 6 (LLM)
│   │   ├── gabarito_cardapio.csv  # conferência manual dos artigos
│   │   ├── loja.md              # dados da empresa, enviados pelo restaurante
│   │   ├── produtos.csv         # descrição de cada produto, enviada pelo restaurante
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
│   ├── etapa5_exploracao.py
│   └── etapa6_cardapio.py
├── modelo/
│   ├── regras.py                # cestas e regras de associação
│   ├── validacao.py             # validação do carrinho
│   ├── recomendador.py          # sugestões para um carrinho
│   ├── avaliacao.py             # versões, divisões de teste e taxa de acerto
│   └── explicacao.py            # frase de cada sugestão
├── agente/                      # assistente de conversa
│   ├── orquestrador.py          # conversa, histórico e escolha do especialista
│   ├── especialista.py          # agente especialista com a sua ferramenta
│   ├── ferramentas.py           # funções que consultam os dados da loja
│   ├── prompts.py               # montagem das instruções de cada agente
│   ├── llm.py                   # conexão com a OpenAI
│   └── prompts/                 # um prompt por agente, em Markdown
│       ├── orquestrador/        # persona.md e diretrizes.md
│       ├── cardapio/            # prompt.md
│       ├── combinacoes/         # prompt.md
│       └── loja/                # prompt.md
├── api.py                       # API em FastAPI
├── dados_loja.py                # arquivos de cada loja em memória
├── lojas.py                     # lojas, assistentes e caminhos dos arquivos
├── analise_dados.py             # executa o pipeline
├── gerar_regras.py              # calcula e compara as regras
├── avaliar.py                   # executa a avaliação offline
├── avaliar_cardapio.py          # compara os artigos do LLM com o gabarito
├── .env.example                 # variáveis da OpenAI, sem a chave
├── pytest.ini
└── tests/                       # testes das regras de negócio, das ferramentas e da API
```

## 4. Funcionamento dos componentes

### Cestas de itens

As linhas de `pedidos.csv` são agrupadas por `id_pedido`. Cada pedido vira um conjunto, então um item repetido no mesmo pedido conta uma vez só (RN-01). As cestas são convertidas em uma tabela de verdadeiro/falso (pedido × item), que é o formato esperado pelo Apriori.

### Cardápio com artigos (etapa 6)

A etapa 6 pede ao LLM, em lotes de 50 itens, a forma de cada item no meio de uma frase, com o artigo certo. A resposta vem em JSON e cada forma é conferida: precisa começar com um, uma, uns ou umas e conter o nome do item. O que não passar na conferência, ou todo o lote quando não há chave ou a chamada falha, fica com o nome do item, sem artigo. O resultado é salvo em `cardapio.csv`, e as próximas execuções só chamam o LLM para itens novos. O motivo da escolha do LLM e do modelo está no [README](../README.md#modelos-e-uso-de-llm).

### Regras de associação

O Apriori encontra os conjuntos de itens frequentes, ou seja, com suporte acima do mínimo. A partir deles, são geradas as regras A → B com confiança acima do mínimo (RN-04). Só ficam as regras em que B é um único item, e cada regra guarda suporte, confiança e lift.

Não há um valor padrão para os limites. `gerar_regras.py` compara 12 combinações pela quantidade de regras, pela cobertura dos pedidos, pela confiança média e pelo lift médio, e a escolha final veio da avaliação offline (seção 5):

- **suporte mínimo de 1%**, para que a regra tenha evidência suficiente. Na Sabor na Mesa, sem esse limite, 88% das regras viriam de apenas 1 ou 2 pedidos;
- **confiança mínima de 10%**, ou seja, pelo menos 1 em cada 10 pedidos com o antecedente também tem o consequente;
- **sem filtro de lift**. A primeira versão mantinha só as regras com lift maior que 1, mas isso deixava carrinhos sem regra e diminuía o acerto.

### Validação do carrinho

Antes de recomendar, `validar_carrinho` confere o carrinho que chegou do site (RN-09) e devolve `{"ok": True, "value": [itens]}` ou `{"ok": False, "errors": [...]}`, em que cada erro tem o campo (`carrinho` ou `carrinho[posição]`) e um código:

| Código | Quando |
|---|---|
| `null` | carrinho ou item com valor vazio (`None`) |
| `invalid_type` | carrinho que não é lista, ou item que não é texto |
| `empty` | carrinho sem itens, ou item só com espaços |
| `unknown_item` | item que não está no cardápio da loja |

Os nomes são comparados sem diferença de maiúsculas e espaços e devolvidos com a grafia do cardápio, e um item repetido conta uma vez (RN-01). A função não lança exceção, não altera a entrada, informa todos os erros na ordem dos itens e não repete nos erros o valor recebido.

### Recomendador

Para um carrinho:

1. seleciona as regras cujo lado A está contido no carrinho;
2. descarta as regras cujo item B já está no carrinho (RN-02);
3. ordena por confiança e, em caso de empate, por lift (RN-05);
4. quando um mesmo item B vem de mais de uma regra, mantém a de maior confiança;
5. devolve até 3 sugestões (RN-03);
6. se sobrarem menos de 3, completa as vagas com os itens mais pedidos que não estão no carrinho (RN-06).

As regras ficam em uma lista, com o antecedente como conjunto de itens, para que a busca seja rápida mesmo com centenas de regras. Cada sugestão carrega a regra que a gerou, para que a explicação e o assistente possam usá-la. Os parâmetros `criterio="lift"` e `completar=False` reproduzem as primeiras versões, usadas só na avaliação.

### Explicação

A frase de cada sugestão é montada com os itens da regra que a gerou (RN-07): a regra Água Mineral → Bowl de Frango vira “Já que você escolheu Água Mineral, que tal incluir Bowl de Frango no pedido?”. Quando a regra tem mais de um item no lado A, os itens são citados juntos. Com o `cardapio.csv` da etapa 6, cada item aparece com o artigo certo: “Já que você escolheu um bowl de frango e uma água mineral, que tal incluir uma porção de nachos no pedido?”. Sem o cardápio, a frase usa o nome do item. As sugestões que vêm dos mais vendidos recebem a frase “Um dos itens mais pedidos da casa” (RN-08).

A explicação não usa modelo de linguagem: como a frase só cita itens da regra, um modelo de linguagem acrescentaria custo, demora e risco de citar algo fora da regra, sem acrescentar informação.

### API

A API em FastAPI (`api.py`) é a porta de entrada do backend: o site chama as rotas, e a API usa o código dos outros componentes. Os dados de cada loja são carregados uma vez (`dados_loja.py`) e ficam em memória.

| Rota | O que faz |
|---|---|
| `GET /api/saude` | responde que a API está no ar; o Render usa para saber se ela acordou |
| `GET /api/lojas` | lista as lojas e o nome da assistente de cada uma |
| `GET /api/lojas/{loja}/cardapio` | itens da loja com categoria e descrição, do mais pedido para o menos pedido |
| `POST /api/lojas/{loja}/sugestoes` | recebe `{"carrinho": [...]}`, valida (RN-09), recomenda e devolve as 3 sugestões com a frase |
| `POST /api/lojas/{loja}/chat` | recebe `{"conversa_id": ..., "mensagem": ...}` e devolve a resposta do assistente |
| `POST /api/lojas/{loja}/chat/reiniciar` | apaga o histórico da conversa |

Entradas inválidas voltam com status 400 e a lista de erros no formato do validador (`{"ok": false, "errors": [{"field": ..., "code": ...}]}`). Loja desconhecida volta com 404, e loja sem os arquivos gerados, com 503. Sem a chave da OpenAI, só o chat responde 503; as sugestões continuam funcionando (RNF-03).

### Assistente de conversa

O assistente segue o padrão de agentes com ferramentas: um **orquestrador** conversa com o cliente e decide, a cada mensagem, quais **especialistas** consultar. Cada especialista tem o seu prompt e uma única ferramenta, que lê uma fonte de dados da loja.

| Agente | Prompt | Ferramenta | Fonte de dados |
|---|---|---|---|
| orquestrador | `prompts/orquestrador/persona.md` e `diretrizes.md` | uma ferramenta por especialista (`consultar_cardapio`, `consultar_combinacoes`, `consultar_loja`) | — |
| cardápio | `prompts/cardapio/prompt.md` | `buscar_produtos(termo)` | `produtos.csv` |
| combinações | `prompts/combinacoes/prompt.md` | `itens_que_saem_junto(itens)`, que usa o validador e o recomendador | `regras.csv` |
| loja | `prompts/loja/prompt.md` | `consultar_dados_da_loja()` | `loja.md` |

Fluxo de uma mensagem:

1. o orquestrador recebe a mensagem e o histórico da conversa;
2. escolhe um ou mais especialistas e escreve para cada um uma pergunta completa (por exemplo, troca “e ele é picante?” por “o Burrito de Frango é picante?”);
3. cada especialista chama a sua ferramenta e devolve a informação encontrada;
4. o orquestrador escreve a resposta ao cliente, com a persona da loja (Lupe na Sabor na Mesa, Maya na Casa Masala).

**Histórico.** Cada conversa guarda a lista de mensagens em memória e a envia inteira a cada chamada, até o cliente reiniciar o chat. Os especialistas não guardam histórico: recebem só a pergunta do orquestrador. A API mantém até 200 conversas; as mais antigas saem da memória.

**Cuidados.** As respostas vêm só das ferramentas (RN-10); o assistente não fecha pedidos (RN-11) e não pede dados pessoais. Há limite de 4 consultas por mensagem no orquestrador e de 3 chamadas de ferramenta por especialista. As chamadas usam `store=False`, então a OpenAI não guarda as conversas. Se a OpenAI falhar, a mensagem sai do histórico e o cliente recebe um aviso para tentar de novo.

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

`avaliar.py` salva o resultado de cada loja em `dados/<loja>/avaliacao.csv`, como registro da avaliação.

Os resultados de cada loja estão nos relatórios: [Sabor na Mesa](mexicano/relatorio.md) e [Casa Masala](indiano/relatorio.md).

## 6. Testes

Os testes usam pytest (`python -m pytest`). Os das regras de negócio usam regras pequenas montadas no próprio teste; os da API e das ferramentas usam os dados das lojas e são pulados quando os arquivos gerados não existem. Nenhum teste chama o LLM.

| Arquivo | Teste | Regra verificada |
|---|---|---|
| `test_dados_e_avaliacao.py` | item repetido no mesmo pedido conta uma vez | RN-01 |
| `test_dados_e_avaliacao.py` | cada item de um pedido de teste é escondido uma vez; nenhum pedido fica no treino e no teste | avaliação |
| `test_recomendador.py` | item do carrinho nunca aparece nas sugestões | RN-02 |
| `test_recomendador.py` | no máximo 3 sugestões | RN-03 |
| `test_recomendador.py` | sugestões em ordem de confiança, com desempate pelo lift; cada item sugerido uma vez | RN-05 |
| `test_recomendador.py` | vagas sem regra são completadas com os mais pedidos | RN-06 |
| `test_validacao.py` | carrinho válido é normalizado; repetidos contam uma vez; cada erro recebe o código certo, na ordem dos itens; a entrada não é alterada | RN-01, RN-09 |
| `test_explicacao.py` | frase montada com os itens da regra | RN-07 |
| `test_explicacao.py` | sugestão dos mais vendidos recebe a frase dos mais pedidos | RN-08 |
| `test_api.py` | rotas de saúde, lojas, cardápio e sugestões; carrinho inválido barrado pelo validador; erros de entrada do chat antes de chamar o assistente | RF-01, RF-04, RN-09 |
| `test_agente.py` | busca no cardápio (plural, maiúsculas, descrição); combinações com “a cada 100 pedidos”; nome incompleto devolve itens parecidos; ferramenta nunca lança exceção; prompts preenchidos com a loja e a hora | RN-10 |
