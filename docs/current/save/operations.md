# Profile API Operations

The profile API is a standalone DD service. The game client can continue to play and save locally if this service or the network is unavailable. The service owns DD account/session state, profile ownership, immutable remote revisions, and entitlement records; it does not simulate or authorize gameplay progression.

## Configuration

Required environment variable:

- `DATABASE_URL`: SQLAlchemy URL for PostgreSQL using the `psycopg` driver, for example `postgresql+psycopg://dd_profile:<secret>@<host>:5432/dd_profile`.

Optional environment variables:

- `DD_ACCESS_TOKEN_TTL_SECONDS`: access-token lifetime; defaults to `900`.
- `DD_REFRESH_TOKEN_TTL_SECONDS`: refresh-token lifetime; defaults to `2592000`.

Keep the database URL in the deployment platform's secret store. Serve hosted traffic only through HTTPS. Do not log authorization headers, request bodies containing credentials, or raw tokens. The API stores only SHA-256 token hashes. Configure connection limits, backups, monitoring, and request rate limits at the deployment/database boundary before public launch.

## Local PostgreSQL

From `root/services/profile_api/`, create an isolated PostgreSQL database and set `DATABASE_URL`. Install the service dependencies into the chosen environment:

```powershell
python -m pip install -r requirements.txt
```

Apply schema migrations before starting the service:

```powershell
$env:PYTHONPATH = "src;../../src"
python -m alembic -c alembic.ini upgrade head
```

Start the ASGI service:

```powershell
$env:PYTHONPATH = "src;../../src"
python -m uvicorn profile_api.main:app --host 127.0.0.1 --port 8000
```

The readiness route is `GET /v1/health`; it returns only generic service status and checks database connectivity. Do not expose the local development bind address publicly.

## Tests and Migration Discipline

Service tests run from the repository root so they can import the existing save-document validator:

```powershell
$env:PYTHONPATH = "root/src;root/services/profile_api/src"
python -m pytest root/services/profile_api/tests -q
```

Set `PROFILE_API_TEST_DATABASE_URL` to a dedicated disposable PostgreSQL database to enable row-locking/concurrent-writer qualification. Set `PROFILE_API_MIGRATION_TEST_DATABASE_URL` to a separate clean disposable database to exercise PostgreSQL Alembic upgrade/downgrade and immutable-revision triggers. Never point either variable at production or a database containing user data. The migration test also exercises upgrade/downgrade on SQLite for fast local feedback.

Use Alembic revisions for schema changes. Back up production before applying a migration, apply `upgrade head` as a deployment step, and verify `/v1/health` after rollout. Downgrades are emergency recovery tools, not routine deployment behavior; immutable profile-revision data must be backed up before destructive schema changes.

## Security and Data Boundaries

- Anonymous-account creation issues a canonical DD account and a device session; there is no username/password endpoint.
- Access and refresh credentials are opaque and stored as hashes. Refresh keeps the refresh credential stable until expiry/revocation while replacing the access credential.
- Profile IDs are client-created stable slot identities. A profile can be claimed only once; account isolation is indistinguishable from absence.
- Progression payloads must pass the existing schema-8 validator. The server computes canonical payload digests itself.
- Each accepted remote revision is immutable. Clients submit a base revision; stale writes return conflict metadata without a payload, and clients fetch the head separately.
- Entitlements are account-scoped and have no client grant/revoke route. Purchase-proof verification and identity-provider linking require trusted future adapters.
- Firebase and other vendor-specific identity/storage choices remain unevaluated and behind the DD service contract.
