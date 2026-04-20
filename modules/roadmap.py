import streamlit as st
import json
import re
import base64
from utils import ai_helper, storage, ui_helper

def main(user_id):
    user_profile = st.session_state.get('user_profile', {})
    daily_time   = user_profile.get('daily_time', '1 hour')
    agent        = ai_helper.get_ai_agent()

    main_col = st.container()

    # ── SIDEBAR Branding & Navigation ──
    with st.sidebar:
        ui_helper.render_sidebar_branding()
        st.markdown("## 🛣️ Roadmap")
        latest = storage.get_latest_roadmap(user_id)
        if latest:
            tasks = storage.get_tasks(user_id, latest['id']) or []
            done  = len([t for t in tasks if t['status'] == 'done'])
            perc  = int((done / len(tasks)) * 100) if tasks else 0
            st.markdown(f"**🏆 {perc}% Complete**")
            st.progress(perc / 100)
            st.caption(f"{done} of {len(tasks)} milestones")
            pending = [t for t in tasks if t['status'] == 'pending'][:3]
            if pending:
                st.markdown("---")
                st.markdown("**🎯 Next Up**")
                for p in pending:
                    st.markdown(f"• {p['description'][:40]}...")
            st.markdown("---")
            if st.button("🆕 New Roadmap", use_container_width=True, key="new_rm"):
                st.session_state.force_new_roadmap = True
                for k in ["roadmap_msgs","roadmap_mode"]:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()
        else:
            st.info("No roadmap yet.\nStart chatting below!")

    # ── MAIN CONTENT ──
    with main_col:
        st.title("🛣 AI Study Planner")
        st.caption("Disciplined Monthly → Weekly → Daily roadmap built for your schedule.")

        if "roadmap_msgs" not in st.session_state:
            latest = storage.get_latest_roadmap(user_id) if not st.session_state.get("force_new_roadmap") else None
            if latest:
                st.session_state.roadmap_msgs = [
                    {"role":"user","content":f"Show my roadmap for: {latest['goal']}"},
                    {"role":"assistant","content":latest['content']}
                ]
                st.session_state.roadmap_mode = "interact"
            elif not st.session_state.get("force_new_roadmap") and user_profile.get("primary_goal","").strip():
                st.session_state.roadmap_target    = user_profile.get("primary_goal").strip()
                dur = user_profile.get("target_deadline","2 months")
                st.session_state.roadmap_dur       = dur.strip() or "2 months"
                st.session_state.roadmap_level     = user_profile.get("skill_level","Absolute Beginner")
                st.session_state.roadmap_resources = f"Quality free links for {user_profile.get('learning_style','Mixed')} style"
                st.session_state.roadmap_msgs = [
                    {"role":"user","content":f"Create roadmap for: {st.session_state.roadmap_target}"},
                    {"role":"assistant","content":f"Welcome! 🚀 Engineering your **{st.session_state.roadmap_target}** roadmap..."}
                ]
                st.session_state.roadmap_mode = "generate"
            else:
                st.session_state.roadmap_msgs = [
                    {"role":"assistant","content":"Hey! 👋 What **Domain or Interest** are we diving into? (e.g., Python, UI/UX, Data Science)"}
                ]
                st.session_state.roadmap_mode      = "ask_domain"
                st.session_state.force_new_roadmap = False

        for msg in st.session_state.roadmap_msgs:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        prompt = st.chat_input("Type your response here...")
        if prompt:
            st.session_state.roadmap_msgs.append({"role":"user","content":prompt})
            mode = st.session_state.roadmap_mode

            if mode == "ask_domain":
                res = agent.chat([{"role":"system","content":"Extract learning domain. If off-topic reply EXACTLY 'INVALID'. Otherwise reply ONLY with the domain."},{"role":"user","content":prompt}])
                val = res.choices[0].message.content.strip() if res else "INVALID"
                if "INVALID" in val.upper() or len(val)>50:
                    conv = agent.chat(st.session_state.roadmap_msgs+[{"role":"system","content":"Ask again for domain friendly."}])
                    if conv: st.session_state.roadmap_msgs.append({"role":"assistant","content":conv.choices[0].message.content})
                else:
                    st.session_state.roadmap_target = val
                    st.session_state.roadmap_mode   = "ask_level"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":f"**{val}** — great choice! What is your current level? (Beginner / Intermediate / Advanced)"})

            elif mode == "ask_level":
                res = agent.chat([{"role":"system","content":"Extract knowledge level. If off-topic reply EXACTLY 'INVALID'. Otherwise reply ONLY with the level."},{"role":"user","content":prompt}])
                val = res.choices[0].message.content.strip() if res else "INVALID"
                if "INVALID" in val.upper() or len(val)>40:
                    conv = agent.chat(st.session_state.roadmap_msgs+[{"role":"system","content":"Ask again for level."}])
                    if conv: st.session_state.roadmap_msgs.append({"role":"assistant","content":conv.choices[0].message.content})
                else:
                    st.session_state.roadmap_level = val
                    st.session_state.roadmap_mode  = "ask_duration"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":f"Starting from **{val}**. How long for this journey? (e.g., 4 weeks, 2 months)"})

            elif mode == "ask_duration":
                res = agent.chat([{"role":"system","content":"Extract duration. If off-topic reply EXACTLY 'INVALID'. Otherwise reply ONLY with duration."},{"role":"user","content":prompt}])
                val = res.choices[0].message.content.strip() if res else "INVALID"
                if "INVALID" in val.upper() or len(val)>30:
                    conv = agent.chat(st.session_state.roadmap_msgs+[{"role":"system","content":"Ask again for duration."}])
                    if conv: st.session_state.roadmap_msgs.append({"role":"assistant","content":conv.choices[0].message.content})
                else:
                    st.session_state.roadmap_dur  = val
                    st.session_state.roadmap_mode = "ask_resources"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"Include **YouTube videos** and **article links**? (Yes to both / Just YouTube / No resources)"})

            elif mode == "ask_resources":
                res = agent.chat([{"role":"system","content":"Extract resource preference. If unclear reply EXACTLY 'INVALID'. Otherwise reply ONLY with preference."},{"role":"user","content":prompt}])
                val = res.choices[0].message.content.strip() if res else "INVALID"
                if "INVALID" in val.upper() or len(val)>50:
                    conv = agent.chat(st.session_state.roadmap_msgs+[{"role":"system","content":"Ask again for resource preference."}])
                    if conv: st.session_state.roadmap_msgs.append({"role":"assistant","content":conv.choices[0].message.content})
                else:
                    st.session_state.roadmap_resources = val
                    st.session_state.roadmap_mode      = "generate"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"⏳ Engineering your roadmap..."})
            else:
                ans = agent.chat(st.session_state.roadmap_msgs+[{"role":"system","content":"Be concise. Bullet points only."}], user_profile=user_profile)
                if ans: st.session_state.roadmap_msgs.append({"role":"assistant","content":ans.choices[0].message.content})
            st.rerun()

        if st.session_state.get("roadmap_mode") == "generate":
            with st.spinner("Engineering your roadmap..."):
                gen_prompt = f"""Create a highly structured study roadmap for '{st.session_state.roadmap_target}' over {st.session_state.roadmap_dur}.
- LEVEL: {st.session_state.get('roadmap_level','Beginner')}
- NO PARAGRAPHS: Only bullet points and headers. Max 10 words per line.
- RESOURCES: {st.session_state.get('roadmap_resources','relevant links')}
- DAILY LIMIT: Every task under {daily_time}
- FORMAT: Bold key terms, use emojis for structure"""
                ans = agent.chat([{"role":"user","content":gen_prompt}], user_profile=user_profile)
                if ans:
                    content = ans.choices[0].message.content
                    st.session_state.temp_roadmap_content = content
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":content})
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"Roadmap ready! Would you like to **Commit** to this path or **Modify** it?"})
                    st.session_state.roadmap_mode = "commit_modify"
                    st.rerun()

        if st.session_state.get("roadmap_mode") == "commit_modify":
            st.info("⚠️ Committing locks this roadmap and sends tasks to your Focus Tracker.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Commit & Start", use_container_width=True, type="primary", key="commit_btn"):
                    with st.spinner("Locking tasks..."):
                        roadmap_id = storage.save_roadmap(user_id, st.session_state.roadmap_target, st.session_state.roadmap_dur, st.session_state.temp_roadmap_content)
                        extract_prompt = f"Convert this into JSON list: {st.session_state.temp_roadmap_content}. Format: [{{'week':1,'desc':'Task','vault_breakdown':['Step 1']}}]. No text outside JSON."
                        extract_res = agent.chat([{"role":"user","content":extract_prompt}])
                        try:
                            match = re.search(r'\[.*\]', extract_res.choices[0].message.content, re.DOTALL)
                            if match: storage.save_tasks(user_id, roadmap_id, json.loads(match.group()))
                        except: pass
                        st.session_state.roadmap_mode = "interact"
                        if "temp_roadmap_content" in st.session_state: del st.session_state.temp_roadmap_content
                        st.session_state.navigate_to = "Focus Timer"
                        st.rerun()
            with c2:
                if st.button("✏️ Modify", use_container_width=True, key="modify_btn"):
                    st.session_state.roadmap_mode = "modify_input"
                    st.rerun()

        if st.session_state.get("roadmap_mode") == "modify_input":
            st.info("💡 Tell me what to change (e.g., 'Make it harder', 'Less videos')")
            mod = st.chat_input("How to modify?")
            if mod:
                st.session_state.roadmap_msgs.append({"role":"user","content":mod})
                st.session_state.roadmap_mode = "regenerate"
                st.rerun()

        if st.session_state.get("roadmap_mode") == "regenerate":
            with st.spinner("Refining..."):
                ans = agent.chat(st.session_state.roadmap_msgs+[{"role":"system","content":"Update roadmap per user request. Keep same formatting. Output full roadmap."}], user_profile=user_profile)
                if ans:
                    content = ans.choices[0].message.content
                    st.session_state.temp_roadmap_content = content
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":content})
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"Revised! **Commit** or **Modify** again?"})
                    st.session_state.roadmap_mode = "commit_modify"
                    st.rerun()