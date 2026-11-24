import React from 'react'
import { casas, foto, rota } from './casas'
import { Aviso, Icone, Marca } from './ui'

function CartaoCasa({ loja }) {
  const casa = casas[loja.loja]
  return (
    <article className="cartaoCasa">
      <img
        className="fotoCasa"
        src={foto(loja.loja)}
        alt={'Pratos da ' + casa.cozinha.toLowerCase()}
      />
      <div className="conteudoCasa">
        <h2>{casa.nome}</h2>
        <p className="bairro">
          <Icone nome="local" tam={17} />
          {casa.cozinha} · {casa.bairro}
        </p>
        <p>{casa.resumo}</p>
        <a className="botao" href={rota(loja.loja)}>
          Conhecer cardápio <Icone nome="seta" />
        </a>
      </div>
    </article>
  )
}

// Página inicial: escolha da loja
export default function Entrada({ lojas, estado, repetir }) {
  return (
    <main className="entrada largura">
      <header className="cabEntrada">
        <div className="palavra">
          <Marca plataforma />
          PratoTech
        </div>
        <div className="filete" aria-hidden="true">
          <i />
          <b />
          <i />
        </div>
      </header>
      <h1>Escolha onde pedir</h1>
      <p className="intro">Explore o cardápio e descubra combinações para o seu pedido.</p>

      {estado.erro && <Aviso texto={estado.erro} repetir={repetir} />}
      {estado.carregando && <p role="status">Buscando restaurantes…</p>}

      <div className="gradeCasas">
        {lojas.map((loja) => (
          <CartaoCasa key={loja.loja} loja={loja} />
        ))}
      </div>
      <footer>
        <span className="filete pequeno" aria-hidden="true">
          ◆
        </span>{' '}
        Demonstração PratoTech · São Paulo
      </footer>
    </main>
  )
}
