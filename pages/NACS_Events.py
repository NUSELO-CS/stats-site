import streamlit as st
from collections import defaultdict
from datetime import datetime
from api import get_event_regions

def format_date(iso_date_str):
    dt = datetime.fromisoformat(iso_date_str.replace("Z", ""))
    return dt.strftime("%d %b %Y")

events = get_event_regions('NA', st.session_state.api_key)

grouped_events = defaultdict(list)
for event in events:
    organizer = event.get("organizer") or "Other"
    grouped_events[organizer].append(event)

cols_per_row = 4

for organizer, organizer_events in grouped_events.items():
    st.header(organizer)

    for i in range(0, len(organizer_events), cols_per_row):
        row = organizer_events[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        
        for col, event in zip(cols, row):
            with col:
                st.write(f"**{event['name']}**")
                start = format_date(event['earliest_date'])
                end = format_date(event['latest_date'])
                st.caption(f"{start} → {end}")
                if st.button(label="View Event", use_container_width=False, key=f"view_{event['id']}"):
                    st.session_state.selected_comp_id = event["id"]
                    st.switch_page("pages/Events.py")

        st.markdown("---")
