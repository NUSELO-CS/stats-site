import streamlit as st

current_page = "Home"
if st.session_state.get("last_page") != current_page:
    st.session_state.last_page = current_page  

st.markdown(
        """
        # NUSELO Home Page
        
        Welcome to the Alpha version of NUSELO Stats

        Features are being rolled out in stages, for access, feedback or bug reporting please use the link to the discord below:
    """
)


st.link_button("NUSELO Discord", "https://discord.nuselo.uk/", help=None, type="primary")

st.markdown(
        """
        You can supply your API key via the sidebar, it is recommended you save this API key to your password manager while this approach is used.


        ### Special Thanks

        Thanks to Gumpster and Bonglord for support as well as m2k, shoobie and Maru for inspiration. Thanks to UKCS for its constant support.
    """
)