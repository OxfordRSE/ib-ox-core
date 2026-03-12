import json
from collections.abc import Generator
from typing import Optional

from sqlalchemy import Boolean, Column, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ib_ox_api.settings import settings


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    scope_json = Column(String, nullable=False, default="{}")
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_all() -> None:
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_username(db: Session, username: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.username == username).first()


def create_user(
    db: Session,
    username: str,
    hashed_password: str,
    scope_json: str = "{}",
    is_active: bool = True,
    is_admin: bool = False,
) -> UserModel:
    user = UserModel(
        username=username,
        hashed_password=hashed_password,
        scope_json=scope_json,
        is_active=is_active,
        is_admin=is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(
    db: Session,
    user: UserModel,
    hashed_password: Optional[str] = None,
    scope_json: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
) -> UserModel:
    if hashed_password is not None:
        user.hashed_password = hashed_password
    if scope_json is not None:
        user.scope_json = scope_json
    if is_active is not None:
        user.is_active = is_active
    if is_admin is not None:
        user.is_admin = is_admin
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: UserModel) -> None:
    db.delete(user)
    db.commit()


def list_users(db: Session) -> list[UserModel]:
    return db.query(UserModel).all()


def scope_json_to_dict(scope_json: str) -> dict:
    """Parse the scope_json string into a dict."""
    try:
        return json.loads(scope_json)
    except (json.JSONDecodeError, TypeError):
        return {}
