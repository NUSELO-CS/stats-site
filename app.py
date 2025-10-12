import streamlit as st
from api import get_profile
from tools.perms import has_access

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
    'db_name': "",
    'comp_data': {},
    'comp_stats': {},
    'player_db_data': {},
    'selected_comp_id': "",
    'user_steam_id': None,
    'redirected': "",
    'db_steam_id': "",
    'db_searching': True
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

if st.user.is_logged_in:
    if not st.user.get("https://nuselo.uk//api_token"):
        st.logout()
    st.session_state["api_key"] = st.user["https://nuselo.uk//api_token"]
    discord_sub = st.user.get("sub", "")
    user_id = discord_sub.split("|")[-1] if "discord" in discord_sub else None
    if st.session_state["user_steam_id"] is None:
        user_response = get_profile(user_id, st.session_state.api_key)
        user_steam_id = user_response.get("steam_id", None)
        st.session_state["user_steam_id"] = user_steam_id

        user_roles = user_response.get("roles", [])
        st.session_state["user_roles"] = user_roles
    

events_page = st.Page("pages/Events.py", title="Events", icon=":material/trophy:")
player_page = st.Page("pages/Player.py", title="Player Data", icon=":material/person:")
home_page = st.Page("pages/Home.py", title="Home", icon=":material/home:",default=True)
matches_page = st.Page("pages/Matches.py", title="Matches", icon=":material/tv:")

rankings_page = st.Page("pages/Rankings.py", title="Rankings", icon=":material/language_gb_english:")
ukcs_events_page = st.Page("pages/UKCS_Events.py",title="UK Events",icon=":material/trophy:")
ukcs_database_page = st.Page("pages/UKCS_Database.py",title="UKCS Database",icon=":material/database:")

nacs_events_page = st.Page("pages/NACS_Events.py",title="NA Events",icon=":material/trophy:")

login_page = st.Page("pages/User.py", title="Log in", icon=":material/person:")
profile_page = st.Page("pages/User.py", title="Profile", icon=":material/person:")

ukic_admin_home = st.Page("ukic/admin_home.py", title = "Home", icon=":material/manage_accounts:")
ukic_roster = st.Page("ukic/admin_roster.py", title = "Rosters", icon=":material/contacts:")
ukic_match = st.Page("ukic/admin_match.py", title = "Match", icon=":material/tv:")

if st.user.is_logged_in:
    pages = {
        "Landing": [home_page],
        "Stats": [player_page, events_page, matches_page],
        "UKCS": [rankings_page, ukcs_events_page, ukcs_database_page],
        "NACS": [nacs_events_page],
        "User": [profile_page],
        "UKIC": []
    }
    if has_access(["platform_admin", "ukic_admin"]):
        pages["UKIC"].append(ukic_admin_home)
        pages["UKIC"].append(ukic_roster)
        pages["UKIC"].append(ukic_match)
else:
    pages = {
        "Log in here": [login_page],
        "Landing": [home_page],
        "UKCS": [rankings_page],
        "Unavailable": [
            player_page, events_page, matches_page,
            ukcs_events_page, ukcs_database_page, nacs_events_page
        ],
    }

pg = st.navigation(pages, expanded=True, position="top")


pg.run()