import streamlit as st

st.set_page_config(
    page_title="NUSELO",
    page_icon="public/favicon.png",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://discord.nuselo.uk'
    }
)

st.logo("public/favicon.png")

if st.user.is_logged_in:
    st.session_state["api_key"] = st.user["https://nuselo.uk//api_token"]

events_page = st.Page("pages/Events.py", title="Events", icon=":material/trophy:")
player_page = st.Page("pages/Player.py", title="Player Data", icon=":material/person:")
home_page = st.Page("pages/Home.py", title="Home", icon=":material/home:")
matches_page = st.Page("pages/Matches.py", title="Matches", icon=":material/tv:")
rankings_page = st.Page("pages/Rankings.py", title="Rankings", icon=":material/language_gb_english:")
profile_page = st.Page("pages/User.py", title="Profile", icon=":material/person:")

if st.user.is_logged_in:
    pages = {
    "Landing": [
        home_page
    ],
    "Stats": [
        player_page,
        events_page,
        matches_page
    ],
    "UKCS": [
        rankings_page
    ],
    "User": [
        profile_page
    ],
    }
else:
    pages = {
    "Landing": [
        home_page
    ],
    "User": [
        profile_page
    ],
    }

pg = st.navigation(pages, expanded=False)

# --- SESSION STATE INIT ---
for key, default in {
    'api_key': "",
    'offset': 0,
    'matches': [],
    'end_of_data': False,
    'current_steam_id': "", # holding steam id value for usage in player stats section, incorp event
    'active_tab': 'matches',
    'selected_match_id': "", # holding match id value for usage in player stats section, incorp event
    'current_page': "",
    'last_page': "",
    'match_data': None,
    'player_name': "",
    'comp_data': {}, # check prev clash
    'selected_comp_id': ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


pg.run()