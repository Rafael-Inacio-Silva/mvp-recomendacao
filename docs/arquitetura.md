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
site (Vercel) → API (Render) → serviço de recomendação → validação → recomendador → explicação → sugestões com a frase
site (Vercel) → API (Render) → serviço do chat → assistente: orquestrador (coordenador) → analistas → resposta do chat
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
| `agente` | assistente de conversa: orquestrador, analistas, fontes de dados e prompts | RF-07, RF-08, RN-10, RN-11, RNF-03 |
| `servicos` | validações e regras de negócio das rotas: lojas, cardápio, sugestões e conversas do chat | RF-01, RF-02, RF-04, RF-06, RF-07, RF-08, RN-09 |
| `api` | controller: recebe as requisições do site, chama os serviços e converte os erros em status HTTP | RF-01, RF-02, RF-04, RF-06, RF-07, RF-08 |
| `frontend/` | seleção de restaurante, cardápio, carrinho com sugestões e chat por loja (React e Vite) | RF-01, RF-02, RF-07 |

O recomendador não depende do site, da explicação nem do assistente. Assim, ele pode ser testado sozinho, e a forma de explicar pode mudar sem afetar as sugestões.

## 2. Tecnologias

| Parte | Escolha | Motivo |
|---|---|---|
| Linguagem | Python | bibliotecas prontas para dados e regras de associação |
| Dados | pandas | leitura e agrupamento dos pedidos |
| Regras | mlxtend (Apriori) | implementação conhecida, que já calcula suporte, confiança e lift |
| Explicação | frase montada em Python | exata, instantânea e sem custo, porque só cita itens da própria regra |
| Artigos do cardápio | OpenAI `gpt-6-luna` (Responses API, saída em JSON) | tarefa de linguagem; roda uma vez no pipeline e o resultado fica salvo |
| Assistente de conversa | OpenAI `gpt-6-luna` (Responses API, function calling) | coordenador e analistas entendem as perguntas e escrevem as respostas; os fatos vêm dos dados da loja |
| API | FastAPI e uvicorn, no Render (plano gratuito) | rotas em Python sobre o código que já existe; o Render atualiza a cada envio ao GitHub |
| Site | React e Vite, na Vercel | interface separada do backend; a Vercel repassa as chamadas `/api` ao Render |
| Testes | pytest | testes das regras de negócio, da montagem do assistente, dos serviços e da API |

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
│   ├── orquestrador.py          # coordenador: conversa, histórico e escolha dos analistas
│   ├── analista.py              # subagente analista, que lê os dados da sua área
│   ├── fontes.py                # dados de cada analista em texto
│   ├── prompts.py               # montagem das instruções de cada agente
│   ├── llm.py                   # conexão com a OpenAI
│   └── prompts/                 # um prompt por agente, em Markdown
│       ├── orquestrador/        # template_base.md e estagios/ (um arquivo por etapa)
│       ├── cardapio/            # prompt.md
│       ├── combinacoes/         # prompt.md
│       └── loja/                # prompt.md
├── servicos/                    # camada de serviço, chamada pela API
│   ├── recomendacao.py          # lojas, cardápio e sugestões
│   ├── chat.py                  # validação das mensagens e conversas em memória
│   └── erros.py                 # erros dos serviços, com código e texto
├── api.py                       # controller: rotas da API em FastAPI
├── frontend/                    # site em React e Vite
│   ├── public/imagens/          # capas das lojas e foto de cada produto
│   └── src/
│       ├── main.jsx             # rotas pelo endereço (#/<loja>/<página>)
│       ├── Entrada.jsx          # escolha da loja
│       ├── Restaurante.jsx      # topo, carrinho e páginas de uma loja
│       ├── Cardapio.jsx         # cardápio com categorias, busca e resumo do pedido
│       ├── Pedido.jsx           # pedido e sugestões com a frase
│       ├── Chat.jsx             # conversa com a assistente
│       ├── useConsulta.js       # chamadas à API, com a mais recente valendo
│       └── casas.js             # textos e imagens de cada loja
├── dados_loja.py                # arquivos de cada loja em memória
├── lojas.py                     # lojas, assistentes e caminhos dos arquivos
├── analise_dados.py             # executa o pipeline
├── gerar_regras.py              # calcula e compara as regras
├── avaliar.py                   # executa a avaliação offline
├── avaliar_cardapio.py          # compara os artigos do LLM com o gabarito
├── .env.example                 # variáveis da OpenAI, sem a chave
├── pytest.ini
└── tests/                       # testes das regras de negócio, do assistente e da API
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

A API em FastAPI é a porta de entrada do backend. O código é organizado em camadas, e cada camada só chama a de baixo:

| Camada | Arquivos | Responsabilidade |
|---|---|---|
| controller | `api.py` | recebe a requisição, extrai os parâmetros da rota e do corpo, chama o serviço e devolve a resposta em JSON; converte os erros dos serviços em status HTTP |
| serviço | `servicos/recomendacao.py`, `servicos/chat.py` | validações e regras de negócio: conferir se a loja existe, validar o carrinho e as mensagens, ordenar o cardápio, montar as sugestões e guardar as conversas abertas |
| domínio | `modelo/`, `agente/` | recomendador, validador, explicação e assistente de conversa |
| repositório | `dados_loja.py` | leitura dos arquivos de cada loja, carregados uma vez e mantidos em memória |

O controller não acessa os dados diretamente, e os serviços não conhecem HTTP: quando encontram um problema, lançam um erro (`EntradaInvalida`, `NaoEncontrado` ou `Indisponivel`), e o controller escolhe o status.

| Rota | O que faz |
|---|---|
| `GET /api/saude` | responde que a API está no ar; o Render usa para saber se ela acordou |
| `GET /api/lojas` | lista as lojas e o nome da assistente de cada uma |
| `GET /api/lojas/{loja}/cardapio` | itens da loja com categoria e descrição, do mais pedido para o menos pedido |
| `POST /api/lojas/{loja}/sugestoes` | recebe `{"carrinho": [...]}`, valida (RN-09), recomenda e devolve as 3 sugestões com a frase |
| `POST /api/lojas/{loja}/chat` | recebe `{"conversa_id": ..., "mensagem": ...}` e devolve a resposta do assistente, os analistas consultados, a etapa e se a conversa começou nessa mensagem (`nova_conversa`) |
| `DELETE /api/lojas/{loja}/chat/{conversa_id}` | apaga o histórico da conversa, quando o cliente reinicia o chat |

Todo erro volta no mesmo formato, com o campo, o código e um texto explicativo:

```
{"ok": false, "errors": [{"field": "carrinho[0]", "code": "unknown_item", "message": "Item fora do cardápio da loja."}]}
```

| Status | Quando |
|---|---|
| 200 | requisição atendida |
| 400 | entrada inválida: corpo que não é um objeto JSON, carrinho barrado pelo validador, mensagem ou `conversa_id` inválidos |
| 404 | loja ou rota que não existe |
| 405 | método que a rota não aceita |
| 503 | loja sem os arquivos gerados ou chat sem a chave da OpenAI |

Sem a chave da OpenAI, só o chat responde 503; as sugestões continuam funcionando (RNF-03).

### Assistente de conversa

O assistente é organizado como uma equipe: um **orquestrador**, que faz o papel de coordenador, conversa com o cliente e decide, a cada mensagem, quais **subagentes analistas** consultar. Para o orquestrador, cada analista é uma ferramenta (function calling). Cada analista também é um LLM, com o seu prompt e os dados da sua área, que recebe junto com o prompt e analisa para responder.

| Agente | Prompt | Dados que recebe | Fonte |
|---|---|---|---|
| orquestrador (coordenador) | `prompts/orquestrador/template_base.md` e a etapa atual de `estagios/` | histórico da conversa; ferramentas `consultar_cardapio`, `consultar_combinacoes`, `consultar_loja` e `avancar_estagio` | — |
| analista do cardápio | `prompts/cardapio/prompt.md` | todos os produtos, com categoria e descrição, do mais pedido para o menos pedido | `produtos.csv` |
| analista de combinações | `prompts/combinacoes/prompt.md` | todas as regras da loja, escritas como “pedidos com A → B: N de cada 100 pedidos”, e os itens mais pedidos | `regras.csv` |
| analista da loja | `prompts/loja/prompt.md` | o documento da empresa | `loja.md` |

Os dados de cada área cabem inteiros no prompt (no maior caso, as regras da Casa Masala têm cerca de 52 mil caracteres), então não é preciso dividi-los nem usar um banco vetorial. As partes fixas vêm primeiro e a hora por último, para que a OpenAI reaproveite o começo do prompt em cache.

**Prompts.** Os prompts usam marcadores `{{nome}}`, trocados pelo código: `{{loja}}`, `{{atendente}}`, `{{agora}}` e `{{referencias_data}}` (hoje e os próximos 7 dias, com o dia da semana), além de `{{dados}}` nos analistas. O orquestrador tem um **template base** (identidade, fluxo, regras de conversa, segurança, restrições críticas, analistas, gatilhos de encaminhamento, objeções e situações especiais) e um **arquivo por etapa**, no formato Nome, Objetivo e Instrução:

| Etapa | Arquivo | Objetivo | Avança quando |
|---|---|---|---|
| 1 — Conexão | `estagio_1_conexao.md` | entender o que o cliente procura; não se apresenta, porque o site já mostra a saudação da assistente | o cliente traz uma dúvida, uma preferência ou um item |
| 2 — Atendimento | `estagio_2_atendimento.md` | esclarecer dúvidas e ajudar a escolher, com microcompromissos | o cliente escolhe um item ou diz que vai pedir |
| 3 — Fechamento | `estagio_3_fechamento.md` | sugerir um complemento, tirar dúvidas finais e orientar a finalizar no carrinho | — |

A conversa guarda a etapa atual, e só a instrução dessa etapa entra no prompt (`{{etapa_atual}}`, `{{etapa_objetivo}}` e `{{etapa_instrucao}}`). Quando o critério de avanço é cumprido, o orquestrador chama a ferramenta `avancar_estagio`; o código só aceita avançar, nunca voltar de etapa.

Fluxo de uma mensagem:

1. o orquestrador recebe a mensagem e o histórico da conversa;
2. escolhe um ou mais analistas e escreve para cada um uma pergunta completa (por exemplo, troca “e ele é picante?” por “o Burrito de Frango é picante?”);
3. cada analista lê os dados da sua área e devolve a informação encontrada;
4. se o critério de avanço da etapa foi cumprido, o orquestrador chama `avancar_estagio`;
5. o orquestrador escreve a resposta ao cliente, com a identidade da loja (Lupe na Sabor na Mesa, Maya na Casa Masala) e a instrução da etapa atual.

**Histórico.** Cada conversa guarda a lista de mensagens em memória e a envia inteira a cada chamada, até o cliente reiniciar o chat. Os analistas não guardam histórico: recebem só a pergunta do orquestrador. Ao reiniciar o chat, a conversa volta para a etapa 1. O serviço do chat mantém até 200 conversas; as mais antigas saem da memória. O site guarda o histórico na sessão da aba. Se a API reiniciar ou descartar a conversa, a resposta seguinte vem com `nova_conversa: true`. O site então troca o histórico antigo pela mensagem atual e avisa o cliente de que a conversa anterior expirou.

**Cuidados.** Os analistas respondem só com os dados que recebem (RN-10); o assistente não fecha pedidos (RN-11) e não pede dados pessoais. Há limite de 4 consultas aos analistas e de 8 chamadas de ferramenta por mensagem. As chamadas usam `store=False`, então a OpenAI não guarda as conversas. Se a OpenAI falhar, a mensagem sai do histórico e o cliente recebe um aviso para tentar de novo.

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

Os testes usam pytest (`python -m pytest`). Os das regras de negócio usam regras pequenas montadas no próprio teste; os da API e do assistente usam os dados das lojas e são pulados quando os arquivos gerados não existem. Nenhum teste chama o LLM.

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
| `test_servicos.py` | cardápio do mais pedido para o menos pedido; loja desconhecida; carrinho inválido com código e texto; mensagem do chat validada antes de chamar o assistente; aviso de conversa nova | RF-01, RF-07, RN-09 |
| `test_api.py` | rotas de saúde, lojas, cardápio, sugestões e chat; status 400, 404, 405 e 503 com o mesmo formato de erro; JSON inválido; chat sem a chave da OpenAI; encerramento da conversa | RF-01, RF-04, RF-08, RN-09, RNF-03 |
| `test_agente.py` | ferramentas do orquestrador; dados de cada analista completos (todos os produtos, todas as regras com “N de cada 100 pedidos”, documento da loja); etapas com nome, objetivo e instrução; só a etapa atual no prompt; marcadores preenchidos; datas de referência; a etapa só avança | RN-10 |
