import streamlit as st

# Import all modules
from modules import dashboard
from modules import roadmap
from modules import focus_tracker
from modules import doubt_solver

# App Title
st.set_page_config(page_title="EDUAI", layout="wide")

st.title("EDUAI - Personal AI Study Assistant")

# Sidebar Navigation
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Go to",
    ["Dashboard", "Roadmap Generator", "Focus Tracker", "Doubt Solver"]
)

# Page Routing
if page == "Dashboard":
    dashboard.show()

elif page == "Roadmap Generator":
    roadmap.show()

elif page == "Focus Tracker":
    focus_tracker.show()

elif page == "Doubt Solver":
    doubt_solver.show()