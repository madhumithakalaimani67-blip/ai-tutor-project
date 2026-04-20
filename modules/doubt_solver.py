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
        st.markdown("## 🧠 Solver")
        if st.button("➕ New Chat", use_container_width=True, type="primary", key="new_chat_btn"):
            new_id = storage.create_doubt_chat(user_id)
            st.session_state.current_chat_id   = new_id
            st.session_state.last_processed_id = None
            st.rerun()
        st.markdown("---")
        search = st.text_input("🔍", placeholder="Search chats...", label_visibility="collapsed", key="doubt_search")
        filtered = [c for c in user_chats if search.lower() in (c['title'] or '').lower()] if search else user_chats
        for chat in filtered:
            chat_id = chat['id']
            title   = chat['title'] if chat['title'] != 'New Chat' else f"Chat {chat_id}"
            active  = st.session_state.get('current_chat_id') == chat_id
            c1, c2  = st.columns([5, 1])
            with c1:
                if st.button(f"💬 {title[:16]}", key=f"chat_{chat_id}",
                             use_container_width=True,
                             type="primary" if active else "secondary"):
                    st.session_state.current_chat_id   = chat_id
                    st.session_state.last_processed_id = None
                    st.rerun()
            with c2:
                if st.button("🗑", key=f"del_{chat_id}"):
                    storage.delete_doubt_chat(chat_id)
                    if st.session_state.get('current_chat_id') == chat_id:
                        st.session_state.current_chat_id = None
                    st.rerun()

    # ── MAIN ──
    with main_col:
        # Session init
        if not st.session_state.get('current_chat_id'):
            if user_chats:
                st.session_state.current_chat_id = user_chats[0]['id']
            else:
                new_id = storage.create_doubt_chat(user_id)
                st.session_state.current_chat_id = new_id
                st.rerun()

        current_chat = storage.get_doubt_chat_by_id(st.session_state.current_chat_id)
        if not current_chat:
            st.session_state.current_chat_id = None
            st.rerun()

        messages = json.loads(current_chat['messages'])

        # External query from roadmap links
        if st.session_state.get("doubt_query"):
            query  = st.session_state.doubt_query
            st.session_state.doubt_query = None
            new_id = storage.create_doubt_chat(user_id)
            st.session_state.current_chat_id = new_id
            init_msgs = [{"role":"user","content":query}]
            with st.spinner("Solving..."):
                res = agent.chat(init_msgs, use_vision=True)
                if res and hasattr(res,'choices'):
                    init_msgs.append({"role":"assistant","content":res.choices[0].message.content})
            storage.update_doubt_chat(new_id, init_msgs)
            storage.update_chat_title(new_id, query[:30])
            st.rerun()

        # Chat display
        if not messages:
            st.markdown("<div style='height:15vh;'></div>", unsafe_allow_html=True)
            st.markdown("<h2 style='text-align:center;'>What can I help you solve? 🧠</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center;opacity:0.6;'>Ask anything or upload a photo of your problem.</p>", unsafe_allow_html=True)
        else:
            for msg in messages:
                avatar = "🧠" if msg["role"] == "assistant" else None
                with st.chat_message(msg["role"], avatar=avatar):
                    st.markdown(f"**{'EDUAI' if msg['role']=='assistant' else 'You'}**")
                    st.markdown(msg["content"])
                    if "image" in msg:
                        st.image(msg["image"], width=400)

        # Input row
        c_cam, c_txt = st.columns([1, 10])
        with c_cam:
            with st.popover("📸"):
                st.caption("Upload problem photo")
                uploaded = st.file_uploader("Image", type=["jpg","jpeg","png"],
                                            label_visibility="collapsed",
                                            key=f"up_{st.session_state.current_chat_id}")
        with c_txt:
            prompt = st.chat_input("Ask me anything...")

        interaction_id = f"{prompt}_{uploaded.name if uploaded else ''}_{len(messages)}"
        if (prompt or uploaded) and st.session_state.get("last_processed_id") != interaction_id:
            st.session_state.last_processed_id = interaction_id
            if uploaded:
                img_b64 = base64.b64encode(uploaded.read()).decode()
                messages.append({"role":"user","content":prompt or "Solve this image","image":f"data:image/jpeg;base64,{img_b64}"})
            else:
                messages.append({"role":"user","content":prompt})

            with st.chat_message("assistant", avatar="🧠"):
                st.markdown("**EDUAI**")
                with st.spinner("Thinking..."):
                    res = agent.chat(messages, use_vision=True)
                    if res and hasattr(res,'choices'):
                        reply = res.choices[0].message.content
                        st.markdown(reply)
                        messages.append({"role":"assistant","content":reply})
                    else:
                        st.error("Something went wrong. Try again.")

            storage.update_doubt_chat(st.session_state.current_chat_id, messages)
            if len([m for m in messages if m['role']=='user'])==1 and current_chat['title']=='New Chat':
                res2 = agent.chat([{"role":"user","content":f"3-word title for: {prompt or 'image doubt'}. No quotes."}])
                if res2 and hasattr(res2,'choices'):
                    storage.update_chat_title(st.session_state.current_chat_id, res2.choices[0].message.content.strip()[:30])
            st.rerun()