import streamlit as st
import requests

def _api_get(endpoint: str, api_key: str, params: dict = None):
    url = f"{st.secrets['BASE_URL']}{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get("data")
        else:
            st.error(f"⚠️ API call failed (status {response.status_code})")
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
