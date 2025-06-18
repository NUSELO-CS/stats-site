import streamlit as st
from api import generate_steam_url, build_logout_url, get_match_data, get_player_info
import pandas as pd

current_page = "Profile"


def grab_uplayer_info():
    if st.session_state.api_key and st.session_state.user_steam_id:
        player_response = get_player_info(st.session_state.user_steam_id, st.session_state.api_key)
        player_comp_data = player_response.get("comps", []) if player_response else []
        st.session_state.player_comp_data = player_comp_data

if st.session_state.get("last_page") != current_page:
    st.session_state.active_tab = "matches"
    st.session_state.last_page = current_page  
    st.session_state.matches = []
    st.session_state.offset = 0
    st.session_state.player_name = ""
    st.session_state.end_of_data = False
    if st.session_state.user_steam_id:
        grab_uplayer_info()
    
    st.rerun()

if st.session_state.redirected == True:
    st.session_state.redirected = ""
    st.toast("You must be logged in to view that page.", icon="🚫")

with st.container(border=True):
    col1, col2, col3 = st.columns([0.05, 0.90, 0.05], vertical_alignment="center")

    if st.user.is_logged_in:
        logout_url = build_logout_url()
        with col1: 
            picture = st.user.get("picture")
            if picture:
                st.image(picture, width=48)

        with col2:
            namesect, steambutton = st.columns([0.4,0.6],vertical_alignment="center")
            with namesect:
                name = st.user.get("name", "User")
                st.markdown(f"**{name}**")
            with steambutton:
                if st.session_state["user_steam_id"] is None:
                    # Extract Discord user ID 
                    discord_sub = st.user.get("sub", "")
                    user_id = discord_sub.split("|")[-1] if "discord" in discord_sub else None

                    # Show either the generate button or login link depending on state
                    if 'steam_login_url' not in st.session_state:
                        if st.button("Connect your steam account",type="secondary"):
                            if user_id:
                                steam_url = generate_steam_url(user_id)
                                if steam_url:
                                    st.session_state['steam_login_url'] = steam_url
                                    st.rerun()
                                else:
                                    st.error("Failed to generate Steam login URL")
                            else:
                                st.error("Invalid Discord user ID")
                    else:
                        steam_link = st.session_state['steam_login_url']
                        del st.session_state['steam_login_url']
                        st.toast("You will need to close the old page after connecting")
                        st.link_button("Click here to connect",steam_link,type="primary")
                else:
                    st.write(st.session_state["user_steam_id"])
        with col3:
            if st.button("Log out"):
                st.logout()
    else:
        with col2:
            if st.button("Log in", use_container_width=True):
                st.login("provider") 

if st.user.is_logged_in and st.session_state.user_steam_id:
    try:
        new_matches = get_match_data(st.session_state.user_steam_id, st.session_state.api_key, offset=st.session_state.offset)
        grab_uplayer_info()
        
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

                comp_clicker = st.dataframe(comp_df[comp_columns], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

                if comp_clicker.selection and comp_clicker.selection.rows:
                    comp_row_index = comp_clicker.selection.rows[0]
                    comp_val = comp_df.loc[comp_row_index, "Comp ID"]
                    st.session_state.selected_comp_id = comp_val
                    st.switch_page("pages/Events.py")

        else:
            st.info("ℹ️ No comp data loaded yet.")
    except Exception as e:
        st.error("⚠️ An unexpected error occurred while loading comp data.")
