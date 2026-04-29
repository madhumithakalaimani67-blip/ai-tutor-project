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
    
    # Track selected roadmap
    all_roadmaps = storage.get_all_roadmaps(user_id)
    if "current_roadmap_id" not in st.session_state and all_roadmaps:
        st.session_state.current_roadmap_id = all_roadmaps[0]['id']

    # ── SIDEBAR Branding & Navigation ──
    with st.sidebar:
        ui_helper.render_sidebar_branding()
        ui_helper.render_sidebar_header("My Roadmaps", "🛣️")
        
        if all_roadmaps:
            for rm in all_roadmaps:
                is_active = st.session_state.get("current_roadmap_id") == rm['id']
                label = f"{'🎯 ' if is_active else ''}{rm['goal']}"
                if st.button(label, key=f"sidebar_rm_{rm['id']}", use_container_width=True):
                    st.session_state.current_roadmap_id = rm['id']
                    st.session_state.roadmap_msgs = [
                        {"role":"user","content":f"Show my roadmap for: {rm['goal']}"},
                        {"role":"assistant","content":rm['content']}
                    ]
                    st.session_state.roadmap_mode = "interact"
                    st.rerun()
            
            st.markdown("---")
            # Show progress for active
            curr_id = st.session_state.get("current_roadmap_id")
            active_rm = next((r for r in all_roadmaps if r['id'] == curr_id), None)
            if active_rm:
                tasks = storage.get_tasks(user_id, active_rm['id']) or []
                done  = len([t for t in tasks if t['status'] == 'done'])
                perc  = int((done / len(tasks)) * 100) if tasks else 0
                st.markdown(f"**Progress: {perc}%**")
                st.progress(perc / 100)
                st.caption(f"{done} of {len(tasks)} tasks completed")
            
            st.markdown("---")
            if st.button("➕ New Goal", use_container_width=True, key="new_rm_btn"):
                st.session_state.force_new_roadmap = True
                for k in ["roadmap_msgs", "roadmap_mode", "current_roadmap_id", "roadmap_target", "roadmap_level", "roadmap_dur", "roadmap_resources"]:
                    if k in st.session_state: del st.session_state[k]
                st.rerun()
        else:
            st.info("No roadmaps yet. Start by setting a goal below!")

    # ── MAIN CONTENT ──
    with main_col:
        st.title("🛣 AI Study Planner")
        st.caption("Disciplined Monthly → Weekly → Daily roadmap built for your schedule.")

        if "roadmap_msgs" not in st.session_state:
            curr_id = st.session_state.get("current_roadmap_id")
            selected_rm = storage.get_roadmap_by_id(user_id, curr_id) if curr_id else None
            
            if selected_rm and not st.session_state.get("force_new_roadmap"):
                st.session_state.roadmap_msgs = [
                    {"role":"user","content":f"Show my roadmap for: {selected_rm['goal']}"},
                    {"role":"assistant","content":selected_rm['content']}
                ]
                st.session_state.roadmap_mode = "interact"
            else:
                p_goal = user_profile.get("primary_goal","").strip()
                if p_goal and not st.session_state.get("force_new_roadmap"):
                    st.session_state.roadmap_msgs = [
                        {"role":"assistant","content":f"Welcome back! 👋 I see your primary goal is **{p_goal}**. Should we build a roadmap for this, or do you have something else in mind?"}
                    ]
                    st.session_state.roadmap_mode = "welcome_choice"
                else:
                    st.session_state.roadmap_msgs = [
                        {"role":"assistant","content":"Hey! 👋 What **Domain or Interest** are we diving into today? (e.g., Python, UI/UX, Data Science)"}
                    ]
                    st.session_state.roadmap_mode      = "ask_domain"
                st.session_state.force_new_roadmap = False

        for msg in st.session_state.roadmap_msgs:
            with st.chat_message(msg["role"]):
                if msg["role"] == "assistant":
                    ui_helper.render_roadmap_visual(msg["content"])
                else:
                    st.markdown(msg["content"])

        # Display predictive chips based on current mode
        chip_selection = None
        mode = st.session_state.get("roadmap_mode")
        
        with st.container():
            if mode == "welcome_choice":
                p_goal = user_profile.get("primary_goal","")
                chip_selection = ui_helper.render_chips([f"Use Goal: {p_goal}", "Something else"], "welcome_chips", title="How should we start?")
            elif mode == "ask_level":
                chip_selection = ui_helper.render_chips(["Beginner", "Intermediate", "Advanced"], "level_chips", title="Your current skill level")
            elif mode == "ask_duration":
                chip_selection = ui_helper.render_chips(["4 weeks", "2 months", "3 months"], "dur_chips", title="How long for this journey?")
            elif mode == "ask_resources":
                options = ["YouTube Videos", "Articles & Websites", "Projects & Labs", "Online Courses", "Documentation", "Books", "All Resources"]
                chip_selection = ui_helper.render_multi_chips(options, "res_chips", title="Pick your learning sources")
            elif mode == "commit_modify":
                chip_selection = ui_helper.render_chips(["✅ Commit & Start", "✏️ Modify"], "commit_chips", title="Ready to begin?")

        prompt = st.chat_input("Type your response here...")
        interaction = chip_selection or prompt
        
        if interaction:
            st.session_state.roadmap_msgs.append({"role":"user","content":interaction})
            
            # Smart Import Detection
            if mode in ["ask_domain", "welcome_choice"] and len(interaction) > 200:
                res = agent.chat([{"role":"system","content":"Check if this text contains a structured study roadmap/plan. If yes, respond 'IMPORT'. If no, respond 'CHAT'."},{"role":"user","content":interaction}])
                if "IMPORT" in res.choices[0].message.content.upper():
                    st.session_state.roadmap_mode = "generate"
                    st.session_state.roadmap_target = "Imported Roadmap"
                    st.session_state.roadmap_dur = "Custom"
                    st.session_state.is_import = True
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"I see you've provided a roadmap! 🛰️ Analyzing and formatting it into your EduAI study lifecycle..."})
                    st.rerun()

            if mode == "welcome_choice":
                if "Use Goal" in interaction:
                    st.session_state.roadmap_target = user_profile.get("primary_goal")
                    st.session_state.roadmap_mode = "ask_level"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":f"Excellent! Let's build the **{st.session_state.roadmap_target}** roadmap. What is your current level?"})
                elif interaction == "Something else":
                    st.session_state.roadmap_mode = "ask_domain"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"Understood! What **Domain or Interest** should we focus on instead?"})
                else:
                    st.session_state.roadmap_target = interaction
                    st.session_state.roadmap_mode = "ask_level"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":f"**{interaction}** — great choice! What is your current level?"})

            elif mode == "ask_domain":
                # Only use AI if it wasn't a chip
                val = interaction
                if not chip_selection:
                    res = agent.chat([{"role":"system","content":"Extract ONLY the learning domain/topic from the user input. Return a 2-3 word title ONLY. Do NOT provide any advice, steps, or plans. If the input is gibberish, reply 'INVALID'."},{"role":"user","content":interaction}])
                    val = res.choices[0].message.content.strip().replace('"', '') if res else "INVALID"
                
                if "INVALID" in val.upper() or len(val)>50:
                    conv = agent.chat(st.session_state.roadmap_msgs+[{"role":"system","content":"Ask again for domain friendly."}])
                    if conv: st.session_state.roadmap_msgs.append({"role":"assistant","content":conv.choices[0].message.content})
                else:
                    st.session_state.roadmap_target = val
                    st.session_state.roadmap_mode = "ask_level"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":f"**{val}** — great choice! What is your current level?"})

            elif mode == "ask_level":
                levels = ["Beginner", "Intermediate", "Advanced"]
                val = interaction if interaction in levels else None
                
                if not val:
                    res = agent.chat([{"role":"system","content":"Extract level (Beginner, Intermediate, Advanced). Otherwise reply 'INVALID'."},{"role":"user","content":interaction}])
                    extracted = res.choices[0].message.content.strip() if res else "INVALID"
                    for l in levels:
                        if l.lower() in extracted.lower():
                            val = l
                            break
                
                if not val:
                    conv = agent.chat(st.session_state.roadmap_msgs+[{"role":"system","content":"Ask again for level."}])
                    if conv: st.session_state.roadmap_msgs.append({"role":"assistant","content":conv.choices[0].message.content})
                else:
                    st.session_state.roadmap_level = val
                    st.session_state.roadmap_mode = "ask_duration"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":f"Got it, **{val}**. How long should this roadmap span?"})

            elif mode == "ask_duration":
                durations = ["4 weeks", "2 months", "3 months"]
                val = interaction if interaction in durations else None
                
                if not val:
                    res = agent.chat([{"role":"system","content":"Extract duration. Otherwise 'INVALID'."},{"role":"user","content":interaction}])
                    val = res.choices[0].message.content.strip() if res else "INVALID"
                
                if "INVALID" in val.upper() or len(val)>30:
                    conv = agent.chat(st.session_state.roadmap_msgs+[{"role":"system","content":"Ask again for duration."}])
                    if conv: st.session_state.roadmap_msgs.append({"role":"assistant","content":conv.choices[0].message.content})
                else:
                    st.session_state.roadmap_dur = val
                    st.session_state.roadmap_mode = "ask_resources"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"Which **resources** should I include? You can pick multiple!"})

            elif mode == "ask_resources":
                st.session_state.roadmap_resources = interaction
                st.session_state.roadmap_mode = "generate"
                st.session_state.roadmap_msgs.append({"role":"assistant","content":"⏳ Engineering your roadmap..."})
            
            elif mode == "commit_modify":
                if "Commit" in interaction:
                    st.session_state.roadmap_mode = "do_commit"
                elif "Modify" in interaction:
                    st.session_state.roadmap_mode = "modify_input"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"Sure! What would you like to change?"})
                else:
                    st.session_state.roadmap_mode = "regenerate"

            elif mode == "modify_input":
                st.session_state.roadmap_mode = "regenerate"

            elif mode == "interact":
                ans = agent.chat(st.session_state.roadmap_msgs + [{"role":"system","content":"Be concise and helpful."}], user_profile=user_profile)
                if ans:
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":ans.choices[0].message.content})
            
            else:
                ans = agent.chat(st.session_state.roadmap_msgs + [{"role":"system","content":"Respond naturally."}], user_profile=user_profile)
                if ans:
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":ans.choices[0].message.content})
            
            st.rerun()

        if st.session_state.get("roadmap_mode") == "generate":
            with st.spinner("Engineering your roadmap..." if not st.session_state.get("is_import") else "Processing your roadmap..."):
                if st.session_state.get("is_import"):
                    last_user_msg = st.session_state.roadmap_msgs[-2]["content"]
                    gen_prompt = f"Convert this provided roadmap into the strict EduAI format: {last_user_msg}. \nFORMAT: Week X -> Day Y -> [Tasks]. Use bold headers for Days. Max 10 words per task. No paragraphs."
                else:
                    gen_prompt = f"""Create a COMPLETE, UNABRIDGED 12-WEEK study roadmap for '{st.session_state.roadmap_target}'.
- DURATION: {st.session_state.roadmap_dur} (Break this into EXACTLY 12 INDIVIDUAL WEEKS).
- LEVEL: {st.session_state.get('roadmap_level','Beginner')}
- CRITICAL RULE: DO NOT GROUP WEEKS. You MUST list: Week 1, Week 2, Week 3, Week 4, Week 5, Week 6, Week 7, Week 8, Week 9, Week 10, Week 11, and Week 12 separately.
- DAILY TASKS: 2 specific tasks per day with resource names (e.g. [Learn] Python basics from Codecademy).
- PACING: 2 hours per day.
- STRUCTURE: Use **Week X** and **Day Y** headers.
- NO SUMMARIES: Every day must have its own entry. No 'Rest of the weeks' summaries allowed."""
                
                ans = agent.chat([{"role":"user","content":gen_prompt}], user_profile=user_profile)
                if ans:
                    content = ans.choices[0].message.content
                    st.session_state.temp_roadmap_content = content
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":content})
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"Roadmap ready! Would you like to **Commit** or **Modify** it?"})
                    st.session_state.roadmap_mode = "commit_modify"
                    st.session_state.is_import = False
                    st.rerun()

        if st.session_state.get("roadmap_mode") == "do_commit":
            with st.spinner("Locking tasks..."):
                target = st.session_state.get("roadmap_target", "New Goal")
                dur = st.session_state.get("roadmap_dur", "Managed")
                content = st.session_state.get("temp_roadmap_content")
                roadmap_id = storage.save_roadmap(user_id, target, dur, content)
                st.session_state.current_roadmap_id = roadmap_id
                
                extract_prompt = f"Convert this roadmap into a JSON list: {content}. \nFORMAT: [{{'week':1, 'day':1, 'task':'Task desc', 'subtasks':['step 1']}}]. No conversational text."
                extract_res = agent.chat([{"role":"user","content":extract_prompt}])
                try:
                    match = re.search(r'\[.*\]', extract_res.choices[0].message.content, re.DOTALL)
                    if match: storage.save_tasks(user_id, roadmap_id, json.loads(match.group()))
                except Exception as e:
                    st.error(f"Sync error: {e}")
                
                st.session_state.roadmap_mode = "interact"
                if "temp_roadmap_content" in st.session_state: del st.session_state.temp_roadmap_content
                st.success(f"Mission Locked! Today's tasks are now available in your Focus Hub.")
                st.session_state.navigate_to = "Focus Timer"
                st.rerun()

        if st.session_state.get("roadmap_mode") == "regenerate":
            with st.spinner("Refining..."):
                ans = agent.chat(st.session_state.roadmap_msgs + [{
                    "role":"system",
                    "content": """Update the roadmap based on the user's request. 
                    STRICT FORMATTING RULES:
                    1. Output the FULL roadmap.
                    2. Use **Week X** and **Day Y** headers only.
                    3. No paragraphs or chatty text.
                    4. Keep tasks concise with resource names (e.g. [Learn] Name).
                    5. Ensure structure matches: Week X -> Day Y -> [Tasks]."""
                }], user_profile=user_profile)
                if ans:
                    content = ans.choices[0].message.content
                    st.session_state.temp_roadmap_content = content
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":content})
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"Revised! **Commit** or **Modify** again?"})
                    st.session_state.roadmap_mode = "commit_modify"
                    st.rerun()

        ui_helper.render_jump_to_bottom()