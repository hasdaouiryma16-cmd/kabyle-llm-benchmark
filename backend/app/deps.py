"""Dépendances FastAPI partagées par les routes."""

from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session

from app.config import Settings
from app.db import get_session


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


SessionDep = Annotated[Session, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
