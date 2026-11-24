import React, { useState } from 'react'
import { foto, fotoProduto, rota } from './casas'
import { Aviso, Icone } from './ui'
import { BotaoItem, ListaDoPedido } from './ItensDoPedido'

const PRATOS_POR_VEZ = 12

// Busca sem diferença de acentos, maiúsculas e minúsculas
const normalizar = (texto) => texto.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

function CartaoPrato({ loja, produto, selecionado, alterar }) {
  return (
    <article className="prato">
      <img
        className="fotoPrato"
        loading="lazy"
        src={fotoProduto(loja, produto.item)}
        width="100"
        height="100"
        alt=""
      />
      <div>
        <small className="rotulo">{produto.categoria}</small>
        <h3>{produto.item}</h3>
        <details>
          <summary>Ingredientes e descrição</summary>
          <p>{produto.descricao}</p>
        </details>
        <BotaoItem item={produto.item} selecionado={selecionado} alterar={alterar} />
      </div>
    </article>
  )
}

// Lateral com o carrinho e a primeira sugestão para o pedido atual
function ResumoDoPedido({ loja, carrinho, alterar, sugestoes }) {
  const primeira = sugestoes.dados?.sugestoes?.[0]
  return (
    <aside className="painel resumo">
      <h2>Seu pedido</h2>
      <ListaDoPedido loja={loja} carrinho={carrinho} remover={alterar} />
      {primeira && (
        <div className="previa" aria-live="polite">
          <small className="rotulo">
            <Icone nome="brilho" tam={14} /> Combina com seu pedido
          </small>
          <p>{primeira.frase}</p>
        </div>
      )}
      {carrinho.length > 0 && (
        <a className="botao" href={rota(loja, 'pedido')}>
          Ver sugestões <Icone nome="seta" />
        </a>
      )}
      <small>Carrinho de demonstração</small>
    </aside>
  )
}

export default function Cardapio({
  loja,
  casa,
  carrinho,
  alterar,
  menu,
  recarregarMenu,
  sugestoes,
}) {
  const [categoria, setCategoria] = useState('Todos')
  const [busca, setBusca] = useState('')
  const [limite, setLimite] = useState(PRATOS_POR_VEZ)

  const produtos = menu.dados?.itens || []
  const categorias = ['Todos', ...new Set(produtos.map((p) => p.categoria))]
  const termo = normalizar(busca.trim())
  const filtrados = produtos.filter(
    (p) =>
      (categoria === 'Todos' || p.categoria === categoria) && normalizar(p.item).includes(termo),
  )

  let titulo = 'Mais pedidos por aqui'
  if (categoria !== 'Todos') titulo = categoria
  else if (busca) titulo = 'Resultados'

  // Trocar o filtro volta a mostrar só os primeiros pratos
  function escolherCategoria(nova) {
    setCategoria(nova)
    setLimite(PRATOS_POR_VEZ)
  }
  function buscar(texto) {
    setBusca(texto)
    setLimite(PRATOS_POR_VEZ)
  }

  let pratos
  if (menu.erro) {
    pratos = <Aviso texto={menu.erro} repetir={recarregarMenu} />
  } else if (menu.carregando) {
    pratos = <p role="status">Carregando o cardápio…</p>
  } else {
    pratos = (
      <>
        {!filtrados.length && <p>Nenhum item encontrado.</p>}
        <div className="gradePratos">
          {filtrados.slice(0, limite).map((p) => (
            <CartaoPrato
              key={p.item}
              loja={loja.loja}
              produto={p}
              selecionado={carrinho.includes(p.item)}
              alterar={alterar}
            />
          ))}
        </div>
        {filtrados.length > limite && (
          <button className="contorno mais" onClick={() => setLimite(limite + PRATOS_POR_VEZ)}>
            Mostrar mais pratos
          </button>
        )}
      </>
    )
  }

  return (
    <>
      <div className="hero" style={{ '--capa': 'url(' + foto(casa.capa) + ')' }}>
        <div className="largura">
          <p className="rotulo">{casa.cozinha}</p>
          <h1>{casa.titulo}</h1>
          <p>{casa.subtitulo}</p>
        </div>
      </div>

      <div className="largura colMenu">
        <section>
          <div className="categorias" aria-label="Categorias">
            {categorias.map((c) => (
              <button
                key={c}
                className={categoria === c ? 'ativo' : ''}
                aria-pressed={categoria === c}
                onClick={() => escolherCategoria(c)}
              >
                {c}
              </button>
            ))}
          </div>
          <div className="tituloMenu">
            <h2>{titulo}</h2>
            <label className="busca">
              <Icone nome="busca" tam={17} />
              <input
                type="search"
                aria-label="Buscar no cardápio"
                placeholder="Buscar prato"
                value={busca}
                onChange={(e) => buscar(e.target.value)}
              />
            </label>
          </div>
          {pratos}
        </section>
        <ResumoDoPedido
          loja={loja.loja}
          carrinho={carrinho}
          alterar={alterar}
          sugestoes={sugestoes}
        />
      </div>

      <a className="flutuante" href={rota(loja.loja, 'chat')}>
        <Icone nome="conversa" /> Converse com a {loja.atendente}
      </a>
    </>
  )
}
