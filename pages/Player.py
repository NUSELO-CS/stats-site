import streamlit as st
import pandas as pd
from api import get_match_data, get_player_stats
from visualizations import create_avg_rating_chart, create_comparison_chart

st.title("Player Stats Viewer")

current_page = "Player"

# Set default tab
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "matches"

# Track last loaded page
if st.session_state.get("last_page") != current_page:
    st.session_state.active_tab = "matches"  # reset on page load
    st.session_state.last_page = current_page  # update tracker
    st.session_state.matches = []
    st.session_state.offset = 0
    st.session_state.end_of_data = False
    st.rerun()

# --- INPUT ---
# Text input for Steam ID
steam_id = st.text_input("🔍 Enter your Steam ID:", value=st.session_state.current_steam_id)

# Function to reset session state on steam id update
def update_steam_id():
    if steam_id != st.session_state.current_steam_id:  # If Steam ID has changed
        st.session_state.matches = []  # Clear matches
        st.session_state.offset = 0
        st.session_state.end_of_data = False
        st.session_state.current_steam_id = steam_id  # Save the newer Steam ID
        st.rerun()  # Force rerun

# Trigger the function when the Steam ID is different
if steam_id and steam_id != st.session_state.current_steam_id:
    update_steam_id()

# --- API Key Check and create buttons for tabs, incorporate more future use Matches schema ---
if steam_id and st.session_state.api_key:
    col1, col2 = st.columns(2)
    if col1.button("Matches", use_container_width=True):
        st.session_state.active_tab = 'matches'
    if col2.button("Stats", use_container_width=True):
        st.session_state.active_tab = 'stats'

if steam_id and not st.session_state.api_key:
    st.warning("⚠️ API key required. Please enter it in the sidebar.")
    st.stop()

# --- Fetch and display data given active tab ---
if st.session_state.active_tab == 'matches' and steam_id:
    try:
        new_matches = get_match_data(steam_id, st.session_state.api_key, offset=st.session_state.offset)
        
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
                    df[col] = None  # blank define if no column data in api response

            # Identify numeric columns to provide a consistent number of decimal places.
            numeric_columns = ['Rating', 'K/D', 'ADR', 'KAST%', 'HS%']
            for col in numeric_columns:
                df[col] = df[col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else None)

            # Convert all values to strings for consistent display
            df = df.applymap(str)

            # --- Render Table ---
            event = st.dataframe(df[display_columns], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
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
                    st.rerun()

            with col2:
                if not st.session_state.end_of_data and col2.button("Next Page"):
                    st.session_state.offset += 20
                    st.session_state.matches = []
                    st.rerun()

            # --- Chart ---
            avg_rating_chart = create_avg_rating_chart(df)
            st.altair_chart(avg_rating_chart, use_container_width=True)
        else:
            st.info("ℹ️ No match data loaded yet.")
    
    except Exception as e:
        st.error("⚠️ An unexpected error occurred while loading match data.")

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
            'kd': 'K/D',
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
            st.altair_chart(charts['kills'], use_container_width=True)

        with col2:
            st.altair_chart(charts['assists'], use_container_width=True)

        with col3:
            st.altair_chart(charts['deaths'], use_container_width=True)

        col4, col5, col6 = st.columns(3)

        with col4:
            st.altair_chart(charts['kd'], use_container_width=True)

        with col5:
            st.altair_chart(charts['kdr'], use_container_width=True)

        with col6:
            st.altair_chart(charts['kpr'], use_container_width=True)

        col7, col8, col9 = st.columns(3)

        with col7:
            st.altair_chart(charts['adr'], use_container_width=True)

        with col8:
            st.altair_chart(charts['kast'], use_container_width=True)

        with col9:
            st.altair_chart(charts['multi_kills'], use_container_width=True)

        col10, col11, col12 = st.columns(3)

        with col10:
            st.altair_chart(charts['rating'], use_container_width=True)

        with col11:
            st.altair_chart(charts['t_rating'], use_container_width=True)

        with col12:
            st.altair_chart(charts['ct_rating'], use_container_width=True)

    else:
        st.error("❌ Failed to load player stats.")
