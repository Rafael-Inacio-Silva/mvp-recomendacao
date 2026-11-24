import { useEffect, useState } from 'react'
import { consultar } from './api'

// Consulta a API quando o caminho ou o carrinho mudam. Sem carrinho, é um GET; com carrinho, um POST.
export function useConsulta(caminho, carrinhoJSON) {
  const [tentativa, setTentativa] = useState(0)
  const [resultado, setResultado] = useState({})
  const chave = JSON.stringify([caminho, carrinhoJSON, tentativa])

  useEffect(() => {
    if (!caminho) return
    const controle = new AbortController()
    const opcoes = { signal: controle.signal }
    if (carrinhoJSON) {
      opcoes.method = 'POST'
      opcoes.dados = { carrinho: JSON.parse(carrinhoJSON) }
    }
    // Uma consulta cancelada (o carrinho mudou antes da resposta) não altera o resultado
    consultar(caminho, opcoes)
      .then((dados) => {
        if (!controle.signal.aborted) setResultado({ chave, dados })
      })
      .catch((e) => {
        if (!controle.signal.aborted) setResultado({ chave, erro: e.message })
      })
    return () => controle.abort()
  }, [caminho, carrinhoJSON, chave])

  // Resultado de uma consulta anterior não vale para a chave atual
  const estado = resultado.chave === chave ? resultado : { carregando: Boolean(caminho) }
  const repetir = () => setTentativa((t) => t + 1)
  return [estado, repetir]
}
