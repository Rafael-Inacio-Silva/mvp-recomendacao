import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource/dm-serif-text'
import '@fontsource-variable/dm-sans'
import './style.css'
import { casas } from './casas'
import { useConsulta } from './useConsulta'
import Entrada from './Entrada'
import Restaurante from './Restaurante'
import BuscaRestaurantes from './garfo/BuscaRestaurantes'

const PAGINAS = ['cardapio', 'pedido', 'chat']

function tituloDaAba(loja, pagina, id) {
  if (!loja)
    return id === 'lojas' ? 'PratoTech · Escolha sua cozinha' : 'Garfo Certo · Onde pedir hoje?'
  const nomes = { cardapio: 'Cardápio', pedido: 'Meu pedido', chat: loja.atendente }
  return nomes[pagina] + ' · ' + casas[loja.loja].nome
}

function App() {
  const [hash, setHash] = useState(location.hash)
  const [estado, repetir] = useConsulta('lojas')
  // Lojas já abertas continuam montadas (ocultas) para não perder o carrinho e o chat
  const [visitadas, setVisitadas] = useState([])

  const lojas = (estado.dados || []).filter((l) => casas[l.loja])
  const [, id, paginaDoHash] = hash.replace(/^#/, '').split('/')
  const pagina = PAGINAS.includes(paginaDoHash) ? paginaDoHash : 'cardapio'
  const ativa = lojas.find((l) => l.loja === id)

  useEffect(() => {
    function navegar() {
      setHash(location.hash)
      window.scrollTo(0, 0)
    }
    window.addEventListener('hashchange', navegar)
    return () => window.removeEventListener('hashchange', navegar)
  }, [])

  useEffect(() => {
    if (ativa) setVisitadas((ids) => (ids.includes(id) ? ids : [...ids, id]))
    document.title = tituloDaAba(ativa, pagina, id)
  }, [ativa, id, pagina])

  return (
    <>
      {/* Início: busca de restaurantes; #/lojas: escolha direta das duas lojas */}
      {!ativa &&
        (id === 'lojas' ? (
          <Entrada lojas={lojas} estado={estado} repetir={repetir} />
        ) : (
          <BuscaRestaurantes />
        ))}
      {lojas
        .filter((l) => l === ativa || visitadas.includes(l.loja))
        .map((l) => (
          <Restaurante key={l.loja} loja={l} visivel={l === ativa} pagina={pagina} />
        ))}
    </>
  )
}

createRoot(document.getElementById('root')).render(<App />)
