import React from 'react'
import { fotoProduto } from './casas'
import { Icone } from './ui'

export function Miniatura({ loja, item }) {
  return <img className="mini" src={fotoProduto(loja, item)} alt="" />
}

export function ListaDoPedido({ loja, carrinho, remover }) {
  if (!carrinho.length) {
    return (
      <div className="vazio">
        <Icone nome="sacola" tam={30} />
        <p>Seu pedido está vazio.</p>
        <small>Escolha um item do cardápio para descobrir combinações.</small>
      </div>
    )
  }
  return (
    <ul className="itens">
      {carrinho.map((item) => (
        <li key={item}>
          <Miniatura loja={loja} item={item} />
          <strong>{item}</strong>
          <button className="icone" aria-label={'Remover ' + item} onClick={() => remover(item)}>
            <Icone nome="remover" tam={17} />
          </button>
        </li>
      ))}
    </ul>
  )
}

// Botão que adiciona o item ou, se ele já estiver no pedido, remove
export function BotaoItem({ item, selecionado, alterar }) {
  return (
    <button
      className={'botao' + (selecionado ? ' selecionado' : '')}
      aria-label={(selecionado ? 'Remover ' : 'Adicionar ') + item}
      aria-pressed={selecionado}
      onClick={() => alterar(item)}
    >
      <Icone nome={selecionado ? 'ok' : 'mais'} tam={17} />
      {selecionado ? 'No pedido' : 'Adicionar'}
    </button>
  )
}
