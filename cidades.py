"""Cidades atendidas pela recomendação de restaurantes e caminhos dos arquivos."""

# Identificador usado na API -> nome e código IBGE do município
CIDADES = {
    "belo-horizonte": {"nome": "Belo Horizonte", "ibge": 3106200},
    "sao-paulo": {"nome": "São Paulo", "ibge": 3550308},
    "rio-de-janeiro": {"nome": "Rio de Janeiro", "ibge": 3304557},
}

# Catálogo recebido (fora do repositório, por ser grande) e catálogo tratado pelo pipeline
ARQUIVO_ORIGINAL = "dados/restaurante/restaurants.csv"
ARQUIVO_TRATADO = "dados/restaurante/restaurantes.csv"

# Simulação do MVP: dois restaurantes do catálogo representam as lojas atendidas pelo projeto.
# Eles aparecem com o nome da loja e levam ao site dela (cardápio, sugestões e chat).
LOJAS_PARCEIRAS = {
    "sao-paulo": {
        "Rica Pancita": "mexicano",
        "Queen's Kitchen": "indiano",
    },
}
