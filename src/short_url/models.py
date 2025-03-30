from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Table, MetaData


metadata = MetaData()


links = Table(
    "links",
    metadata,
    Column("link_id", Integer, primary_key=True, index=True, autoincrement=True),
    Column("original_url", String, nullable=False),
    Column("short_code", String, unique=True, nullable=False),
    Column("created_at", DateTime, default=datetime.now),
    Column("expires_at", DateTime),
    Column("user_id", Integer, ForeignKey('users.id')),
    Column("click_count", Integer, default=0),
    Column("last_accessed", DateTime)
)
