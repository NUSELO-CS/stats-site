import streamlit as st
from api import ukic_match_get, ukic_match_update
from tools.perms import has_access
import re
from datetime import datetime
from zoneinfo import ZoneInfo

if not has_access(["platform_admin", "ukic_admin"]):
    st.session_state.redirected = False
    st.switch_page("pages/User.py")

st.header("UKIC Roster Manage")

user_input = st.text_input("Enter Match ID or Faceit URL:")

# Reset session state for new match 
if user_input and "last_input" in st.session_state and st.session_state.last_input != user_input:
    for key in list(st.session_state.keys()):
        if key.startswith(("faction1_", "faction2_", "spectator_", "subs_", "coach_")):
            del st.session_state[key]
    st.session_state.editing_team = None
st.session_state.last_input = user_input

# Extract Match ID
def extract_match_id(text: str) -> str | None:
    match_url_pattern = r"https://www\.faceit\.com/.+/cs2/room/([a-zA-Z0-9\-]+)"
    match = re.search(match_url_pattern, text)
    return match.group(1) if match else text

match_id = extract_match_id(user_input) if user_input else None

#Player dict builder
def build_player_item(nickname, existing_players):
    existing = next((p for p in existing_players if p["nickname"] == nickname), None)
    return {"nickname": nickname, "id": existing["id"] if existing else None}


def render_team_editor(team, max_subs):
    st.subheader(f"Edit {team['name']}")
    st.checkbox(
        "Debug Mode",
        value=st.session_state.match_debug_mode,
        key="match_debug_mode"
    )

    #Players
    roster = team.get("roster", [])
    roster_nicks = [p["nickname"] for p in roster] + [""] * (5 - len(roster))

    st.markdown("**Players (first is Leader)**")
    new_roster = [
        st.text_input(f"Player {i+1}", value=roster_nicks[i], key=f"roster_{team['team_id']}_{i}")
        for i in range(5)
    ]

    #Subs
    if f"subs_{team['team_id']}" not in st.session_state:
        st.session_state[f"subs_{team['team_id']}"] = [s["nickname"] for s in team.get("substitutes", [])]

    st.markdown("**Substitutes**")
    subs = st.session_state[f"subs_{team['team_id']}"]

    for i, sub in enumerate(subs):
        subs[i] = st.text_input(f"Sub {i+1}", value=sub, key=f"sub_{team['team_id']}_{i}")

    col_add, col_remove = st.columns(2)
    with col_add:
        if st.button("➕ Add Substitute", key=f"add_sub_{team['team_id']}"):
            subs.append("")
            st.rerun()
    with col_remove:
        if subs and st.button("➖ Remove Substitute", key=f"remove_sub_{team['team_id']}"):
            subs.pop()
            st.rerun()

    # Coach
    if f"coach_{team['team_id']}" not in st.session_state:
        st.session_state[f"coach_{team['team_id']}"] = [c["nickname"] for c in team.get("coaches", [])]

    st.markdown("**Coach**")
    coach_list = st.session_state[f"coach_{team['team_id']}"]

    if coach_list:
        coach_list[0] = st.text_input("Coach", value=coach_list[0], key=f"coach_{team['team_id']}_0")
        if st.button("➖ Remove Coach", key=f"remove_coach_{team['team_id']}"):
            st.session_state[f"coach_{team['team_id']}"] = []
            st.rerun()
    else:
        if st.button("➕ Add Coach", key=f"add_coach_{team['team_id']}"):
            st.session_state[f"coach_{team['team_id']}"] = [""]
            st.rerun()

    #save
    with st.form(f"form_{team['team_id']}"):
        submitted = st.form_submit_button("💾 Save Changes", width='stretch')
        if submitted:
            existing_players = team.get("roster", []) + team.get("substitutes", []) + team.get("coaches", [])

            payload = {
                "match_id": match_id,
                "avatar": team["avatar"],
                "faction": team["faction"],
                "coaches": [build_player_item(n, existing_players) for n in coach_list if n],
                "id": team["team_id"],
                "leader": build_player_item(new_roster[0], existing_players),
                "name": team["name"],
                "roster": [build_player_item(n, existing_players) for n in new_roster if n],
                "substituted": team["substituted"],
                "substitutes": [build_player_item(n, existing_players) for n in subs if n],
                "type": team["type"],
            }

            try:
                result = ukic_match_update(team["team_id"], payload, st.session_state.api_key)
                st.success("✅ Saved to API!")
                st.json(result)
                st.session_state.editing_team = None
                for key in list(st.session_state.keys()):
                    if key.startswith(("faction1_", "faction2_", "spectator_", "subs_", "coach_")):
                        del st.session_state[key]
                    st.session_state.editing_team = None
                if not st.session_state.match_debug_mode:
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Failed to save: {e}")

# display
if match_id:
    match_data = ukic_match_get(match_id, st.session_state.api_key)

    if not match_data:
        st.warning("No match data found.")
    else:
        # Match Info,d efault Lopndon time
        iso_schedule = match_data["schedule"]
        dt_utc = datetime.fromisoformat(iso_schedule.replace("Z", "+00:00"))
        london_time = dt_utc.astimezone(ZoneInfo("Europe/London"))
        formatted_time = london_time.strftime("%a, %b %d, %Y %H:%M")

        with st.container():
            _, mid, _ = st.columns([1, 2, 1])
            with mid:
                st.subheader(match_data["comp_name"])
                st.write(f"State: {match_data['state']}")
                st.write(formatted_time)

        teams = match_data.get("teams", [])
        if len(teams) == 2:
            team1, team2 = teams
            col_left, col_right = st.columns(2)

            max_subs = max(len(team1.get("substitutes", [])), len(team2.get("substitutes", [])))

            for col, team in zip([col_left, col_right], [team1, team2]):
                with col:
                    st.markdown(f"### {team['name']}")

                    info_col1, info_col2 = st.columns([1, 2])
                    with info_col1:
                        st.image(team["avatar"], width=100)
                    with info_col2:
                        st.write(f"Leader: {team['leader']}")
                        st.write(f"Type: {team['type']}")
                        st.write(f"Substituted: {team['substituted']}")

                    #Roster
                    st.markdown("**Roster:**")
                    for player in team.get("roster", []):
                        with st.container(border=True):
                            st.write(player["nickname"])

                    #Subs
                    st.markdown("**Substitutes:**")
                    for sub in team.get("substitutes", []):
                        with st.container(border=True):
                            st.write(sub["nickname"])
                    for _ in range(max_subs - len(team.get("substitutes", []))):
                        with st.container(border=True):
                            st.write("\u200B")

                    #Coach
                    st.markdown("**Coaches:**")
                    if team.get("coaches"):
                        for coach in team["coaches"]:
                            with st.container(border=True):
                                st.write(coach["nickname"])
                    else:
                        with st.container(border=True):
                            st.write("\u200B")

                    # Edit
                    if st.button(f"Edit {team['name']}", key=f"edit_{team['team_id']}"):
                        st.session_state.editing_team = team["team_id"]
                        st.rerun()  


                    if st.session_state.get("editing_team") == team["team_id"]:
                        render_team_editor(team, max_subs)

            st.divider()
            st.subheader("Spectators")
            for spectator in match_data.get("spectators", []):
                with st.container(border=True):
                    st.write(spectator["nickname"])
