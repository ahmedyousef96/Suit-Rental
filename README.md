### Suit Rental

Suit/Dress Rental App

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app suit_rental
```

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/suit_rental
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit

-----
Documentation:

Suit Rental
Suit/Dress Rental App
The Suit Rental app streamlines suit and dress rental businesses with a complete workflow from booking to return, across multiple branches.

Key Features:
Reservations – Manage customer bookings with availability checks to prevent overlaps.
Deliveries – Generate Sales Invoices and Stock Entries when items are handed over.
Returns – Record item returns and auto-reverse stock entries.
Multi-Branch Support – Track stock, invoices, and rentals per branch.
Customer Measurements – Store and reuse customer measurements for faster reservations.
Statistical Dashboard – Live snapshot of pending deliveries, pending returns, and active reservations with clickable detailed reports.

Compatibility:
ERPNext & Frappe version 15

This app is ideal for boutiques, rental stores, and fashion academies managing clothing inventory across multiple outlets.
