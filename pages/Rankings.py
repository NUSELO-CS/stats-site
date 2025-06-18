import streamlit as st
from api import get_current_rankings

current_page = "UKCS_Events"

if st.session_state.get("last_page") != current_page:
    st.session_state.last_page = current_page

st.title("UKCS Rankings")

rankings = get_current_rankings()

# Add column headers
header_cols = st.columns([0.1,0.9, 3, 5, 1])
with header_cols[1]:
    st.markdown("**Ranking**")
with header_cols[2]:
    st.markdown("**Team Name**")

if not rankings:
    st.markdown("No rankings available.")
else:
    for team in rankings:
        with st.container(border=True):
            cols = st.columns([0.1, 1, 3, 6.4, 0.5])
            with cols[0]:
                st.write("") 
            with cols[1]:
                st.markdown(f"**{team['ranking']}**")
            with cols[2]:
                st.markdown(f"**{team['team_name']}**")
            with cols[3]:
                st.markdown("\u00A0\u00A0-\u00A0\u00A0".join(team['roster_names']))
            with cols[4]:
                st.markdown(f"**{team['points']}**")