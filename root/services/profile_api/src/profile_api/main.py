import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from profile_api.app import create_app
from profile_api.config import Settings


database_url = os.environ["DATABASE_URL"]
engine = create_engine(database_url, pool_pre_ping=True)
session_factory = sessionmaker(engine, expire_on_commit=False)
app = create_app(
    session_factory=session_factory,
    settings=Settings.from_environment(),
)
