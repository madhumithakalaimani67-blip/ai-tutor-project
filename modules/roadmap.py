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
                    st.session_state.roadmap_target = rm['goal'] # CRITICAL FIX: Update target on switch
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
                
                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️ Delete Roadmap", use_container_width=True, key="del_rm_btn"):
                    storage.delete_roadmap(active_rm['id'])
                    st.session_state.force_new_roadmap = True
                    for k in ["roadmap_msgs", "roadmap_mode", "current_roadmap_id", "roadmap_target", "roadmap_level", "roadmap_dur", "roadmap_resources"]:
                        if k in st.session_state: del st.session_state[k]
                    st.rerun()
            
            st.markdown("---")
            if st.button("➕ New Goal", use_container_width=True, key="new_rm_btn"):
                st.session_state.force_new_roadmap = True
                st.session_state.is_new_request = True
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
                st.session_state.roadmap_target = selected_rm['goal'] # PRESERVE TITLE
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
                    st.session_state.is_new_request     = True
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
            elif mode == "ask_known":
                chip_selection = ui_helper.render_chips(["New to this / Nothing"], "known_chips", title="What topics do you already know? (Optional)")
            elif mode == "ask_duration":
                chip_selection = ui_helper.render_chips(["4 weeks", "2 months", "3 months"], "dur_chips", title="How long for this journey? (Or type manually below)")
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
                    st.session_state.roadmap_mode = "ask_known"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":f"Got it, **{val}**. What are the topics you already know in this field? (If none, just say 'Nothing' or 'New to this')"})

            elif mode == "ask_known":
                if "New to this" in interaction or "Nothing" in interaction:
                    st.session_state.roadmap_known = "None"
                else:
                    st.session_state.roadmap_known = interaction
                
                st.session_state.roadmap_mode = "ask_duration"
                st.session_state.roadmap_msgs.append({"role":"assistant","content":"Excellent! How long should this roadmap span?"})

            elif mode == "ask_duration":
                durations = ["4 weeks", "2 months", "3 months"]
                val = interaction if interaction in durations else None
                
                if not val:
                    m_match = re.search(r'(\d+)\s*month', interaction.lower())
                    w_match = re.search(r'(\d+)\s*week', interaction.lower())
                    
                    if m_match:
                        val = f"{m_match.group(1)} months"
                    elif w_match:
                        val = f"{w_match.group(1)} weeks"
                    else:
                        val = "INVALID"
                
                if val == "INVALID":
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"I didn't quite catch that duration. Could you specify it in weeks or months? (e.g. '5 months')"})
                else:
                    st.session_state.roadmap_dur = val
                    st.session_state.roadmap_mode = "ask_resources"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"Which **resources** should I include? You can pick multiple!"})

            elif mode == "ask_resources":
                st.session_state.roadmap_resources = interaction
                st.session_state.roadmap_mode = "generate"
                st.session_state.roadmap_msgs.append({"role":"assistant","content":"⏳ Engineering your roadmap..."})
            
            elif mode == "commit_modify":
                interaction_lower = interaction.lower()
                if "commit" in interaction_lower:
                    st.session_state.roadmap_mode = "do_commit"
                elif "modify" in interaction_lower:
                    st.session_state.roadmap_mode = "modify_input"
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"Sure! What would you like to change? (e.g., 'Make it 2 months' or 'Add more Python basics')"})
                else:
                    # Fallback to chat if they didn't pick a chip action
                    st.session_state.roadmap_mode = "interact"
                    st.rerun()

            elif mode == "modify_input":
                st.session_state.modify_request = interaction
                st.session_state.roadmap_mode = "regenerate"

            elif mode == "interact":
                ans = agent.chat(st.session_state.roadmap_msgs + [{
                    "role":"system",
                    "content": "You are a roadmap expert. If the user asks for any change (duration, topic, level), you MUST output the COMPLETE, UNABRIDGED roadmap. Do NOT give summaries. For every Week, you MUST list Day 1 through Day 7. Use the format: **Week X** followed by **Day Y** and then bullet points for tasks. This is CRITICAL for the system to parse your response."
                }], user_profile=user_profile)
                if ans:
                    content = ans.choices[0].message.content
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":content})
                    
                    # Smart Detection: If response contains a roadmap structure, allow committing
                    if ("Week 1" in content or "Mission 1" in content) and ("Day 1" in content):
                        st.session_state.temp_roadmap_content = content
                        st.session_state.roadmap_mode = "commit_modify"
                        st.session_state.roadmap_msgs.append({"role":"assistant","content":"I've generated an updated roadmap! Would you like to **Commit** these changes to your Focus Hub?"})
            
            else:
                ans = agent.chat(st.session_state.roadmap_msgs + [{"role":"system","content":"Respond naturally."}], user_profile=user_profile)
                if ans:
                    content = ans.choices[0].message.content
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":content})
                    
                    if ("Week 1" in content or "Mission 1" in content) and ("Day 1" in content):
                        st.session_state.temp_roadmap_content = content
                        st.session_state.roadmap_mode = "commit_modify"
                        st.session_state.roadmap_msgs.append({"role":"assistant","content":"New roadmap detected! Would you like to **Commit** this to your profile?"})
            
            st.rerun()

        if st.session_state.get("roadmap_mode") in ["generate", "regenerate"]:
            dur_label = st.session_state.get('roadmap_dur', 'roadmap')
            with st.spinner(f"Engineering your {dur_label}..." if st.session_state.roadmap_mode == "generate" else "Refining your journey..."):
                full_content = ""
                mod_req = st.session_state.get("modify_request", "")
                
                # Calculate weeks
                dur_str = st.session_state.get('roadmap_dur', '4 weeks').lower()
                weeks = 4
                y_match = re.search(r'(\d+)\s*year', dur_str)
                m_match = re.search(r'(\d+)\s*month', dur_str)
                w_match = re.search(r'(\d+)\s*week', dur_str)
                
                if y_match: weeks = int(y_match.group(1)) * 52
                elif m_match: weeks = int(m_match.group(1)) * 4
                elif w_match: weeks = int(w_match.group(1))
                
                weeks = max(1, min(weeks, 52)) # Cap at 1 year for performance
                
                chunks = (weeks + 3) // 4
                for i in range(chunks):
                    start_w = i * 4 + 1
                    end_w = min((i + 1) * 4, weeks)
                    
                    res_context = st.session_state.get('roadmap_resources', 'Mixed Resources')
                    target_domain = st.session_state.get('roadmap_target', 'the subject')
                    system_instr = f"""You are a Master Study Architect generating a structured daily roadmap for '{target_domain}'.
This is PART {i+1} OF {chunks}: generate ONLY Weeks {start_w} to {end_w}.

USER PROFILE:
- Domain/Goal: {target_domain}
- Level: {st.session_state.get('roadmap_level','Beginner')}
- Already Knows: {st.session_state.get('roadmap_known','None')}
- Preferred Resources: {res_context}

DOMAIN INTELLIGENCE — READ THIS CAREFULLY:
First, classify the domain into one of these:

1. TECHNICAL DOMAIN (e.g., Data Science, Machine Learning, Web Development, App Development, Cybersecurity, Cloud Computing, DevOps, Embedded Systems, Game Development, AI, Python, Java, etc.):
   - You MUST include specific programming languages, libraries, tools, and frameworks that are industry-standard for this domain.
   - Examples: Python, Pandas, NumPy, Scikit-learn, TensorFlow, React, Node.js, Docker, SQL, Git, Jupyter Notebook, etc.
   - Each task must be hands-on — include actual code exercises, real dataset names (e.g., Titanic on Kaggle), specific library function names, and project ideas with file names.
   - Frame tasks as placement-ready skills — things that companies will expect from a hired candidate.

2. NON-TECHNICAL DOMAIN (e.g., Communication Skills, Public Speaking, Leadership, HR, Design Thinking, Business Strategy, Marketing, Product Management, Finance, etc.):
   - Do NOT include programming languages or coding unless directly relevant.
   - Focus on frameworks, books, case studies, practice exercises, and soft skill development.
   - Frame tasks as interview-ready and workplace-applicable skills.

3. HYBRID DOMAIN (e.g., UI/UX Design, Data Analytics, Digital Marketing, Product Design):
   - Combine both: soft skill frameworks AND relevant tools (e.g., Figma for UI/UX, Google Analytics for Digital Marketing, Excel/Tableau for Data Analytics).

You MUST correctly classify '{target_domain}' and tailor the roadmap content accordingly.
For TECHNICAL and HYBRID domains, every week must build toward a portfolio project or interview-ready skill.

OUTPUT FORMAT — YOU MUST FOLLOW THIS EXACTLY:

**Week {start_w}**
**Day 1**
- Task 1: [specific learning task with tool/language/library name if technical]
- Task 2: [practical hands-on task using {res_context} — be specific about what to build or practice]
**Day 2**
- Task 1: [...]
- Task 2: [...]
...
**Day 7**
- Task 1: [...]
- Task 2: [...]

**Week {start_w + 1}**
...

RULES — VIOLATING ANY OF THESE IS NOT ACCEPTABLE:
1. Each week MUST start with "**Week N**" on its own line.
2. Each day MUST start with "**Day N**" on its own line. Day numbers MUST be 1 through 7 within every week. NEVER use Day 8, 9, 10, etc.
3. Each day MUST have EXACTLY 2 bullet points starting with "- Task 1:" and "- Task 2:". NEVER split one day into two Day headers.
4. ALL tasks must be directly, deeply relevant to '{target_domain}' at a placement/industry level of depth.
5. Do NOT skip days. Do NOT write "Day 1-7". Do NOT combine multiple days in one block.
6. Do NOT output anything except the Week/Day structure above — no introductions, summaries, or closing remarks.
{f"MODIFICATION REQUEST: {mod_req}" if mod_req else ""}"""
                    
                    ans = agent.chat([{"role":"system","content":system_instr}, {"role":"user","content":f"Generate Weeks {start_w} to {end_w} for {target_domain}"}], user_profile=user_profile)
                    if ans:
                        full_content += ans.choices[0].message.content + "\n\n"
                        st.session_state.roadmap_msgs.append({"role":"assistant","content":f"✅ Part {i+1}/{chunks} (Weeks {start_w}-{end_w}) complete."})
                
                if full_content:
                    st.session_state.temp_roadmap_content = full_content
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":full_content})
                    st.session_state.roadmap_msgs.append({"role":"assistant","content":"Your personalised roadmap is ready! Review and **Commit** to begin."})
                    st.session_state.roadmap_mode = "commit_modify"
                    if "modify_request" in st.session_state: del st.session_state.modify_request
                    st.rerun()
                else:
                    st.error("Engine failed. Re-initiating...")
                    st.session_state.roadmap_mode = "ask_domain"
                    st.rerun()

        if st.session_state.get("roadmap_mode") == "do_commit":
            with st.spinner("Locking tasks..."):
                # Robust Title Recovery
                current_id = st.session_state.get("current_roadmap_id")
                existing_rm = storage.get_roadmap_by_id(user_id, current_id) if current_id else None
                
                target = st.session_state.get("roadmap_target")
                if (not target or target == "New Goal") and existing_rm:
                    target = existing_rm['goal']
                if not target: target = "My Roadmap"
                
                dur = st.session_state.get("roadmap_dur", "Managed")
                content = st.session_state.get("temp_roadmap_content")
                
                # Decision: Update existing or Save as new?
                current_id = st.session_state.get("current_roadmap_id")
                # If we aren't forcing a new roadmap and we have an ID, we update.
                if current_id and not st.session_state.get("is_new_request", False):
                    storage.update_roadmap(current_id, target, dur, content)
                    storage.clear_roadmap_tasks(current_id)
                    roadmap_id = current_id
                else:
                    roadmap_id = storage.save_roadmap(user_id, target, dur, content)
                    st.session_state.current_roadmap_id = roadmap_id
                
                # Sequential Parsing — resets day counter to 1 for every week
                tasks_to_save = []
                current_w = 1
                current_d = 0  # Start at 0, increment on first Day header

                for line in content.split('\n'):
                    line = line.strip()
                    if not line: continue
                    
                    # Detect Week header
                    w_match = re.search(r'\b(?:Week|WEEK)\s+(\d+)\b', line, re.IGNORECASE)
                    if w_match and len(line) < 30:
                        current_w = int(w_match.group(1))
                        current_d = 0  # Reset day count for the new week
                        continue
                        
                    # Detect Day header
                    d_match = re.search(r'\b(?:Day|DAY)\s+(\d+)\b', line, re.IGNORECASE)
                    if d_match and len(line) < 30:
                        current_d += 1  # Just increment to keep it 1-7
                        if current_d > 7: current_d = 7 # safety
                        continue
                        
                    # If we haven't seen a day yet but see a task, assume Day 1
                    if current_d == 0:
                        is_likely_task = line.startswith('-') or line.startswith('*') or re.match(r'^\d+\.', line)
                        if is_likely_task: current_d = 1

                        
                    is_task = line.startswith('-') or line.startswith('*') or re.match(r'^\d+\.', line)
                    if not is_task and (line.lower().startswith('technical') or line.lower().startswith('non-technical') or line.lower().startswith('task')):
                        is_task = True
                        
                    if is_task:
                        task_desc = re.sub(r'^[\-\*\d\.\s]+', '', line).strip()
                        task_desc = re.sub(r'^(?:Technical|Non-Technical|Task)[\w\s]*:\s*', '', task_desc, flags=re.IGNORECASE).strip()
                        task_desc = task_desc.replace('**', '').replace('*', '')
                        if task_desc:
                            tasks_to_save.append({
                                'week': current_w,
                                'day': current_d,
                                'task': task_desc[:150],
                                'subtasks': []
                            })
                
                if tasks_to_save:
                    storage.save_tasks(user_id, roadmap_id, tasks_to_save)
                else:
                    st.error("Could not extract tasks. Please try generating again.")
                
                st.session_state.roadmap_mode = "interact"
                st.session_state.is_new_request = False
                if "temp_roadmap_content" in st.session_state: del st.session_state.temp_roadmap_content
                st.success(f"Mission Locked! Today's tasks are now available in your Focus Hub.")
                st.session_state.navigate_to = "Focus Timer"
                st.rerun()

        ui_helper.render_jump_to_bottom()