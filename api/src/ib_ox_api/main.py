from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ib_ox_api import __version__
from ib_ox_api.auth import authenticate_user, create_access_token, get_current_user
from ib_ox_api.data import datastore
from ib_ox_api.database import create_all, get_db
from ib_ox_api.models import (
    FrequencyQuery,
    FrequencyResult,
    MeansQuery,
    MeansResult,
    Token,
    UserRead,
)
from ib_ox_api.query import (
    execute_frequency_query,
    execute_means_query,
    validate_frequency_query,
    validate_means_query,
)
from ib_ox_api.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.warn_insecure_defaults()
    create_all()
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
    access_token = create_access_token(data={"sub": user.username})
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
