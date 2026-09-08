# RuleScope

Dockerized web app that ingests exported firewall/router/switch rule sets, builds a
graphical network topology (with subnets, public IPs, and ISP/ASN enrichment), flags
rule vulnerabilities and issues (regardless of documented business justification), and
exports a branded PDF/HTML/Excel report.

## Stack
- **Frontend**: React + TypeScript + Vite + Tailwind (dark theme, orange/green/white accents), React Flow for topology.
- **Backend**: FastAPI + Celery/Redis for async parse/analyze/report jobs.
- **Auth**: Keycloak (OIDC) with `admin` / `analyst` / `viewer` realm roles.
- **Storage**: Postgres for jobs/findings/custom rules.
- **Parsers**: Cisco ASA, Cisco IOS, Palo Alto (set-format), FortiGate, Juniper (set-format), and a generic CSV template — pluggable architecture (`backend/app/parsers/`) for adding more vendors.

## Quick start

1. Copy `.env.example` to `.env` and adjust secrets/passwords.
2. `docker compose up --build`
3. Frontend: http://localhost:3000 (Keycloak realm auto-imported: users `admin/admin`, `analyst/analyst`, `viewer/viewer` — all temporary passwords, change on first login)
4. Keycloak admin console: http://localhost:8081 (`admin` / value of `KEYCLOAK_ADMIN_PASSWORD`)
5. Backend API docs: http://localhost:8000/docs

## Try it out
Sample rule exports are in `samples/`:
- `cisco_asa_sample.txt` — Cisco ASA config with an insecure any/any rule, exposed RDP/Telnet, and a shadowed rule.
- `generic_template_sample.csv` — universal CSV template for any vendor not yet natively supported.

Upload either via the dashboard to see parsing, findings, topology, and report export end-to-end.

## Generic CSV template (for unsupported vendors)
Columns: `name, action, source, destination, service` (required), plus optional
`zone_from, zone_to, log, disabled, hitcount, description, device`.

## Adding a new vendor parser
Implement `BaseParser` in `backend/app/parsers/<vendor>.py` (see existing parsers for the pattern),
then register it in `backend/app/parsers/registry.py`.

## Security notes
- Only extracted public IP addresses are sent to IP/ISP enrichment APIs — never full configs.
- Uploaded files and findings are stored in the app database; access is scoped by Keycloak role (analysts see only their own jobs, admins see all).
- Change all default passwords/secrets in `.env` and the Keycloak realm before any non-local use.
