import streamlit as st
import pandas as pd
import altair as alt
from api import get_match_info

current_page = "Matches"

if not st.user.is_logged_in:
    st.session_state.redirected = True
    st.switch_page("pages/User.py")

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
    "Util thrown": ("total", "{}", 0, None), 
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
    "box-stats": {"label": "Box Stats"},
    "contribution": {"fields": CONTRIBUTION_FIELDS, "sort": "Rating", "label": "Contribution"},
    "extended-kills": {"fields": EXTENDED_KILL_FIELDS, "sort": "Kills", "label": "Extended Kills"},
    "extended-deaths": {"fields": EXTENDED_DEATH_FIELDS, "sort": "Deaths", "label": "Extended Deaths"},
    "extended-duels": {"fields": EXTENDED_DUEL_FIELDS, "sort": "First Kills", "label": "Extended Duels"},
    "utility": {"fields": UTILITY_FIELDS, "sort": "Util thrown", "label": "Utility"},
    "comparison": {"label": "Comparison"},
}

status_styles = {
    "pick": (":green[Picked]", "Picked"),
    "drop": (":red[Dropped]", "Dropped"),
    "left": (":orange[Left Over]", "Left Over")
}

st.title("Match Data")

# Set default tab
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "box-stats"

match_id_param = st.query_params.get("match_id")
if match_id_param:
    st.session_state.selected_match_id = match_id_param

# Track last loaded page
if st.session_state.get("last_page") != current_page:
    st.session_state.active_tab = "box-stats"  # reset on page load
    st.session_state.last_page = current_page  # update tracker
    st.session_state.match_data = None
    st.query_params.clear()



# --- INPUT ---
# Text input for Steam ID
match_id = st.text_input("🔍 Enter a NUSELO Match ID:", value=st.session_state.selected_match_id)

# Function to update steam_id and reset session state
def update_match_id():
    if match_id != st.session_state.selected_match_id:
        st.session_state.selected_match_id = match_id
        st.session_state.match_data = None  
        st.query_params.clear()
        st.rerun()

def display_team_table(team_name, team_score, df):
    st.subheader(f"{team_name} - {team_score}")
    st.dataframe(df, use_container_width=True, hide_index=True)

def build_team_df(team_data, fields, sort_by=None, ascending=False):
    try:
        players_data = []
        for player in team_data["players"]:
            stats = player["stats"]
            row = {"Player": player["name"]}
            raw_values = {}

            for label, (key, fmt, default, relative_to) in fields.items():
                value = stats.get(key, default)
                if relative_to:
                    relative_value = stats.get(relative_to, 1)
                    value = (value / relative_value * 100) if relative_value > 0 else 0.0

                raw_values[label] = value
                row[label] = fmt.format(value)

            players_data.append((row, raw_values))

        df = pd.DataFrame([row for row, _ in players_data])

        if sort_by:
            raw_df = pd.DataFrame([raw for _, raw in players_data])
            df['raw_sort_value'] = raw_df[sort_by]
            df = df.sort_values(by='raw_sort_value', ascending=ascending).drop('raw_sort_value', axis=1)

        return df

    except Exception:
        st.error("⚠️ Error while building player stats table.")
        return pd.DataFrame()  # Return empty DF to fail gracefully


def handle_extra_table(match_data, fields, sort_by):
    try:
        score_list = match_data["score"]
        final_score = next((item for item in score_list if item.get("finish")), None)

        if final_score:
            team_a_name = final_score["team_a_name"]
            team_b_name = final_score["team_b_name"]
            team_a_score = final_score["team_a_score"]
            team_b_score = final_score["team_b_score"]
        else:
            team_a_name = team_b_name = ""
            team_a_score = team_b_score = 0

        df_a = build_team_df(match_data["teams"]["team_a"], fields, sort_by=sort_by, ascending=False)
        df_b = build_team_df(match_data["teams"]["team_b"], fields, sort_by=sort_by, ascending=False)

        display_team_table(team_a_name, team_a_score, df_a)
        display_team_table(team_b_name, team_b_score, df_b)

    except Exception:
        st.error("⚠️ Unable to generate team comparison tables.")



def extract_score_data(score_info, team_type):
    try:
        score_string = ""
        overtime_counts = {}

        if team_type == 'a':
            team_name_key = "team_a_name"
            team_score_key = "team_a_score"
            team_side_key = "team_a_side"
        elif team_type == 'b':
            team_name_key = "team_b_name"
            team_score_key = "team_b_score"
            team_side_key = "team_b_side"
        else:
            st.error("⚠️ Invalid team type provided.")
            return ""

        filtered_scores = [item for item in score_info if item[team_name_key] is not None]

        previous_score = 0

        for item in filtered_scores:
            team_score = item[team_score_key]
            team_side = item[team_side_key]
            separator = ""

            overtime_round = item["overtime_number"]
            overtime_key = f"OT{overtime_round}"
            overtime_counts.setdefault(overtime_key, 0)

            round_won = team_score - previous_score
            if overtime_round == 0:
                if overtime_counts[overtime_key] == 0:
                    score_string += f"Regulation: "
                else:
                    separator = " - "
            else:
                if overtime_counts[overtime_key] == 0:
                    score_string += f"\n\nOT{overtime_round}: "
                else:
                    separator = " - "

            formatted_score = f":red[{round_won}]" if team_side == 't' else f":blue[{round_won}]"
            score_string += f"{separator}{formatted_score}"

            overtime_counts[overtime_key] += 1
            previous_score = team_score

        return score_string.rstrip(" ")

    except Exception:
        st.error("⚠️ Failed to extract score breakdown.")
        return ""

def get_or_set_match_data():
    if st.session_state.get("match_data"):
        return st.session_state.match_data
    else:
        match_data = get_match_info(match_id, st.session_state.api_key)
        if match_data:
            st.session_state.match_data = match_data
            return match_data
        else:
            return None

# Trigger the update_steam_id function when the Steam ID changes
if match_id and match_id != st.session_state.selected_match_id:
    update_match_id()


if match_id and st.session_state.api_key:
    cols = st.columns(len(TAB_CONFIGS))
    for i, (key, config) in enumerate(TAB_CONFIGS.items()):
        if cols[i].button(config["label"], use_container_width=True):
            st.session_state.active_tab = key

if match_id and not st.session_state.api_key:
    st.warning("⚠️ API key required. Please enter it in the sidebar.")
    st.stop()

active = st.session_state.active_tab

if active == "box-stats" and match_id:
    try:
        match_data = get_match_info(match_id, st.session_state.api_key)
        st.query_params.match_id = match_id

        if match_data:
            score_info = match_data.get("score", [])
            veto_info  = match_data.get("vetos", [])
            final_score = next((item for item in score_info if item.get("finish")), {})

            team_a_name = final_score.get("team_a_name", "")
            team_b_name = final_score.get("team_b_name", "")
            team_a_score = final_score.get("team_a_score", 0)
            team_b_score = final_score.get("team_b_score", 0)

            comp_info = match_data.get("match",[])
            comp_id = comp_info.get("competition","")
            comp_name = comp_info.get("comp_name","")

            team_a_data = match_data["teams"]["team_a"]
            team_b_data = match_data["teams"]["team_b"]

            def build_team_df(team_data):
                players_data = []
                for player in team_data.get("players", []):
                    stats = player.get("stats", {})
                    formatted_data = {
                        "Player": player.get("name", "Unknown"),
                        "Steam ID": player.get("steam_id", ""),
                        "Rating": f"{stats.get('rating', 0.0):.2f}",
                        "ADR": f"{stats.get('adr', 0.0):.1f}",
                        "KAST%": f"{stats.get('kast', 0):.1f}",
                        "Kills": str(stats.get("kills", 0)),
                        "Assists": str(stats.get("assists", 0)),
                        "Deaths": str(stats.get("deaths", 0)),
                        "K-D": f"{stats.get('kd', 0)}",
                        "KDR": f"{stats.get('kdr', 0.0):.2f}",
                        "HS%": f"{stats.get('hs', 0)}",
                    }
                    players_data.append(formatted_data)

                df_full = pd.DataFrame(players_data).sort_values(by="Rating", ascending=False).reset_index(drop=True)

                match_columns = ['Player', 'Rating', 'ADR', 'KAST%', 'Kills', 'Assists', 'Deaths', 'K-D', 'KDR', 'HS%']
                for col in match_columns:
                    if col not in df_full.columns:
                        df_full[col] = None 

                return df_full, match_columns

            df_team_a_full, df_team_a_columns = build_team_df(team_a_data)
            df_team_b_full, df_team_b_columns = build_team_df(team_b_data)

            team_a_score_md = extract_score_data(score_info, 'a')
            score1, score2 = st.columns([3,1])
            with score1:
                st.markdown(f"### {team_a_name} - {team_a_score}")
            with score2:
                with st.popover(f"{team_a_name} Scores",use_container_width=True):
                    st.markdown(team_a_score_md)

            team1 = st.dataframe(df_team_a_full[df_team_a_columns], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

            if team1.selection and team1.selection.rows:
                selected_row_index = team1.selection.rows[0]
                val = df_team_a_full.loc[selected_row_index, "Steam ID"]
                st.session_state.current_steam_id = val
                st.switch_page("pages/Player.py")

            team_b_score_md = extract_score_data(score_info, 'b')
            score3, score4 = st.columns([3,1])
            with score3:
                st.markdown(f"### {team_b_name} - {team_b_score}")
            with score4:
                with st.popover(f"{team_b_name} Scores",use_container_width=True):
                    st.markdown(team_b_score_md)

            team2 = st.dataframe(df_team_b_full[df_team_b_columns], use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

            if team2.selection and team2.selection.rows:
                selected_row_index = team2.selection.rows[0]
                val = df_team_b_full.loc[selected_row_index, "Steam ID"]
                st.session_state.current_steam_id = val
                st.switch_page("pages/Player.py")
            
            ### - Handle vetos and return


            veto_lines = []
            for item in sorted(veto_info, key=lambda x: x["round"]):
                team = team_a_name if item["team_letter"] == "a" else team_b_name
                map_name = item["map"].replace("de_", "").capitalize()
                color_label = status_styles.get(item["status"], (f":gray[{item['status'].capitalize()}]", item["status"].capitalize()))[0]
                veto_lines.append(f"{team} {color_label} {map_name}")

            veto_output = "\n\n".join(veto_lines)

            st.divider()
            extra_details1, extra_details2 = st.columns([3,1],vertical_alignment="top")
            with extra_details1:
                st.subheader("Match Vetos")
                st.markdown(veto_output)
            
            with extra_details2:
                if st.button(label=f"Return to {comp_name}",use_container_width=True):
                    st.session_state.selected_comp_id = comp_id
                    st.switch_page("pages/Events.py")
        else:
            st.info("ℹ️ No match data could be loaded")

    except Exception:
        st.error("⚠️ An error occurred while loading box stats.")

elif active == "comparison" and match_id:
    st.subheader("Player Comparison")

    match_data = get_or_set_match_data()
    if not match_data:
        st.info("ℹ️ No match data found.")
        st.stop()

    # --- Select category
    category_label = st.selectbox("📂 Select category", [config["label"] for config in TAB_CONFIGS.values() if "fields" in config])
    reverse_tab_configs = {v["label"]: k for k, v in TAB_CONFIGS.items()}
    selected_key = reverse_tab_configs[category_label]
    selected_config = TAB_CONFIGS[selected_key]
    fields = selected_config["fields"]

    # --- Select field
    selected_field_label = st.selectbox("📊 Select field", list(fields.keys()))
    selected_field_key, fmt, default, relative_to = fields[selected_field_label]

    def gather_players(team_data, team_name, color):
        players = []
        for player in team_data["players"]:
            name = player["name"]
            stats = player["stats"]
            raw_value = stats.get(selected_field_key, default)
            if relative_to:
                relative_value = stats.get(relative_to, 1)
                raw_value = (raw_value / relative_value * 100) if relative_value > 0 else 0.0

            players.append({
                "Player": name,
                "Value": raw_value,
                "Team": team_name,
                "Color": color
            })
        return players

    # Team info
    score_info = match_data.get("score", [])
    final_score = next((item for item in score_info if item.get("finish")), {})
    team_a_name = final_score.get("team_a_name", "Team A")
    team_b_name = final_score.get("team_b_name", "Team B")

    # Gather all players in match
    players_data = gather_players(match_data["teams"]["team_a"], team_a_name, "blue") + \
                   gather_players(match_data["teams"]["team_b"], team_b_name, "red")

    df_chart = pd.DataFrame(players_data)
    df_chart = df_chart.sort_values(by="Value", ascending=False)

    # Chart
    st.altair_chart(
        alt.Chart(df_chart)
        .mark_bar()
        .encode(
            x=alt.X("Value:Q", title=selected_field_label),
            y=alt.Y("Player:N", sort='-x'),
            color=alt.Color("Team:N", scale=alt.Scale(domain=[team_a_name, team_b_name], range=["#1f77b4", "#d62728"])),
            tooltip=["Player", "Team", alt.Tooltip("Value", format=".2f")]
        )
        .properties(height=500),
        use_container_width=True
    )



elif active in TAB_CONFIGS and match_id:
    config = TAB_CONFIGS[active]
    try:
        match_data = get_or_set_match_data()
        if match_data:
            handle_extra_table(match_data, config["fields"], config["sort"])
        else:
            st.info("ℹ️ No match data could be loaded")
    except Exception:
        st.error(f"⚠️ Error loading {config['label'].lower()} stats.")