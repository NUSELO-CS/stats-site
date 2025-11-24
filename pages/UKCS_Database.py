import streamlit as st
import pandas as pd
import string
from api import get_ukcs_details, get_ukcs_players

current_page = "UKCS_Database"

if not st.user.is_logged_in:
    st.session_state.redirected = True
    st.switch_page("pages/User.py") 

# Set default tab
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "events"

# Track last loaded page
if st.session_state.get("last_page") != current_page:
    st.session_state.active_tab = "events"
    st.session_state.last_page = current_page 
    st.session_state.player_db_data = None
    st.session_state.db_searching = True

steam_id_param = st.query_params.get("steam_id")
if steam_id_param:
    st.session_state.db_steam_id = steam_id_param
    st.session_state.db_searching = False

def update_steam_id():
    if steam_id != st.session_state.db_steam_id:
        st.session_state.db_steam_id = steam_id 
        st.session_state.player_db_data = None
        st.session_state.db_name = ""
        st.query_params.clear()
        get_or_set_player_db_data()
        st.rerun()  
    
top_cols = st.columns([0.92,0.08])
if st.session_state.db_searching == True:
    with top_cols[1]:
        advanced = st.toggle("Advanced")
else:
    with top_cols[1]:
        if st.button("Return",width='stretch'):
            st.session_state.active_tab = "events"
            st.session_state.player_db_data = None
            st.session_state.db_name = ""
            st.session_state.db_searching = True
            st.session_state.db_steam_id = ""
            st.query_params.clear()
            st.rerun()

        

if not st.session_state.db_steam_id:
    steam_id = None
else: 
    steam_id = st.session_state.db_steam_id

def get_or_set_player_db_data():
    if st.session_state.get("player_db_data"):
        return st.session_state.player_db_data
    else:
        player_db_data = get_ukcs_details(steam_id, st.session_state.api_key)
        if player_db_data:
            st.session_state.player_db_data = player_db_data
            return player_db_data
        else:
            return None


if steam_id and st.session_state.api_key and st.session_state.db_searching == False:
    player_db_data = get_or_set_player_db_data()

if(st.session_state.player_db_data):
    player_name = st.session_state.player_db_data.get("name", "Player")
else:
    player_name = "Player"
st.title(f"{player_name}")

if st.session_state.db_searching == True:
    if advanced:
        steam_id = st.text_input("🔍 Enter a players Steam ID:", value=st.session_state.db_steam_id)

if steam_id and steam_id != st.session_state.db_steam_id:
    update_steam_id()

if steam_id and not st.session_state.api_key:
    st.warning("⚠️ API key required.") # Somewhat redundant but will remove when all of alpha <v1.1 would have expired
    st.stop()

if st.session_state.api_key and st.session_state.db_searching == True:
    letters = list(string.ascii_uppercase)

    selected_letter = st.selectbox("Select a letter to search player:", letters)

    ukcs_p_response = get_ukcs_players(selected_letter, st.session_state.api_key)
    players = sorted(ukcs_p_response["players"], key=lambda p: p["name"].lower())

    st.write(f"Players starting with **{selected_letter}**:")

    chunk_size = 5
    for i in range(0, len(players), chunk_size):
        row_players = players[i:i + chunk_size]

        col_widths = []
        for idx in range(9):
            if idx % 2 == 0:
                col_widths.append(6) 
            else:
                col_widths.append(2) 

        cols = st.columns(col_widths)

        for j in range(9):
            if j % 2 == 0:
                player_idx = j // 2
                if player_idx < len(row_players):
                    player = row_players[player_idx]
                    with cols[j]:
                        if st.button(player["name"], key=player["steam_id"], width='stretch'):
                            st.session_state.db_steam_id = player['steam_id'] 
                            st.session_state.player_db_data = None
                            st.session_state.db_name = ""
                            st.session_state.db_searching = False
                            st.rerun()
                else:
                    with cols[j]:
                        st.write("")  
            else:
                with cols[j]:
                    st.write("")


if steam_id and st.session_state.api_key and st.session_state.db_searching == False:
    st.query_params.steam_id = steam_id
    col1, col2, col3 = st.columns(3)
    if col1.button("Events", width='stretch'):
        st.session_state.active_tab = 'events'
    if col2.button("ESEA", width='stretch'):
        st.session_state.active_tab = 'esea'
    if col3.button("UKIC", width='stretch'):
        st.session_state.active_tab = 'ukic'

if st.session_state.active_tab == 'events' and st.session_state.api_key and steam_id and st.session_state.player_db_data and st.session_state.db_searching == False:
    events = st.session_state.player_db_data.get("events",{})
    st.markdown("---")
    header_cols = st.columns([0.05,0.6,1.025,1.95,0.375])
    with header_cols[1]:
        st.markdown("**Event**")
    with header_cols[2]:
        st.markdown("**Team**")
    with header_cols[3]:
        st.markdown("**Roster**")
    with header_cols[4]:
        st.markdown("**Placement**")
    if events:
        for event in events:
            with st.container(border=True):
                roster_names = [player["name"] for player in event["roster"]]
                joined_names = "\u00A0\u00A0-\u00A0\u00A0".join(roster_names)
                cols = st.columns([0.6,0.8,2.275,0.325])
                with cols[0]:
                    st.markdown(f"**{event['event_name']}**")
                with cols[1]:
                    st.markdown(f"**{event['team_name']}**")
                with cols[2]:
                    st.markdown(f"**{joined_names}**")
                with cols[3]:
                    st.markdown(f"**{event['placement_text']}**")

if st.session_state.active_tab == 'esea' and st.session_state.api_key and steam_id and st.session_state.player_db_data and st.session_state.db_searching == False:
    esea_seasons = st.session_state.player_db_data.get("esea",{})
    st.markdown("---")
    header_cols = st.columns([0.1,0.5,0.5,1.3,2.1,0.5])
    with header_cols[1]:
        st.markdown("**Team**")
    with header_cols[2]:
        st.markdown("**Season**")
    with header_cols[3]:
        st.markdown("**Division**")
    with header_cols[4]:
        st.markdown("**Roster**")
    with header_cols[5]:
        st.markdown("**Record**")
    if esea_seasons:
        for esea in esea_seasons:
            with st.container(border=True):
                roster_names = [player["name"] for player in esea["roster"]]
                joined_names = "\u00A0\u00A0-\u00A0\u00A0".join(roster_names)
                cols = st.columns([0.6,0.45,0.95,2.475,0.425])
                with cols[0]:
                    st.markdown(f"**{esea['team_name']}**")
                with cols[1]:
                    st.markdown(f"**{esea['season']}**")
                with cols[2]:
                    st.markdown(f"**{esea['division']}**")
                with cols[3]:
                    st.markdown(f"**{joined_names}**")
                with cols[4]:
                    st.markdown(f"**{esea['record']}**")

if st.session_state.active_tab == 'ukic' and st.session_state.api_key and steam_id and st.session_state.player_db_data and st.session_state.db_searching == False:
    ukic_seasons = st.session_state.player_db_data.get("ukic",{})
    st.markdown("---")
    header_cols = st.columns([0.1,0.5,0.5,1.3,1.6,0.5,0.5])
    with header_cols[1]:
        st.markdown("**Team**")
    with header_cols[2]:
        st.markdown("**Season**")
    with header_cols[3]:
        st.markdown("**Division**")
    with header_cols[4]:
        st.markdown("**Roster**")
    with header_cols[5]:
        st.markdown("**Wins**")
    with header_cols[6]:
        st.markdown("**Placement**")
    if ukic_seasons:
        for ukic in ukic_seasons:
            with st.container(border=True):
                roster_names = [player["name"] for player in ukic["roster"]]
                joined_names = "\u00A0\u00A0-\u00A0\u00A0".join(roster_names)
                cols = st.columns([0.6,0.45,0.95,1.975,0.5,0.425])
                with cols[0]:
                    st.markdown(f"**{ukic['team_name']}**")
                with cols[1]:
                    st.markdown(f"**{ukic['season']}**")
                with cols[2]:
                    st.markdown(f"**{ukic['division']}**")
                with cols[3]:
                    st.markdown(f"**{joined_names}**")
                with cols[4]:
                    st.markdown(f"**{ukic['wins']}**")
                with cols[5]:
                    st.markdown(f"**{ukic['placement']}**")