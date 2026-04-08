import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class EDUAIAgent:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            api_key = st.secrets.get("GROQ_API_KEY", "")
        
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"
        self.vision_model = "llama-3.2-11b-vision-preview"

    def get_system_prompt(self, user_profile=None):
        profile_context = ""
        if user_profile:
            profile_context = f"""
            USER CONTEXT:
            - Name: {user_profile.get('name', 'Student')}
            - Age: {user_profile.get('age', '')}
            - Interests: {user_profile.get('interests', '')}
            - Learning Style: {user_profile.get('learning_style', 'Mixed')}
            - Daily Time: {user_profile.get('daily_time', '1 hour')}
            """

        return f"""You are EDUAI, an AI study assistant.

{profile_context}

RULES:
- Be concise and direct. No unnecessary motivation or fluff.
- Give structured, actionable answers.
- For doubts: solve step-by-step, explain clearly.
- For image questions: analyze and solve step-by-step.
- Use markdown formatting for readability."""

    def chat(self, messages, user_profile=None, stream=False, use_vision=False):
        system_msg = {"role": "system", "content": self.get_system_prompt(user_profile)}
        
        # Determine model
        model_to_use = self.vision_model if use_vision else self.model
        
        # Format messages for the Vision API if necessary
        formatted_messages = [system_msg]
        if use_vision:
            for m in messages:
                content_parts = [{"type": "text", "text": m["content"]}]
                if "image" in m:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": m["image"]}
                    })
                formatted_messages.append({"role": m["role"], "content": content_parts})
        else:
            formatted_messages += messages

        try:
            response = self.client.chat.completions.create(
                model=model_to_use,
                messages=formatted_messages,
                temperature=0.7,
                max_completion_tokens=2048,
                stream=stream
            )
            return response
        except Exception as e:
            st.error(f"Groq API Error: {e}")
            return None

    def analyze_image(self, prompt, image_base64, user_profile=None):
        """Single-shot image analysis (deprecated in favor of vision-aware chat)"""
        return self.chat([{"role": "user", "content": prompt, "image": f"data:image/jpeg;base64,{image_base64}"}], user_profile, use_vision=True)

@st.cache_resource
def get_ai_agent():
    return EDUAIAgent()
