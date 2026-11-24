import React from 'react'
import { rota } from './casas'
import { Aviso, Icone } from './ui'
import { BotaoItem, ListaDoPedido, Miniatura } from './ItensDoPedido'

function Sugestoes({ loja, carrinho, sugestoes, repetir, alterar }) {
  if (!carrinho.length) return <p>Adicione um prato para ver sugestões.</p>
  if (sugestoes.erro) return <Aviso texto={sugestoes.erro} repetir={repetir} />
  if (sugestoes.carregando) return <p>Buscando combinações…</p>

  const lista = sugestoes.dados?.sugestoes || []
  if (!lista.length) return <p>Você já explorou todas as sugestões disponíveis.</p>

  return lista.map((s) => (
    <article className="sugestao" key={s.item}>
      <Miniatura loja={loja} item={s.item} />
      <div>
        <h3>{s.item}</h3>
        <p>{s.frase}</p>
      </div>
      <BotaoItem item={s.item} alterar={alterar} />
    </article>
  ))
}

export default function Pedido({ loja, carrinho, alterar, sugestoes, repetir }) {
  return (
    <div className="largura areaPedido">
      <a className="link" href={rota(loja.loja)}>
        <Icone nome="voltar" tam={17} /> Voltar ao cardápio
      </a>
      <h1>Seu pedido</h1>
      <p>Revise sua seleção e descubra o que costuma sair junto.</p>

      <div className="colPedido">
        <section className="painel">
          <h2>Sua seleção</h2>
          <ListaDoPedido loja={loja.loja} carrinho={carrinho} remover={alterar} />
          <a className="link" href={rota(loja.loja)}>
            Continuar escolhendo <Icone nome="seta" tam={16} />
          </a>
        </section>
        <section className="sugestoes">
          <p className="rotulo">
            <Icone nome="brilho" tam={15} /> Sugestões da casa
          </p>
          <h2>Que tal completar?</h2>
          <div aria-live="polite">
            <Sugestoes
              loja={loja.loja}
              carrinho={carrinho}
              sugestoes={sugestoes}
              repetir={repetir}
              alterar={alterar}
            />
          </div>
        </section>
      </div>

      <a className="botao verde" href={rota(loja.loja, 'chat')}>
        <Icone nome="conversa" /> Converse com a {loja.atendente}
      </a>
    </div>
  )
}
