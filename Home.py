import streamlit as st

st.set_page_config(
    page_title="Stonks", page_icon=":chart_with_upwards_trend:", layout="wide"
)

st.title("Welcome to my Stonks App")

st.image("stonks.jpg", width=500)

st.sidebar.success("Click on a page.")
