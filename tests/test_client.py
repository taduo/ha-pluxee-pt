"""Unit tests for the Pluxee Portugal client helpers."""

from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from custom_components.pluxee_pt.client import (
    PluxeeLoginResponse,
    PluxeePtAuthError,
    PluxeePtClient,
    PluxeePtParseError,
    extract_balance_data,
    extract_recent_transactions,
    is_login_page,
    parse_decimal_text,
    parse_login_response_text,
    resolve_post_login_url,
    sanitize_url,
    title_for_nif,
)
from custom_components.pluxee_pt.const import BALANCE_PAGE_URL, is_valid_nif, normalize_nif


BALANCE_HTML = """
<html>
  <body>
    <main>
      <div class="card">
        <h1 class="card-heading demi-bold">74,17&nbsp;</h1>
      </div>
    </main>
  </body>
</html>
"""

LOGIN_HTML = """
<form action="/login_processing.php" id="login_form_page">
  <input name="nif" />
  <input name="pass" />
</form>
"""

BROKEN_TRANSACTIONS_HTML = """
<html>
  <body>
    <main>
      <div class="card">
        <h1 class="card-heading demi-bold">43,09&nbsp;</h1>
      </div>
      <table id="plx-table">
        <tbody>
          <tr>
            <td><p class="dateFormatDesk">not-a-date</p></td>
            <td><p class="text-left">Compra TESTE</p></td>
            <td><span class="saldo_p">-31.08 €</span></td>
          </tr>
        </tbody>
      </table>
    </main>
  </body>
</html>
"""

FIXTURES_DIR = Path(__file__).parent / "fixtures"
DASHBOARD_HTML = (FIXTURES_DIR / "dashboard_with_transactions.html").read_text(
    encoding="utf-8"
)


def test_parse_login_response_text_supports_plain_json() -> None:
    """The login endpoint can return plain JSON."""
    result = parse_login_response_text(
        '{"sucesso":true,"mensagem":"","local":"https://consumidores.pluxee.pt"}'
    )

    assert result.success is True
    assert result.redirect_url == "https://consumidores.pluxee.pt"


def test_parse_login_response_text_supports_jsonp() -> None:
    """The parser accepts the JSONP variant used by the website."""
    result = parse_login_response_text(
        'callback({"sucesso":false,"mensagem":"invalid","local":"https://consumidores.pluxee.pt"})'
    )

    assert result.success is False
    assert result.message == "invalid"


def test_resolve_post_login_url_defaults_to_balance_page() -> None:
    """Missing redirect targets should fall back to the balance page."""
    assert resolve_post_login_url(None) == BALANCE_PAGE_URL


def test_resolve_post_login_url_accepts_expected_hosts() -> None:
    """Only known Pluxee hosts should be followed after login."""
    assert (
        resolve_post_login_url("https://consumidores.pluxee.pt/dashboard?token=abc")
        == "https://consumidores.pluxee.pt/dashboard?token=abc"
    )
    assert (
        resolve_post_login_url("/area-reservada")
        == "https://portal.admin.pluxee.pt/area-reservada"
    )


def test_resolve_post_login_url_rejects_unexpected_hosts() -> None:
    """The client should not follow arbitrary redirect destinations."""
    with pytest.raises(PluxeePtParseError):
        resolve_post_login_url("https://evil.example.com/steal-session")


def test_sanitize_url_removes_query_and_fragment() -> None:
    """URLs stored for diagnostics should not keep sensitive parts."""
    assert (
        sanitize_url("https://consumidores.pluxee.pt/dashboard?token=abc#fragment")
        == "https://consumidores.pluxee.pt/dashboard"
    )


def test_normalize_nif_strips_outer_whitespace() -> None:
    """NIF values should be normalized before storage or comparison."""
    assert normalize_nif(" 123456789 ") == "123456789"


def test_is_valid_nif_requires_exactly_nine_digits() -> None:
    """Only 9-digit numeric NIFs should be accepted."""
    assert is_valid_nif("123456789") is True
    assert is_valid_nif("1234 56789") is False
    assert is_valid_nif("12345678") is False


def test_extract_balance_data_returns_decimal_value() -> None:
    """The page parser normalizes comma decimals into Decimal."""
    result = extract_balance_data(BALANCE_HTML)

    assert result.balance == Decimal("74.17")
    assert result.balance_raw == "74,17"
    assert result.recent_transactions == ()


def test_parse_decimal_text_supports_balance_and_transaction_formats() -> None:
    """The numeric parser accepts both observed separators."""
    assert parse_decimal_text("74,17") == Decimal("74.17")
    assert parse_decimal_text("-31.08 €") == Decimal("-31.08")


def test_extract_recent_transactions_returns_newest_five_rows() -> None:
    """The dashboard parser keeps the newest visible order and caps at five rows."""
    result = extract_recent_transactions(DASHBOARD_HTML)

    assert len(result) == 5
    assert result[0].date == "2026-04-08"
    assert result[0].date_raw == "08/04/2026"
    assert result[0].description == "Compra MERCADONA,SINTRA,PRT"
    assert result[0].amount == Decimal("-31.08")
    assert result[0].amount_raw == "-31.08 €"
    assert result[3].description == "Carregamento de FORTINET PORTUGAL, UNIPESSOAL LDA"
    assert result[3].amount == Decimal("152.60")


def test_extract_balance_data_includes_recent_transactions() -> None:
    """The combined dashboard parser returns balance and transaction data together."""
    result = extract_balance_data(DASHBOARD_HTML)

    assert result.balance == Decimal("43.09")
    assert result.balance_raw == "43,09"
    assert len(result.recent_transactions) == 5
    assert result.recent_transactions[4].date == "2026-03-08"


def test_extract_balance_data_keeps_balance_when_transactions_fail() -> None:
    """A transaction parsing problem should not hide a valid balance."""
    result = extract_balance_data(BROKEN_TRANSACTIONS_HTML)

    assert result.balance == Decimal("43.09")
    assert result.recent_transactions == ()


def test_extract_balance_data_raises_when_missing() -> None:
    """Unexpected markup should be treated as a parse failure."""
    with pytest.raises(PluxeePtParseError):
        extract_balance_data("<html><body>No balance here</body></html>")


def test_is_login_page_detects_login_markup() -> None:
    """The client should recognize the unauthenticated form."""
    assert is_login_page(LOGIN_HTML) is True
    assert is_login_page(BALANCE_HTML) is False


def test_title_for_nif_masks_display_name() -> None:
    """Only the last four digits are shown in the UI title."""
    assert title_for_nif(" 123456789 ") == "Pluxee PT 6789"


@pytest.mark.asyncio
async def test_async_fetch_balance_uses_generic_auth_error() -> None:
    """Auth failures should not expose upstream response messages."""
    client = PluxeePtClient(object(), "123456789", "secret")
    client._async_fetch_page = AsyncMock(return_value=LOGIN_HTML)
    client._async_prime_session = AsyncMock()
    client._async_login = AsyncMock(
        return_value=PluxeeLoginResponse(
            success=False,
            message="Conta bloqueada 123456789",
            redirect_url=None,
        )
    )

    with pytest.raises(PluxeePtAuthError) as exc_info:
        await client.async_fetch_balance()

    assert str(exc_info.value) == "Pluxee rejected the credentials provided for this account."
    assert "Conta bloqueada" not in str(exc_info.value)
