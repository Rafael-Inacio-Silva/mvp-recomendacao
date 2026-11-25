import { useEffect, useState } from 'react'

export function useConsulta(caminho, corpo = null) {
  const [tentativa, repetir] = useState(0)
  const [resposta, registrar] = useState({})
  const chave = JSON.stringify([caminho, corpo, tentativa])
  useEffect(() => {
    if (!caminho) return
    const controle = new AbortController()
    async function consultar() {
      try {
        const opcoes = { signal: controle.signal }
        if (corpo)
          Object.assign(opcoes, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: corpo,
          })
        const r = await fetch('/api/restaurantes/' + caminho, opcoes)
        const json = await r.json().catch(() => null)
        if (!r.ok || !json)
          throw new Error(
            json?.errors?.map((e) => e.message).join(' ') ||
              'Não foi possível consultar o catálogo.',
          )
        if (!controle.signal.aborted) registrar({ chave, dados: json })
      } catch (e) {
        if (!controle.signal.aborted) registrar({ chave, erro: e.message })
      }
    }
    const timer = setTimeout(consultar, corpo ? 240 : 0)
    return () => {
      clearTimeout(timer)
      controle.abort()
    }
  }, [caminho, corpo, chave])
  return {
    ...(chave === resposta.chave ? resposta : {}),
    repetir: () => repetir((v) => v + 1),
  }
}
