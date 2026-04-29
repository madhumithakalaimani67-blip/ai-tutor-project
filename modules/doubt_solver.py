import streamlit as st
import json
import base64
from utils import ai_helper, storage, ui_helper

def main():
    user_id    = st.session_state.get('user_id')
    agent      = ai_helper.get_ai_agent()
    user_chats = storage.get_user_doubt_chats(user_id)

    main_col = st.container()

    # ── SIDEBAR Branding & Navigation ──
    with st.sidebar:
        ui_helper.render_sidebar_branding()
        st.markdown("<h2 style='margin-bottom:10px;'>🧠 Solver History</h2>", unsafe_allow_html=True)
        
        if st.button("➕ START NEW CHAT", use_container_width=True, type="primary", key="new_chat_btn"):
            new_id = storage.create_doubt_chat(user_id)
            st.session_state.current_chat_id   = new_id
            st.session_state.last_processed_id = None
            st.rerun()
            
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        search = st.text_input("🔍", placeholder="Search sessions...", label_visibility="collapsed", key="doubt_search")
        st.markdown("---")
        
        # History List (Premium Styling)
        filtered = [c for c in user_chats if search.lower() in (c['title'] or '').lower()] if search else user_chats
        for chat in filtered:
            chat_id = chat['id']
            title   = chat['title'] if chat['title'] != 'New Chat' else f"Chat {chat_id}"
            active  = st.session_state.get('current_chat_id') == chat_id
            
            # Using st.columns for the delete button, but wrapping title in a div-like button
            c1, c2 = st.columns([5, 1])
            with c1:
                btn_label = f"💬 {title[:20]}"
                if st.button(btn_label, key=f"chat_{chat_id}", use_container_width=True, 
                             type="primary" if active else "secondary"):
                    st.session_state.current_chat_id   = chat_id
                    st.session_state.last_processed_id = None
                    st.rerun()
            with c2:
                if st.button("🗑", key=f"del_{chat_id}", help="Delete chat"):
                    storage.delete_doubt_chat(chat_id)
                    if st.session_state.get('current_chat_id') == chat_id:
                        st.session_state.current_chat_id = None
                    st.rerun()

    # ── MAIN ──
    with main_col:
        if not st.session_state.get('current_chat_id'):
            if user_chats:
                st.session_state.current_chat_id = user_chats[0]['id']
            else:
                st.session_state.current_chat_id = storage.create_doubt_chat(user_id)
                st.rerun()

        current_chat = storage.get_doubt_chat_by_id(st.session_state.current_chat_id)
        if not current_chat:
            st.session_state.current_chat_id = None
            st.rerun()

        messages = json.loads(current_chat['messages'])

        # External query handler (from Roadmap)
        if st.session_state.get("doubt_query"):
            query  = st.session_state.doubt_query
            st.session_state.doubt_query = None
            new_id = storage.create_doubt_chat(user_id)
            st.session_state.current_chat_id = new_id
            init_msgs = [{"role":"user","content":query}]
            with st.spinner("Analyzing doubt..."):
                res = agent.chat(init_msgs, use_vision=True)
                if res and hasattr(res,'choices'):
                    init_msgs.append({"role":"assistant","content":res.choices[0].message.content})
            storage.update_doubt_chat(new_id, init_msgs)
            storage.update_chat_title(new_id, query[:30])
            st.rerun()

        # Chat display
        if not messages:
            st.markdown("<div style='height:15vh;'></div>", unsafe_allow_html=True)
            st.markdown("<h1 style='text-align:center;'>How can I help you learn today? 🧠</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; opacity:0.6; font-size:1.1rem;'>Ask a complex question or upload an image of a problem.</p>", unsafe_allow_html=True)
        else:
            for msg in messages:
                is_ai = msg["role"] == "assistant"
                with st.chat_message(msg["role"], avatar="🧠" if is_ai else None):
                    st.markdown(f"<p style='font-size:0.85rem; opacity:0.5; margin-bottom:5px; font-weight:700;'>{'EDUAI' if is_ai else 'YOU'}</p>", unsafe_allow_html=True)
                    st.markdown(msg["content"])
                    if "image" in msg:
                        st.image(msg["image"], use_column_width=False, width=500)

        # Interaction Row
        st.markdown("<div style='height:40px;'></div>", unsafe_allow_html=True)
        c_cam, c_txt = st.columns([1, 15])
        with c_cam:
            with st.popover("📸", help="Upload image"):
                uploaded = st.file_uploader("Upload Image", type=["jpg","jpeg","png"], 
                                            label_visibility="collapsed", 
                                            key=f"cam_{st.session_state.current_chat_id}")
        with c_txt:
            prompt = st.chat_input("Describe your doubt or paste a concept...")

        # Process input
        if (prompt or uploaded):
            interaction_id = f"{prompt}_{uploaded.name if uploaded else ''}_{len(messages)}"
            if st.session_state.get("last_processed_id") != interaction_id:
                st.session_state.last_processed_id = interaction_id
                
                user_msg = {"role":"user","content":prompt or "Please analyze the uploaded image."}
                if uploaded:
                    img_b64 = base64.b64encode(uploaded.read()).decode()
                    user_msg["image"] = f"data:image/jpeg;base64,{img_b64}"
                
                messages.append(user_msg)
                
                with st.chat_message("assistant", avatar="🧠"):
                    st.markdown("<p style='font-size:0.85rem; opacity:0.5; margin-bottom:5px; font-weight:700;'>EDUAI</p>", unsafe_allow_html=True)
                    with st.spinner("Synthesizing answer..."):
                        res = agent.chat(messages, use_vision=True)
                        if res and hasattr(res,'choices'):
                            reply = res.choices[0].message.content
                            st.markdown(reply)
                            messages.append({"role":"assistant","content":reply})
                            storage.update_doubt_chat(st.session_state.current_chat_id, messages)
                            
                            # Handle automatic title naming for new chats
                            if len([m for m in messages if m['role']=='user']) == 1 and current_chat['title'] == 'New Chat':
                                t_res = agent.chat([{"role":"user","content":f"3-word title for: {prompt or 'image doubt'}. No quotes."}])
                                if t_res and hasattr(t_res,'choices'):
                                    storage.update_chat_title(st.session_state.current_chat_id, t_res.choices[0].message.content.strip()[:30])
                            st.rerun()
                        else:
                            st.error("AI connection interrupted. Please try again.")

    # ── JUMP TO BOTTOM UTILITY ──
    ui_helper.render_jump_to_bottom()