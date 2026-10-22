from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import auth, users
from app.core.config import settings
from app.db.session import Base, SessionLocal, engine
from app.models.user import User
from app.services.security import hash_password

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Convenient for learning/local development. Use Alembic migrations in production.
    Base.metadata.create_all(bind=engine)
    # Bootstrap one admin account if it does not exist.
    with SessionLocal() as db:
        admin_email = settings.bootstrap_admin_email.lower()
        admin = db.query(User).filter(User.email == admin_email).first()
        if not admin:
            admin = User(email=admin_email, full_name="System Admin",
                         password_hash=hash_password(settings.bootstrap_admin_password),
                         role="admin", is_active=True)
            db.add(admin)
            db.commit()
    yield

app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
