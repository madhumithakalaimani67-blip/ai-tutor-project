import streamlit as st

def show():
    st.title("Doubt Solver 🤖")

    user_question = st.text_input("Ask your doubt here:")

    if st.button("Get Answer"):
        if user_question:
            st.write("Generating answer...")
            # Later we connect Ollama here
        else:
            st.warning("Please enter a question.")