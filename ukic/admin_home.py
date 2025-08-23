import streamlit as st
import pandas as pd
from tools.perms import has_access

if not has_access(["platform_admin", "ukic_admin"]):
    st.session_state.redirected = True
    st.switch_page("pages/User.py") 

current_page = "ukic_admin_home"

if not st.user.is_logged_in:
    st.session_state.redirected = True
    st.switch_page("pages/User.py") 

# Set default tab
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "home"

# Track last loaded page
if st.session_state.get("last_page") != current_page:
    st.session_state.active_tab = "home"
    st.session_state.last_page = current_page 

st.header("UKIC Admin Home")