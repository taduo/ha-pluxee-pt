"""HTTP client for the Pluxee Portugal portal."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import json
import logging
import re

from aiohttp import ClientError, ClientSession
from bs4 import BeautifulSoup

from .const import BALANCE_PAGE_URL, LOGIN_PAGE_URL, LOGIN_PROCESSING_URL, REQUEST_TIMEOUT_SECONDS

_LOGGER = logging.getLogger(__name__)

_BALANCE_PATTERN = re.compile(r"(\d{1,3}(?:\.\d{3})*,\d{2})")


class PluxeePtError(Exception):
    """Base integration error."""


class PluxeePtAuthError(PluxeePtError):
    """Raised when authentication fails."""


class PluxeePtConnectionError(PluxeePtError):
    """Raised when the website cannot be reached."""


class PluxeePtParseError(PluxeePtError):
    """Raised when the balance cannot be parsed."""


@dataclass(slots=True)
class PluxeeLoginResponse:
    """Result returned by the login endpoint."""

    success: bool
    message: str | None
    redirect_url: str | None


@dataclass(slots=True)
class PluxeeBalanceData:
    """Normalized balance data."""

    balance: Decimal
    balance_raw: str
    source_url: str


def title_for_nif(nif: str) -> str:
    """Build a user-friendly config entry title."""
    masked = nif[-4:] if len(nif) >= 4 else nif
    return f"Pluxee PT {masked}"


def is_login_page(html: str) -> bool:
    """Return True when the returned page is the login form."""
    normalized = html.lower()
    return (
        "login_processing.php" in normalized
        and 'name="nif"' in normalized
        and 'name="pass"' in normalized
    )


def parse_login_response_text(payload: str) -> PluxeeLoginResponse:
    """Parse the login endpoint response."""
    cleaned = payload.lstrip("\ufeff").strip()

    if not cleaned:
        raise PluxeePtParseError("Empty response from the Pluxee login endpoint.")

    if cleaned.endswith(")") and "(" in cleaned and cleaned.split("(", 1)[0].isidentifier():
        cleaned = cleaned[cleaned.find("(") + 1 : -1]

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as err:
        raise PluxeePtParseError("Could not decode the Pluxee login response.") from err

    return PluxeeLoginResponse(
        success=bool(data.get("sucesso")),
        message=data.get("mensagem"),
        redirect_url=data.get("local"),
    )


def extract_balance_data(html: str, source_url: str) -> PluxeeBalanceData:
    """Extract the available balance from the authenticated page."""
    soup = BeautifulSoup(html, "html.parser")

    for element in soup.select("h1.card-heading.demi-bold, h1.card-heading, .card-heading"):
        raw_text = element.get_text(" ", strip=True).replace("\xa0", " ")
        normalized_text = raw_text.replace("€", "").strip()
        match = _BALANCE_PATTERN.search(normalized_text)
        if not match:
            continue

        raw_balance = match.group(1)
        try:
            balance = Decimal(raw_balance.replace(".", "").replace(",", "."))
        except InvalidOperation as err:
            raise PluxeePtParseError(
                f"Found a balance value but could not parse it: {raw_balance}"
            ) from err

        return PluxeeBalanceData(
            balance=balance,
            balance_raw=raw_balance,
            source_url=source_url,
        )

    raise PluxeePtParseError(
        "Logged in successfully, but could not find the available balance element."
    )


class PluxeePtClient:
    """Client used by the coordinator and config flow."""

    def __init__(self, session: ClientSession, nif: str, password: str) -> None:
        """Initialize the client."""
        self._session = session
        self._nif = nif
        self._password = password

    async def async_fetch_balance(self) -> PluxeeBalanceData:
        """Fetch the current balance, logging in again if needed."""
        html, source_url = await self._async_fetch_page(BALANCE_PAGE_URL)
        if not is_login_page(html):
            return extract_balance_data(html, source_url)

        await self._async_prime_session()
        login_result = await self._async_login()

        if not login_result.success:
            raise PluxeePtAuthError(
                login_result.message
                or "Pluxee rejected the credentials provided for this account."
            )

        target_url = login_result.redirect_url or BALANCE_PAGE_URL
        html, source_url = await self._async_fetch_page(target_url)

        if is_login_page(html):
            raise PluxeePtAuthError(
                "Pluxee accepted the login request but did not create an authenticated session."
            )

        return extract_balance_data(html, source_url)

    async def _async_prime_session(self) -> None:
        """Fetch the login page first so any required cookies are set."""
        await self._async_fetch_page(LOGIN_PAGE_URL)

    async def _async_login(self) -> PluxeeLoginResponse:
        """Call the login endpoint with the live query-string flow used by the site."""
        try:
            response = await self._session.get(
                LOGIN_PROCESSING_URL,
                params={"nif": self._nif, "pass": self._password},
                allow_redirects=True,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except ClientError as err:
            raise PluxeePtConnectionError(
                "Could not reach the Pluxee login endpoint."
            ) from err

        async with response:
            if response.status >= 400:
                raise PluxeePtConnectionError(
                    f"Pluxee login endpoint returned HTTP {response.status}."
                )

            return parse_login_response_text(await response.text())

    async def _async_fetch_page(self, url: str) -> tuple[str, str]:
        """Fetch an HTML page from the portal."""
        try:
            response = await self._session.get(
                url,
                allow_redirects=True,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except ClientError as err:
            raise PluxeePtConnectionError(
                f"Could not reach the Pluxee portal at {url}."
            ) from err

        async with response:
            if response.status >= 400:
                raise PluxeePtConnectionError(
                    f"Pluxee page request failed with HTTP {response.status}."
                )

            text = await response.text()
            final_url = str(response.url)

        _LOGGER.debug("Fetched Pluxee page %s", final_url)
        return text, final_url
