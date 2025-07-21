import streamlit as st
import pandas as pd
from api import get_event_details, get_event_stats, get_event_matches
import altair as alt

current_page = "Event"

## this is duplicated. sort when more time

BOX_FIELDS = {
    "Matches": ("matches", "{}", 0, None), 
    "Kills": ("kills", "{}", 0, None), 
    "Deaths": ("deaths", "{}", 0, None), 
    "Assists": ("assists", "{}", 0, None), 
    "Rating": ("rating", "{:.2f}", 0.0, None),
    "CT Rating": ("ct_rating", "{:.2f}", 0.0, None),
    "T Rating": ("t_rating", "{:.2f}", 0.0, None),
    "KAST%": ("kast", "{:.2f}", 0.0, None),
    "K-D": ("kd", "{}", 0, None), 
    "KDR": ("kdr", "{:.2f}", 0.0, None),
    "HS%": ("hs", "{:.1f}%", 0.0, "kills"),
}

EXTENDED_KILL_FIELDS = {
    "Kills": ("kills", "{}", 0, None), 
    "Close Kills %": ("close_duels", "{:.1f}%", 0.0, "kills"),
    "Flawless Kills %": ("flawless_kills", "{:.1f}%", 0.0, "kills"),
    "Kills against worse econ %": ("kills_better_econ", "{:.1f}%", 0.0, "kills"),
    "Kills against ecos %": ("kills_against_ecos", "{:.1f}%", 0.0, "kills"),
    "Trade Kills %": ("kills_traded", "{:.1f}%", 0.0, "kills"),
    "Kills that are traded %": ("kills_that_are_trades", "{:.1f}%", 0.0, "kills"),
    "Kills assisted by flash": ("kills_assisted_by_flash", "{}", 0, None),  #
    "AWP Kills": ("awp_kills", "{}", 0, None), 
    "Pistol Round Kills": ("pistol_round_kills", "{}", 0, None), 
}

CONTRIBUTION_FIELDS = {
    "Rating": ("rating", "{:.2f}", 0.0, None),
    "CT Rating": ("ct_rating", "{:.2f}", 0.0, None),
    "T Rating": ("t_rating", "{:.2f}", 0.0, None),
    "KAST%": ("kast", "{:.2f}", 0.0, None),
    "KAST leading to win": ("kast_leading_to_win", "{:.1f}", 0.0, None),
    "KAST in team wins": ("kast_in_team_win", "{:.1f}", 0.0, None),
    "CT KAST leading to win": ("ct_kast_leading_to_win", "{:.1f}", 0.0, None),
    "CT KAST in team wins": ("ct_kast_in_team_win", "{:.1f}", 0.0, None),
    "T KAST leading to win": ("t_kast_leading_to_win", "{:.1f}", 0.0, None),
    "T KAST in team wins": ("t_kast_in_team_win", "{:.1f}", 0.0, None),
}

EXTENDED_DEATH_FIELDS = {
    "Deaths": ("deaths", "{}", 0, None), 
    "Close Deaths %": ("close_duels", "{:.1f}%", 0.0, "deaths"),
    "Flawless Deaths %": ("flawless_deaths", "{:.1f}%", 0.0, "deaths"),
    "Deaths against worse econ %": ("deaths_better_econ", "{:.1f}%", 0.0, "deaths"),
    "Deaths against ecos %": ("deaths_against_ecos", "{:.1f}%", 0.0, "deaths"),
    "Deaths that are traded %": ("deaths_traded", "{:.1f}%", 0.0, "kideathslls"),
    "Deaths assisted by flash": ("deaths_assisted_by_flash", "{}", 0, None),  #
    "Deaths to AWP": ("awp_deaths", "{}", 0, None), 
    "Pistol Round Deaths": ("pistol_round_deaths", "{}", 0, None), 
}

EXTENDED_DUEL_FIELDS = {
    "First Kills": ("first_kills", "{}", 0, None), 
    "FK lead to win%": ("fk_wr", "{:.1f}%", 0.0, "first_kills"), 
    "T First Kills": ("t_fk", "{}", 0.0, None), 
    "T FK win%": ("t_fk_wr", "{:.1f}%", 0.0, "t_fk"), 
    "CT First Kills": ("ct_fk", "{}", 0.0, None), 
    "CT FK win%": ("ct_fk_wr", "{:.1f}%", 0.0, "ct_fk"), 
    "First Deaths": ("first_deaths", "{}", 0.0, None), 
    "FD lead to loss%": ("fd_lr", "{:.1f}%", 0.0, "first_deaths"), 
    "T First Deaths": ("t_fd", "{}", 0.0, None), 
    "T FD loss%": ("t_fd_lr", "{:.1f}%", 0.0, "t_fd"), 
    "CT First Deaths": ("ct_fd", "{}", 0.0, None), 
    "CT FK loss%": ("ct_fd_lr", "{:.1f}%", 0.0, "ct_fd"), 
}

UTILITY_FIELDS = {
    "Util thrown": ("total_util", "{}", 0, None), 
    "HE's thrown": ("hegrenade", "{}", 0, None), 
    "Flashbangs thrown": ("flashbang", "{}", 0, None), 
    "Smokes thrown": ("smokegrenade", "{}", 0, None), 
    "Molotovs thrown": ("molotov", "{}", 0, None), 
    "Incendinarys thrown": ("incgrenade", "{}", 0, None), 
    "Utility Damage": ("ud", "{}", 0, None), 
    "Fire grenade damage": ("fire_damage", "{}", 0, None), 
    "HE Damage": ("he_damage", "{}", 0, None), 
}

TAB_CONFIGS = {
    "box_stats": {"fields": BOX_FIELDS, "sort": "Rating", "label": "Box"},
    "contribution": {"fields": CONTRIBUTION_FIELDS, "sort": "Rating", "label": "Contribution"},
    "extended-kills": {"fields": EXTENDED_KILL_FIELDS, "sort": "Kills", "label": "Extended Kills"},
    "extended-deaths": {"fields": EXTENDED_DEATH_FIELDS, "sort": "Deaths", "label": "Extended Deaths"},
    "extended-duels": {"fields": EXTENDED_DUEL_FIELDS, "sort": "First Kills", "label": "Extended Duels"},
    "utility": {"fields": UTILITY_FIELDS, "sort": "Util thrown", "label": "Utility"},
    "comparison": {"label": "Comparison"},
}

def make_table_from_fields(stats_data, fields_dict):
    if not stats_data:
        return pd.DataFrame()

    rows = []
    for player in stats_data:
        row = {}
        row["name"] = player.get("name", "")
        row["team_name"] = player.get("team_name", "")
        for col_name, (key, fmt, default, base_key) in fields_dict.items():
            val = player.get(key, default)
            row[col_name] = val
        # Add steam_id for tracking selection, always hide the val
        row["steam_id"] = player.get("steam_id", None)
        rows.append(row)

    df = pd.DataFrame(rows)
    return df

if not st.user.is_logged_in:
    st.session_state.redirected = True
    st.switch_page("pages/User.py")

comp_id_param = st.query_params.get("comp_id")
if comp_id_param:
    st.session_state.selected_comp_id = comp_id_param

if st.session_state.get("last_page") != current_page:
    st.session_state.active_tab = "summary"
    st.session_state.last_page = current_page
    st.session_state.comp_data = None
    st.query_params.clear()
    st.rerun()

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
    
def get_or_set_comp_stats():
    if st.session_state.selected_comp_id:
        if st.session_state.get("comp_stats"):
            return st.session_state.comp_stats
        else:
            comp_stats = get_event_stats(st.session_state.selected_comp_id, st.session_state.api_key)
            if comp_stats:
                st.session_state.comp_stats = comp_stats
                return comp_stats
            else:
                return None
    else:
        return None

comp_data = get_or_set_comp_data()

comp_stats = get_or_set_comp_stats()

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
    st.query_params.clear()  
    st.rerun()

if comp_id and comp_id != st.session_state.selected_comp_id:
    update_comp_id()

if comp_id and st.session_state.api_key:
    col1, col2, col3 = st.columns(3)
    if col1.button("Summary", use_container_width=True):
        st.session_state.active_tab = 'summary'
    if col2.button("Players", use_container_width=True):
        st.session_state.active_tab = 'players'
    if col3.button("Matches", use_container_width=True):
        st.session_state.active_tab = 'matches'

if comp_id and not st.session_state.api_key:
    st.warning("⚠️ API key required. Please enter it in the sidebar.")
    st.stop()
        
if st.session_state.active_tab == 'summary' and comp_id:
    try:
        comp_data = get_or_set_comp_data()
        st.query_params.comp_id = comp_id

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
        comp_stats = get_or_set_comp_stats()

        if comp_stats:
            # Select category
            category_label = st.selectbox(
                "📂 Select category",
                [config["label"] for config in TAB_CONFIGS.values() if "fields" in config]
            )
            reverse_tab_configs = {v["label"]: k for k, v in TAB_CONFIGS.items()}
            selected_key = reverse_tab_configs[category_label]
            selected_config = TAB_CONFIGS[selected_key]
            fields = selected_config["fields"]

            df = make_table_from_fields(comp_stats, fields)

            df = df.rename(columns={"name": "Player", "team_name": "Team"})

            teams = sorted({p.get("team_name") for p in comp_stats if p.get("team_name")})
            teams.insert(0, "All Teams")

            selected_team = st.selectbox("Filter by Team", teams)

            # Filter based on selected team ---- potentially add multiple teams at once in future?
            if selected_team != "All Teams":
                filtered_df = df[df['Team'] == selected_team].reset_index(drop=True)
                height_val = None 
            else:
                filtered_df = df
                height_val = 600  

            # Sort by defined column
            sort_col = selected_config.get("sort")
            if sort_col and sort_col in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by=sort_col, ascending=False).reset_index(drop=True)

            # Prepare display columns, forcing Player and Team as columns on allt ables
            other_cols = [col for col in filtered_df.columns if col not in ("Player", "Team", "steam_id")]
            display_cols = ["Player", "Team"] + other_cols

            st.subheader(category_label + " Stats")

            table_event = st.dataframe(
                filtered_df[display_cols],
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                height=height_val
            )

            # Handle row selection for nav
            if table_event.selection and table_event.selection.rows:
                selected_row_index = table_event.selection.rows[0]
                steam_id = filtered_df.loc[selected_row_index, "steam_id"]
                if steam_id:
                    st.session_state.current_steam_id = steam_id
                    st.switch_page("pages/Player.py")

    except Exception as e:
        st.error(f"Failed to load player stats: {e}")

if st.session_state.active_tab == 'matches' and comp_id:
    try:
        new_matches = get_event_matches(comp_id, st.session_state.api_key, offset=st.session_state.offset)
        
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
            # Flatten the vals
            flat_matches = []
            for m in matches:
                flat_matches.append({
                    "Match ID": m.get("checksum"),
                    "Date": pd.to_datetime(m.get("match_time")).date() if m.get("match_time") else None,
                    "Map": m.get("map_name"),
                    "Team A": m.get("team_a", {}).get("name"),
                    "Team A Score": m.get("team_a", {}).get("score"),
                    "Team B": m.get("team_b", {}).get("name"),
                    "Team B Score": m.get("team_b", {}).get("score"),
                })

            df = pd.DataFrame(flat_matches)

            st.subheader("Matches")
            event = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                height=600
            )

            # Select a match row
            if event.selection and event.selection.rows:
                selected_row_index = event.selection.rows[0]
                val = df.loc[selected_row_index, "Match ID"]
                st.session_state.selected_match_id = val
                st.switch_page("pages/Matches.py")

            # Pagination controls
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

        else:
            st.info("ℹ️ No comp data loaded yet.")

    except Exception as e:
        st.error(f"Failed to load match data: {e}")
    
    except Exception as e:
        st.error("⚠️ An unexpected error occurred while loading comp data.")    