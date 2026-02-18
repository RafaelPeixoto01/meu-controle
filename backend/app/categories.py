"""
CR-005: Categorias e métodos de pagamento para Gastos Diários.

Categorias fixas no código, baseadas em docs/categorias_gastos.md.
Fonte única de verdade para validação no backend e endpoint GET /categories.
"""

DAILY_EXPENSE_CATEGORIES: dict[str, list[str]] = {
    "Alimentação": [
        "Supermercado",
        "Feira / Hortifruti",
        "Açougue",
        "Padaria",
        "Delivery de mercado",
        "Restaurante",
        "Fast-food",
        "Café",
        "Delivery (iFood etc.)",
        "Bar",
    ],
    "Transporte": [
        "Combustível",
        "Uber / 99 / Taxi",
        "Transporte público",
        "Pedágio",
        "Estacionamento",
        "Manutenção do veículo",
        "Seguro do veículo",
        "Multas",
    ],
    "Moradia": [
        "Aluguel",
        "Condomínio",
        "Energia elétrica",
        "Água",
        "Gás",
        "Internet",
        "Manutenção doméstica",
        "Faxina",
        "Móveis",
        "Decoração",
    ],
    "Compras Pessoais": [
        "Roupas",
        "Calçados",
        "Acessórios",
        "Cosméticos",
        "Eletrônicos",
        "Itens para celular",
        "Presentes",
    ],
    "Lazer e Entretenimento": [
        "Cinema",
        "Shows",
        "Streaming",
        "Jogos",
        "Viagens",
        "Passeios",
        "Eventos",
    ],
    "Saúde": [
        "Farmácia",
        "Consultas médicas",
        "Exames",
        "Plano de saúde",
        "Terapia",
        "Academia",
        "Suplementos",
    ],
    "Educação": [
        "Cursos",
        "Escola / Faculdade",
        "Livros",
        "Material escolar",
        "Idiomas",
    ],
    "Filhos / Dependentes": [
        "Escola",
        "Lanche",
        "Material escolar",
        "Roupas",
        "Lazer infantil",
        "Saúde infantil",
    ],
    "Pets": [
        "Ração",
        "Veterinário",
        "Banho e tosa",
        "Acessórios",
    ],
    "Financeiro": [
        "Juros",
        "Multas bancárias",
        "IOF",
        "Taxas",
        "Anuidade de cartão",
        "Parcelas",
    ],
    "Presentes e Doações": [
        "Presente",
        "Aniversário",
        "Casamento",
        "Doações",
    ],
    "Assinaturas e Serviços": [
        "Streaming",
        "Apps",
        "SaaS",
        "Clube de assinatura",
    ],
    "Trabalho": [
        "Reembolso pendente",
        "Almoço corporativo",
        "Ferramentas",
        "Transporte trabalho",
    ],
    "Outros": [
        "Outros",
    ],
}

PAYMENT_METHODS: list[str] = [
    "Dinheiro",
    "Cartão de Crédito",
    "Cartão de Débito",
    "Pix",
    "Vale Alimentação",
    "Vale Refeição",
]


def get_category_for_subcategory(subcategoria: str) -> str | None:
    """Retorna a categoria pai de uma subcategoria, ou None se não encontrada."""
    for category, subcategories in DAILY_EXPENSE_CATEGORIES.items():
        if subcategoria in subcategories:
            return category
    return None


def is_valid_subcategory(subcategoria: str) -> bool:
    """Verifica se uma subcategoria existe em qualquer categoria."""
    return get_category_for_subcategory(subcategoria) is not None


def is_valid_payment_method(metodo: str) -> bool:
    """Verifica se um método de pagamento é válido."""
    return metodo in PAYMENT_METHODS
