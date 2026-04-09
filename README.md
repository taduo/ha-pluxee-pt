# Pluxee Portugal for Home Assistant

Unofficial Home Assistant custom integration for Pluxee Portugal. It logs in to the
consumer portal, reads the available balance shown on the dashboard, and exposes
that value as a Home Assistant sensor in EUR.

This project is not affiliated with or endorsed by Pluxee.
Build with codex assistance.

## Features

- UI-based setup from `Settings > Devices & Services`
- Stores your credentials in the Home Assistant config entry
- Refreshes your balance on a configurable interval, with 30 minutes as the default
- Lets you change the refresh interval from the integration options
- Automatically retries with a fresh login when the session expires
- Adds the latest 5 card transactions as attributes on the balance sensor
- Installs through HACS as a custom repository

## Current Scope

Version `0.3.0` currently includes:

- available balance from the Portugal consumer portal
- last 5 card transactions as balance sensor attributes
- configurable refresh interval from the options flow

Out of scope for now:

- multiple balance types from one account
- default HACS catalog submission

## Installation

### HACS custom repository

1. Open HACS in Home Assistant.
2. Go to `Integrations`.
3. Open the three-dot menu and choose `Custom repositories`.
4. Add `https://github.com/taduo/ha-pluxee-pt`.
5. Choose category `Integration`.
6. Search for `Pluxee Portugal` in HACS and install it.
7. Restart Home Assistant.

### Manual install

1. Copy the `custom_components/pluxee_pt` folder into your Home Assistant
   `custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. In Home Assistant, open `Settings > Devices & Services`.
2. Click `Add Integration`.
3. Search for `Pluxee Portugal`.
4. Enter your `NIF` and `Password`.
5. Finish the flow and wait for the first refresh.

The integration will create one sensor per configured account:

- `Available balance`

That sensor also exposes these attributes:

- `recent_transactions`
- `recent_transactions_count`

## Options

After the integration is added, you can change the refresh interval from the
integration options in Home Assistant.

Available presets:

- `15 minutes`
- `30 minutes`
- `60 minutes`
- `120 minutes`

## Notes About Login

The current implementation is based on the live Portugal login flow observed on
`2026-04-08`:

- login page: `https://portal.admin.pluxee.pt/`
- login endpoint: `https://portal.admin.pluxee.pt/login_processing.php`
- request parameters: `nif` and `pass`

If Pluxee adds CAPTCHA, mandatory one-time codes, or changes the post-login
markup, the integration may need to be updated. Transaction parsing currently
uses the same authenticated dashboard HTML fetch as the balance parser.

## Local Validation

From the repository root:

```bash
PYTHONPYCACHEPREFIX=.pycache python3 -m compileall custom_components tests
```

If you want to run the test suite locally, use a project-only virtual environment so
the installs stay inside this repository and do not affect your other Python work.
Local validation expects Python 3.12 or newer.

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements_test.txt
python -m pytest
deactivate
```

Home Assistant installs the runtime dependency declared in
`custom_components/pluxee_pt/manifest.json` inside its own environment, so you do
not need to install that package globally on your machine.

## Legal

Use this integration at your own risk. Balance data comes from the Pluxee web
portal and can change if the site or authentication flow changes.
