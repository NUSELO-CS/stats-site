import streamlit as st
from api import get_current_rankings

current_page = "UKCS_Events"

if st.session_state.get("last_page") != current_page:
    st.session_state.last_page = current_page

st.title("UKCS Rankings")

rankings = get_current_rankings()

# Add column headers
header_cols = st.columns([1, 3, 5, 2])
with header_cols[0]:
    st.markdown("**Ranking**")
with header_cols[1]:
    st.markdown("**Team Name**")
with header_cols[2]:
    st.markdown("**Players**")
with header_cols[3]:
    st.markdown("**Points**")

st.markdown("---")

if not rankings:
    st.markdown("No rankings available.")
else:
    for team in rankings:
        cols = st.columns([1, 3, 5, 2])
        with cols[0]:
            st.markdown(f"**{team['ranking']}**")
        with cols[1]:
            st.markdown(f"**{team['team_name']}**")
        with cols[2]:
            st.markdown(" - ".join(team['roster_names']))
        with cols[3]:
            st.markdown(f"**{team['points']}**")
        st.markdown("---")