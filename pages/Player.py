import streamlit as st
import re
import pandas as pd
from api import get_match_data, get_player_stats, get_player_info, grab_steam_from_faceit
from visualizations import create_avg_rating_chart, create_comparison_chart

current_page = "Player"

if not st.user.is_logged_in:
    st.session_state.redirected = True
    st.switch_page("pages/User.py") 

# Set default tab
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "matches"

steam_id_param = st.query_params.get("steam_id")
if steam_id_param:
    st.session_state.current_steam_id = steam_id_param

def grab_player_info():
    if st.session_state.api_key and st.session_state.current_steam_id and st.session_state.active_tab == "matches":
        player_response = get_player_info(st.session_state.current_steam_id, st.session_state.api_key)
        player_name = player_response.get("player_name", "Player") if player_response else "Player"
        player_comp_data = player_response.get("comps", []) if player_response else []
        st.session_state.player_name = player_name
        st.session_state.player_comp_data = player_comp_data

# Track last loaded page
if st.session_state.get("last_page") != current_page:
    st.session_state.active_tab = "matches"
    st.session_state.last_page = current_page  
    st.session_state.matches = []
    st.session_state.offset = 0
    st.session_state.player_name = ""
    st.session_state.end_of_data = False
    st.query_params.clear()
    if st.session_state.current_steam_id:
        grab_player_info()
    
    st.rerun()

# Function to reset session state on steam id update
def update_steam_id():
    if steam_id != st.session_state.current_steam_id:
        st.session_state.matches = [] 
        st.session_state.offset = 0
        st.session_state.end_of_data = False
        st.session_state.current_steam_id = steam_id 
        st.session_state.player_name = ""
        grab_player_info()
        st.query_params.clear()
        st.rerun()  


player_name = st.session_state.get("player_name", "Player")
st.title(f"{player_name} Stats")


# --- INPUT ---
# Text input for Steam ID
user_input = st.text_input("🔍 Enter your Steam ID or players exact FACEIT name:", value=st.session_state.current_steam_id)
steam_id = None

if user_input:
    if user_input.isdigit():
        steam_id = user_input 
    elif re.fullmatch(r"[A-Za-z0-9_-]+", user_input):
        user_faceit = user_input
        faceit_steam = grab_steam_from_faceit(user_faceit)

        if not faceit_steam:
            st.error("❌ Could not retrieve FACEIT ID for the provided nickname.")
            st.stop()
        
        steam_id = faceit_steam
    else:
        st.error("❌ Input must be either all numbers (Steam ID) or all letters (FACEIT nickname).")
        st.stop()



# Trigger the function when the Steam ID is different
if steam_id and steam_id != st.session_state.current_steam_id:
    update_steam_id()

# --- API Key Check and create buttons for tabs, incorporate more future use Matches schema ---
if steam_id and st.session_state.api_key:
    col1, col2 = st.columns(2)
    if col1.button("Matches", width='stretch'):
        st.session_state.active_tab = 'matches'
    if col2.button("Stats", width='stretch'):
        st.session_state.active_tab = 'stats'

if steam_id and not st.session_state.api_key:
    st.warning("⚠️ API key required. Please enter it in the sidebar.")
    st.stop()

# --- Fetch and display data given active tab ---
if st.session_state.active_tab == 'matches' and steam_id:
    try:
        new_matches = get_match_data(steam_id, st.session_state.api_key, offset=st.session_state.offset)
        grab_player_info()
        st.query_params.steam_id = steam_id
        
        if new_matches is None:
            st.toast("⚠️ Failed to load match data.")
            matches = []
        elif len(new_matches) == 0:
            st.session_state.end_of_data = True
            st.toast("📉 No matches to load.")
            matches = []
        else:
            if len(new_matches) < 20:
                st.session_state.end_of_data = True
                st.toast("✅ All available matches loaded.")
            matches = new_matches

        if matches:
            df = pd.DataFrame(matches)

            # Format date
            df['Date'] = pd.to_datetime(df['match_date'].astype(int), unit='s').dt.date

            # Rename columns
            df.rename(columns={
                'match_checksum': 'Match ID',
                'comp_name': 'Event',
                'map': 'Map',
                'team_name': 'Team',
                'opponent_name': 'Opponent',
                'score': 'Score',
                'rating': 'Rating',
                'kills': 'Kills',
                'assists': 'Assists',
                'deaths': 'Deaths',
                'kdr': 'K/D',
                'kast': 'KAST%',
                'adr': 'ADR',
                'hs_per': 'HS%'
            }, inplace=True)

            # Define columns to be displayed
            display_columns = ['Date', 'Score', 'Map', 'Team', 'Opponent', 'Rating', 'Kills', 'Assists', 'Deaths', 'K/D', 'KAST%', 'ADR', 'HS%', 'Event']
            for col in display_columns:
                if col not in df.columns:
                    df[col] = None 

            # Identify numeric columns to provide a consistent number of decimal places.
            numeric_columns = ['Rating', 'K/D', 'ADR', 'KAST%', 'HS%']
            for col in numeric_columns:
                df[col] = df[col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else None)

            # Convert all values to strings for consistent display
            df = df.applymap(str)

            # --- Render Table ---
            event = st.dataframe(df[display_columns], width='stretch', hide_index=True, on_select="rerun", selection_mode="single-row")
            # Select a match row to jump to that match page
            if event.selection and event.selection.rows:
                selected_row_index = event.selection.rows[0]
                val = df.loc[selected_row_index, "Match ID"]
                st.session_state.selected_match_id = val
                st.switch_page("pages/Matches.py")

            # --- Pagination, dynamically change requests offset to get more pages. Limit currently defined ---
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.session_state.offset > 0 and col1.button("Previous Page"):
                    st.session_state.offset -= 20
                    st.session_state.matches = []
                    if st.session_state.offset == 0:
                        st.session_state.end_of_data = False
                    st.rerun()

            with col2:
                if not st.session_state.end_of_data and col2.button("Next Page"):
                    st.session_state.offset += 20
                    st.session_state.matches = []
                    st.rerun()
            
            # --- Events --- 
            st.subheader("Comps")
            if st.session_state.player_comp_data:
                comp_values = st.session_state.player_comp_data
                comp_df = pd.DataFrame(comp_values)

                # Format date
                comp_df['Date'] = pd.to_datetime(comp_df['last_match'].astype(int), unit='s').dt.date

                comp_df.rename(columns={
                'comp_id': 'Comp ID',
                'comp_name': 'Event',
                'team': 'Team',
                'maps': 'Maps',
                'rating': 'Rating',
                'kills': 'Kills',
                'deaths': 'Deaths',
                'kd_diff': 'K-D',
                'kast': 'KAST%',
                'adr': 'ADR'
                }, inplace=True)

                comp_columns = ['Date','Event', 'Team', 'Maps', 'Rating','Kills','Deaths','K-D','KAST%','ADR']
                for col in comp_columns:
                    if col not in comp_df.columns:
                        comp_df[col] = None 
                comp_df = comp_df.applymap(str)

                comp_clicker = st.dataframe(comp_df[comp_columns], width='stretch', hide_index=True, on_select="rerun", selection_mode="single-row")

                if comp_clicker.selection and comp_clicker.selection.rows:
                    comp_row_index = comp_clicker.selection.rows[0]
                    comp_val = comp_df.loc[comp_row_index, "Comp ID"]
                    st.session_state.selected_comp_id = comp_val
                    st.switch_page("pages/Events.py")

            # --- Chart ---
            avg_rating_chart = create_avg_rating_chart(df)
            st.altair_chart(avg_rating_chart, width='stretch')
        else:
            st.info("ℹ️ No comp data loaded yet.")
    
    except Exception as e:
        st.error("⚠️ An unexpected error occurred while loading comp data.")

elif st.session_state.active_tab == 'stats':
    stats = get_player_stats(steam_id, st.session_state.api_key)

    if stats:
        # Create the stats dictionary
        stat_categories = ['kills', 'deaths', 'assists','kd','kdr','kpr','adr','kast','rating', 'multi_kills', 't_rating', 'ct_rating']
        stat_data = {}
        stat_name_map = {
            'kills': 'Kills',
            'deaths': 'Deaths',
            'assists': 'Assists',
            'kd': 'K-D',
            'kdr': 'K/D Ratio',
            'kpr': 'Kills Per Round',
            'adr': 'ADR',
            'kast': 'KAST%',
            'rating': 'Rating',
            'multi_kills': 'Multi Kill%', 
            't_rating': 'T Rating', 
            'ct_rating': 'CT Rating'
        }

        for category in stat_categories:
            stat_data[category] = {
                'player': stats.get(category, {}).get('player', 0),
                'team': stats.get(category, {}).get('team', 0),
                'opponents': stats.get(category, {}).get('opponents', 0)
            }

        # Create the charts
        charts = {}
        for category in stat_categories:
            data = pd.DataFrame({
                'Category': ['Player', 'Team', 'Opponents'],
                category.capitalize(): [stat_data[category]['player'], stat_data[category]['team'], stat_data[category]['opponents']]
            })
            # Use the stat_name_map to get the user-friendly name, need to fix y axis
            charts[category] = create_comparison_chart(
                data, 'Category', category.capitalize(), f"AVG {stat_name_map.get(category, category.capitalize())}"
            )

        # Create rows of contained graphs
        col1, col2, col3 = st.columns(3)

        with col1:
            st.altair_chart(charts['kills'], width='stretch')

        with col2:
            st.altair_chart(charts['assists'], width='stretch')

        with col3:
            st.altair_chart(charts['deaths'], width='stretch')

        col4, col5, col6 = st.columns(3)

        with col4:
            st.altair_chart(charts['kd'], width='stretch')

        with col5:
            st.altair_chart(charts['kdr'], width='stretch')

        with col6:
            st.altair_chart(charts['kpr'], width='stretch')

        col7, col8, col9 = st.columns(3)

        with col7:
            st.altair_chart(charts['adr'], width='stretch')

        with col8:
            st.altair_chart(charts['kast'], width='stretch')

        with col9:
            st.altair_chart(charts['multi_kills'], width='stretch')

        col10, col11, col12 = st.columns(3)

        with col10:
            st.altair_chart(charts['rating'], width='stretch')

        with col11:
            st.altair_chart(charts['t_rating'], width='stretch')

        with col12:
            st.altair_chart(charts['ct_rating'], width='stretch')

    else:
        st.error("❌ Failed to load player stats.")
