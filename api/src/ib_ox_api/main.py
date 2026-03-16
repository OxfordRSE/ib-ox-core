import json
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ib_ox_api import __version__
from ib_ox_api.auth import authenticate_user, create_access_token, get_current_user, get_password_hash
from ib_ox_api.data import datastore
from ib_ox_api.database import (
    UserModel,
    run_migrations,
    create_user,
    delete_user,
    get_db,
    get_user_by_username,
    list_users,
    scope_json_to_dict,
    update_user,
)
from ib_ox_api.models import (
    FrequencyQuery,
    FrequencyResult,
    MeansQuery,
    MeansResult,
    Token,
    UserCreate,
    UserRead,
    UserScope,
    UserUpdate,
    WaveChangeQuery,
    WaveChangeResult,
)
from ib_ox_api.query import (
    execute_frequency_query,
    execute_means_query,
    execute_wave_change_query,
    validate_frequency_query,
    validate_means_query,
    validate_wave_change_query,
)
from ib_ox_api.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.warn_insecure_defaults()
    run_migrations()
    datastore.startup()
    yield
    datastore.shutdown()


app = FastAPI(
    title="IB-Oxford API",
    description="Read-only API for IB-Oxford longitudinal questionnaire data",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "version": __version__}


@app.post("/auth/login", response_model=Token, tags=["auth"])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "is_admin": user.is_admin})
    return Token(access_token=access_token, token_type="bearer")


@app.get("/data/columns", response_model=list[str], tags=["data"])
def get_columns(current_user: UserRead = Depends(get_current_user)) -> list[str]:
    df = datastore.get_dataframe()
    return list(df.columns)


@app.post("/query/frequency", response_model=FrequencyResult, tags=["query"])
def frequency_query(
    query: FrequencyQuery,
    current_user: UserRead = Depends(get_current_user),
) -> FrequencyResult:
    df = datastore.get_dataframe()
    df_cols = set(df.columns)
    try:
        validate_frequency_query(query, df_cols)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return execute_frequency_query(df, query, current_user.scope, settings.MIN_N)


@app.post("/query/means", response_model=MeansResult, tags=["query"])
def means_query(
    query: MeansQuery,
    current_user: UserRead = Depends(get_current_user),
) -> MeansResult:
    df = datastore.get_dataframe()
    df_cols = set(df.columns)
    try:
        validate_means_query(query, df_cols)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return execute_means_query(df, query, current_user.scope, settings.MIN_N)


@app.post("/query/wave-change", response_model=WaveChangeResult, tags=["query"])
def wave_change_query(
    query: WaveChangeQuery,
    current_user: UserRead = Depends(get_current_user),
) -> WaveChangeResult:
    """Compute within-person change between two waves.

    For each student with data in both `from_wave` and `to_wave`, computes the
    difference `(value at to_wave) - (value at from_wave)` for each value column.
    The per-student differences are then optionally grouped and averaged.
    Suppression is applied when fewer than `min_n` students contribute to a cell.
    """
    df = datastore.get_dataframe()
    df_cols = set(df.columns)
    try:
        validate_wave_change_query(query, df_cols)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    return execute_wave_change_query(df, query, current_user.scope, settings.MIN_N)


def _scope_to_json(scope: UserScope) -> str:
    return json.dumps(scope.model_dump())


# ---------------------------------------------------------------------------
# Admin helpers
# ---------------------------------------------------------------------------


def _require_admin(current_user: UserRead = Depends(get_current_user)) -> UserRead:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@app.get("/admin/users", response_model=list[UserRead], tags=["admin"])
def admin_list_users(
    _: UserRead = Depends(_require_admin),
    db: Session = Depends(get_db),
) -> list[UserRead]:
    users = list_users(db)
    result = []
    for u in users:
        scope_data = scope_json_to_dict(u.scope_json)
        result.append(
            UserRead(
                id=u.id,
                username=u.username,
                scope=UserScope(filters=scope_data.get("filters", {})),
                is_active=u.is_active,
                is_admin=u.is_admin,
            )
        )
    return result


@app.post("/admin/users", response_model=UserRead, status_code=status.HTTP_201_CREATED, tags=["admin"])
def admin_create_user(
    payload: UserCreate,
    _: UserRead = Depends(_require_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    existing = get_user_by_username(db, payload.username)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{payload.username}' already exists",
        )
    hashed = get_password_hash(payload.password)
    scope_json = _scope_to_json(payload.scope)
    user = create_user(
        db,
        username=payload.username,
        hashed_password=hashed,
        scope_json=scope_json,
        is_admin=payload.is_admin,
    )
    scope_data = scope_json_to_dict(user.scope_json)
    return UserRead(
        id=user.id,
        username=user.username,
        scope=UserScope(filters=scope_data.get("filters", {})),
        is_active=user.is_active,
        is_admin=user.is_admin,
    )


@app.put("/admin/users/{user_id}", response_model=UserRead, tags=["admin"])
def admin_update_user(
    user_id: int,
    payload: UserUpdate,
    _: UserRead = Depends(_require_admin),
    db: Session = Depends(get_db),
) -> UserRead:
    user = db.query(UserModel).filter_by(id=user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    hashed = get_password_hash(payload.password) if payload.password else None
    scope_json = _scope_to_json(payload.scope) if payload.scope is not None else None
    updated = update_user(
        db,
        user,
        hashed_password=hashed,
        scope_json=scope_json,
        is_active=payload.is_active,
        is_admin=payload.is_admin,
    )
    scope_data = scope_json_to_dict(updated.scope_json)
    return UserRead(
        id=updated.id,
        username=updated.username,
        scope=UserScope(filters=scope_data.get("filters", {})),
        is_active=updated.is_active,
        is_admin=updated.is_admin,
    )


@app.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["admin"])
def admin_delete_user(
    user_id: int,
    current_admin: UserRead = Depends(_require_admin),
    db: Session = Depends(get_db),
) -> None:
    user = db.query(UserModel).filter_by(id=user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    delete_user(db, user)


@app.get("/admin/me", response_model=UserRead, tags=["admin"])
def admin_me(current_user: UserRead = Depends(get_current_user)) -> UserRead:
    """Return the current user's details, including is_admin flag."""
    return current_user
