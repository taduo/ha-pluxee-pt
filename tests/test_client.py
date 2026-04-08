"""Unit tests for the Pluxee Portugal client helpers."""

from decimal import Decimal

import pytest

from custom_components.pluxee_pt.client import (
    PluxeePtParseError,
    extract_balance_data,
    is_login_page,
    parse_login_response_text,
    title_for_nif,
)


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


def test_extract_balance_data_returns_decimal_value() -> None:
    """The page parser normalizes comma decimals into Decimal."""
    result = extract_balance_data(BALANCE_HTML, "https://consumidores.pluxee.pt/")

    assert result.balance == Decimal("74.17")
    assert result.balance_raw == "74,17"


def test_extract_balance_data_raises_when_missing() -> None:
    """Unexpected markup should be treated as a parse failure."""
    with pytest.raises(PluxeePtParseError):
        extract_balance_data("<html><body>No balance here</body></html>", "https://x")


def test_is_login_page_detects_login_markup() -> None:
    """The client should recognize the unauthenticated form."""
    assert is_login_page(LOGIN_HTML) is True
    assert is_login_page(BALANCE_HTML) is False


def test_title_for_nif_masks_display_name() -> None:
    """Only the last four digits are shown in the UI title."""
    assert title_for_nif("123456789") == "Pluxee PT 6789"
