import React from 'react'

// Traço SVG de cada ícone (grade 24 x 24)
const caminhos = {
  seta: 'M4 12h15m-6-6 6 6-6 6',
  voltar: 'M20 12H5m6-6-6 6 6 6',
  local: 'M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0ZM14 10a2 2 0 1 1-4 0 2 2 0 0 1 4 0Z',
  sacola: 'M4 8h16l-1 13H5L4 8Zm4 0V6a4 4 0 0 1 8 0v2',
  conversa: 'M20 11a8 8 0 0 1-8 8H9l-5 3 1-6A8 8 0 1 1 20 11ZM8 11h.2m3.8 0h.2m3.8 0h.2',
  enviar: 'm3 10 18-7-6 18-4-7-8-4Zm8 4L21 3',
  mais: 'M12 5v14M5 12h14',
  ok: 'm4 12 5 5L20 6',
  remover: 'm6 6 12 12M18 6 6 18',
  reiniciar: 'M3 4v6h6M3 10a9 9 0 1 1 1 7',
  busca: 'M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Zm-2 5 6 6',
  prato: 'M3 14h18a9 9 0 0 1-18 0Zm2 8h14M8 4c-3 3 3 3 0 6m5-8c-3 3 3 4 0 7m5-5c-3 3 3 3 0 6',
  brilho: 'm12 3 2.4 6.6L21 12l-6.6 2.4L12 21l-2.4-6.6L3 12l6.6-2.4L12 3Z',
}

export function Icone({ nome, tam = 20 }) {
  return (
    <svg
      width={tam}
      height={tam}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={caminhos[nome]} />
    </svg>
  )
}

// Logotipo desenhado em CSS: folhas (i) e, na versão da plataforma, a tigela (b)
export function Marca({ plataforma = false }) {
  return (
    <span className={'marca' + (plataforma ? ' plataforma' : '')} aria-hidden="true">
      <i />
      <i />
      <i />
      <b />
    </span>
  )
}

export function Aviso({ texto, repetir }) {
  return (
    <div className="aviso" role="alert">
      {texto}{' '}
      {repetir && (
        <button className="link" onClick={repetir}>
          Tentar novamente
        </button>
      )}
    </div>
  )
}
