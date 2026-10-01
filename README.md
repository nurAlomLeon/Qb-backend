# Question Bank Backend

FastAPI + SQLite backend for university admission question-bank apps (DU, RU, JU, CU, ...).
One deployment serves **many apps**: each app authenticates with its own `X-App-Key`, and every
content row is scoped by `university_id` (tenant).

## Highlights

- **Multi-tenant by design** - one SQLite database, tenant column on all content, per-app API keys.
- **Fast reads** - keyset pagination on `serial`, FTS5 full-text search (Bangla + English),
  eager-loaded options (no N+1), GZip, per-tenant `content_version` for cheap sync checks.
- **Optimized SQLite** - WAL journal, `foreign_keys=ON`, `busy_timeout`, tuned cache,
  covering composite indexes, nightly `PRAGMA optimize`.
- **Admin panel** - SQLAdmin CRUD at `/admin` plus custom pages: dashboard, bulk question
  import (CSV/XLSX/JSON), app-key generation, audit log.
- **Anonymous device users** - `POST /api/v1/auth/device` returns a signed token; bookmarks and
  practice results sync per device without login friction.

## Layout

```
backend/
  app/
    api/v1/        # public, user and health endpoints
    admin/         # SQLAdmin setup, auth, custom views and templates
    core/          # settings, security (bcrypt, tokens), rate limit, errors
    db/            # engine factory, SQLite pragmas, FTS5 schema
    models/        # SQLAlchemy 2.0 models
    schemas/       # Pydantic v2 request/response models
    services/      # content, search, bookmarks, sessions, importing
  alembic/         # migrations
  scripts/         # seed_demo, create_admin, import_questions, backup, optimize_db
  tests/           # pytest suite (33 tests)
  passenger_wsgi.py
  requirements.txt
```

## Local setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt      # Windows
# source .venv/bin/activate && pip install -r requirements-dev.txt   # Linux/macOS

copy .env.example .env                                  # then edit secrets
.venv\Scripts\python -m alembic upgrade head            # create schema + FTS
.venv\Scripts\python scripts\seed_demo.py --reset --admin-username admin --admin-password admin123
.venv\Scripts\python -m uvicorn app.main:app --reload --port 8000
```

- API docs: `http://127.0.0.1:8000/docs`
- Admin panel: `http://127.0.0.1:8000/admin` (login with the admin you created)
- The seed script prints the **app key** - copy it into the Flutter app.

Run the tests:

```bash
.venv\Scripts\python -m pytest tests -q
```

## API quick reference

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| GET | `/healthz` | - | health probe |
| GET | `/api/v1/config` | app key | branding, units, min/latest version, content version |
| GET | `/api/v1/units` | app key | units with paper/question counts |
| GET | `/api/v1/units/{id}/papers` | app key | published papers, newest first |
| GET | `/api/v1/papers/{id}` | app key | paper + subject breakdown |
| GET | `/api/v1/papers/{id}/questions` | app key | keyset pagination: `subject`, `after_serial`, `limit` |
| GET | `/api/v1/questions/{id}` | app key | full question incl. answer + explanation |
| GET | `/api/v1/search?q=` | app key | FTS5 search, snippet included |
| GET | `/api/v1/version/latest` | app key | force-update info |
| POST | `/api/v1/auth/device` | app key | register device, returns bearer token |
| GET/POST/DELETE | `/api/v1/bookmarks` | bearer | list / add / clear |
| DELETE | `/api/v1/bookmarks/{question_id}` | bearer | remove one |
| POST | `/api/v1/sessions` | bearer | submit answers, get score (0.25 negative marking) |
| GET | `/api/v1/progress/recent` | bearer | last practice for the home card |
| GET | `/api/v1/progress/stats` | bearer | score %, weekly solved, totals |

Headers: `X-App-Key: <per-app key>` for every API call, `Authorization: Bearer <token>` for user data.
Errors always look like `{"error": {"code": "...", "message": "..."}}`.

## Adding a new university app

1. Admin panel -> **Universities** -> create (e.g. slug `ru`).
2. Admin panel -> **Units / Subjects / Papers** -> create the structure.
3. Admin panel -> **App Keys** -> generate a key for that university (shown once).
4. Admin panel -> **Import Questions** -> upload CSV/XLSX/JSON into each paper.
5. Ship the key inside the new Flutter app build (`X-App-Key`).

## Question import format

Columns (CSV/XLSX header row, or JSON objects):

```
serial, subject_code, chapter_bn, stem_bn, stem_en,
option_a, option_b, option_c, option_d, correct,
explanation_bn, explanation_en, shortcut_bn, difficulty
```

- `correct`: `ক/খ/গ/ঘ`, `A/B/C/D` or `0-3`.
- `difficulty`: `easy`, `medium`, `hard`.
- Rows with an existing `serial` are updated, options replaced.
- JSON: a list of objects, or `{"questions": [...]}`.
- CLI alternative: `python scripts/import_questions.py --paper-id 1 --file q.csv`.

## Performance notes

- **Keyset pagination** - `WHERE paper_id=? AND serial>? ORDER BY serial LIMIT n` uses the
  `uq_questions_paper_serial` / `ix_questions_paper_subject_serial` index; no OFFSET scans.
- **Search** - FTS5 external-content table (`questions_fts`) with insert/update/delete triggers
  and `bm25()` ranking; `scripts/optimize_db.py` runs `optimize`.
- **Analytics** - per-question counters are updated on session submit; nightly
  `--recompute-analytics` rebuilds percentages from `session_answers`.
- **SQLite pragmas** - WAL + `synchronous=NORMAL` + `busy_timeout=5000` + `temp_store=MEMORY`
  + 64 MB page cache, applied on every connection.
- **Caching** - GZip for responses > 500 bytes; `content_version` lets apps skip re-syncs.

## cPanel deployment

Prerequisites: cPanel with **Setup Python App** (CloudLinux/Passenger) and a Python version
`3.9+` (check with `python3 --version` in the app's virtualenv; the code is 3.9-compatible).

1. **Upload** the `backend/` folder, e.g. to `/home/CPANEL_USER/duqbank-backend`.
2. **Create the app**: cPanel -> Setup Python App -> Create Application
   - Python version: newest available (3.11+ preferred)
   - Application root: `duqbank-backend`
   - Application URL: your domain or subdomain (e.g. `api.example.com`)
   - Application startup file: `passenger_wsgi.py`
   - Application Entry point: `application`
3. **Install dependencies**: in the app's virtualenv (cPanel shows the activate command):

   ```bash
   pip install -r requirements.txt
   ```

   `passenger_wsgi.py` wraps the ASGI app with `a2wsgi` because Passenger speaks WSGI.
4. **Environment variables**: paste into the Setup Python App "Environment variables" box
   (or create `.env` in the app root - never inside `public_html`):

   ```
   DUQB_ENVIRONMENT=production
   DUQB_DEBUG=false
   DUQB_DATABASE_URL=sqlite:////home/CPANEL_USER/data/duqbank/app.db
   DUQB_SECRET_KEY=<long random string>
   DUQB_ADMIN_SESSION_SECRET=<another long random string>
   DUQB_CORS_ORIGINS=*
   ```

   `DUQB_CORS_ORIGINS` accepts `*`, a comma list (`https://a.com,https://b.com`), or a JSON
   array (`["*"]`).

5. **Database**: create the data directory outside the webroot, then migrate and seed:

   ```bash
   mkdir -p /home/CPANEL_USER/data/duqbank
   python -m alembic upgrade head
   python scripts/seed_demo.py --reset --admin-username admin --admin-password '<strong-password>'
   ```

   For an existing database, skip `--reset`; use `scripts/import_questions.py` instead.
6. **Restart** the app from cPanel, then verify:
   - `https://api.example.com/healthz`
   - `https://api.example.com/docs`
   - `https://api.example.com/admin`
7. **HTTPS**: enable AutoSSL for the domain; apps should always use `https://`.

### Cron jobs (cPanel -> Cron Jobs)

```bash
# nightly backup, keep 14
0 2 * * * cd /home/CPANEL_USER/duqbank-backend && /home/CPANEL_USER/virtualenv/duqbank-backend/3.11/bin/python scripts/backup.py --out /home/CPANEL_USER/data/duqbank/backups --keep 14

# nightly maintenance + analytics recompute
30 2 * * * cd /home/CPANEL_USER/duqbank-backend && /home/CPANEL_USER/virtualenv/duqbank-backend/3.11/bin/python scripts/optimize_db.py --recompute-analytics

# weekly vacuum
0 3 * * 0 cd /home/CPANEL_USER/duqbank-backend && /home/CPANEL_USER/virtualenv/duqbank-backend/3.11/bin/python scripts/optimize_db.py --vacuum
```

(Adjust the virtualenv python path to the one cPanel shows for your app.)

### Restore a backup

```bash
cp /home/CPANEL_USER/data/duqbank/backups/app-<stamp>.db /home/CPANEL_USER/data/duqbank/app.db
```

## Security checklist

- Long random `DUQB_SECRET_KEY` and `DUQB_ADMIN_SESSION_SECRET`.
- Strong admin password; create admins with `python scripts/create_admin.py`.
- Admin panel is session-cookie protected, CSRF-protected on custom forms, and every admin
  action is written to `admin_audit_log`.
- Rate limiting on all `/api/*` routes (stricter on `/api/v1/auth`).
- Keep the database file and `.env` outside the webroot.
- Device tokens are signed (`itsdangerous`); rotate `DUQB_SECRET_KEY` to invalidate all of them.

## Troubleshooting

Run the built-in doctor first - it checks settings, database, tables, FTS, admin user and the
Passenger entry point in one shot:

```bash
cd /home/CPANEL_USER/duqbank-backend
python scripts/doctor.py
```

- **`no such table`** - run `python -m alembic upgrade head`.
- **`SettingsError ... error parsing value for field "cors_origins"`** - you are on an older
  copy of the code; update `app/core/config.py` (CORS is now a plain string parsed internally)
  or set `DUQB_CORS_ORIGINS=["*"]` as a stop-gap.
- **Search returns nothing** - rebuild the index:
  `python -c "from app.db.session import create_db_engine; from app.db.fts import rebuild_fts; e=create_db_engine('sqlite:///./duqbank.db'); [rebuild_fts(c) or c.commit() for c in [e.connect()]]"`.
- **Passenger 500 with "ASGI"** - make sure `passenger_wsgi.py` is the startup file and
  `a2wsgi` is installed in the app's virtualenv.
- **Bengali output garbled in terminal** - set `PYTHONIOENCODING=utf-8` (Windows).
- **bcrypt errors** - reinstall: `pip install --force-reinstall bcrypt`.
