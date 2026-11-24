import React, { useEffect, useRef, useState } from 'react'
import { consultar, gravarSessao, lerSessao } from './api'
import { foto, rota } from './casas'
import { Aviso, Icone } from './ui'

const TEMAS = [
  ['prato', 'Cardápio e ingredientes'],
  ['brilho', 'Combinações de pedidos'],
  ['local', 'Horários e informações da loja'],
]

function novaConversa() {
  return { id: crypto.randomUUID(), mensagens: [] }
}

function Mensagens({ loja, casa, mensagens, pendente, lista }) {
  return (
    <div className="mensagens" role="log" aria-live="polite" ref={lista}>
      <div className="saudacao">
        {casa.avatar && <img src={foto(casa.avatar)} alt="" />}
        <p>
          Oi! Sou a {loja.atendente}. Posso ajudar com o cardápio, combinações ou informações da
          casa.
        </p>
      </div>
      {mensagens.map((par, i) => (
        <React.Fragment key={i}>
          <p className="cliente">{par.mensagem}</p>
          <p className="assistente">{par.resposta}</p>
        </React.Fragment>
      ))}
      {pendente && (
        <>
          <p className="cliente">{pendente}</p>
          <p className="assistente">{loja.atendente} está respondendo…</p>
        </>
      )}
    </div>
  )
}

// Conversa com a assistente da loja; o histórico fica na sessão da aba e na memória da API
export default function Chat({ loja, casa, ativa }) {
  const chaveSessao = 'pratotech:chat:' + loja.loja
  const [conversa, setConversa] = useState(() => lerSessao(chaveSessao, null) || novaConversa())
  const [texto, setTexto] = useState('')
  const [pendente, setPendente] = useState('')
  const [ocupado, setOcupado] = useState(false)
  const [erro, setErro] = useState('')
  const [aviso, setAviso] = useState('')
  const lista = useRef(null)
  const caminho = 'lojas/' + loja.loja + '/chat'

  useEffect(() => {
    gravarSessao(chaveSessao, conversa)
  }, [chaveSessao, conversa])

  // Rola até a última mensagem
  useEffect(() => {
    if (ativa && lista.current) lista.current.scrollTop = lista.current.scrollHeight
  }, [ativa, conversa, pendente, erro])

  async function enviar(pergunta) {
    const mensagem = pergunta.trim()
    if (!mensagem || ocupado) return
    setOcupado(true)
    setPendente(mensagem)
    setTexto('')
    setErro('')
    setAviso('')
    try {
      const r = await consultar(caminho, {
        method: 'POST',
        dados: { mensagem, conversa_id: conversa.id },
      })
      const par = { mensagem, resposta: r.resposta }
      // A API não tinha mais esta conversa (reiniciou ou descartou): o histórico da tela não vale
      const expirou = r.nova_conversa && conversa.mensagens.length > 0
      if (expirou) {
        setAviso(
          `A conversa anterior expirou, e a ${loja.atendente} começou uma nova a partir desta mensagem.`,
        )
      }
      setConversa((atual) => ({
        ...atual,
        mensagens: expirou ? [par] : [...atual.mensagens, par],
      }))
    } catch (e) {
      setErro(e.message)
      setTexto(mensagem)
    } finally {
      setOcupado(false)
      setPendente('')
    }
  }

  async function reiniciar() {
    if (ocupado) return
    setOcupado(true)
    setErro('')
    setAviso('')
    try {
      await consultar(caminho + '/' + conversa.id, { method: 'DELETE' })
      setConversa(novaConversa())
      setTexto('')
    } catch (e) {
      setErro(e.message)
    } finally {
      setOcupado(false)
    }
  }

  // Sugestões de pergunta só na conversa vazia
  const mostrarPerguntas = !conversa.mensagens.length && !pendente

  return (
    <section hidden={!ativa}>
      <div className="hero chatHero" style={{ '--capa': 'url(' + foto(casa.capaChat) + ')' }}>
        <div className="largura">
          <a className="link" href={rota(loja.loja)}>
            <Icone nome="voltar" /> Voltar ao cardápio
          </a>
          <h1>Converse com a {loja.atendente}</h1>
          <p>Sua assistente da {casa.nome}.</p>
        </div>
      </div>

      <div className="largura colChat">
        <div className="painel conversa">
          <div className="chatTopo">
            <strong>
              <Icone nome="conversa" /> {loja.atendente}
            </strong>
            <button className="link" disabled={ocupado} onClick={reiniciar}>
              <Icone nome="reiniciar" tam={16} /> Nova conversa
            </button>
          </div>
          <Mensagens
            loja={loja}
            casa={casa}
            mensagens={conversa.mensagens}
            pendente={pendente}
            lista={lista}
          />
          {aviso && <Aviso texto={aviso} />}
          {erro && <Aviso texto={erro} />}
          {mostrarPerguntas && (
            <div className="perguntas">
              {casa.perguntas.map((p) => (
                <button key={p} disabled={ocupado} onClick={() => enviar(p)}>
                  {p}
                </button>
              ))}
            </div>
          )}
          <form
            className="compor"
            onSubmit={(e) => {
              e.preventDefault()
              enviar(texto)
            }}
          >
            <input
              aria-label="Sua mensagem"
              placeholder="Escreva sua dúvida…"
              maxLength={1000}
              disabled={ocupado}
              value={texto}
              onChange={(e) => setTexto(e.target.value)}
            />
            <button
              className="botao"
              aria-label="Enviar mensagem"
              disabled={ocupado || !texto.trim()}
            >
              <Icone nome="enviar" />
            </button>
          </form>
        </div>

        <aside className="painel ajuda">
          <h2>Posso ajudar com</h2>
          {TEMAS.map(([icone, tema]) => (
            <p key={tema}>
              <Icone nome={icone} />
              {tema}
            </p>
          ))}
        </aside>
      </div>
    </section>
  )
}
