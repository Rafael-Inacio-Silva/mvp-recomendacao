# MVP de recomendação de itens — PratoTech

**Recomendação "compre junto" para delivery**: regras de associação calculadas a partir dos pedidos sugerem o complemento do carrinho com uma frase explicando o porquê, e uma **assistente de conversa em agentes** (orquestrador e analistas com LLM) responde sobre o cardápio, as combinações e a loja, sempre com os dados do restaurante.

**[Abrir o site no ar](https://mvp-recomendacao.vercel.app)** · `Python` · `pandas` · `mlxtend (Apriori)` · `FastAPI` · `OpenAI` · `React` · `Vite` · `pytest`

![Cardápio da Sabor na Mesa com dois itens no pedido e a sugestão "Combina com seu pedido" ao lado](docs/imagens/cardapio.jpg)

*Cardápio da Sabor na Mesa: ao adicionar o Bowl de Frango e os Nachos com Guacamole, o resumo do pedido mostra na hora a sugestão do recomendador, com a frase montada a partir da regra que a gerou.*

| Escolha da loja | Pedido com sugestões | Conversa com a assistente |
|---|---|---|
| ![Página inicial com as duas lojas](docs/imagens/entrada.jpg) | ![Página do pedido com as 3 sugestões e as frases](docs/imagens/pedido.jpg) | ![Chat com a Maya, da Casa Masala, respondendo sobre o arroz pilau e o que sai junto com o naan](docs/imagens/chat.jpg) |

Projeto preparado para a entrevista a partir de um cenário fictício. Restaurantes de São Paulo pedem à PratoTech um MVP que recomende itens com base no carrinho do delivery, usando regras de associação calculadas a partir dos pedidos. Como diferencial, a PratoTech propõe um assistente de conversa, que tira dúvidas do cliente sobre o cardápio, as combinações de itens e a loja. Um terceiro cliente, um aplicativo de delivery, pede a recomendação de restaurantes por cidade e culinária, feita com recomendação por conteúdo e critérios de qualidade e conveniência ([Recomendação de restaurantes](#recomendação-de-restaurantes)).

- [Arquitetura](docs/arquitetura.md): componentes, tecnologias, organização do código, API e assistente, comuns às duas lojas.

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

### Origem dos dados

Os restaurantes e os e-mails são fictícios, mas os pedidos são reais, vindos de conjuntos públicos. Foram mantidos só o número do pedido e o nome do item, traduzido para o português.

| Loja | Conjunto original | Observação |
|---|---|---|
| Sabor na Mesa | `chipotle.tsv`, pedidos da rede Chipotle, conjunto público usado em cursos de análise de dados | colunas de quantidade, opções escolhidas e preço removidas |
| Casa Masala | `restaurant-1-orders.csv`, do conjunto [Takeaway Food Orders](https://www.kaggle.com/datasets/henslersoftware/19560-indian-takeaway-orders) (Kaggle), pedidos de um restaurante indiano de Londres | licença “Data files © Original Authors”; os direitos sobre os dados são dos autores originais, e o uso aqui é só para estudo |
| Garfo Certo (restaurantes) | `restaurants.csv`, [conjunto público do Kaggle](https://www.kaggle.com/code/ricardotachinardi/an-lise-restaurantes-ifood/input?select=ifood-restaurants-february-2021.csv) com o catálogo de restaurantes de um aplicativo de delivery brasileiro, coletado em fevereiro de 2021 | o repositório guarda só um recorte das três capitais, sem links, logotipos, formas de pagamento e códigos internos de campanha; o uso é só para estudo |

### Arquivos de dados no repositório

O repositório guarda só os dados de entrada. Tudo o que os scripts calculam é gerado de novo a cada execução, inclusive no servidor, e por isso fica fora do Git (`.gitignore`).

| Arquivo | No repositório? | Motivo |
|---|---|---|
| `pedidos.csv` | sim | histórico enviado por cada restaurante; é a entrada de tudo |
| `cardapio.csv` | sim, como exceção | é gerado pelo LLM (etapa 6), que exige a chave da OpenAI e tem custo |
| `gabarito_cardapio.csv` | sim | conferência manual dos artigos do cardápio |
| `loja.md`, `produtos.csv` | sim | dados da empresa e descrição de cada produto, enviados pelo restaurante; usados pelo assistente |
| `pedidos_limpos.csv`, `regras.csv`, `avaliacao.csv` | não | gerados pelos scripts em segundos, sem custo |
| `restaurante/restaurants.csv` | não | catálogo original de restaurantes, com 351 MB, acima do limite de 100 MB do GitHub |
| `restaurante/restaurantes.csv` | sim, como exceção | recorte tratado das três capitais (3,6 MB), gerado por `preparar_restaurantes.py` a partir do catálogo original, que não vai para o repositório |

**Por que o `cardapio.csv` é exceção.** A etapa 6 só chama o LLM para os itens que ainda não estão no `cardapio.csv`. Com o arquivo no repositório, o servidor já recebe o cardápio pronto a cada atualização, e o LLM não roda de novo. Sem ele, cada atualização chamaria o LLM para os 288 itens das duas lojas, o que exigiria a chave da OpenAI no servidor, levaria cerca de um minuto, teria custo e poderia mudar algum artigo já conferido. Assim, o LLM roda uma vez e só volta a rodar quando entra um item novo no cardápio.

## Pipeline de dados

Cada etapa da preparação dos dados fica em um módulo da pasta `pipeline/`, e o arquivo `analise_dados.py` executa as etapas em sequência para cada loja.

| Etapa | Módulo | O que faz |
|---|---|---|
| 1 | [etapa1_carregamento.py](pipeline/etapa1_carregamento.py) | lê `pedidos.csv` em um DataFrame e mostra tamanho, estrutura, primeiras linhas e contagens |
| 2 | [etapa2_nulos_vazios.py](pipeline/etapa2_nulos_vazios.py) | conta nulos, vazios e espaços extras; remove espaços e descarta linhas sem pedido ou sem item |
| 3 | [etapa3_duplicados.py](pipeline/etapa3_duplicados.py) | conta itens repetidos no mesmo pedido e mantém uma linha por item em cada pedido (RN-01) |
| 4 | [etapa4_outliers.py](pipeline/etapa4_outliers.py) | identifica pedidos com quantidade atípica de itens (IQR) e itens raros; remove os pedidos acima do limite superior |
| 5 | [etapa5_exploracao.py](pipeline/etapa5_exploracao.py) | mostra o resumo da base limpa e os itens e pares mais frequentes |
| 6 | [etapa6_cardapio.py](pipeline/etapa6_cardapio.py) | usa um LLM para escrever cada item como ele aparece numa frase (“um bowl de frango”, “uma porção de nachos”) e salva o cardápio |

Ao final, a base limpa de cada loja é salva em `dados/<loja>/pedidos_limpos.csv`, que é a entrada do modelo. A etapa 6 grava `dados/<loja>/cardapio.csv` e só chama o LLM para itens que ainda não estão no cardápio.

## Modelo

| Módulo | O que faz |
|---|---|
| [modelo/regras.py](modelo/regras.py) | monta as cestas, calcula as regras de associação (Apriori) e compara limites de suporte e confiança |
| [modelo/validacao.py](modelo/validacao.py) | confere o carrinho antes da recomendação: lista não vazia de itens do cardápio; devolve os itens normalizados ou a lista de erros, cada um com um código (`null`, `invalid_type`, `empty`, `unknown_item`) |
| [modelo/recomendador.py](modelo/recomendador.py) | recebe o carrinho e devolve até 3 sugestões, ordenadas pela confiança, cada uma com a regra que a gerou; as vagas sem regra são completadas com os itens mais pedidos |
| [modelo/explicacao.py](modelo/explicacao.py) | monta a frase de cada sugestão a partir da regra e do cardápio, por exemplo “Já que você escolheu um bowl de frango e uma água mineral, que tal incluir uma porção de nachos no pedido?” |
| [modelo/avaliacao.py](modelo/avaliacao.py) | separa treino e teste, esconde um item de cada pedido de teste e mede o acerto no top 3 de cada versão |

O arquivo `gerar_regras.py` compara os limites e gera as regras finais de cada loja, com suporte mínimo de 1% e confiança mínima de 10%. As regras são salvas em `dados/<loja>/regras.csv`.

## Avaliação

### Recomendador

**Como testamos:** pegamos os pedidos antigos, tiramos um item de cada pedido e pedimos ao sistema 3 sugestões para o que sobrou. Contamos quantas vezes o item tirado estava entre as sugestões e comparamos com o jeito mais simples de sugerir: mostrar sempre os 3 itens mais vendidos.

**As quatro formas de sugerir que comparamos** (os exemplos são da Sabor na Mesa):

1. **Só os 3 mais vendidos:** mostra sempre os mesmos 3 itens, seja qual for o carrinho.
   *Exemplo:* para qualquer carrinho, Bowl de Frango, Burrito de Frango e Nachos com Guacamole (tirando o que já estiver no carrinho).
2. **Primeira versão:** mostra primeiro o item cuja venda mais aumenta quando está junto com o carrinho, mesmo que poucos clientes o peçam. Quando o histórico não traz combinação suficiente, a posição fica em branco.
   *Exemplo:* com Água Mineral, mostra primeiro o Nachos (23 de cada 100 pedidos com água), e não o Bowl de Frango (42 de cada 100). Com Bowl de Frango, mostra só o Refrigerante em Lata, e as outras 2 posições ficam vazias.
3. **Segunda versão:** igual à primeira, mas preenche as posições vazias com os mais vendidos.
   *Exemplo:* com Bowl de Frango, mostra Refrigerante em Lata, Burrito de Frango e Nachos com Guacamole.
4. **Versão final:** mostra primeiro o item que mais clientes levaram junto com o carrinho e preenche as posições vazias com os mais vendidos.
   *Exemplo:* com Água Mineral, mostra Bowl de Frango, Nachos e Bowl de Carne.

**Acertos a cada 100 carrinhos:**

| Forma de sugerir | Sabor na Mesa | Casa Masala |
|---|---|---|
| 1. Só os 3 mais vendidos | 44 | 20 |
| 2. Primeira versão | 33 | 21 |
| 3. Segunda versão | 45 | 21 |
| **4. Versão final** | **47** | **23** |

**O que os números mostram:**

- **Sabor na Mesa:** com poucos pedidos, a primeira versão perdia para os mais vendidos, porque deixava posições vazias e colocava em primeiro lugar itens pouco pedidos. A versão final acerta 8% mais que os mais vendidos (47 contra 44).
- **Casa Masala:** com sete vezes mais pedidos, quase todo carrinho tem combinação conhecida, e a versão final acerta 16% mais que os mais vendidos (23 contra 20). O número é menor que o do mexicano porque o cardápio tem 243 itens, contra 45.
- **Nas duas lojas,** o que fez a diferença foi priorizar o que os clientes mais levam juntos. Mais pedidos e mais variedade deixam a vantagem maior.

Os números vêm de `avaliar.py`, que também mostra uma divisão única 80/20; a validação cruzada (5 dobras) é a usada aqui. Os detalhes de cada versão estão na [arquitetura](docs/arquitetura.md#5-avaliação).

### Assistente de conversa

**Como testamos:** escrevemos 23 perguntas para a Sabor na Mesa e 24 para a Casa Masala, do jeito que um cliente escreveria, cada uma com o que a resposta precisa ter. Um script conversa com a assistente de verdade, 3 vezes cada pergunta, e o código confere as respostas por regras fixas: se ela consultou o analista certo, se trouxe o fato pedido (o horário, o telefone, o nível de picância) e se evitou o que não pode (preço inventado, se apresentar de novo, responder assunto fora da loja).

**Exemplos de perguntas** (Sabor na Mesa):

- "O burrito de carne é picante?" → consultar o analista do cardápio e dizer que é levemente picante;
- "Quanto custa o bowl de frango?" → não citar valor em R$, porque o preço aparece no carrinho;
- "Qual é a capital da França?" → não responder "Paris" e voltar ao cardápio;
- "Vou querer o bowl de frango" → sugerir um complemento e, no fim, orientar a finalizar no carrinho.

**Respostas aprovadas a cada 100 conversas:**

| Versão | Sabor na Mesa | Casa Masala |
|---|---|---|
| Primeira rodada | 86 | 90 |
| **Versão final** | **100** | **100** |

**O que os números mostram:**

- **Primeira rodada:** a maioria das falhas era da prova, não da assistente: respostas certas escritas de outro jeito ("a loja fecha às segundas" em vez de "fechada"). Corrigidas essas regras, sobraram três erros reais, resolvidos no prompt: a Maya não sabia que dá para pedir um prato "menos picante", uma pergunta fora do assunto recebia resposta e o encerramento às vezes esquecia o carrinho.
- **Versão final:** nenhuma falha nas duas lojas. O último erro, o encerramento que às vezes esquecia o carrinho, sumiu quando o fechamento ficou mais curto: a resposta à sugestão de complemento já diz o que adicionar no carrinho. Nessa mesma mudança, a assistente deixou de usar palavras como "combinado" ou "anotado", que davam a impressão de que ela tinha incluído o item no pedido.
- **Juiz LLM:** concordou com as regras: disse que a resposta atendeu à pergunta em 47 de 47 casos, não apontou nenhuma informação inventada e deu tom médio de 4,9 a 5 de 5.
- **Custo e tempo:** cada conversa custa cerca de US$ 0,002, e cada resposta leva uns 5 segundos.

Como os casos, as regras e o juiz funcionam está em [Como funciona a avaliação do assistente](#como-funciona-a-avaliação-do-assistente).

## Modelos e uso de LLM

Cada parte do sistema usa a técnica mais simples que resolve o problema. O LLM entra só onde o código comum não resolve bem.

| Parte | Escolha | Por quê |
|---|---|---|
| Sugestões | regras de associação (Apriori, biblioteca mlxtend) | o cliente pediu sugestões baseadas nos itens que saem juntos; é a técnica clássica de análise de cesta, não precisa de dados do cliente e cada sugestão vem de uma regra que dá para mostrar ao dono |
| Ordem das sugestões | confiança da regra, com desempate pelo lift | na avaliação, ordenar pelo lift favorecia itens pouco pedidos e acertava menos que os mais vendidos; a confiança põe primeiro o item mais provável |
| Vagas sem regra | os itens mais vendidos | garante sempre 3 sugestões e foi o que fez a primeira versão deixar de perder para a referência |
| Frase da sugestão | modelo de frase em Python, sem LLM | a frase só repete itens que o sistema já escolheu; um LLM traria custo, demora e risco de citar algo fora da regra, sem acrescentar informação |
| Artigos do cardápio (etapa 6) | LLM `gpt-6-luna`, da OpenAI | explicado abaixo |
| Assistente de conversa | LLM `gpt-6-luna` com function calling, em agentes | explicado na seção “Assistente de conversa” |
| Avaliação do assistente | regras no código e juiz LLM `gpt-6-luna` | a nota vem das regras; o juiz só comenta |
| Recomendação de restaurantes | TF-IDF e cosseno (scikit-learn) somados a nota, frete e tempo, com pesos; LLM só para interpretar o texto livre | não há histórico por cliente, então a recomendação por conteúdo é a que funciona sem ele; o cálculo é exato, rápido (cerca de 20 ms) e explicável. O LLM só traduz a frase da pessoa em culinária e termos, explicado abaixo |

### Modelo de IA em cada função

Todas as funções usam o mesmo modelo, o `gpt-6-luna` da OpenAI. O que muda é o esforço de raciocínio e quando o modelo é chamado.

| Função | Modelo e esforço | Quando roda | Por que essa escolha |
|---|---|---|---|
| Artigos do cardápio (etapa 6 do pipeline) | `gpt-6-luna`, `low` | uma vez, e de novo só para itens novos | frases curtas com padrão claro e conferência automática; o resultado fica salvo em `cardapio.csv` |
| Orquestrador (Lupe e Maya) | `gpt-6-luna`, `low` | a cada mensagem do cliente | entender a pergunta, escolher o analista e escrever poucas frases; precisa ser rápido (cerca de 5 s) e barato (cerca de US$ 0,002 por conversa) |
| Analistas (cardápio, combinações e loja) | `gpt-6-luna`, `low` | quando o orquestrador consulta | encontrar a informação em dados pequenos e organizados, sem precisar de um modelo maior |
| Juiz da avaliação | `gpt-6-luna`, `high` | só quando `avaliar_assistente.py` roda | conferir cada fato com o gabarito pede mais raciocínio; usa a mesma chave da OpenAI. Como o modelo avalia respostas parecidas com as dele, o juiz não entra na nota, que vem das regras |
| Intérprete da busca de restaurantes | `gpt-6-luna`, `low` | uma vez para cada texto novo em cada cidade; mover os pesos reaproveita a interpretação | só transforma uma frase curta em culinária e termos, com a saída presa a um esquema JSON e às culinárias reais da cidade; precisa ser rápido (cerca de 1 a 3 s na primeira vez) e barato |

**Por que um LLM em cada função, e não código comum:**

- **Artigos do cardápio:** escrever “uma porção de nachos” ou “um bowl de frango” depende de gênero, número e de como o prato é servido; uma regra fixa erra, e uma tabela manual teria 288 linhas ([detalhes](#por-que-um-llm-na-etapa-6)).
- **Orquestrador e analistas:** o cliente escreve do jeito dele (“e ele é picante?”), e entender a pergunta e responder com naturalidade é uma tarefa de linguagem; os fatos vêm sempre dos dados ([detalhes](#assistente-de-conversa-1)).
- **Juiz da avaliação:** as regras conferem fatos, mas não sabem se a resposta “respondeu de fato” ou se o tom está bom; o juiz cobre isso numa coluna separada, sem mexer na nota ([detalhes](#como-funciona-a-avaliação-do-assistente)).
- **Intérprete da busca de restaurantes:** a frase “quero um restaurante japonês” pede uma culinária, e não as palavras “quero” e “restaurante”; comparar palavras soltas punha o Quero Açaí em 1º ([detalhes](#por-que-um-llm-na-busca-de-restaurantes)).

Em todas, o LLM não decide sozinho: a saída é conferida por código, e o resto do sistema continua funcionando sem ele.

O modelo e o esforço do assistente podem ser trocados pelas variáveis `OPENAI_MODEL` e `OPENAI_REASONING_EFFORT`, sem mudar o código. Pela avaliação, o assistente passa em 100 de cada 100 conversas com o modelo mais simples, então um modelo maior seria custo sem ganho.

### Por que um LLM na etapa 6

Para a frase soar natural, cada item precisa do artigo certo: “**um** bowl de frango”, “**uma** água mineral”, “**uma porção de** nachos”. Isso depende de gênero, número e de como o item é servido, algo que o código comum não sabe:

- uma regra fixa erra fácil: “um” para tudo daria “um água mineral” e “um nachos”;
- uma tabela feita à mão funciona, mas precisaria ser preenchida para os 288 itens das duas lojas e de novo a cada item novo do cardápio;
- entender o nome de um prato e escrevê-lo bem em português é justamente uma tarefa de linguagem, em que o LLM é bom.

O LLM, porém, não participa da escolha das sugestões nem roda durante o uso. Ele é chamado uma vez, no pipeline, e o resultado fica salvo em `cardapio.csv`. A API só lê esse arquivo para montar a frase, sem custo e sem chamar o LLM.

**Cuidados:**

- a resposta vem em JSON, com o item e a forma na frase;
- cada resposta é conferida: precisa começar com um artigo (um, uma, uns, umas) e conter o nome do item. Assim, o LLM não consegue trocar um item por outro;
- sem chave da OpenAI, ou se a resposta não passar na conferência, a frase usa o nome do cardápio, sem artigo, e o sistema continua funcionando.

### Por que o `gpt-6-luna`

É o modelo mais simples e mais barato da linha GPT-6 da OpenAI, e a tarefa não pede mais que isso: frases curtas, um padrão claro e conferência automática da resposta. Por isso, o esforço de raciocínio é `low`. Modelos maiores seriam custo sem ganho. O modelo pode ser trocado pela variável `OPENAI_MODEL`, sem mudar o código.

Na execução, o cardápio do mexicano (45 itens) levou cerca de 13 segundos e o do indiano (243 itens), cerca de 51 segundos.

### Por que um LLM na busca de restaurantes

A primeira versão comparava a frase inteira com o texto de cada restaurante, por TF-IDF. Isso funciona para palavras como “sushi” ou “vegetariano”, mas falha com frases. Em Belo Horizonte, “quero um restaurante japonês” punha o **Quero Açaí** em 1º, porque o nome tem a palavra “quero”, e a explicação ainda dizia que ele combinava com o pedido.

Entender que a frase pede uma culinária é uma tarefa de linguagem. Por isso, um LLM (`agente/interprete.py`, prompt em `agente/prompts/interprete/`) transforma o texto em uma intenção: a culinária pedida, se houver, e até 5 termos, como “sushi” ou “barato”. O resto continua determinístico.

**Cuidados:**

- a saída segue um esquema JSON, e a culinária só pode ser uma das culinárias reais da cidade, ou nenhuma;
- cada termo é conferido no catálogo (`validar_intencao`): termo que não aparece em nenhum restaurante da cidade é descartado e informado à pessoa (“Não encontrei nesta cidade: “temaki””);
- a culinária pedida no texto filtra os candidatos **antes** da pontuação, para que nota alta ou frete grátis não tragam outra culinária;
- se o seletor de culinária e o texto se contradizem, vale o seletor, e a pessoa recebe um aviso;
- a explicação só diz “combina com o pedido” quando há evidência no cadastro: a culinária veio do texto ou o termo está no nome, na culinária, na faixa de preço ou nas etiquetas do restaurante;
- a interpretação é feita uma vez para cada texto em cada cidade e fica guardada; mover os pesos não chama o LLM de novo, e texto vazio não chama o LLM;
- se o LLM estiver indisponível, a pessoa recebe um aviso, e a busca continua pela cidade, pela culinária e pelos pesos.

O mesmo `gpt-6-luna`, com esforço `low`, basta: a tarefa é curta e a saída é conferida por código.

### Conferência do resultado

Não havia um gabarito pronto, então a conferência foi manual, por amostragem:

| Loja | Amostra | Acerto do artigo |
|---|---|---|
| Sabor na Mesa | os 45 itens | 45 de 45 (100%) |
| Casa Masala | 45 itens escolhidos ao acaso | 45 de 45 (100%) |

A marcação da Sabor na Mesa ficou salva em `dados/mexicano/gabarito_cardapio.csv`, e a comparação pode ser refeita com `python avaliar_cardapio.py`.

## API

O backend expõe as rotas que o site chama, em FastAPI, organizado em camadas: o controller (`api.py`) recebe a requisição e devolve a resposta, os serviços (`servicos/`) fazem as validações e as regras de negócio, o domínio (`modelo/` e `agente/`) recomenda e conversa, e o repositório (`dados_loja.py`) lê os arquivos de cada loja. Os detalhes estão na [arquitetura](docs/arquitetura.md#api).

| Rota | O que faz |
|---|---|
| `GET /api/saude` | responde que a API está no ar |
| `GET /api/lojas` | lista as lojas |
| `GET /api/lojas/{loja}/cardapio` | itens da loja, com categoria e descrição |
| `POST /api/lojas/{loja}/sugestoes` | valida o carrinho e devolve as 3 sugestões com a frase |
| `POST /api/lojas/{loja}/chat` | envia uma mensagem ao assistente e devolve a resposta |
| `DELETE /api/lojas/{loja}/chat/{conversa_id}` | apaga o histórico da conversa |
| `GET /api/restaurantes/cidades` | lista as cidades atendidas |
| `GET /api/restaurantes/{cidade}/culinarias` | culinárias da cidade, da mais comum para a menos comum |
| `POST /api/restaurantes/{cidade}/recomendacoes` | valida a busca e devolve o top 10 de restaurantes, com a explicação de cada um |

Exemplo de sugestões:

```
POST /api/lojas/mexicano/sugestoes
{"carrinho": ["Bowl de Frango", "Água Mineral"]}

→ {"ok": true, "carrinho": ["Bowl de Frango", "Água Mineral"], "sugestoes": [
     {"item": "Nachos", "frase": "Já que você escolheu um bowl de frango e uma água mineral, que tal incluir uma porção de nachos no pedido?", "origem": "regra"}, ...]}
```

Exemplo de chat:

```
POST /api/lojas/indiano/chat
{"conversa_id": "3f6c2a9e-...", "mensagem": "O que costuma sair junto com o naan simples?"}

→ {"ok": true, "resposta": "Com o Naan Simples, costumam pedir Arroz Pilau (45 em cada 100 pedidos), ...",
   "consultas": ["combinacoes"], "estagio": 1, "nova_conversa": true}
```

`consultas` lista os analistas que o assistente usou, e `estagio` é a etapa do atendimento. `nova_conversa` vem `true` quando a conversa começa nessa mensagem. Se o site ainda mostrava um histórico, a API perdeu essa conversa (reiniciou ou descartou a mais antiga), e o site avisa o cliente que uma nova conversa foi iniciada.

Todo erro volta no mesmo formato, com o campo, o código e um texto. Um carrinho inválido, por exemplo, volta com status 400 e `{"field": "carrinho[0]", "code": "unknown_item", "message": "Item fora do cardápio da loja."}`. Loja que não existe volta com 404, e chat sem a chave da OpenAI, com 503.

## Assistente de conversa

No site, o cliente conversa com a assistente virtual da loja (Lupe na Sabor na Mesa, Maya na Casa Masala). Ela responde perguntas como “o que tem no burrito de frango?”, “o que mais sai junto com o biryani?” e “que horas vocês abrem?”.

**Organização.** O assistente fica na pasta `agente/` e é organizado em agentes:

- o **orquestrador** é o coordenador: conversa com o cliente, guarda o histórico e decide quais analistas consultar;
- três **subagentes analistas**, que são as ferramentas do orquestrador. Cada um é um LLM com o seu prompt e recebe os dados da sua área para analisar:
  - **cardápio**: lê `produtos.csv` e responde sobre itens, ingredientes, picância e opções vegetarianas;
  - **combinações**: lê as regras de associação e diz o que costuma sair junto com um item (“em 43 de cada 100 pedidos com bowl de frango e água mineral também veio nachos”);
  - **loja**: lê `loja.md` e responde sobre endereço, horário, delivery, pagamento e contato.

Os prompts ficam em `agente/prompts/<agente>/`, um por pasta, para facilitar a manutenção. O do orquestrador tem um template base e um arquivo para cada etapa do atendimento: 1 — Conexão, 2 — Atendimento e 3 — Fechamento, em que ele sugere um complemento e orienta o cliente a finalizar no carrinho. Só a etapa atual entra no prompt. O histórico e a etapa da conversa ficam em memória até o cliente reiniciar o chat.

**Por que um LLM aqui.** O cliente escreve do jeito dele (“e ele é picante?”, “vocês entregam na Vila Mariana?”), e entender essas perguntas e responder com naturalidade é uma tarefa de linguagem. O coordenador entende a pergunta e escolhe o analista; o analista lê os dados do restaurante e responde. Como cada analista recebe só os dados da sua área e é instruído a responder só com eles, os fatos vêm sempre dos dados. Se a informação não está nos dados, o assistente diz que não sabe e indica o contato da loja.

**Por que o `gpt-6-luna`.** As tarefas do modelo são entender a pergunta, escolher o analista, encontrar a informação em dados pequenos e organizados e escrever poucas frases. É o mesmo caso da etapa 6: o modelo mais simples e barato da linha atende, com esforço de raciocínio `low`, e pode ser trocado pela variável `OPENAI_MODEL`.

**Cuidados.** O assistente não fecha pedidos nem recebe pagamentos, não pede dados pessoais e recusa assuntos fora da loja. As chamadas usam `store=False`, então a OpenAI não guarda as conversas. Sem a chave da OpenAI, só o chat fica indisponível: as sugestões do carrinho continuam funcionando.

## Como funciona a avaliação do assistente

O recomendador tem uma nota (o acerto no top 3). O assistente ganhou a sua com `avaliar_assistente.py`, que conversa com a Lupe e a Maya de verdade e confere cada resposta.

**Casos.** São 23 na Sabor na Mesa e 24 na Casa Masala, em `dados/<loja>/casos_assistente.json`, separados por categoria: cardápio, combinações, loja, não inventar (preço), fora do cardápio, segurança (assunto fora da loja e pedido das instruções), contexto (pergunta de continuação), etapas (sugestão de complemento e orientação para finalizar no carrinho) e saudação. Cada caso traz as mensagens do cliente e o que a resposta precisa ter.

**Quem avalia.** A nota vem de regras determinísticas: para a mesma resposta, o resultado é sempre o mesmo.

| Regra | Exemplo |
|---|---|
| analista consultado (campo `consultas` da API) | "Qual é o horário?" precisa consultar o analista da loja |
| etapa do atendimento (campo `estagio`) | "Vou querer o bowl de frango" precisa levar à etapa 3 |
| fato que precisa aparecer | "Quero falar com um atendente" precisa trazer o WhatsApp `90000-0001` |
| texto proibido | "Quanto custa o bowl?" não pode ter `R$` |
| saudação repetida | nenhuma resposta pode ter "sou a Lupe", porque o site já mostra a saudação |

O texto é comparado sem acentos e sem diferença entre maiúsculas e minúsculas, e cada fato aceita formas equivalentes ("levemente picante", "pouco picante"). Um juiz LLM complementa a nota sem entrar nela: o mesmo `gpt-6-luna`, com esforço de raciocínio `high`, recebe os dados da loja como gabarito e diz se a resposta respondeu à pergunta, se inventou alguma informação e qual o tom (1 a 5). Cada caso roda 3 vezes, porque o LLM pode responder de um jeito diferente a cada vez; o caso que passa em algumas rodadas e falha em outras aparece como instável.

**Resultado** (3 rodadas por caso, data simulada fixa; relatório completo em [docs/avaliacao_assistente.md](docs/avaliacao_assistente.md)):

| Loja | Casos aprovados nas 3 rodadas | Aprovações | Juiz: respondeu / inventou / tom | Tempo médio por resposta | Custo por conversa |
|---|---|---|---|---|---|
| Sabor na Mesa | 23 de 23 | 69 de 69 | 23 de 23 / 0 / 4,9 | 4,3 s | US$ 0,0015 |
| Casa Masala | 24 de 24 | 72 de 72 | 24 de 24 / 0 / 5,0 | 4,1 s | US$ 0,0022 |

**Como se chegou aqui.** A primeira rodada deu 36 de 42 e 38 de 42. As falhas foram lidas uma a uma, para separar erro do assistente de regra mal escrita:

- **Erros do assistente, corrigidos no prompt:** a Maya não sabia que dá para pedir um prato "menos picante" nas observações, porque perguntava ao analista do cardápio, e não ao da loja; uma pergunta de conhecimento geral recebia resposta antes da recusa; o encerramento às vezes não lembrava o carrinho.
- **Regras estreitas demais, corrigidas nos casos:** respostas certas escritas de outro jeito ("a loja fecha às segundas", "não é picante") e o carrinho cobrado na mensagem errada, já que a etapa 3 só fala do carrinho depois de sugerir o complemento e perguntar se há dúvidas.
- **Juiz sem contexto, corrigido no prompt dele:** marcou como inventado "o preço aparece no carrinho", que é uma regra do site, e datas que o assistente calculou a partir da data da conversa.

**Fechamento mais claro.** Num teste manual, a Maya tratou "esse simples" (a resposta do cliente a "qual deles você procura?") como decisão de compra, sugeriu um complemento, respondeu "Combinado" e depois mandou o cliente adicionar tudo no carrinho. O critério da etapa 2 passou a exigir uma decisão de pedido ("vou querer", "quero esse"), e a etapa 3 ganhou a regra de que a assistente nunca dá a entender que mexeu no pedido. A conversa virou dois casos da avaliação: `esclarecimento-nao-e-pedido` (a etapa não pode avançar) e `aceita-complemento` (a resposta precisa falar do carrinho e não pode ter "combinado" nem "anotado").

**Quando rodar.** Só quando algo do assistente muda: um prompt, o modelo ou os dados da loja. A avaliação chama a OpenAI e tem custo (menos de US$ 0,50 por execução completa, com o juiz), por isso fica fora do `pytest`. As regras de conferência, essas sim, têm testes em `tests/test_avaliacao_assistente.py`, com respostas escritas à mão.

```bash
python avaliar_assistente.py                 # duas lojas, 2 rodadas, com juiz
python avaliar_assistente.py --rodadas 3     # como no resultado acima
python avaliar_assistente.py --loja indiano --sem-juiz
```

## Recomendação de restaurantes

O Garfo Certo, um aplicativo de delivery fictício de Belo Horizonte, São Paulo e Rio de Janeiro, pediu à PratoTech uma recomendação de restaurantes: a pessoa escolhe a cidade e a culinária e recebe os 10 restaurantes mais indicados, em vez da lista em ordem alfabética.

| Cliente | Solicitação | Proposta | Relatório | Restaurantes | Culinárias |
|---|---|---|---|---|---|
| Garfo Certo | [e-mail](docs/restaurantes/solicitacao-cliente.md) | [proposta](docs/restaurantes/proposta.md) | [relatório](docs/restaurantes/relatorio.md) | 57.382 nas três capitais | 60 |

**Pipeline** (`preparar_restaurantes.py` e `pipeline/restaurantes.py`). Lê do catálogo original só as três capitais, pelo código IBGE, e só as colunas usadas. A nota 0, que no catálogo significa “sem avaliação”, vira ausente; 33 restaurantes com tempo de entrega impossível saem; pedidos mínimos absurdos deixam de ser exibidos. A distância fica de fora, porque foi medida a partir de um endereço fixo. As etiquetas do catálogo são códigos internos de campanha: só três viram palavras (vegetariano, saudável e “bom e barato”). O resultado é o `dados/restaurante/restaurantes.csv`.

**Como funciona** (`modelo/restaurantes.py`). Cada restaurante da cidade e da culinária escolhidas recebe quatro notas de 0 a 1, somadas com pesos ajustáveis (padrão: conteúdo 40%, avaliação 30%, frete 15% e entrega 15%):

| Critério | Cálculo |
|---|---|
| Conteúdo | TF-IDF e cosseno entre os termos que o intérprete extraiu do texto livre (“sushi”, “vegetariano”), já conferidos no catálogo, e o texto do restaurante: nome, culinária, faixa de preço e etiquetas |
| Avaliação | nota ÷ 5; sem avaliação, a nota do primeiro quartil da cidade (cerca de 4,3) |
| Frete | R$ 0 vale 1 e R$ 15 ou mais vale 0 |
| Entrega | 20 minutos ou menos vale 1 e 70 minutos ou mais vale 0 |

O texto livre passa antes pelo intérprete com LLM ([por quê](#por-que-um-llm-na-busca-de-restaurantes)): “quero um restaurante japonês” vira o filtro da culinária Japonesa, e “temaki barato” vira os termos “temaki” e “barato”. Sem texto livre, ou sem termos conferidos, o peso do conteúdo é dividido entre os outros critérios. Unidades de uma mesma rede aparecem uma vez. Cada restaurante vem com uma frase montada a partir dos dados, por exemplo “Nota 4,8 · frete grátis · entrega em cerca de 40 min · combina com o pedido: culinária japonesa e “sushi””. A busca é validada antes (`modelo/validacao_restaurantes.py`), no mesmo formato de erros do carrinho: culinária inexistente na cidade, texto acima de 200 caracteres e pesos negativos, não numéricos, não finitos, desconhecidos ou todos zero.

**Avaliação** (`avaliar_restaurantes.py`). O catálogo não registra quais restaurantes as pessoas escolheram, então não há “acerto” para medir. O top 10 é comparado com a lista atual do cliente, em ordem alfabética, e com ordenações por um critério só, nas 5 culinárias mais comuns de cada cidade:

| Forma de ordenar | Nota média | Sem avaliação | Frete médio | Tempo médio |
|---|---|---|---|---|
| Ordem alfabética (lista atual) | 4,47 | 45% | R$ 7,60 | 47 min |
| Só a nota | 5,00 | 0% | R$ 8,00 | 45 min |
| Só o frete | 4,94 | 2% | R$ 0,00 | 42 min |
| Só o tempo | 4,83 | 2% | R$ 4,45 | 19 min |
| **Sistema híbrido** | **4,83** | **8%** | **R$ 0,32** | **23 min** |

- **Equilíbrio:** cada ordenação por um critério só ganha nesse critério e perde nos outros; o sistema híbrido fica perto do melhor nos quatro.
- **Texto livre:** em 8 buscas como “sushi” e “poke”, 87% do top 10 combina com o texto, contra 5% na ordem só pela nota. Os termos abaixo de 100% são raros em alguma cidade: Belo Horizonte não tem nenhum restaurante com “temaki”.
- **Pesos:** dobrar o peso da avaliação troca 3 dos 10 restaurantes; dobrar o do frete quase não muda nada, porque o top 10 já é quase todo de frete grátis.
- **Primeira versão:** premiava quem repetia a culinária no nome (“Yama Gastronomia Japonesa”) e punha restaurantes sem avaliação na frente dos bem avaliados, porque usava a nota mediana (4,67). As duas coisas foram corrigidas antes da avaliação.

**Simulação no site.** Dois restaurantes reais do catálogo de São Paulo, que já estavam no top 10 das buscas por culinária, representam as lojas do projeto: o Rica Pancita (Mexicana, 3º lugar) aparece como **Sabor na Mesa** e o Queen's Kitchen (Indiana, 2º lugar) como **Casa Masala** (`LOJAS_PARCEIRAS`, em `cidades.py`). A API devolve o campo `loja` só para eles, e no site só esses dois têm o link “Ver cardápio e pedir”, que abre a página da loja, com as sugestões por associação e o chat. Os demais ficam sem link, porque este é um MVP. Para ver o caminho completo: escolha São Paulo e Mexicana (ou Indiana) na página inicial.

O catálogo tratado já vem no repositório. Para gerar de novo, coloque o original em `dados/restaurante/restaurants.csv` e execute `python preparar_restaurantes.py`.

## Como executar

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha OPENAI_API_KEY (opcional: o cardápio já vem pronto)
python analise_dados.py
python gerar_regras.py
python avaliar.py
python avaliar_restaurantes.py
python -m pytest
python api.py   # API em http://127.0.0.1:8000; documentação das rotas em /docs
```

No PyCharm, selecione o interpretador `.venv` do projeto e execute, nesta ordem, `analise_dados.py`, `gerar_regras.py` e `avaliar.py`. Cada script processa as duas lojas, e `avaliar.py` salva o resultado em `dados/<loja>/avaliacao.csv`. Os testes ficam na pasta `tests/` e podem ser executados pelo PyCharm ou com `python -m pytest`. Por fim, `api.py` liga a API; com ela no ar, as rotas podem ser testadas pelo navegador em `http://127.0.0.1:8000/docs`. O chat precisa da chave da OpenAI no `.env`.

### Abrir o frontend

Com a API em execução na porta 8000 e os arquivos de dados gerados, abra um segundo terminal na raiz do projeto. Use Node.js 20.19 ou superior, ou Node.js 22.12 ou superior.

```bash
cd frontend
npm ci
npm run dev
```

Abra [o site local](http://127.0.0.1:5173). A página inicial é a busca de restaurantes do Garfo Certo. Escolha São Paulo e Mexicana (ou Indiana) e clique em **Ver cardápio e pedir** na Sabor na Mesa (ou na Casa Masala). Na página da loja, adicione um prato e clique em **Ver sugestões**. Ao adicionar ou remover itens, a tela atualiza as sugestões com as frases enviadas pela API. Cada loja guarda seu carrinho e a conversa na sessão da aba, e a busca de restaurantes também fica guardada ao voltar. **Nova conversa** limpa o histórico daquela loja. A escolha direta das duas lojas continua em `#/lojas`. Ao trocar de cidade, a culinária escolhida continua se existir na cidade nova; se não existir, a busca volta para todas as culinárias, com aviso. O texto livre só é enviado quando a pessoa para de digitar. A chave da OpenAI fica apenas no backend.

O site é feito em React com Vite, com um componente por arquivo em `frontend/src/`. A página inicial é a busca de restaurantes, em `garfo/` (`BuscaRestaurantes.jsx`, `Ranking.jsx`, `consulta.js`, `pesos.js` e `garfo.css`, com os estilos escopados na classe `.garfo`). A escolha direta das lojas fica em `Entrada.jsx`. Cada loja fica em `Restaurante.jsx`, com `Cardapio.jsx`, `Pedido.jsx` e `Chat.jsx`. O `useConsulta.js` faz as chamadas à API. As fontes são instaladas pelo npm e servidas pelo próprio site. O código segue a formatação do Prettier: `npm run formatar` formata os arquivos, e `npm run conferir-formato` confere a formatação.

O Vite encaminha `/api` para `http://127.0.0.1:8000` durante o desenvolvimento. O comando `npm run build` gera o site estático em `frontend/dist/`. Para hospedagem separada, configure o encaminhamento de `/api` ao backend na hospedagem ou defina `VITE_API_BASE` com a origem pública do backend antes do build e inclua a origem do frontend em `ORIGENS_PERMITIDAS`.

## Publicação

O site fica na Vercel, em [mvp-recomendacao.vercel.app](https://mvp-recomendacao.vercel.app), e a API fica no Render, em `https://mvp-recomendacao-api.onrender.com`. O site chama `/api` no próprio endereço, e a Vercel repassa as chamadas ao Render ([`frontend/vercel.json`](frontend/vercel.json)). Assim, o navegador não precisa falar direto com a API.

| Serviço | Configuração | O que faz |
|---|---|---|
| Render | [`render.yaml`](render.yaml) | instala as dependências, gera `pedidos_limpos.csv` e `regras.csv` das duas lojas e liga a API com o `uvicorn`; a rota `/api/saude` mostra que ela está no ar |
| Vercel | [`frontend/vercel.json`](frontend/vercel.json) | publica o site da pasta `frontend/` e repassa `/api` ao Render |

A chave da OpenAI fica só nas variáveis de ambiente do Render. No plano gratuito, a API dorme depois de 15 minutos sem uso, e a primeira chamada depois disso leva até um minuto. Antes de uma apresentação, vale abrir o site alguns minutos antes. Se a API reiniciar no meio de uma conversa, o chat avisa que a conversa anterior expirou.
