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

        # Chat display
        if not messages:
            st.markdown("<div style='height:15vh;'></div>", unsafe_allow_html=True)
            st.markdown("<h1 style='text-align:center;'>How can I help you learn today? 🧠</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; opacity:0.6; font-size:1.1rem;'>Ask a complex question or upload images of a problem.</p>", unsafe_allow_html=True)
        else:
            for msg in messages:
                is_ai = msg["role"] == "assistant"
                with st.chat_message(msg["role"], avatar="🧠" if is_ai else None):
                    st.markdown(f"<p style='font-size:0.85rem; opacity:0.5; margin-bottom:5px; font-weight:700;'>{'EDUAI' if is_ai else 'YOU'}</p>", unsafe_allow_html=True)
                    st.markdown(msg["content"])
                    # Handle legacy single image
                    if "image" in msg:
                        st.image(msg["image"], use_column_width=False, width=500)
                    # Handle multiple images
                    if "images" in msg:
                        for img_url in msg["images"]:
                            st.image(img_url, use_column_width=False, width=500)

        # ── Anchor for Jump to Bottom ──
        st.markdown("<div id='chat-bottom' style='height:1px;'></div>", unsafe_allow_html=True)
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

        # ── Handle Multiple Image Staging ─────────────────────────────────────
        staged_key = f"staged_imgs_{st.session_state.current_chat_id}"
        if staged_key not in st.session_state:
            st.session_state[staged_key] = []
        
        # Interaction Row
        c_cam, c_txt = st.columns([1, 15])
        with c_cam:
            with st.popover("📸", help="Upload images"):
                upload_key = f"cam_{st.session_state.current_chat_id}_{st.session_state.get('upload_counter', 0)}"
                # Set accept_multiple_files=True to allow choosing multiple files!
                uploaded_files = st.file_uploader("Upload Image(s)", type=["jpg","jpeg","png"], accept_multiple_files=True, label_visibility="collapsed", key=upload_key)
                
                if uploaded_files:
                    for f in uploaded_files:
                        # Prevent duplicate file additions
                        if not any(img["name"] == f.name for img in st.session_state[staged_key]):
                            img_b64 = base64.b64encode(f.read()).decode()
                            img_url = f"data:image/{f.type.split('/')[-1]};base64,{img_b64}"
                            st.session_state[staged_key].append({
                                "name": f.name,
                                "url": img_url
                            })
                    # Clear widget state to prevent loops
                    st.session_state.upload_counter = st.session_state.get('upload_counter', 0) + 1
                    st.rerun()

        # Display staged image previews side-by-side with separate Discard actions
        staged_list = st.session_state.get(staged_key, [])
        if staged_list:
            st.markdown("<p style='font-size:0.85rem; color:#94a3b8; font-weight:700; margin-bottom:5px;'>🖼️ STAGED IMAGES</p>", unsafe_allow_html=True)
            cols = st.columns(max(1, len(staged_list)))
            for idx, img in enumerate(staged_list):
                with cols[idx]:
                    # Shorten name for premium UI layout
                    short_name = img['name'][:15] + "..." if len(img['name']) > 18 else img['name']
                    st.image(img['url'], width=100)
                    st.caption(short_name)
                    if st.button("❌ Discard", key=f"discard_{idx}"):
                        st.session_state[staged_key].pop(idx)
                        st.rerun()

        with c_txt:
            prompt = st.chat_input("Describe your doubt or ask a question about the uploaded image(s)...")

        # ── Handle Submission ─────────────────────────────────────────────────
        if prompt:
            staged_names = "-".join([img["name"] for img in staged_list])
            interaction_id = f"{prompt}_{staged_names}_{len(messages)}"
            
            if st.session_state.get("last_processed_id") != interaction_id:
                st.session_state.last_processed_id = interaction_id
                
                user_msg = {"role": "user", "content": prompt}
                if staged_list:
                    # Construct multimodal content with prompt text + all uploaded images
                    content_list = [{"type": "text", "text": prompt}]
                    for img in staged_list:
                        content_list.append({"type": "image_url", "image_url": {"url": img["url"]}})
                    user_msg["content"] = content_list
                
                messages.append(user_msg)
                
                # Build clean API messages — strip any raw 'image' or 'images' keys from history
                api_messages = []
                for m in messages:
                    if isinstance(m.get("content"), list):
                        api_messages.append({"role": m["role"], "content": m["content"]})
                    elif "images" in m:
                        content_list = [{"type": "text", "text": m.get("content", "")}]
                        for img_url in m["images"]:
                            content_list.append({"type": "image_url", "image_url": {"url": img_url}})
                        api_messages.append({"role": m["role"], "content": content_list})
                    elif "image" in m:
                        img_content = [
                            {"type": "text", "text": m.get("content", "")},
                            {"type": "image_url", "image_url": {"url": m["image"]}}
                        ]
                        api_messages.append({"role": m["role"], "content": img_content})
                    else:
                        api_messages.append({"role": m["role"], "content": m.get("content", "")})
                
                # Manual display for instant feedback
                with st.chat_message("assistant", avatar="🧠"):
                    # Use vision model if the current staged list has images OR if any message in the chat history has images
                    use_vis = (len(staged_list) > 0) or any("image" in m or "images" in m for m in messages)
                    res = agent.chat(api_messages, use_vision=use_vis)
                    
                    if res and hasattr(res, 'choices'):
                        reply = res.choices[0].message.content
                        st.markdown(reply)
                            
                        # Save with images stored separately for display only
                        save_msg = {"role": "user", "content": prompt}
                        if staged_list:
                            save_msg["images"] = [img["url"] for img in staged_list]
                        messages[-1] = save_msg  # replace multimodal list with storable version
                        messages.append({"role": "assistant", "content": reply})
                        
                        storage.update_doubt_chat(st.session_state.current_chat_id, messages)
                        
                        # Clear staged images list after successful send
                        if staged_key in st.session_state:
                            st.session_state[staged_key] = []
                        
                        if len([m for m in messages if m['role']=='user']) == 1 and current_chat['title'] == 'New Chat':
                            t_res = agent.chat([{"role":"user","content":f"3-word title for: {prompt}. No quotes."}])
                            if t_res and hasattr(t_res,'choices'):
                                storage.update_chat_title(st.session_state.current_chat_id, t_res.choices[0].message.content.strip()[:30])
                        st.rerun()
                    else:
                        st.error("AI connection interrupted. Please try again.")

    # ── JUMP TO BOTTOM UTILITY ──
    ui_helper.render_jump_to_bottom()