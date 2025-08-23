import streamlit as st

def has_access(required_roles):
    user_roles = st.session_state.get("user_roles", [])
    user_role_ids = {role.get("role") for role in user_roles}
    return any(r in user_role_ids for r in required_roles)
