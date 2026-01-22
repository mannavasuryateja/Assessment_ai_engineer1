import streamlit as st
from database import get_all_bookings


def render_admin_dashboard():
    st.header("📊 Admin Dashboard")

    bookings = get_all_bookings()

    if not bookings:
        st.info("No bookings yet.")
        return

    st.dataframe(bookings)

