"""Presentation helpers for Home Assistant entities."""

from __future__ import annotations

from typing import Any

from .client import PluxeeBalanceData


def build_balance_attributes(data: PluxeeBalanceData) -> dict[str, Any]:
    """Build the extra state attributes for the balance sensor."""
    return {
        "balance_text": data.balance_raw,
        "recent_transactions": [
            {
                "date": transaction.date,
                "date_raw": transaction.date_raw,
                "description": transaction.description,
                "amount": float(transaction.amount),
                "amount_raw": transaction.amount_raw,
            }
            for transaction in data.recent_transactions
        ],
        "recent_transactions_count": len(data.recent_transactions),
    }
