import streamlit as st
import requests
import html
from urllib.parse import urlparse

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

def _api_get(endpoint: str, api_key: str, params: dict = None):
    url = f"{st.secrets['BASE_URL']}{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get("data")
        elif response.status_code == 403:
            st.logout()
    except Exception as e:
        st.error(f"⚠️ Network error: {str(e)}")
    
    return None  


def get_match_data(steam_id: str, api_key: str, offset=0, limit=20):
    params = {
        "steam_id": steam_id,
        "order": "desc",
        "offset": offset,
        "limit": limit
    }
    return _api_get("/v2/data/players/matches", api_key, params)


def get_player_stats(steam_id: str, api_key: str):
    params = {
        "steam_id": steam_id,
        "order": "desc"
    }
    return _api_get("/v2/data/players/stats", api_key, params)


def get_match_info(match_id: str, api_key: str):
    return _api_get(f"/v2/data/matches/{match_id}", api_key)

def get_player_info(steam_id: str, api_key: str):
    params = {
        "steam_id": steam_id
    }
    return _api_get("/v2/data/players/info", api_key, params)

def get_event_details(event_id: str, api_key: str):
    return _api_get(f"/v2/data/comps/{event_id}", api_key)

def get_event_regions(region: str, api_key: str):
    return _api_get(f"/v2/data/comps/list?region={region}", api_key)

def get_profile(user_id: str, api_key: str):
    params = {
        "user_id": user_id
    }
    return _api_get(f"/auther/profile", st.secrets['SERVER_API_KEY'],params)

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
            st.error(f"Steam auth API error: {response.status_code} — {response.text}")
    except Exception as e:
        st.error(f"Exception while generating Steam URL: {e}")

    return None

def build_logout_url():
    logout_url = (
        f"https://{st.secrets['LOGOUT_DOMAIN']}/v2/logout?"
        f"client_id={st.secrets['LOGOUT_CLIENT_ID']}&"
        f"returnTo={st.secrets['SITE_DOMAIN']}"
    )
    return logout_url