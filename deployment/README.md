# Whereru AWS production runbook

This is the reproducible production layout for this repository. It documents
the supplied production configuration; it does not provision AWS resources or
contain any credentials. Run commands on the target EC2 instance only after
reviewing them for that environment, unless a command is explicitly labelled
as running on the local workstation.

## 1. Architecture

```
Browser
  └─ HTTPS where-areyou.com ── Nginx on EC2 (80/443)
       ├─ React/Vite static files: /var/www/whereru/dist
       └─ /api/, /docs, /openapi.json ──> Gunicorn/FastAPI 127.0.0.1:8000
                                              ├─ RDS PostgreSQL 16 (private)
                                              ├─ S3 material storage
                                              ├─ OpenRouter chat: google/gemini-2.5-flash-lite
                                              └─ Gemini embeddings: gemini-embedding-001
```

The intended AWS Region is `ap-southeast-2`. The application directory is
`/opt/whereru`; the API runs as `ubuntu` with one Gunicorn/Uvicorn worker and
a 330-second timeout. The EC2 Elastic IP is deliberately not stored here.

## 2. Required AWS resources

Create or verify the following in the new AWS account before deploying:

| Resource | Required production configuration |
| --- | --- |
| EC2 | `whereru-api`, `t3.small`, public subnet and an Elastic IP; Ubuntu is assumed by the systemd unit. |
| EC2 IAM role | Attach `whereru-ec2-role` to the instance. Use instance-role credentials; do not place static AWS keys in `.env`. |
| S3 | `whereru-materials-yt-prod` in `ap-southeast-2`. |
| RDS | `whereru-db-pg16`, PostgreSQL 16, database `whereru`, private networking. |
| DNS | `where-areyou.com` A/AAAA record(s) directed to the EC2 Elastic IP. |
| TLS | Let's Encrypt certificate obtained by Certbot after DNS propagation. |

These names and the region are supplied deployment facts, not resources
verified from this repository or the current AWS account.

## 3. Network security groups

Use security-group references rather than fixed private IP addresses where
possible.

| Target | Inbound rule | Why |
| --- | --- | --- |
| EC2 | TCP 80 and 443 from the Internet | Nginx serves the site and redirects/validates HTTP for Certbot. |
| EC2 | TCP 22 only from the administrator's trusted CIDR, if SSH is required | Administration; do not open SSH to the Internet. |
| RDS | TCP 5432 from the EC2 security group only | PostgreSQL must remain private. |

Allow EC2 outbound connectivity needed for RDS on 5432, DNS, HTTPS calls to
S3, Google/Gemini, OpenRouter, OAuth and package/repository updates. Do not
expose port 8000 publicly: Gunicorn binds only to `127.0.0.1`.

## 4. IAM and S3

The EC2 role needs access only to the production S3 bucket objects used by
the application. Repository code uploads, reads, copies and deletes objects,
so scope object actions to:

```
arn:aws:s3:::whereru-materials-yt-prod/*
```

The precise policy document, bucket policy, encryption choice, and account
permissions have not been verified here. Add bucket-level permissions only if
an identified operation requires them. The role should not need Bedrock for
the documented runtime. Do not infer a Transcribe allow or deny policy from
this runbook.

The backend uses `S3_BUCKET_NAME` to construct storage keys and public S3
URLs, so it must be exactly `whereru-materials-yt-prod` in production. Review
bucket public-access settings and object access design before user profile or
material URLs are exposed; those settings are not defined by this repository.

## 5. RDS and database initialization

Provision PostgreSQL 16 with database name `whereru` and an application
database user. Require SSL, place the RDS global CA bundle at:

```
/opt/whereru/backend/global-bundle.pem
```

For a **fresh, empty** database only, initialize the schema from the
repository; do not run `alembic upgrade head`.

```bash
cd /opt/whereru
psql "$DATABASE_URL" -f backend/schema.sql
```

`backend/schema.sql` creates the `pgcrypto`, `uuid-ossp`, and `vector`
extensions and the cosine HNSW index for `material_chunks.embedding`. It also
creates an `alembic_version` table, but Alembic migrations are not tracked in
this repository. The database principal executing the schema must therefore
be permitted to create those extensions.

Never run `backend/schema.sql` against an existing database. Before any
existing-database migration, take and verify an RDS snapshot. Use the tracked
incremental SQL migration with `ON_ERROR_STOP` instead; the update procedure
and verification queries are in section 13.

Use a production `DATABASE_URL` with SSL verification and the CA path above,
for example (replace every placeholder):

```
postgresql+psycopg://<DB_USER>:<DB_PASSWORD>@<RDS_ENDPOINT>:5432/whereru?sslmode=verify-full&sslrootcert=/opt/whereru/backend/global-bundle.pem
```

The exact endpoint, credentials, CA-download process, subnet group and RDS
parameter group are account configuration and are not represented in Git.

## 6. Install the application and Python 3.13 environment

On the EC2 instance, install Python **3.13**, its virtual-environment support,
Git, Nginx, PostgreSQL client utilities and Certbot using the package process
appropriate for the installed Ubuntu release. Confirm the interpreter before
creating the virtual environment:

```bash
python3.13 --version
git clone https://github.com/yi0805/Oral-Assessment-Platform.git /opt/whereru
cd /opt/whereru/backend
python3.13 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```

If the directory already exists, fetch the intended revision rather than
blindly replacing it. Record the deployed commit with `git rev-parse HEAD`.

## 7. Backend environment file

Create `/opt/whereru/backend/.env` with owner-readable permissions only (for
example, `chmod 600`). Never commit or paste this file. The settings class
requires these variable names:

```
DATABASE_URL
STORAGE_BACKEND
S3_BUCKET_NAME
AWS_REGION
GEMINI_API_KEY
OPENROUTER_API_KEY
GOOGLE_INSTRUCTOR_DOMAINS
GOOGLE_INSTRUCTOR_ALLOWLIST
GOOGLE_ALLOWED_LOGIN_DOMAINS
JWT_SECRET_KEY
JWT_ALGORITHM
JWT_EXPIRE_MINUTES
RATE_LIMIT_DEFAULT
CORS_ORIGINS
```

Set the production-specific non-secret configuration as follows, replacing
only the placeholders and retaining correct JSON syntax for list values:

```
STORAGE_BACKEND=s3
S3_BUCKET_NAME=whereru-materials-yt-prod
AWS_REGION=ap-southeast-2
STT_STREAMING_ENABLED=false
TRANSCRIBE_ENABLED=false
MATERIAL_PROCESSING_STALE_SECONDS=1800
CORS_ORIGINS=["https://where-areyou.com"]
COOKIE_SECURE=true
APP_VERSION=<deployment-version>
GIT_COMMIT=<deployment-git-commit>
```

`AWS_PROFILE_NAME` is optional in the code. On EC2 it should be omitted so
the AWS SDK uses `whereru-ec2-role` through its default credential chain.
Leave `AWS_BEARER_TOKEN_BEDROCK` absent: when it is unset, the code skips
Bedrock and sends chat requests directly to OpenRouter. Do not include secret
values for database passwords, JWTs, Gemini/OpenRouter keys, AWS keys, Google
OAuth credentials or any bearer token in version control or this runbook.

`MATERIAL_PROCESSING_STALE_SECONDS=1800` is the validated production value
(30 minutes). It controls when an interrupted `processing` material becomes
eligible for an instructor-authorised retry. Only stale, not arbitrary
current, processing rows are retryable.

## 8. Current AI and STT state

- Chat/question generation uses OpenRouter model
  `google/gemini-2.5-flash-lite`; embeddings use Gemini
  `gemini-embedding-001`.
- Bedrock is intentionally disabled because the configured Claude 3 Haiku
  model is Legacy. Keeping `AWS_BEARER_TOKEN_BEDROCK` absent is what prevents
  the code from attempting Bedrock first.
- Voice input is disabled in production with `VITE_VOICE_INPUT_ENABLED=false`.
  The browser shows typed-answer input only and does not call transcription
  endpoints.
- The backend independently sets both `STT_STREAMING_ENABLED=false` and
  `TRANSCRIBE_ENABLED=false`. Streaming and batch transcription endpoints do
  not attempt Amazon Transcribe while that flag is false; batch requests return
  HTTP 503.
- The existing batch route remains in the code for a future, separately tested
  enablement. The current AWS account's prior `SubscriptionRequiredException`
  does not establish an IAM allow or deny policy.

## 9. systemd service

Install the tracked service definition and start it:

```bash
sudo install -m 644 /opt/whereru/deployment/whereru-api.service /etc/systemd/system/whereru-api.service
sudo systemctl daemon-reload
sudo systemctl enable --now whereru-api
sudo systemctl status whereru-api --no-pager
```

The service file reads `/opt/whereru/backend/.env`, starts
`app.main:app` through Gunicorn, uses one `uvicorn.workers.UvicornWorker`,
binds `127.0.0.1:8000`, and restarts after five seconds on failure.

## 10. Build and install the frontend

Create a non-tracked production-local frontend environment file at the
repository root. It needs these names (never place a real OAuth secret here):

```
VITE_API_URL=https://where-areyou.com/api
VITE_GOOGLE_CLIENT_ID=<GOOGLE_CLIENT_ID>
VITE_VOICE_INPUT_ENABLED=false
VITE_STT_STREAMING=0
```

Build the frontend **locally**, where the production Vite environment file is
present. Vite substitutes these values at build time, so changing one requires
a new local build. Do not build the frontend on EC2.

```bash
# local workstation, repository root
npm ci
npm run build
```

Transfer the resulting `dist/` directory to a temporary directory on EC2, for
example with an approved `scp` or `rsync` command. On EC2, preserve the current
static release before replacing it:

```bash
# EC2
cd /opt/whereru
sudo install -d -o root -g root /var/www/whereru
if [ -d /var/www/whereru/dist ]; then sudo mv /var/www/whereru/dist /var/www/whereru/dist-previous-<release-id>; fi
sudo mv /tmp/whereru-dist-new /var/www/whereru/dist
sudo chown -R www-data:www-data /var/www/whereru/dist
```

`/var/www/whereru/dist-previous-<release-id>` is the immediate frontend
rollback copy. Use a unique release identifier and temporary upload directory
for each release, and verify its contents before the move.

## 11. Nginx, DNS and HTTPS

The example is deliberately for a direct browser -> EC2 Nginx topology. It
overwrites `X-Forwarded-For` with Nginx's `$remote_addr`, preventing a
browser-supplied header from changing the backend rate-limit identity. Do not
replace this with `$proxy_add_x_forwarded_for`. If an ALB, CDN, or other proxy
is added later, configure Nginx `real_ip` to trust only that proxy before
forwarding a client address.

Install and enable the example configuration:

```bash
sudo install -m 644 /opt/whereru/deployment/nginx.conf.example /etc/nginx/sites-available/whereru
sudo ln -s /etc/nginx/sites-available/whereru /etc/nginx/sites-enabled/whereru
sudo nginx -t
sudo systemctl reload nginx
```

Before requesting a certificate, point the `where-areyou.com` DNS record to
the EC2 Elastic IP and confirm public DNS propagation. Then use Certbot's
Nginx integration for that domain. The production state must have a
Certbot-managed HTTPS server block for the domain and an HTTP-to-HTTPS
redirect. Certbot adds the concrete certificate paths after validation; they
are intentionally absent from the repository. Re-run `sudo nginx -t` before
reloading Nginx afterwards.

Confirm the Google OAuth application's authorised JavaScript origin and
redirect URI settings include the HTTPS production domain. Those Google-side
settings cannot be verified from this repository.

## 12. Validate, restart and reboot

Run these checks from the EC2 instance after deployment; no command here
changes AWS resources:

```bash
sudo systemctl status whereru-api nginx --no-pager
sudo journalctl -u whereru-api -n 100 --no-pager
curl -I http://127.0.0.1:8000/docs
curl -fsS http://127.0.0.1:8000/health/live
curl -fsS http://127.0.0.1:8000/health/ready
curl -fsS http://127.0.0.1:8000/version
curl -I https://where-areyou.com/
curl -I https://where-areyou.com/docs
curl -I https://where-areyou.com/openapi.json
```

After an intentional reboot, reconnect and verify both services are active:

```bash
sudo reboot
# after reconnect
sudo systemctl is-active whereru-api nginx
```

Production smoke-test checklist:

- Confirm browser HTTPS, Google login, and authenticated API calls.
- Confirm `/health/live`, `/health/ready`, and `/version` return successfully.
- Upload and read an authorised material; confirm it reaches `ready` or
  exposes `failed` status without remaining silently in `processing`.
- Generate a question and inspect its supporting context as the course
  instructor.
- Confirm typed assessment answers work. Do not use STT as an acceptance test:
  voice UI and Transcribe are intentionally disabled in production.

## 13. Update and rollback

Before updating, record the current release and snapshot the RDS instance:

```bash
cd /opt/whereru
git rev-parse HEAD
```

For an update, fetch the intended commit and inspect its changes. If the
release includes a database migration, take and verify an RDS snapshot first.
An existing database uses only its incremental migration—never `schema.sql`.
For the migration in this repository, apply it before restarting the API and
stop on the first SQL error. Skip this command when the intended release does
not include that migration:

```bash
# EC2
cd /opt/whereru
git pull --ff-only
psql -v ON_ERROR_STOP=1 "$DATABASE_URL" -f backend/sql/20260830_material_processing_and_question_provenance.sql
./backend/venv/bin/pip install -r backend/requirements.txt
sudo systemctl restart whereru-api
curl -fsS http://127.0.0.1:8000/health/live
curl -fsS http://127.0.0.1:8000/health/ready
curl -fsS http://127.0.0.1:8000/version
```

Update `/opt/whereru/backend/.env` before the dependency installation/restart
when the release requires backend configuration changes; protect its ownership
and permissions. Build the frontend locally with the four production Vite
variables from section 10, transfer its `dist/` directory, then replace
`/var/www/whereru/dist` while retaining `dist-previous`. Validate and reload
Nginx only after the static release is in place:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

Run the smoke-test checklist from section 12 after the deployment.

Rollback procedure:

1. If the migration fails, it stops at the failing statement. Do not restart
   the backend; investigate from the error and use the pre-change RDS snapshot
   only through a separately reviewed database-recovery procedure.
2. If backend startup or readiness fails, restore the previously recorded Git
   revision, restore the matching backend `.env` if it changed, reinstall its
   matching dependencies, then restart `whereru-api` and re-check health.
3. If frontend deployment fails, move the matching
   `dist-previous-<release-id>` directory back to
   `/var/www/whereru/dist`, run `sudo nginx -t`, then reload Nginx.

For this release, apply the checked-in, idempotent SQL upgrade to an existing
database before restarting the API. It marks a historical material `ready` only
when it has at least one persisted chunk and none of its chunks has a missing
or zero-vector embedding. All other historical materials become `failed`; new uploads start
as `processing`.

```bash
psql -v ON_ERROR_STOP=1 "$DATABASE_URL" -f backend/sql/20260830_material_processing_and_question_provenance.sql
```

Immediately verify the classification before allowing question generation:

```sql
SELECT processing_status, count(*)
FROM public.materials
GROUP BY processing_status;

SELECT material.id
FROM public.materials AS material
WHERE material.processing_status = 'ready'
  AND (
    NOT EXISTS (
      SELECT 1 FROM public.material_chunks AS chunk
      WHERE chunk.material_id = material.id
    )
    OR EXISTS (
      SELECT 1 FROM public.material_chunks AS chunk
      WHERE chunk.material_id = material.id
        AND (chunk.embedding IS NULL OR vector_norm(chunk.embedding) = 0)
    )
  );
```

The second query must return zero rows. It validates the structural condition
used by the migration; it cannot prove that source text is semantically useful.

## 14. Troubleshooting

```bash
sudo journalctl -u whereru-api -f
sudo journalctl -u nginx -n 100 --no-pager
sudo nginx -t
sudo ss -ltnp | grep 8000
curl -v http://127.0.0.1:8000/openapi.json
cd /opt/whereru && git status --short && git rev-parse HEAD
```

If FastAPI fails at startup, confirm file ownership/read permissions for
`.env` and `global-bundle.pem`, the `DATABASE_URL` endpoint/SSL settings, and
the RDS security-group path from EC2. For S3 failures, confirm the instance
has `whereru-ec2-role`, `AWS_REGION` and `S3_BUCKET_NAME` are correct, and
review CloudTrail/application logs without exposing credentials. For a 502,
check the service logs and that port 8000 is bound locally. For certificate
problems, verify DNS and Certbot/Nginx logs. For Transcribe errors, the known
account `SubscriptionRequiredException` means the feature is not validated
for production use.
