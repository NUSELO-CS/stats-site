import streamlit as st

current_page = "Profile"

if st.session_state.get("last_page") != current_page:
    st.session_state.last_page = current_page


with st.container(border=True):
    col1, col2, col3 = st.columns([0.05, 0.90, 0.05], vertical_alignment="center")
    if st.user.is_logged_in:
        with col1: 
            picture = st.user.get("picture")
            if picture:
                st.image(picture, width=48)
        with col2:
            name = st.user.get("name", "User")
            st.markdown(f"**{name}**")
        with col3:
            if st.button("Log out"):
                st.logout()
    else:
        with col2:
            if st.button("Log in",use_container_width=True):
                st.login("provider") 
