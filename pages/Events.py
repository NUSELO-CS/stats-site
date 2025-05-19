import streamlit as st
import pandas as pd
from api import get_event_details
import altair as alt

current_page = "Event"

if st.session_state.get("last_page") != current_page:
    st.session_state.active_tab = "summary"
    st.session_state.last_page = current_page
    st.session_state.comp_data = None

if "active_tab" not in st.session_state:
    st.session_state.active_tab = "summary"

def get_or_set_comp_data():
    if st.session_state.selected_comp_id:
        if st.session_state.get("comp_data"):
            return st.session_state.comp_data
        else:
            comp_data = get_event_details(st.session_state.selected_comp_id, st.session_state.api_key)
            if comp_data:
                st.session_state.comp_data = comp_data
                return comp_data
            else:
                return None
    else:
        return None

comp_data = get_or_set_comp_data()

if comp_data:
    comp_name = comp_data.get("comp_details", {}).get("comp_name", "Competition")
else: comp_name = "Competition"


st.title(f"{comp_name} Stats")

# --- INPUT ---
# Text input for Comp ID
comp_id = st.text_input("🔍 Enter a NUSELO Comp ID", value=st.session_state.selected_comp_id)





# Function to update comp_id and reset session state
def update_comp_id():
    st.session_state.selected_comp_id = comp_id
    st.session_state.comp_id = ""
    st.session_state.comp_data = None  
    st.rerun()

if comp_id and comp_id != st.session_state.selected_comp_id:
    update_comp_id()

if comp_id and st.session_state.api_key:
    col1, col2 = st.columns(2)
    if col1.button("Summary", use_container_width=True):
        st.session_state.active_tab = 'summary'
    if col2.button("Players", use_container_width=True):
        st.session_state.active_tab = 'players'

if comp_id and not st.session_state.api_key:
    st.warning("⚠️ API key required. Please enter it in the sidebar.")
    st.stop()
        
if st.session_state.active_tab == 'summary' and comp_id:
    try:
        comp_data = get_or_set_comp_data()

        if comp_data:
            map_data = comp_data.get("maps",[])
            top_performances = comp_data.get("top_matches",[])
            players = comp_data.get("players",[])
            p90 = comp_data.get("comp_details", {}).get("p90_matches", 5)

            top_performance_df = pd.DataFrame(top_performances)
            player_df = pd.DataFrame(players)



            ### - Top Performance Data
            # Create 'Kills-Deaths' column
            if 'kills' in top_performance_df.columns and 'deaths' in top_performance_df.columns:
                top_performance_df['K-D'] = top_performance_df.apply(
                    lambda row: f"{int(row['kills'])}-{int(row['deaths'])}"
                    if pd.notnull(row['kills']) and pd.notnull(row['deaths']) else None,
                    axis=1
                )

            top_performance_df.rename(columns={
            'name': 'Player',
            'match_checksum': 'Match ID',
            'team': 'Team',
            'rating': 'Rating',
            'kast': 'KAST%'
            }, inplace=True)

            tp_columns = ['Match ID','Player','Team','Rating','KAST%','K-D']

            for col in tp_columns:
                if col not in top_performance_df.columns:
                    top_performance_df[col] = None 

            numeric_columns = ['Rating', 'KAST%']
            for col in numeric_columns:
                top_performance_df[col] = top_performance_df[col].apply(lambda x: f"{x:.2f}" if pd.notnull(x) else None)


            top_performance_df = top_performance_df.applymap(str)

            
            ### Player DF

            p90 = comp_data.get("comp_details", {}).get("p90_matches", 5)

            player_df.rename(columns={
                'name': 'Player',
                'steam_id': 'Steam ID',
                'maps': 'Maps',
                'team': 'Team',
                'rating': 'Rating',
                'kast': 'KAST%',
                'adr': 'ADR'
            }, inplace=True)

            # Ensure 'Maps' column is numeric
            player_df['Maps'] = pd.to_numeric(player_df['Maps'], errors='coerce')

            # Filter players with more than 5 maps
            filtered_df = player_df[player_df['Maps'] > p90]

            if 'Rating' in filtered_df.columns:
                filtered_df = filtered_df.copy()
                filtered_df['Rating'] = pd.to_numeric(filtered_df['Rating'], errors='coerce')
                top_players_df = filtered_df.sort_values(by='Rating', ascending=False).head(10)
            else:
                top_players_df = pd.DataFrame()

            pdf_columns = ['Player', 'Team', 'Maps', 'Rating', 'KAST%', 'ADR']

            for col in pdf_columns:
                if col not in top_players_df.columns:
                    top_players_df[col] = None 

            top_players_df = top_players_df.sort_values(by="Rating", ascending=False).reset_index(drop=True)
            top_players_df = top_players_df.applymap(str)


            box1, box2 = st.columns(2,border=False)

            with box1:
                st.subheader("Top Match Performances")
                tp_event = st.dataframe(top_performance_df[tp_columns], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

                if tp_event.selection and tp_event.selection.rows:
                    selected_row_index = tp_event.selection.rows[0]
                    val = top_performance_df.loc[selected_row_index, "Match ID"]
                    st.session_state.selected_match_id = val
                    st.switch_page("pages/Matches.py")

            with box2:
                st.subheader("Top Players")
                pdf_event = st.dataframe(top_players_df[pdf_columns], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

                if pdf_event.selection and pdf_event.selection.rows:
                    selected_row_index = pdf_event.selection.rows[0]
                    val = top_players_df.loc[selected_row_index, "Steam ID"]
                    st.session_state.current_steam_id = val
                    st.switch_page("pages/Player.py")

        st.divider()

        # Map win%
        # Define columns, numeric values and build percents
        map_df = pd.DataFrame(map_data)
        numeric_cols = ['matches', 'rounds', 't_wins', 'ct_wins', 'buy_rounds', 'buy_t_wins', 'buy_ct_wins']
        map_df[numeric_cols] = map_df[numeric_cols].astype(int)

        map_df['T Win %'] = (map_df['t_wins'] / map_df['rounds']) * 100
        map_df['CT Win %'] = (map_df['ct_wins'] / map_df['rounds']) * 100
        map_df['T Buy Win %'] = (map_df['buy_t_wins'] / map_df['buy_rounds']) * 100
        map_df['CT Buy Win %'] = (map_df['buy_ct_wins'] / map_df['buy_rounds']) * 100

        map_df['map'] = map_df['map'].str.replace('de_', '', regex=False).str.capitalize()

        # Melt to format
        melted_df = map_df.melt(
            id_vars='map',
            value_vars=['T Win %', 'CT Win %', 'T Buy Win %', 'CT Buy Win %'],
            var_name='Category',
            value_name='Win %'
        )

        # Create altair chart
        chart = alt.Chart(melted_df).mark_bar().encode(
            x=alt.X('Category:N', title='', axis=alt.Axis(labelAngle=-90),
                    sort=['CT Win %', 'T Win %', 'CT Buy Win %', 'T Buy Win %']),
            y=alt.Y('Win %:Q', title='Win Percentage', scale=alt.Scale(domain=[0, 100])),
            color=alt.Color('Category:N',
                            scale=alt.Scale(
                                domain=['CT Win %', 'T Win %', 'CT Buy Win %', 'T Buy Win %'],
                                range=['#6A9FD1', '#B77D7F', '#044E94', '#e6494d']
                            ),
                            sort=['CT Win %', 'T Win %', 'CT Buy Win %', 'T Buy Win %']),
            column=alt.Column('map:N', title='Map')
        ).properties(
            title='Win % Comparison per Map'
        )

        # Display chart so it fits on screen, need to check what happens on othe res
        chartbox, empty = st.columns([0.12,0.88])
        with chartbox:
            st.altair_chart(chart,use_container_width=True)



    except Exception as e:
        st.error("⚠️ An unexpected error occurred while loading competition data.")

if st.session_state.active_tab == 'players' and comp_id:
    try:
        comp_data = get_or_set_comp_data()

        if comp_data:
            players = comp_data.get("players", [])
            player_df = pd.DataFrame(players)
            
            ### Player DF
            player_df.rename(columns={
                'name': 'Player',
                'steam_id': 'Steam ID',
                'maps': 'Maps',
                'team': 'Team',
                'rating': 'Rating',
                'kast': 'KAST%',
                'adr': 'ADR'
            }, inplace=True)

            player_df['Maps'] = pd.to_numeric(player_df['Maps'], errors='coerce')

            pdf_columns = ['Player', 'Team', 'Maps', 'Rating', 'KAST%', 'ADR']

            for col in pdf_columns:
                if col not in player_df.columns:
                    player_df[col] = None 

            player_df = player_df.sort_values(by="Rating", ascending=False).reset_index(drop=True)
            player_df = player_df.applymap(str)

            # --- Team filter dropdown ---
            teams = sorted(player_df['Team'].dropna().unique())
            teams.insert(0, "All Teams")

            selected_team = st.selectbox("Filter by Team", teams)

            if selected_team != "All Teams":
                filtered_df = player_df[player_df['Team'] == selected_team].reset_index(drop=True)
                height_val = None  
            else:
                filtered_df = player_df
                height_val = 600  # show x amount of players when no team applied

            st.subheader("Players")
            pdf_event = st.dataframe(
                filtered_df[pdf_columns],
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                height=height_val
            )

            if pdf_event.selection and pdf_event.selection.rows:
                selected_row_index = pdf_event.selection.rows[0]
                val = filtered_df.loc[selected_row_index, "Steam ID"]
                st.session_state.current_steam_id = val
                st.switch_page("pages/Player.py")

    except Exception as e:
        st.error("⚠️ An unexpected error occurred while loading competition data.")

       