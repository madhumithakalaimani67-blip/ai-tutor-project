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
        elif not st.session_state.get("force_new_roadmap") and user_profile.get("primary_goal", "").strip():
            # First time logic: Build roadmap automatically from profile
            st.session_state.roadmap_target = user_profile.get("primary_goal").strip()
            dur = user_profile.get("target_deadline", "2 months")
            st.session_state.roadmap_dur = dur.strip() if dur.strip() else "2 months"
            st.session_state.roadmap_level = user_profile.get("skill_level", "Absolute Beginner")
            style = user_profile.get("learning_style", "Mixed")
            st.session_state.roadmap_resources = f"Quality free links handling {style}"
            
            st.session_state.roadmap_msgs = [
                {"role": "user", "content": f"Create my personalized roadmap for: {st.session_state.roadmap_target}"},
                {"role": "assistant", "content": f"Welcome aboard! 🚀 Engineering your personalized **{st.session_state.roadmap_target}** roadmap using your profile settings..."}
            ]
            st.session_state.roadmap_mode = "generate"
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
            val_sys = "Extract the academic domain or learning interest from the user's input. If the input is just conversational, greeting, or off-topic, reply with EXACTLY 'INVALID'. Otherwise, reply ONLY with the extracted domain name."
            res = agent.chat([{"role": "system", "content": val_sys}, {"role": "user", "content": prompt}])
            val = res.choices[0].message.content.strip() if res else "INVALID"
            
            if "INVALID" in val.upper() or len(val) > 50:
                conv_res = agent.chat(st.session_state.roadmap_msgs + [{"role": "system", "content": "The user is chatting instead of answering the query. Be friendly, acknowledge what they said, and politely ask them again what domain/interest they want to learn."}])
                if conv_res:
                    st.session_state.roadmap_msgs.append({"role": "assistant", "content": conv_res.choices[0].message.content})
            else:
                st.session_state.roadmap_target = val
                st.session_state.roadmap_mode = "ask_level"
                st.session_state.roadmap_msgs.append({"role": "assistant", "content": f"Got it! **{val}** is a great choice. What is your current knowledge level with this topic? (e.g., Absolute Beginner, Intermediate, I know the basics)"})
        
        elif st.session_state.roadmap_mode == "ask_level":
            val_sys = "Extract the user's current knowledge or experience level from their input. If it is conversational or off-topic, reply EXACTLY 'INVALID'. Otherwise, reply ONLY with the extracted level (e.g., 'Absolute Beginner', 'Intermediate', 'Advanced', etc.)."
            res = agent.chat([{"role": "system", "content": val_sys}, {"role": "user", "content": prompt}])
            val = res.choices[0].message.content.strip() if res else "INVALID"
            
            if "INVALID" in val.upper() or len(val) > 40:
                conv_res = agent.chat(st.session_state.roadmap_msgs + [{"role": "system", "content": "The user did not provide their knowledge level. Politely ask them again what their current experience level is."}])
                if conv_res:
                    st.session_state.roadmap_msgs.append({"role": "assistant", "content": conv_res.choices[0].message.content})
            else:
                st.session_state.roadmap_level = val
                st.session_state.roadmap_mode = "ask_duration"
                st.session_state.roadmap_msgs.append({"role": "assistant", "content": f"Understood, starting from **{val}**. How long do you want to dedicate to this journey? (e.g., 4 weeks, 2 months)"})
                
        elif st.session_state.roadmap_mode == "ask_duration":
            val_sys = "Extract the duration/time from the user's input. If the input is conversational or lacks a time frame, reply EXACTLY 'INVALID'. Otherwise, reply ONLY with the extracted duration."
            res = agent.chat([{"role": "system", "content": val_sys}, {"role": "user", "content": prompt}])
            val = res.choices[0].message.content.strip() if res else "INVALID"
            
            if "INVALID" in val.upper() or len(val) > 30:
                conv_res = agent.chat(st.session_state.roadmap_msgs + [{"role": "system", "content": "The user did not provide a duration. Politely ask them again how long they want to dedicate to this journey (e.g., 4 weeks, 2 months)."}])
                if conv_res:
                    st.session_state.roadmap_msgs.append({"role": "assistant", "content": conv_res.choices[0].message.content})
            else:
                st.session_state.roadmap_dur = val
                st.session_state.roadmap_mode = "ask_resources"
                st.session_state.roadmap_msgs.append({"role": "assistant", "content": "Perfect. Should I also include specific **YouTube video suggestions** and **educational website links** in your roadmap? (e.g., 'Yes to both', 'No', 'Just YouTube')"})
        
        elif st.session_state.roadmap_mode == "ask_resources":
            val_sys = "Extract the user's preference for resources. If conversational or unclear, reply EXACTLY 'INVALID'. Otherwise, reply ONLY with the extracted preference."
            res = agent.chat([{"role": "system", "content": val_sys}, {"role": "user", "content": prompt}])
            val = res.choices[0].message.content.strip() if res else "INVALID"
            
            if "INVALID" in val.upper() or len(val) > 50:
                conv_res = agent.chat(st.session_state.roadmap_msgs + [{"role": "system", "content": "The user did not provide a clear preference for resources. Politely ask them again if they want YouTube videos and website links."}])
                if conv_res:
                    st.session_state.roadmap_msgs.append({"role": "assistant", "content": conv_res.choices[0].message.content})
            else:
                st.session_state.roadmap_resources = val
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
            - CURRENT PROFICIENCY: The user's current level is: {st.session_state.get('roadmap_level', 'Beginner')}. Tailor the roadmap exactly to this level. If they are a beginner, start from absolute basics. If they are advanced, skip the basics.
            - NO PARAGRAPHS: Use ONLY bullet points and headers. Keep sentences under 10 words.
            - RESOURCES: {st.session_state.roadmap_resources}. 
            - RESOURCE RULE: Do NOT hallucinate deep links to specific videos or articles. For videos, you MUST generate YouTube search links: `[Target Concept on YouTube](https://www.youtube.com/results?search_query=target+concept)`. For articles, use Google search links: `[Target Concept Tutorial](https://www.google.com/search?q=target+concept+tutorial)`. DO NOT guess actual URLs like `watch?v=...` to avoid broken links.
            - CONSTRAINT: Every daily task MUST be achievable in under {daily_time}.
            - DOUBT SOLVER: At the end of each sub-topic, add a Markdown link to instantly ask the AI to teach that topic. The link MUST be strictly formatted as: `[🧠 Teach me: TOPIC](/?nav_to=Doubt%20Solver&doubt_query=Teach+me+about+TOPIC)` where TOPIC is the name of the topic but with spaces replaced by the '+' character for the URL query.
            - FORMAT: Use BOLD for key terms and emojis for visual structure."""
            
            ans = agent.chat([{"role": "user", "content": gen_prompt}], user_profile=user_profile)
            if ans:
                content = ans.choices[0].message.content
                st.session_state.temp_roadmap_content = content
                st.session_state.roadmap_msgs.append({"role": "assistant", "content": content})
                st.session_state.roadmap_msgs.append({"role": "assistant", "content": "Here is your AI engineered roadmap. Would you like to **Commit** to this path, or do you want to **Modify** it?"})
                st.session_state.roadmap_mode = "commit_modify"
                st.rerun()

    # --- COMMIT OR MODIFY FLOW ---
    if st.session_state.get("roadmap_mode") == "commit_modify":
        st.markdown("<hr>", unsafe_allow_html=True)
        st.info("⚠️ **Action Required:** Committing will lock this roadmap and send the daily breakdown to your Focus Tracker.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Commit & Start", use_container_width=True, type="primary"):
                with st.spinner("Locking in your tasks..."):
                    roadmap_id = storage.save_roadmap(user_id, st.session_state.roadmap_target, st.session_state.roadmap_dur, st.session_state.temp_roadmap_content)
                    
                    extract_prompt = f"Convert this into a JSON list: {st.session_state.temp_roadmap_content}. Format: [{{'week': 1, 'desc': 'Task 1', 'vault_breakdown': ['Step 1', 'Step 2', 'Step 3']}}]. No text outside JSON."
                    extract_res = agent.chat([{"role": "user", "content": extract_prompt}])
                    try:
                        import re, json
                        match = re.search(r'\[.*\]', extract_res.choices[0].message.content, re.DOTALL)
                        if match:
                            task_list = json.loads(match.group())
                            storage.save_tasks(user_id, roadmap_id, task_list)
                    except: pass
                    
                    st.session_state.roadmap_mode = "interact"
                    if "temp_roadmap_content" in st.session_state: del st.session_state.temp_roadmap_content
                    st.session_state.navigate_to = "Focus Timer"
                    st.rerun()
        with c2:
            if st.button("✏️ Modify Output", use_container_width=True):
                st.session_state.roadmap_mode = "modify_input"
                st.rerun()
                
    if st.session_state.get("roadmap_mode") == "modify_input":
        st.info("💡 Tell me what to change (e.g., 'Make it harder', 'Less videos, more reading', 'Focus more on X')")
        mod = st.chat_input("How should I modify it?")
        if mod:
            st.session_state.roadmap_msgs.append({"role": "user", "content": mod})
            st.session_state.roadmap_msgs.append({"role": "assistant", "content": "Refining your disciplined routine..."})
            st.session_state.roadmap_mode = "regenerate"
            st.rerun()
            
    if st.session_state.get("roadmap_mode") == "regenerate":
        with st.spinner("Refining Roadmap..."):
            sys_msg = {"role": "system", "content": "Update the roadmap based precisely on the user's latest request. Keep the exact same Markdown formatting rules as before (bullets, specific search query links, doubt solver links at the end of every topic). Output the full new roadmap."}
            ans = agent.chat(st.session_state.roadmap_msgs + [sys_msg], user_profile=st.session_state.get("user_profile", {}))
            if ans:
                content = ans.choices[0].message.content
                st.session_state.temp_roadmap_content = content
                st.session_state.roadmap_msgs.append({"role": "assistant", "content": content})
                st.session_state.roadmap_msgs.append({"role": "assistant", "content": "Would you like to **Commit** to this revised path, or do you want to **Modify** it again?"})
                st.session_state.roadmap_mode = "commit_modify"
                st.rerun()

if __name__ == "__main__":
    main(None)
