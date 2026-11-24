import React, { useEffect, useRef, useState } from 'react'
import { gravarSessao, lerSessao } from './api'
import { casas, rota } from './casas'
import { useConsulta } from './useConsulta'
import { Icone, Marca } from './ui'
import Cardapio from './Cardapio'
import Pedido from './Pedido'
import Chat from './Chat'

function Topo({ id, casa, pagina, quantidade, abrirSobre }) {
  return (
    <header className="topo">
      <div className="largura">
        <a className="palavra" href="#/" aria-label="PratoTech, escolher restaurante">
          <Marca />
          {casa.nome}
        </a>
        <nav>
          <a href={rota(id)} aria-current={pagina === 'cardapio' ? 'page' : undefined}>
            Cardápio
          </a>
          <button onClick={abrirSobre}>Sobre a casa</button>
        </nav>
        <span className="onde">
          <Icone nome="local" tam={16} />
          {casa.bairro}, São Paulo
        </span>
        <a
          className="contorno cestaTopo"
          href={rota(id, 'pedido')}
          aria-current={pagina === 'pedido' ? 'page' : undefined}
        >
          <Icone nome="sacola" tam={18} /> Meu pedido ({quantidade})
        </a>
      </div>
    </header>
  )
}

// Uma loja: cardápio, pedido e chat, com o carrinho guardado na sessão da aba
export default function Restaurante({ loja, pagina, visivel }) {
  const id = loja.loja
  const casa = casas[id]
  const chaveSessao = 'pratotech:pedido:' + id
  const [carrinho, setCarrinho] = useState(() => lerSessao(chaveSessao, []))
  const [menu, recarregarMenu] = useConsulta('lojas/' + id + '/cardapio')
  // Sugestões só para a loja aberta e com carrinho preenchido
  const caminhoSugestoes = visivel && carrinho.length ? 'lojas/' + id + '/sugestoes' : ''
  const [sugestoes, repetirSugestoes] = useConsulta(caminhoSugestoes, JSON.stringify(carrinho))
  const sobre = useRef(null)

  useEffect(() => {
    gravarSessao(chaveSessao, carrinho)
  }, [chaveSessao, carrinho])

  // Adiciona o item ou, se ele já estiver no carrinho, remove
  function alterar(item) {
    setCarrinho((itens) =>
      itens.includes(item) ? itens.filter((i) => i !== item) : [...itens, item],
    )
  }

  return (
    <div hidden={!visivel} className={'loja ' + id}>
      <Topo
        id={id}
        casa={casa}
        pagina={pagina}
        quantidade={carrinho.length}
        abrirSobre={() => sobre.current.showModal()}
      />
      <main>
        {/* O cardápio fica montado (oculto) para manter o filtro e a busca ao trocar de página */}
        <div hidden={pagina !== 'cardapio'}>
          <Cardapio
            loja={loja}
            casa={casa}
            carrinho={carrinho}
            alterar={alterar}
            menu={menu}
            recarregarMenu={recarregarMenu}
            sugestoes={sugestoes}
          />
        </div>
        {pagina === 'pedido' && (
          <Pedido
            loja={loja}
            carrinho={carrinho}
            alterar={alterar}
            sugestoes={sugestoes}
            repetir={repetirSugestoes}
          />
        )}
        <Chat loja={loja} casa={casa} ativa={visivel && pagina === 'chat'} />
      </main>

      <dialog ref={sobre} aria-label="Sobre a casa">
        <h2>{casa.nome}</h2>
        <p>{casa.sobre}</p>
        <p className="bairro">
          <Icone nome="local" />
          {casa.endereco}
        </p>
        <form method="dialog">
          <button className="botao">Fechar</button>
        </form>
      </dialog>
    </div>
  )
}
