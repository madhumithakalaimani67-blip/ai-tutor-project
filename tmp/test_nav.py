import streamlit as st
import urllib.parse
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

pages = ["Dashboard", "Roadmap", "Focus Timer"]

# Using st.markdown with inline js
nav_items_html = ""
for page in pages:
    nav_items_html += f"""
    <a href="#" onclick="
        var labels = document.querySelectorAll('[data-testid=\\'stRadio\\'] label');
        for (var i = 0; i < labels.length; i++) {{
            if (labels[i].innerText === '{page}') {{
                labels[i].click();
                return false;
            }}
        }}
        console.log('Not found: {page}');
        return false;
    ">{page}</a> |
    """

st.markdown(f"<div>{nav_items_html}</div>", unsafe_allow_html=True)
st.write(f"Current Page: {st.session_state.page}")

page = st.radio("Nav", pages, horizontal=True, label_visibility="collapsed")
if page != st.session_state.page:
    st.session_state.page = page
    st.rerun()
