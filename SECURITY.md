# Security Policy

## Supported Versions

Security fixes are expected to land in the latest released version of this
integration and on the current `main` branch.

Older versions may not receive fixes.

## Reporting a Vulnerability

Please do not open a public GitHub issue for vulnerabilities that could expose:

- portal credentials such as `NIF` or `Password`
- authenticated session data
- personal transaction history
- unexpected redirects or data leaks from the Pluxee portal flow

Prefer GitHub's private vulnerability reporting for this repository if it is
available. If private reporting is not available, contact the maintainer
privately through GitHub instead of posting the details publicly.

When reporting a vulnerability:

- describe the impact and the conditions required to reproduce it
- include the integration version or commit SHA
- include Home Assistant and Python versions if relevant
- redact credentials, NIFs, cookies, session identifiers, and private account data
- sanitize any copied URLs so query strings and fragments are removed

## Security Notes

This integration depends on a third-party website and login flow controlled by
Pluxee Portugal. As of `2026-04-08`, the consumer portal still uses a
query-string login flow at `https://portal.admin.pluxee.pt/login_processing.php`.

Because of that upstream limitation, the project treats the following as
security-sensitive areas:

- credential handling in the Home Assistant config flow
- auth failures and error messages returned by the portal
- redirects after login
- URL logging and state attributes
- HTML parsing changes that could accidentally expose account data

Reports about hardening opportunities are welcome even when they do not yet
produce a confirmed exploit.
