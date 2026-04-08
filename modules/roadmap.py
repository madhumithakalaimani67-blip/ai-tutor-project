import streamlit as st
import json
import re
from utils import ai_helper, storage

def main(user_id):
    st.title("🛣 AI Study Planner")
    st.write("Disciplined Monthly → Weekly → Daily roadmap built specifically for your schedule.")

    user_profile = st.session_state.get('user_profile', {})
    daily_time = user_profile.get('daily_time', '1 hour')
    agent = ai_helper.get_ai_agent()

    # --- SIDEBAR: PROGRESS & CHECKLIST ---
    with st.sidebar:
        st.markdown("### 🏆 Your Progress")
        latest = storage.get_latest_roadmap(user_id)
        if latest:
            tasks = storage.get_tasks(user_id, latest['id']) or []
            done = len([t for t in tasks if t['status'] == 'done'])
            perc = int((done / len(tasks)) * 100) if tasks else 0
            st.progress(perc / 100)
            st.write(f"**{perc}% Goal Achieved** ({done}/{len(tasks)} tasks)")
            
            if tasks:
                pending = [t for t in tasks if t['status'] == 'pending'][:3]
                if pending:
                    st.markdown("---")
                    st.caption("Next Missions:")
                    for p in pending:
                        st.markdown(f"🔹 {p['description']}")
            
            st.markdown("---")
            if st.button("🆕 Create New Roadmap", use_container_width=True):
                st.session_state.force_new_roadmap = True
                if "roadmap_msgs" in st.session_state: del st.session_state.roadmap_msgs
                if "roadmap_mode" in st.session_state: del st.session_state.roadmap_mode
                st.rerun()

    # --- MAIN ADVISOR CHAT ---
    if "roadmap_msgs" not in st.session_state:
        # Check for existing roadmap in DB (If not forcing new)
        latest = storage.get_latest_roadmap(user_id) if not st.session_state.get("force_new_roadmap") else None
        if latest:
            st.session_state.roadmap_msgs = [
                {"role": "user", "content": f"Show my roadmap for: {latest['goal']}"},
                {"role": "assistant", "content": latest['content']}
            ]
            st.session_state.roadmap_mode = "interact"
        else:
            st.session_state.roadmap_msgs = [
                {"role": "assistant", "content": "Hey! 👋 What **Domain or Interest** are we diving into today? (e.g., Python, UI/UX Design, Data Science)"}
            ]
            st.session_state.roadmap_mode = "ask_domain"
            st.session_state.force_new_roadmap = False # Reset flag

    # Display History
    for msg in st.session_state.roadmap_msgs:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input Logic
    prompt = st.chat_input("Type your response here...")
    if prompt:
        st.session_state.roadmap_msgs.append({"role": "user", "content": prompt})

        if st.session_state.roadmap_mode == "ask_domain":
            st.session_state.roadmap_target = prompt
            st.session_state.roadmap_mode = "ask_duration"
            st.session_state.roadmap_msgs.append({"role": "assistant", "content": f"Got it! **{prompt}** is a great choice. How long do you want to dedicate to this journey? (e.g., 4 weeks, 2 months)"})
        
        elif st.session_state.roadmap_mode == "ask_duration":
            st.session_state.roadmap_dur = prompt
            st.session_state.roadmap_mode = "ask_resources"
            st.session_state.roadmap_msgs.append({"role": "assistant", "content": "Perfect. Should I also include specific **YouTube video suggestions** and **educational website links** in your roadmap? (e.g., 'Yes to both', 'No', 'Just YouTube')"})
        
        elif st.session_state.roadmap_mode == "ask_resources":
            st.session_state.roadmap_resources = prompt
            st.session_state.roadmap_mode = "generate"
            st.session_state.roadmap_msgs.append({"role": "assistant", "content": "⏳ Engineering your disciplined path with the best resources. No fluff, just the plan..."})
        
        else:
            ans = agent.chat(st.session_state.roadmap_msgs + [{"role": "system", "content": "Be extremely concise. Use bullet points. No paragraphs.start from basics of user input."}], user_profile=user_profile)
            if ans:
                st.session_state.roadmap_msgs.append({"role": "assistant", "content": ans.choices[0].message.content})
        
        st.rerun()

    # --- GENERATION LOGIC WITH VISUAL JOURNEY ---
    if st.session_state.get("roadmap_mode") == "generate":
        with st.spinner("Engineering Disciplined Routine..."):
            # VISUAL JOURNEY ONLY SHOWS HERE
            st.markdown("### 🗺️ Your Visual Journey Flow")
            
            import base64
            mermaid_code = """
            graph LR
                A[Goal Set] --> B[Roadmap Gen]
                B --> C[Daily Task Alert]
                C --> D[Focused Study]
                D --> E[Mark Done]
                E --> F[Progress Insight]
                F --> C
            """
            b64_code = base64.b64encode(mermaid_code.encode("ascii")).decode("ascii")
            st.image(f"https://mermaid.ink/svg/{b64_code}")

            # PRECISION GENERATION PROMPT
            gen_prompt = f"""Create a highly structured study roadmap for '{st.session_state.roadmap_target}' over {st.session_state.roadmap_dur}.
            - START FROM ABSOLUTE BASICS: Assume the user knows nothing. Day 1 must be the most fundamental concept.
            - NO PARAGRAPHS: Use ONLY bullet points and headers. Keep sentences under 10 words.
            - RESOURCES: {st.session_state.roadmap_resources}. 
            - RESOURCE RULE: Provide specific, high-quality links (e.g., 'Intro to {st.session_state.roadmap_target} on YouTube by FreeCodeCamp', 'Official {st.session_state.roadmap_target} Documentation'). 
            - DO NOT tell the user to 'search on Google' or 'visit a roadmap website'. YOU are the roadmap provider.
            - CONSTRAINT: Every daily task MUST be achievable in under {daily_time}.
            - FORMAT: Use BOLD for key terms and emojis for visual structure."""
            
            ans = agent.chat([{"role": "user", "content": gen_prompt}], user_profile=user_profile)
            if ans:
                content = ans.choices[0].message.content
                roadmap_id = storage.save_roadmap(user_id, st.session_state.roadmap_target, st.session_state.roadmap_dur, content)
                
                # EXTRACT TASKS VIA AI - INCLUDES DISCIPLINED BREAKDOWN
                extract_prompt = f"Convert this into a JSON list: {content}. Format: [{{'week': 1, 'desc': 'Task 1', 'vault_breakdown': ['Step 1', 'Step 2', 'Step 3']}}]. No text outside JSON."
                extract_res = agent.chat([{"role": "user", "content": extract_prompt}])
                try:
                    match = re.search(r'\[.*\]', extract_res.choices[0].message.content, re.DOTALL)
                    if match:
                        task_list = json.loads(match.group())
                        storage.save_tasks(user_id, roadmap_id, task_list)
                except: pass
                
                st.session_state.roadmap_msgs.append({"role": "assistant", "content": content})
                st.session_state.roadmap_mode = "interact"
                st.rerun()

if __name__ == "__main__":
    main(None)
