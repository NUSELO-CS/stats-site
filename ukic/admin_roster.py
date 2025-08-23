import streamlit as st
import time
from api import ukic_roster_list, ukic_roster_get, submit_ukic_roster
from tools.perms import has_access

if not has_access(["platform_admin", "ukic_admin"]):
    st.session_state.redirected = False
    st.switch_page("pages/User.py") 

st.header("UKIC Roster Manage")

# Fetch roster data
roster_data = ukic_roster_list(st.session_state.api_key)

# Advanced mode tottle
advanced_mode = st.checkbox("Advanced mode (manual team input)")

# Tracking
if "prev_selected_team" not in st.session_state:
    st.session_state.prev_selected_team = None
if "last_team_load" not in st.session_state:
    st.session_state.last_team_load = 0
if "loaded_roster" not in st.session_state:
    st.session_state.loaded_roster = None


selected_team_id = None
if advanced_mode:
    team_input = st.text_input("Enter team_id or team_url:")
    if team_input:
        selected_team_id = team_input.rstrip("/").split("/")[-1] if "http" in team_input else team_input
else:
    divisions = list(roster_data.keys())
    selected_division = st.selectbox("Select Division", divisions)
    teams = roster_data.get(selected_division, [])
    teams_sorted = sorted(teams, key=lambda x: x["team_name"])
    team_names = [team["team_name"] for team in teams_sorted]
    selected_team_name = st.selectbox("Select Team", team_names)
    selected_team = next((t for t in teams_sorted if t["team_name"] == selected_team_name), None)
    selected_team_id = selected_team["team_id"] if selected_team else None

# Clear details if new team
if st.session_state.prev_selected_team != selected_team_id:
    st.session_state.loaded_roster = None
    st.session_state.prev_selected_team = selected_team_id

    # Wipe fields
    for key in list(st.session_state.keys()):
        if key.startswith(("player", "sub", "coach", "captain")):
            del st.session_state[key]

# ensure that the API limit isnt hit, protectionary
if selected_team_id:
    if st.button("Load Team Roster"):
        now = time.time()
        if now - st.session_state.last_team_load < 5:
            st.warning("Please wait 5 seconds between team loads.")
        else:
            st.session_state.loaded_roster = ukic_roster_get(selected_team_id, st.session_state.api_key)
            st.session_state.last_team_load = now

# Loaded roster
if st.session_state.loaded_roster:
    roster_info = st.session_state.loaded_roster
    roster = roster_info.get("roster", [])
    members = roster_info.get("members", [])

    roster_map = {p["player_id"]: p for p in roster}

    # Merge eligible users with team page
    merged_members = []
    for m in members:
        player_id = m["player_id"]
        merged_members.append({
            "player_id": player_id,
            "player_name": m["player_name"],
            "player_role": roster_map.get(player_id, {}).get("player_role", None),
            "is_core": roster_map.get(player_id, {}).get("is_core", False),
            "is_uk": roster_map.get(player_id, {}).get("is_uk", False),
            "matches": roster_map.get(player_id, {}).get("matches", "0"),
        })

    members_sorted = sorted(merged_members, key=lambda x: x["player_name"])
    member_names = [m["player_name"] for m in members_sorted]

    st.subheader("Edit Roster")

    def get_default_player(role, idx=0):
        matches = [p for p in roster if p["player_role"].lower() == role.lower()]
        if idx < len(matches):
            return matches[idx]["player_name"]
        return ""

    def get_member_obj(player_name):
        return next((m for m in members_sorted if m["player_name"] == player_name), {})

    # Required role 1
    captain_default = get_default_player("Captain")
    col1, col2, col3 = st.columns([8, 1, 1], vertical_alignment="bottom")
    with col1:
        captain_name = st.selectbox(
            "Captain (required)",
            options=member_names,
            index=member_names.index(captain_default) if captain_default in member_names else 0,
            key="captain_select"
        )
    captain_obj = get_member_obj(captain_name)
    with col2:
        captain_is_core = st.checkbox("Core", value=captain_obj.get("is_core", False), key="captain_core")
    with col3:
        captain_is_uk = st.checkbox("UK?", value=captain_obj.get("is_uk", False), key="captain_uk")

    # Required role 2-5
    player_objs = []
    for i in range(4):
        default_val = get_default_player("Player", i)
        idx_default = member_names.index(default_val) if default_val in member_names else 0
        col1, col2, col3 = st.columns([8, 1, 1], vertical_alignment="bottom")
        with col1:
            player_name = st.selectbox(
                f"Player {i+1} (required)",
                options=member_names,
                index=idx_default,
                key=f"player_select_{i}"
            )
        player_obj = get_member_obj(player_name)
        player_objs.append(player_obj)
        with col2:
            st.checkbox("Core", value=player_obj.get("is_core", False), key=f"player{i}_core")
        with col3:
            st.checkbox("UK?", value=player_obj.get("is_uk", False), key=f"player{i}_uk")

    # subs and coaches
    optional_member_names = [""] + member_names
    sub_objs = []
    for i in range(3):
        default_val = get_default_player("Sub", i)
        idx_default = optional_member_names.index(default_val) if default_val in optional_member_names else 0
        col1, col2, col3 = st.columns([8, 1, 1], vertical_alignment="bottom")
        with col1:
            sub_name = st.selectbox(
                f"Sub {i+1} (optional)",
                options=optional_member_names,
                index=idx_default,
                key=f"sub_select_{i}"
            )
        sub_obj = get_member_obj(sub_name) if sub_name else {}
        sub_objs.append(sub_obj)
        with col2:
            st.checkbox("Core", value=sub_obj.get("is_core", False), key=f"sub{i}_core")
        with col3:
            st.checkbox("UK?", value=sub_obj.get("is_uk", False), key=f"sub{i}_uk")

    coach_default = get_default_player("Coach")
    idx_default = optional_member_names.index(coach_default) if coach_default in optional_member_names else 0
    col1, col2, col3 = st.columns([8, 1, 1], vertical_alignment="bottom")
    with col1:
        coach_name = st.selectbox(
            "Coach (optional)",
            options=optional_member_names,
            index=idx_default,
            key="coach_select"
        )
    coach_obj = get_member_obj(coach_name) if coach_name else {}
    with col2:
        st.checkbox("Core", value=coach_obj.get("is_core", False), key="coach_core")
    with col3:
        st.checkbox("UK?", value=coach_obj.get("is_uk", False), key="coach_uk")

    if st.button("Submit to Backend"):
        def build_role_list(objs, role_prefix):
            lst = []
            for i, obj in enumerate(objs):
                if obj.get("player_id"):
                    lst.append({
                        "player_id": obj["player_id"],
                        "player_name": obj["player_name"],
                        "is_core": st.session_state.get(f"{role_prefix}{i}_core", obj.get("is_core", False)),
                        "is_uk": st.session_state.get(f"{role_prefix}{i}_uk", obj.get("is_uk", False))
                    })
            return lst

        captains_to_send = build_role_list([captain_obj], "captain_")
        players_to_send = build_role_list(player_objs, "player")
        subs_to_send = build_role_list(sub_objs, "sub")
        coach_to_send = build_role_list([coach_obj], "coach_")

        team_members = [m["player_id"] for m in members_sorted]

        result = submit_ukic_roster(
            api_key=st.session_state.api_key,
            roster_id=selected_team_id,
            captains=captains_to_send,
            players=players_to_send,
            subs=subs_to_send,
            coach=coach_to_send,
            team_members=team_members
        )

        if result["success"]:
            st.success("Roster submitted successfully!")
            st.json(result["data"])
        else:
            st.error(f"Failed to submit roster: {result.get('status_code')}")
            st.text(result.get("message"))

