import streamlit as st
import json
import base64
from utils import ai_helper, storage

def main():
    user_id = st.session_state.get('user_id')
    agent = ai_helper.get_ai_agent()

    # --- SIDEBAR: ChatGPT-Style Persistence ---
    with st.sidebar:
        # 1. Search Bar
        st.write("<div style='height: 1.5rem'></div>", unsafe_allow_html=True)
        st.text_input("🔍 Search chats", placeholder="Search...", label_visibility="collapsed")
        
        # 2. New Chat Button (Prominent)
        if st.button("➕ New chat", use_container_width=True, key="new_chat_btn_v7"):
            new_id = storage.create_doubt_chat(user_id)
            st.session_state.current_chat_id = new_id
            st.session_state.last_processed_id = None
            st.rerun()
        
        st.markdown("---")
        st.markdown("<p style='opacity: 0.5; font-size: 0.8rem; margin-bottom: 0.5rem;'>YOUR CHATS</p>", unsafe_allow_html=True)
        
        # 3. Chat History
        user_chats = storage.get_user_doubt_chats(user_id)
        for chat in user_chats:
            chat_id = chat['id']
            chat_title = chat['title'] if chat['title'] != 'New Chat' else f"Chat {chat_id}"
            is_active = st.session_state.get('current_chat_id') == chat_id
            
            c_link, c_del = st.columns([5, 1])
            with c_link:
                if st.button(f"💬 {chat_title[:20]}", key=f"chat_nav_{chat_id}", use_container_width=True, type="secondary" if not is_active else "primary"):
                    st.session_state.current_chat_id = chat_id
                    st.session_state.last_processed_id = None
                    st.rerun()
            with c_del:
                if st.button("🗑️", key=f"chat_del_{chat_id}"):
                    storage.delete_doubt_chat(chat_id)
                    if st.session_state.get('current_chat_id') == chat_id:
                        st.session_state.current_chat_id = None
                    st.rerun()

    # --- SESSION RECOVERY ---
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

    # --- MAIN VIEW ---
    if not messages:
        st.markdown("<div style='height: 20vh;'></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; font-size: 3.5rem; opacity: 0.95; font-weight: 700; margin-bottom: 0.5rem;'>What mission can I help you solve?</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; opacity: 0.6; font-size: 1.2rem;'>Ask anything. Upload details. Let's solve it.</p>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
        for msg in messages:
            avatar = "🧠" if msg["role"] == "assistant" else None
            name = "EDUAI" if msg["role"] == "assistant" else "Learner"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(f"**{name}**")
                st.markdown(msg["content"])
                if "image" in msg:
                    st.image(msg["image"], width=400)

    # --- STICKY FOOTER INPUT ---
    st.markdown("<div style='height: 15vh;'></div>", unsafe_allow_html=True)
    _, mid_bar, _ = st.columns([1, 4, 1])
    with mid_bar:
        # Integrated Camera Icon inside popover
        c_cam, c_txt = st.columns([1, 10])
        with c_cam:
            with st.popover("📸"):
                st.caption("Upload problem photo")
                uploaded_file = st.file_uploader("Select Image", type=["jpg", "jpeg", "png"], label_visibility="collapsed", key=f"up_{st.session_state.current_chat_id}")
        with c_txt:
            prompt = st.chat_input("Ask me anything...")

    # --- INTERACTION GUARD & PROCESSING ---
    interaction_id = f"{prompt}_{uploaded_file.name if uploaded_file else ''}_{len(messages)}"
    if (prompt or uploaded_file) and st.session_state.get("last_processed_id") != interaction_id:
        st.session_state.last_processed_id = interaction_id
        
        # 1. Update List
        img_b64 = None
        if uploaded_file:
            img_b64 = base64.b64encode(uploaded_file.read()).decode()
            messages.append({"role": "user", "content": prompt or "Image Answer Request", "image": f"data:image/jpeg;base64,{img_b64}"})
        else:
            messages.append({"role": "user", "content": prompt})

        # 2. Get Response
        with st.chat_message("assistant", avatar="🧠"):
            st.markdown(f"**EDUAI**")
            with st.spinner("AI Engineering Answer..."):
                # Always use vision-aware chat for consistency
                full_res = agent.chat(messages, use_vision=True)
                if full_res and hasattr(full_res, 'choices'):
                    reply = full_res.choices[0].message.content
                    st.markdown(reply)
                    messages.append({"role": "assistant", "content": reply})
                else:
                    st.error("I'm sorry, I encountered a minor hiccup. Please try again.")

        # 3. Auto-Save & Auto-Title
        storage.update_doubt_chat(st.session_state.current_chat_id, messages)
        
        user_msg_count = len([m for m in messages if m['role'] == 'user'])
        if user_msg_count == 1 and (current_chat['title'] == 'New Chat'):
            title_p = f"Create a short 3-word title for this doubt: {prompt or 'Image doubt'}. No quotes."
            title_res = agent.chat([{"role": "user", "content": title_p}])
            if title_res and hasattr(title_res, 'choices'):
                new_title = title_res.choices[0].message.content.strip()[:30]
                storage.update_chat_title(st.session_state.current_chat_id, new_title)
        
        st.rerun()

if __name__ == "__main__":
    main()