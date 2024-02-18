"""Loader for listening history to db."""

import os
import shutil
import zipfile
from typing import IO
import pandas as pd
import duckdb

from database.db import Session


SQL ="""
CREATE OR REPLACE TABLE youtube AS
SELECT
    header,
    title,
    titleUrl,
    CAST(time AS DATE) as time,
    products,
    activityControls,
    JSON_EXTRACT(subtitles, '$[0].name') as channel,
    JSON_EXTRACT(subtitles, '$[0].url') as channel_url,
    1 as count
FROM
    read_json_auto('data/watch-history.json')
WHERE subtitles IS NOT NULL
"""


def load_to_db(session: Session) -> None:
    """Load music listening history to db.

    Args:
        session (Session): Database session.
        input (os.PathLike | IO[bytes]): youtube extract.
    """
    with session.get_bind().connect() as conn:
        # Create the audio table
        conn.exec_driver_sql(
            SQL
        )
        conn.exec_driver_sql(SQL)
        conn.commit()

