"""Unit tests for the Pluxee Portugal sensor helpers."""

from decimal import Decimal

from custom_components.pluxee_pt.client import PluxeeBalanceData, PluxeeTransaction
from custom_components.pluxee_pt.presentation import build_balance_attributes


def test_build_balance_attributes_includes_recent_transactions() -> None:
    """The balance sensor should expose the latest transactions as attributes."""
    data = PluxeeBalanceData(
        balance=Decimal("43.09"),
        balance_raw="43,09",
        recent_transactions=(
            PluxeeTransaction(
                date="2026-04-08",
                date_raw="08/04/2026",
                description="Compra MERCADONA,SINTRA,PRT",
                amount=Decimal("-31.08"),
                amount_raw="-31.08 €",
            ),
            PluxeeTransaction(
                date="2026-04-01",
                date_raw="01/04/2026",
                description="Carregamento de FORTINET PORTUGAL, UNIPESSOAL LDA",
                amount=Decimal("152.60"),
                amount_raw="152.60 €",
            ),
        ),
        source_url="https://consumidores.pluxee.pt/",
    )

    attributes = build_balance_attributes(data)

    assert attributes["balance_text"] == "43,09"
    assert attributes["recent_transactions_count"] == 2
    assert "source_url" not in attributes
    assert attributes["recent_transactions"] == [
        {
            "date": "2026-04-08",
            "date_raw": "08/04/2026",
            "description": "Compra MERCADONA,SINTRA,PRT",
            "amount": -31.08,
            "amount_raw": "-31.08 €",
        },
        {
            "date": "2026-04-01",
            "date_raw": "01/04/2026",
            "description": "Carregamento de FORTINET PORTUGAL, UNIPESSOAL LDA",
            "amount": 152.6,
            "amount_raw": "152.60 €",
        },
    ]
