# FastAPI User Management API (learning project)

A simple layered REST API using FastAPI, Pydantic v2, SQLAlchemy 2, MySQL, JWT, Google ID-token login, and Uvicorn.

## 1. What we are building

- Register and log in with email + password
- Log in with Google Identity Services (Google ID token verification)
- Read/update/delete your own profile
- Change password and request/reset a forgotten password
- Admin can list/read/update/deactivate/delete users
- JWT bearer access token for protected routes
- MySQL persistence and Uvicorn development server

**Important scope choices:** this sample uses a Google ID-token exchange endpoint (`POST /api/v1/auth/google`) rather than a server-side redirect/callback flow. The frontend must obtain the ID token using Google Identity Services. Logout is stateless for JWT: the client deletes the token. For immediate revocation, implement a token denylist or refresh-token rotation. Password-reset tokens are printed to the server console only when SMTP is not configured; this is for local learning only.

## 2. Request flow (real-time behavior)

```text
Browser / Postman
    |
    | HTTP request + JSON / Bearer JWT
    v
FastAPI Router (REST API: URL, HTTP method, validation)
    |
    v
Pydantic Schema (validates incoming JSON and shapes response)
    |
    v
Service Layer (business rules: duplicate email, password checks, role rules)
    |
    v
SQLAlchemy ORM / SQL query
    |
    v
MySQL database
    |
    v
Service -> Router -> JSON response (password_hash is never in public schemas)
```

Example: `POST /api/v1/auth/register` -> `UserCreate` validates email/password -> `user_service.create_user()` hashes password and checks duplicate email -> SQLAlchemy INSERT -> MySQL -> response contains public user fields only.

## 3. What / Why / Where

| Part | What | Why |
|---|---|---|
| FastAPI router | HTTP endpoints | Maps URL + method to Python function |
| Pydantic schema | Request/response validation | Rejects invalid data and prevents exposing internal fields |
| Service | Business logic | Reuse logic independent of HTTP |
| SQLAlchemy model | Python mapping of a DB table | Work with rows as Python objects |
| Session / engine | Database connection lifecycle | Reuse pooled connections and close each request's session |
| MySQL | Durable storage | Keeps users after server restarts |
| Password hashing | Argon2 hash, not plain text | Database leak should not reveal raw passwords |
| JWT | Signed access token | Stateless authentication between requests |
| Role dependency | `user` vs `admin` | Enforces authorization on server |
| Google ID token verification | Verify token audience/signature with Google library | Do not trust client-submitted email alone |

## 4. Setup from zero

### Step 1 — Create a virtual environment

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
# macOS/Linux
source .venv/bin/activate
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Create the MySQL database and account

Run in MySQL as a privileged user (choose your own strong password):

```sql
CREATE DATABASE user_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'app_user'@'localhost' IDENTIFIED BY 'change_me';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX ON user_management.* TO 'app_user'@'localhost';
FLUSH PRIVILEGES;
```

### Step 4 — Configure environment

```bash
# Windows
copy .env.example .env
# macOS/Linux
cp .env.example .env
```

Edit `.env`: set `DATABASE_URL`, a unique long `JWT_SECRET_KEY`, and a strong `BOOTSTRAP_ADMIN_PASSWORD`. Do not commit `.env`.

Generate a secret, for example:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### Step 5 — Run server

```bash
uvicorn app.main:app --reload
```

Open:
- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json
- Health: http://127.0.0.1:8000/health

Tables are created automatically on startup for this learning project. For production, replace `create_all()` with Alembic migrations.

## 5. Google login setup

1. Create/select a project in Google Cloud Console.
2. Configure OAuth consent screen and create a Web OAuth client ID.
3. Configure allowed JavaScript origins for your frontend.
4. Put that client ID into `GOOGLE_CLIENT_ID` in `.env`.
5. Frontend uses Google Identity Services to obtain an ID token.
6. Send `{ "id_token": "<Google ID token>" }` to `POST /api/v1/auth/google`.
7. Backend verifies token signature, audience, expiry, and verified email via `google-auth`.

Never accept an email/name from the browser as proof of Google identity. For a server-rendered redirect/callback flow, add OAuth authorization-code handling separately.

## 6. Endpoints: normal user vs admin

Base URL: `http://127.0.0.1:8000/api/v1`

| Method | URL | Access | Purpose |
|---|---|---|---|
| POST | `/auth/register` | Public | Create email/password account |
| POST | `/auth/login` | Public | Login and get JWT |
| POST | `/auth/google` | Public + valid Google ID token | Google login and get JWT |
| POST | `/auth/forgot-password` | Public | Request reset instructions |
| POST | `/auth/reset-password` | Public + reset token | Set a new password |
| POST | `/auth/logout` | Authenticated | Client logout signal; delete token |
| POST | `/auth/change-password` | Authenticated | Change password using current password |
| GET | `/users/me` | User/Admin | Read own profile |
| PATCH | `/users/me` | User/Admin | Update own profile name |
| DELETE | `/users/me` | User/Admin | Delete own account |
| GET | `/admin/users` | Admin only | List all users |
| GET | `/admin/users/{user_id}` | Admin only | Read a user |
| PATCH | `/admin/users/{user_id}` | Admin only | Update name, role, active status |
| DELETE | `/admin/users/{user_id}` | Admin only | Delete a user |

## 7. Login and JWT usage

1. Call `POST /api/v1/auth/login` with:

```json
{ "email": "user@example.com", "password": "a-strong-password" }
```

2. Copy `access_token` from response.
3. In Swagger click **Authorize**, enter `Bearer YOUR_ACCESS_TOKEN` (or use `Authorization: Bearer YOUR_ACCESS_TOKEN` in Postman).
4. Call a protected endpoint. JWT payload contains `sub` (user ID), `role`, `type`, and `exp`. Never put passwords or secrets in JWT claims.
5. Access token expires after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 30). Log in again when expired in this starter app.

## 8. Try it with curl

Register a user:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\\"email\\":\\"user@example.com\\",\\"full_name\\":\\"Demo User\\",\\"password\\":\\"A-strong-pass-123\\"}"
```

Login:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login ^
  -H "Content-Type: application/json" ^
  -d "{\\"email\\":\\"user@example.com\\",\\"password\\":\\"A-strong-pass-123\\"}"
```

Then call profile:

```bash
curl http://127.0.0.1:8000/api/v1/users/me -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

PowerShell users can use `curl.exe`; in Postman, select Body -> raw -> JSON. Replace `^` with backticks for multi-line PowerShell commands, or send the requests in Swagger UI.

## 9. Admin login

The app creates an initial admin during startup if `BOOTSTRAP_ADMIN_EMAIL` is not already in the database. Set a strong password in `.env`, start the app, then call the normal login endpoint with those credentials. The JWT's `role` claim is informative; authorization is enforced by loading the user from DB and checking `user.role` on each protected request.

Do not expose a default admin password in a deployed environment. Change it before first startup and protect the bootstrap settings.

## 10. File layout

```text
fastapi_user_management/
├── app/
│   ├── api/
│   │   ├── deps.py             # current user + admin authorization
│   │   └── routes/
│   │       ├── auth.py         # register/login/Google/reset/logout
│   │       └── users.py        # self-service + admin CRUD
│   ├── core/config.py          # environment settings
│   ├── db/session.py           # SQLAlchemy engine/session/dependency
│   ├── models/user.py          # users table
│   ├── schemas/user.py         # Pydantic validation/response models
│   ├── services/
│   │   ├── security.py         # hashing + JWT
│   │   ├── email_service.py    # reset email or local console link
│   │   └── user_service.py     # business logic and DB operations
│   └── main.py                 # app startup + routers
├── .env.example
├── requirements.txt
└── README.md
```

## 11. Production checklist (do not skip before public deployment)

- Use HTTPS and secure reverse-proxy settings.
- Use a strong random JWT secret stored in a secret manager/environment, not source control.
- Replace schema auto-creation with Alembic migrations.
- Add rate limiting to login, Google login, and forgot-password routes.
- Add generic responses and rate limits to reduce account enumeration.
- Store password reset tokens hashed in a DB table, make them single-use, and revoke existing sessions after reset.
- Use a token denylist or short-lived access tokens plus refresh-token rotation if server-side logout/revocation is required.
- Configure SMTP and never print reset tokens in production logs.
- Add email verification, audit logs, password policy, CORS allowlist, request-size limits, and security monitoring.
- Prevent admins from disabling/deleting the last active admin.
- Add tests and database migrations; use a separate least-privilege DB account.
- Add pagination to `GET /admin/users` for large datasets.
- Keep Google OAuth client IDs and secrets in environment config; do not trust client profile data without validating Google's token.

## 12. Practice exercises

1. Add pagination (`limit`, `offset`) to admin user listing.
2. Add `phone_number` and `bio` to the model/schema, then create a migration.
3. Implement refresh tokens with rotation and revocation.
4. Create a DB-backed one-time reset-token table.
5. Add pytest tests for duplicate registration, wrong password, user-vs-admin access, and disabled accounts.
6. Add a separate admin audit log table for role changes and user deletion.

## 13. Interview questions

- Why should passwords be hashed rather than encrypted or stored as plain text?
- What does Pydantic validate and what does SQLAlchemy do?
- Why use a service layer instead of writing SQL in every route?
- What is the difference between authentication and authorization?
- What are `401 Unauthorized` and `403 Forbidden` used for?
- What is inside a JWT, and why must sensitive data not be placed in it?
- Why does JWT logout need extra work for immediate revocation?
- Why must Google ID tokens be verified server-side?
- Why use a SQLAlchemy session dependency per request?
- Why use Alembic in production rather than `Base.metadata.create_all()`?

## 14. Cheat sheet

- Register: `POST /api/v1/auth/register`
- Email/password login: `POST /api/v1/auth/login`
- Google login: `POST /api/v1/auth/google`
- My profile: `GET /api/v1/users/me`
- Update profile: `PATCH /api/v1/users/me`
- Change password: `POST /api/v1/auth/change-password`
- Forgot/reset password: `POST /api/v1/auth/forgot-password` -> email link -> `POST /api/v1/auth/reset-password`
- Logout: `POST /api/v1/auth/logout` then delete token client-side
- Admin list: `GET /api/v1/admin/users`
- Admin update: `PATCH /api/v1/admin/users/{user_id}`
- Admin delete: `DELETE /api/v1/admin/users/{user_id}`
- Run: `uvicorn app.main:app --reload`
- Swagger: `http://127.0.0.1:8000/docs`
