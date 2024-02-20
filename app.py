
from datetime import date, timedelta

from database_modules.data_loader import load_to_db
from database_modules.db import (
    get_session,
    get_date_range,
    get_channels,
    get_videos,
    get_video_metrics_by_channel,
    get_video_count_by_day,
    get_total_video_count,
    get_video_metrics_by_video,
    get_total_unique_video_count,
    get_total_unique_channel_count,
)
import streamlit as st
from streamlit_player import st_player
import humanize

@st.cache_data()
def process_history(_session):
    """Process json file"""
    return load_to_db(_session)

@st.cache_data()
def total_video_count(_session, **filters) -> int:
    """Total number of videos."""
    return get_total_video_count(_session, **filters)

@st.cache_data()
def video_count_by_day(_session, **filters):
    """Videos by day."""
    return get_video_count_by_day(_session, **filters)

@st.cache_data()
def video_metrics_by_channel(_session, limit, **filters):
    """Stream count and play time by artist."""
    return get_video_metrics_by_channel(_session, limit, **filters)

@st.cache_data()
def date_range(_session) -> tuple[date, date]:
    """Minimum and maximum date of the data."""
    return get_date_range(_session)

@st.cache_data()
def channels(_session) -> list[str]:
    """List of channels."""
    return get_channels(_session)

@st.cache_data()
def videos(_session) -> list[str]:
    """List of videos."""
    return get_videos(_session)

@st.cache_data()
def total_unique_channels(_session, **filters) -> int:
    """List of videos."""
    return get_total_unique_channel_count(_session, **filters)

@st.cache_data()
def total_unique_videos(_session, **filters) -> int:
    """List of videos."""
    return get_total_unique_video_count(_session, **filters)

def display_filters(session) -> dict:
    """Display the data filters."""
    date_range_start, date_range_end = date_range(session)
    start_date, end_date = st.sidebar.slider(
        "Watch date",
        min_value=date_range_start,
        max_value=date_range_end,
        value=[date_range_start, date_range_end],
    )

    return {
        "start_date": start_date,
        "end_date": end_date,
        "channels": st.sidebar.multiselect("Channels", channels(session)),
        "videos": st.sidebar.multiselect("Videos", videos(session)),
    }

def display_statistics(session) -> None:
    """Display the listening statistics."""
    filters = display_filters(session)

    video_count = total_video_count(session, **filters)
    unique_channels = total_unique_channels(session, **filters)

    st.markdown(
        f"""
        You listened to **{humanize.intcomma(video_count)}** videos,
        and **{humanize.intcomma(unique_channels)}** unique channels :astonished:
        """,
    )
    st.bar_chart(
        video_count_by_day(session, **filters), x="date", y="views", color="#1DB954"
    )

    st.header(":microphone: Most Watched Channel")
    columns = st.columns(6)
    for i, channel_metric in enumerate(
        get_video_metrics_by_channel(session, limit=6, **filters)
    ):
        with columns[i].container(height=200):
            st.container(height=70, border=False).markdown(
                f"**{channel_metric.channel}** - {humanize.intcomma(channel_metric.views)} views"
            )
            st.markdown(channel_metric.channel_url)

    more = st.button('See more')
    if more:
        for i, channel_metric in enumerate(
            get_video_metrics_by_channel(session, limit=6, offset=6, **filters)
        ):
            with columns[i].container(height=200):
                st.container(height=70, border=False).markdown(
                    f"**{channel_metric.channel}** - {humanize.intcomma(channel_metric.views)} views"
                )
                st.markdown(channel_metric.channel_url)



    st.header(":musical_note: Most Watched Videos")
    columns = st.columns(3)
    for i, video_metric in enumerate(
        get_video_metrics_by_video(session, limit=3, **filters)
    ):
        with columns[i].container(border=True, height=500):
            st.markdown(f"{video_metric.title}")
            st.markdown(f"**{humanize.intcomma(video_metric.views)}** views")
            st_player(video_metric.titleUrl)

    see_more = st.button('See More')

    if see_more:
        video_metrics = get_video_metrics_by_video(session, limit=60, offset=3, **filters)
        
        # Assuming each video_metric contains title and titleUrl attributes
        for i in range(0, len(video_metrics), 3):
            row_videos = video_metrics[i:i+3]
            
            # Create three columns for each row
            col1, col2, col3 = st.columns(3)
            
            for j, video_metric in enumerate(row_videos):
                # Display each video in a separate column
                col = col1 if j == 0 else col2 if j == 1 else col3
                with col.container(border=True, height=500):
                    st.markdown(f"{video_metric.title}")
                    st.markdown(f"**{humanize.intcomma(video_metric.views)}** views")
                    st_player(video_metric.titleUrl)


def run() -> None:
    """Run the streamlit app."""
    st.set_page_config(
        page_title="YouTube Watch History",
        page_icon="🎧",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    db_session = st.cache_resource(get_session)()

    # Process uploaded file
    st.title("Youtube Watch History")

    placeholder = st.empty()
    placeholder.markdown(":point_left: _Upload the json file to get started_")

    uploaded_file = st.sidebar.file_uploader(
        "Upload Youtube Watch History", type="json"
    )
    if not uploaded_file:
        st.stop()
    placeholder.empty()

    with st.spinner("Processing YouTube history..."):
        file_path = 'data/watch-history.json'
        with open(file_path,'wb') as f:
            f.write(uploaded_file.read())
        process_history(db_session)

    display_statistics(db_session)

if __name__ == '__main__':
    run()
