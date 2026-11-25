export const criterios = {
  conteudo: 'Preferência escrita',
  avaliacao: 'Avaliação',
  frete: 'Taxa de entrega',
  entrega: 'Tempo de entrega',
}
export const padrao = { conteudo: 40, avaliacao: 30, frete: 15, entrega: 15 }
export const semTexto = { conteudo: 0, avaliacao: 50, frete: 25, entrega: 25 }

// Distribui somente os percentuais dos controles. As recomendações e suas notas vêm da API.
export function ajustar(atual, criterio, valor, base) {
  const outros = Object.keys(base).filter((c) => c !== criterio && base[c] > 0)
  const referencia = outros.some((c) => atual[c] > 0) ? atual : base
  const soma = outros.reduce((s, c) => s + referencia[c], 0)
  const partes = outros.map((c) => ({
    c,
    exato: ((100 - valor) * referencia[c]) / soma,
  }))
  const proximo = { ...atual, [criterio]: valor }
  for (const { c, exato } of partes) proximo[c] = Math.floor(exato)
  const faltam = 100 - Object.values(proximo).reduce((a, b) => a + b, 0)
  partes.sort((a, b) => (b.exato % 1) - (a.exato % 1))
  for (const { c } of partes.slice(0, faltam)) proximo[c]++
  return proximo
}
