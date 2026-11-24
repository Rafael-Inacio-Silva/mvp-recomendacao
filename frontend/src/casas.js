// Textos e imagens de cada loja; os dados de negócio (endereço, horário) seguem dados/<loja>/loja.md
export const casas = {
  mexicano: {
    nome: 'Sabor na Mesa',
    cozinha: 'Cozinha mexicana',
    bairro: 'Pinheiros',
    resumo: 'Burritos, bowls, tacos e guacamole da casa.',
    titulo: 'Comida de verdade, feita na casa.',
    subtitulo: 'Tortilhas, guacamole e molhos preparados aqui todos os dias.',
    capa: 'tacos',
    capaChat: 'burrito-capa',
    avatar: 'lupe',
    sobre:
      'Desde 2019, a Sabor na Mesa prepara tortilhas, guacamole e molhos todos os dias em Pinheiros.',
    endereco: 'Rua dos Pinheiros, 1000 · São Paulo',
    perguntas: [
      'O bowl vegetariano é picante?',
      'O que costuma sair junto com nachos?',
      'Qual é o horário da casa?',
    ],
  },
  indiano: {
    nome: 'Casa Masala',
    cozinha: 'Cozinha indiana',
    bairro: 'Vila Madalena',
    resumo: 'Curries, biryanis e pães do forno tandoor.',
    titulo: 'Especiarias à mesa.',
    subtitulo: 'Descubra curries, arrozes perfumados e pães do forno tandoor.',
    capa: 'indiano',
    capaChat: 'indiano',
    avatar: null,
    sobre:
      'Desde 2016, a Casa Masala serve curries, biryanis e grelhados do forno tandoor na Vila Madalena.',
    endereco: 'Rua Harmonia, 2000 · São Paulo',
    perguntas: [
      'O que tem no arroz pilau?',
      'O que costuma sair junto com o naan simples?',
      'Qual é o horário da casa?',
    ],
  },
}

// Nome do arquivo da foto: sem acentos, minúsculo e com hífens ("Água Mineral" → agua-mineral.webp)
export function fotoProduto(loja, item) {
  const nome = item
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
  return '/imagens/produtos/' + loja + '/' + nome + '.webp'
}

export const foto = (nome) => '/imagens/' + nome + '.jpg'

// Rotas pelo hash: #/<loja>/<pagina>
export const rota = (loja, pagina = 'cardapio') => '#/' + loja + '/' + pagina
