import streamlit as st
import requests
import html
from urllib.parse import urlparse
from datetime import datetime

def is_safe_url(url: str, allowed_domain: str) -> bool:
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in ("http", "https") and
            parsed.netloc == allowed_domain
        )
    except Exception:
        return False

def get_allowed_domain():
    parsed = urlparse(st.secrets["BASE_URL"])
    return parsed.netloc

def _api_data_get(endpoint: str, api_key: str, params: dict = None, logout_on_403: bool = True):
    url = f"{st.secrets['BASE_URL']}{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get("data")
        elif response.status_code == 403:
            if logout_on_403:
                st.logout()
                st.stop()
            else:
                st.toast("⚠️ API Error 403: Access forbidden (logout skipped)")
    except Exception as e:
        st.error(f"⚠️ Network error: {str(e)}")
    
    return None  


def _api_db_get(endpoint: str, api_key: str, params: dict = None):
    url = f"{st.secrets['DB_BASE_URL']}{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json().get("data")
        elif response.status_code == 403:
            st.logout()
            st.stop()
        else:
            try:
                error_data = response.json()
                message = error_data.get("message", "Unknown error")
                code = error_data.get("status_code", response.status_code)
            except Exception:
                message = response.text
                code = response.status_code

            st.toast(f"⚠️ API Error {code}: {message}")
    
    except requests.exceptions.RequestException as e:
        st.toast(f"⚠️ Network error: {str(e)}")
    
    return None


def get_match_data(steam_id: str, api_key: str, offset=0, limit=20):
    params = {
        "steam_id": steam_id,
        "order": "desc",
        "offset": offset,
        "limit": limit
    }
    return _api_data_get("/v2/data/players/matches", api_key, params)


def get_player_stats(steam_id: str, api_key: str):
    params = {
        "steam_id": steam_id,
        "order": "desc"
    }
    return _api_data_get("/v2/data/players/stats", api_key, params)


def get_match_info(match_id: str, api_key: str):
    return _api_data_get(f"/v2/data/matches/{match_id}", api_key)

def get_player_info(steam_id: str, api_key: str):
    params = {
        "steam_id": steam_id
    }
    return _api_data_get("/v2/data/players/info", api_key, params)

def get_event_details(event_id: str, api_key: str):
    return _api_data_get(f"/v2/data/comps/{event_id}", api_key)

def get_event_regions(region: str, api_key: str):
    return _api_data_get(f"/v2/data/comps/list?region={region}", api_key)

def get_event_stats(event_id: str, api_key: str):
    return _api_data_get(f"/v2/data/comps/stats?comp_id={event_id}", api_key)

def get_event_matches(event_id: str, api_key: str, offset=0, limit=20):
    params = {
        "comp_id": event_id,
        "order": "desc",
        "offset": offset,
        "limit": limit
    }
    return _api_data_get("/v2/data/comps/matches", api_key, params)

def get_profile(user_id: str, api_key: str):
    params = {
        "user_id": user_id
    }
    return _api_data_get(f"/auther/profile", st.secrets['SERVER_API_KEY'],params)


def ukic_roster_list(api_key: str):
    return _api_data_get(f"/v2/ukic/roster/list", api_key)

def ukic_match_get(match_id: str, api_key: str):
    params = {
        "match_id": match_id
    }
    return _api_data_get(
        f"/v2/ukic/matches/get",
        api_key,
        params=params,         
        logout_on_403=False    
    )

def ukic_roster_get(team_id: str, api_key: str):
    params = {
        "team_id": team_id
    }
    return _api_data_get(f"/v2/ukic/roster/get", api_key, params)


def ukic_match_update(team_id: str, payload: dict, api_key: str):
    """Update UKIC roster via PUT."""
    url = f"{st.secrets['BASE_URL']}/v2/ukic/matches/update"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Merge team_id into payload
    data = {"team_id": team_id, **payload}

    response = requests.put(url, json=data, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"PUT {url} failed: {response.status_code} - {response.text}")

def submit_ukic_roster(
    api_key: str,
    roster_id: str,
    captains: list,
    players: list,
    subs: list,
    coach: list,
    team_members: list,
):
    payload = {
        "rosterId": roster_id,
        "timeString": datetime.now().isoformat(sep=' ', timespec='microseconds'),
        "captains": captains,
        "players": players,
        "subs": subs,
        "coach": coach,
        "teamMembers": team_members
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    url = f"{st.secrets['BASE_URL']}/v2/ukic/roster/update"

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Will raise HTTPError for non-2xx
        return {"success": True, "data": response.json()}
    except requests.HTTPError as e:
        return {
            "success": False,
            "status_code": e.response.status_code,
            "message": e.response.text
        }
    except requests.RequestException as e:
        return {
            "success": False,
            "status_code": None,
            "message": str(e)
        }











def get_ukcs_details(steam_id: str, api_key: str):
    return _api_db_get(f"/player/details?steam_id={steam_id}", api_key)

def get_ukcs_players(letter: str, api_key: str):
    return _api_db_get(f"/player/find?letter={letter}", api_key)

def get_current_rankings():
    api_url = st.secrets["RANKING_URL"]
    headers = {
        "Authorization": f"Bearer {st.secrets['RANKING_API_KEY']}"
    }

    try:
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            return response.json().get("data")
    except Exception as e:
        st.error(f"⚠️ Network error")

def generate_steam_url(user_id: str) -> str | None:
    api_url = st.secrets["STEAM_AUTH_URL"]
    allowed_domain = get_allowed_domain()

    headers = {
        "Authorization": f"Bearer {st.secrets['SERVER_API_KEY']}"
    }
    json_data = {
        "user_id": user_id,
        "auth_ver": st.secrets['AUTH_VER']
    }

    try:
        response = requests.post(api_url, headers=headers, json=json_data)
        if response.status_code == 200:
            data = response.json()
            steam_url = data.get("data", {}).get("steamAuthUrl")
            if steam_url and is_safe_url(steam_url, allowed_domain):
                return steam_url
            else:
                st.error("Invalid or unsafe Steam auth URL.")
        else:
            st.error(f"Steam auth API error: {response.status_code}")
    except Exception as e:
        st.error(f"Exception while generating Steam URL")

    return None

def build_logout_url():
    logout_url = (
        f"https://{st.secrets['LOGOUT_DOMAIN']}/v2/logout?"
        f"client_id={st.secrets['LOGOUT_CLIENT_ID']}&"
        f"returnTo={st.secrets['SITE_DOMAIN']}"
    )
    return logout_url


def grab_steam_from_faceit(nickname: str):
    headers = {
        "Authorization": f"Bearer {st.secrets['FACEIT_OPEN']}"
    }
    user_url = f"https://open.faceit.com/data/v4/players?game=cs2&nickname={nickname}"

    try:
        response = requests.get(user_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get("games", {}).get("cs2", {}).get("game_player_id")
        else:
            st.error(f"FACEIT API error {response.status_code}")
    except Exception as e:
        st.error(f"Exception while executing FACEIT data grab")

    return None