import streamlit as st

if not st.user.is_logged_in:
    st.session_state.redirected = True
    st.switch_page("pages/User.py")

st.title("UKCS Rankings")
st.markdown('## Coming soon')