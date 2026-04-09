"""Presentation helpers for Home Assistant entities."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .client import PluxeeBalanceData


def build_balance_attributes(
    data: PluxeeBalanceData,
    last_refresh: datetime | None = None,
) -> dict[str, Any]:
    """Build the extra state attributes for the balance sensor."""
    attributes: dict[str, Any] = {
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

    if last_refresh is not None:
        attributes["last_refresh"] = last_refresh.isoformat()

    return attributes
