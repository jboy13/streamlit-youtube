"""Database module."""
import datetime
from typing import Sequence, Tuple

from sqlalchemy import (
    create_engine, distinct, Column, String, ARRAY, JSON, DateTime, and_, Integer, select
)
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.sql import func
from sqlalchemy.engine.row import Row


class Base(DeclarativeBase):  # noqa: D101
    pass

from sqlalchemy.sql import func

class Videos(Base):
    """YouTube Watch History table"""

    __tablename__ = "youtube"

    header = Column(String)
    title = Column(String)
    titleUrl = Column(String)
    time = Column(DateTime, primary_key=True, default=func.now())
    products = Column(ARRAY(String))
    activityControls = Column(ARRAY(String))
    channel = Column(String)
    channel_url = Column(String)
    count = Column(Integer)


def get_session() -> Session:
    """Get a database session.

    Returns:
        Session: Database session.
    """
    engine = create_engine("duckdb:///data/youtube.duckdb")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)
    return session()

def apply_filters(  # noqa: PLR0913
    select_stmt,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    channels: list[str] | None = None,
    videos: list[str] | None = None,
):
    """Apply where clauses to the provided select statement."""
    filters = set()

    if start_date:
        filters.add(Videos.time >= start_date)
    if end_date:
        filters.add(Videos.time <= end_date)
    if channels:
        filters.add(Videos.channel.in_(channels))
    if videos:
        filters.add(Videos.title.in_(videos))

    return select_stmt.where(and_(*filters))

def get_date_range(session) -> Row[Tuple[datetime.date, datetime.date]]:
    """Minimum and maximum date range of the data."""
    return session.execute(
        select(
            func.min(Videos.time).label("start"),
            func.max(Videos.time).label("end"),
        )
    ).one()

def get_channels(session) -> list[str]:
    """Distinct list of channels."""
    return [
        r.channel
        for r in session.execute(
            select(Videos.channel)
            .distinct()
            .order_by(Videos.channel)
            .where(Videos.channel.is_not(None))
        )
    ]

def get_videos(session) -> list[str]:
    """Distinct list of videos."""
    return [
        r.title
        for r in session.execute(
            select(Videos.title)
            .distinct()
            .order_by(Videos.title)
            .where(Videos.title.is_not(None))
        )
    ]

def get_video_metrics_by_channel(
    session: Session, limit: int = 10, offset: int = None, **filters
) -> Sequence[Row[Tuple[str, int, datetime.timedelta]]]:
    """List of tuples containing the artist, stream count and time played."""
    return session.execute(
        apply_filters(
            select(
                Videos.channel,
                func.count(Videos.channel).label("views")
            )
            .group_by(Videos.channel)
            .order_by(func.count(Videos.channel).desc(), Videos.channel)
            .limit(limit)
            .offset(offset),
            **filters
        )
    ).all()

def get_video_metrics_by_video(
    session: Session, limit: int = 10, offset: int = None, **filters
) -> Sequence[Row[Tuple[str, int, datetime.timedelta]]]:
    """List of tuples containing the artist, stream count and time played."""
    return session.execute(
        apply_filters(
            select(
                Videos.title,
                Videos.channel,
                func.count(Videos.count).label("views")
            )
            .group_by(Videos.title,Videos.channel)
            .order_by(func.count(Videos.title).desc(),Videos.title)
            .limit(limit)
            .offset(offset),
            **filters
        )
    ).all()

def get_video_count_by_day(
    session: Session, **filters
) -> Sequence[Row[Tuple[datetime.date, int]]]:
    """List of tuples containing the date and the stream count."""
    return session.execute(
        apply_filters(
            select(
                Videos.time.label("date"),
                func.sum(Videos.count).label("views"),
            ).group_by(Videos.time),
            **filters,
        )
    ).all()

def get_total_video_count(session: Session, **filters) -> int:
    """Total stream count."""
    return (
        session.scalar(apply_filters(select(func.count(Videos.title)), **filters))
        or 0
    )

def get_total_unique_video_count(session: Session, **filters) -> int:
    """Total stream count."""
    return (
        session.scalar(apply_filters(select(func.count(func.distinct(Videos.title))), **filters))
        or 0
    )

def get_total_unique_channel_count(session: Session, **filters) -> int:
    """Total stream count."""
    return (
        session.scalar(apply_filters(select(func.count(func.distinct(Videos.channel))), **filters))
        or 0
    )