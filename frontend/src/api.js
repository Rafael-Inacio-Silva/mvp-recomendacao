const base = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

export async function consultar(caminho, { method = 'GET', dados, signal } = {}) {
  let resposta
  try {
    resposta = await fetch(base + '/api/' + caminho, {
      method,
      signal,
      headers: dados ? { 'Content-Type': 'application/json' } : undefined,
      body: dados ? JSON.stringify(dados) : undefined,
    })
  } catch (erro) {
    if (erro.name === 'AbortError') throw erro
    throw new Error('Não foi possível conectar. Confira a conexão e tente novamente.')
  }
  const json = await resposta.json().catch(() => null)
  if (!resposta.ok || !json || json.ok === false) {
    throw new Error(
      json?.errors?.[0]?.message ||
        json?.resposta ||
        'O serviço está indisponível. Tente novamente.',
    )
  }
  return json
}

export function lerSessao(chave, padrao) {
  try {
    return JSON.parse(sessionStorage.getItem(chave)) ?? padrao
  } catch {
    return padrao
  }
}

export function gravarSessao(chave, dados) {
  try {
    sessionStorage.setItem(chave, JSON.stringify(dados))
  } catch {
    // Em navegadores com armazenamento restrito, a seleção permanece na memória.
  }
}
