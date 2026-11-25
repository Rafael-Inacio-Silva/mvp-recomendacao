import React from 'react'
import { criterios } from './pesos'

const real = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
})
const numero = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 })
export function Aviso({ consulta }) {
  return (
    <div role="alert" className="gAviso">
      {consulta.erro} <button onClick={consulta.repetir}>Tentar novamente</button>
    </div>
  )
}

function Restaurante({ r, posicao, pesos }) {
  return (
    <li className="cartao">
      <div className="cabCard">
        <span className="posicao" aria-label={'Posição ' + posicao}>
          {String(posicao).padStart(2, '0')}
        </span>
        <div className="nome">
          <span className="culinaria">{r.culinaria}</span>
          {/* Só as lojas com site próprio no MVP têm link */}
          <h3>{r.loja ? <a href={'#/' + r.loja + '/cardapio'}>{r.nome}</a> : r.nome}</h3>
        </div>
        <div className="score">
          <strong>{numero.format(r.pontuacao * 100)}</strong>
          <small>/ 100 pts</small>
        </div>
      </div>
      <dl className="metricas">
        <div>
          <dt>Avaliação</dt>
          <dd>{r.avaliado ? '★ ' + numero.format(r.nota) : 'Sem avaliação'}</dd>
        </div>
        <div>
          <dt>Frete</dt>
          <dd>{r.frete === 0 ? 'Grátis' : real.format(r.frete)}</dd>
        </div>
        <div>
          <dt>Entrega</dt>
          <dd>{r.tempo} min</dd>
        </div>
      </dl>
      {r.loja && (
        <a className="irLoja" href={'#/' + r.loja + '/cardapio'}>
          Ver cardápio e pedir →
        </a>
      )}
      <details>
        <summary>Como chegou a essa pontuação?</summary>
        <p>{r.explicacao}</p>
        {Object.entries(criterios).map(([c, label]) => {
          const pontos = r.partes[c] * pesos[c] * 100
          return (
            <div className="parte" key={c}>
              <span>{label}</span>
              <div className="trilho">
                <i
                  style={{
                    width: pontos + '%',
                    background: 'var(--' + c + ')',
                  }}
                />
              </div>
              <strong>{numero.format(pontos)} pts</strong>
            </div>
          )
        })}
        <small>Contribuições aproximadas em uma escala de 100 pontos.</small>
      </details>
    </li>
  )
}
export function Ranking({ consulta, cidade }) {
  return (
    <section id="ranking" aria-labelledby="tituloRanking">
      <div className="tituloRanking">
        <h2 id="tituloRanking">Restaurantes recomendados</h2>
        {consulta.dados && <span>{consulta.dados.restaurantes.length} resultados</span>}
      </div>
      <p className="local" aria-live="polite">
        {cidade}
      </p>
      {consulta.erro ? (
        <Aviso consulta={consulta} />
      ) : !consulta.dados ? (
        <p role="status">Buscando recomendações…</p>
      ) : consulta.dados.restaurantes.length ? (
        <ol>
          {consulta.dados.restaurantes.map((r, i) => (
            <Restaurante key={r.nome} r={r} posicao={i + 1} pesos={consulta.dados.pesos} />
          ))}
        </ol>
      ) : (
        <p>Nenhum restaurante encontrado para esta busca.</p>
      )}
    </section>
  )
}
