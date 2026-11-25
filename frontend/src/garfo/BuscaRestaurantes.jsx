import React, { useEffect, useState } from 'react'
import { gravarSessao, lerSessao } from '../api'
import { useConsulta } from './consulta'
import { ajustar, criterios, padrao, semTexto } from './pesos'
import { Aviso, Ranking } from './Ranking'
import './garfo.css'

const CHAVE_SESSAO = 'pratotech:restaurantes'

// Rolagem para as seções; o hash da página fica reservado para as rotas das lojas
function rolarPara(id) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

function Cabecalho() {
  return (
    <>
      <header>
        <div className="gLargura gTopo">
          <a href="#/" className="gMarca">
            <span className="simbolo" aria-hidden="true">
              <i />
              <i />
              <i />
              <b />
            </span>
            PratoTech
          </a>
          <span className="produto">Garfo Certo</span>
          <nav>
            <button onClick={() => rolarPara('busca')}>Busca</button>
            <button onClick={() => rolarPara('ranking')}>Ranking</button>
          </nav>
        </div>
      </header>
      <div className="gHero">
        <div className="gLargura">
          <h1>Onde pedir hoje?</h1>
          <p>Escolha a cidade e diga o que pesa mais no seu pedido.</p>
        </div>
      </div>
    </>
  )
}

function Explorar({ cidades }) {
  // A busca fica na sessão da aba, para voltar igual depois de visitar uma loja
  const salvo = lerSessao(CHAVE_SESSAO, {})
  const [id, setId] = useState(
    cidades.some((c) => c.cidade === salvo.id) ? salvo.id : cidades[0].cidade,
  )
  const [culinaria, setCulinaria] = useState(salvo.culinaria || '')
  const [texto, setTexto] = useState(salvo.texto || '')
  const [perfis, setPerfis] = useState(salvo.perfis || { com: padrao, sem: semTexto })
  const temTexto = Boolean(texto.trim())
  const perfil = temTexto ? 'com' : 'sem'
  const base = temTexto ? padrao : semTexto
  const pesos = perfis[perfil]
  const opcoes = useConsulta(id + '/culinarias')
  const ranking = useConsulta(
    id + '/recomendacoes',
    JSON.stringify({ culinaria: culinaria || null, preferencia: texto.trim(), pesos }),
  )

  useEffect(() => {
    gravarSessao(CHAVE_SESSAO, { id, culinaria, texto, perfis })
  }, [id, culinaria, texto, perfis])

  function mudarPeso(c, valor) {
    setPerfis((p) => ({ ...p, [perfil]: ajustar(p[perfil], c, valor, base) }))
  }

  return (
    <div className="gLargura colunas">
      <aside id="busca">
        <h2>Sua busca</h2>
        <label>
          Cidade
          <select
            value={id}
            onChange={(e) => {
              setId(e.target.value)
              setCulinaria('')
            }}
          >
            {cidades.map((c) => (
              <option key={c.cidade} value={c.cidade}>
                {c.nome}
              </option>
            ))}
          </select>
        </label>
        <label>
          Culinária
          <select
            disabled={!opcoes.dados}
            value={culinaria}
            onChange={(e) => setCulinaria(e.target.value)}
          >
            <option value="">Todas as culinárias</option>
            {opcoes.dados?.culinarias.map((c) => (
              <option key={c.culinaria}>{c.culinaria}</option>
            ))}
          </select>
        </label>
        {opcoes.erro && <Aviso consulta={opcoes} />}
        <label>
          O que você procura?
          <input
            maxLength={200}
            placeholder="Ex.: sushi, vegetariano, barato…"
            value={texto}
            onChange={(e) => setTexto(e.target.value)}
          />
        </label>
        <fieldset>
          <legend>O que mais importa?</legend>
          <p className="dica">
            {temTexto
              ? 'Ajuste um peso para redistribuir os demais.'
              : 'Escreva uma preferência para incluir o texto no cálculo.'}
          </p>
          {Object.entries(criterios).map(([c, nome]) => (
            <label className="peso" key={c}>
              <span>
                {nome}
                <strong>{pesos[c]}%</strong>
              </span>
              <input
                type="range"
                min="0"
                max="100"
                step="1"
                aria-label={nome}
                aria-valuetext={pesos[c] + '%'}
                style={{ accentColor: 'var(--' + c + ')' }}
                disabled={!temTexto && c === 'conteudo'}
                value={pesos[c]}
                onChange={(e) => mudarPeso(c, Number(e.target.value))}
              />
            </label>
          ))}
          <div className="total">
            <span>Total</span>
            <strong>{Object.values(pesos).reduce((a, b) => a + b, 0)}%</strong>
          </div>
          <button className="restaurar" onClick={() => setPerfis({ com: padrao, sem: semTexto })}>
            Restaurar pesos padrão
          </button>
        </fieldset>
      </aside>
      <Ranking consulta={ranking} cidade={cidades.find((c) => c.cidade === id)?.nome} />
    </div>
  )
}

// Página inicial do site: recomendação de restaurantes do Garfo Certo
export default function BuscaRestaurantes() {
  const cidades = useConsulta('cidades')
  return (
    <div className="garfo">
      <Cabecalho />
      <main>
        {cidades.erro ? (
          <div className="gLargura">
            <Aviso consulta={cidades} />
          </div>
        ) : !cidades.dados ? (
          <p className="gLargura" role="status">
            Carregando cidades…
          </p>
        ) : cidades.dados.length ? (
          <Explorar cidades={cidades.dados} />
        ) : (
          <p className="gLargura">Nenhuma cidade disponível.</p>
        )}
      </main>
      <footer className="gLargura">
        PratoTech · Garfo Certo <span>Catálogo de fevereiro de 2021</span>
      </footer>
    </div>
  )
}
