import os
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ── Optional Gemini import ─────────────────────────────────────────────────
try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False


class EDUAIAgent:
    def __init__(self):
        # ── Groq setup ──────────────────────────────────────────────────────
        groq_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
        self.client = Groq(api_key=groq_key)
        self.model = "llama-3.3-70b-versatile"
        self.vision_model = "llama-3.2-11b-vision-preview"
        self.groq_fallbacks = [
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]

        # ── Gemini setup ────────────────────────────────────────────────────
        gemini_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", "")
        self.gemini_available = False
        if _GEMINI_AVAILABLE and gemini_key and gemini_key != "YOUR_GEMINI_KEY_HERE":
            try:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")
                self.gemini_available = True
            except Exception:
                pass

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

    def _call_gemini(self, messages, system_prompt):
        """Convert messages to Gemini format and call the API."""
        if not self.gemini_available:
            return None
        try:
            history_text = system_prompt + "\n\n"
            for m in messages:
                role = "User" if m["role"] == "user" else "Assistant"
                content = m.get("content", "")
                # Handle multimodal content — extract text only
                if isinstance(content, list):
                    content = " ".join(
                        part.get("text", "") for part in content
                        if isinstance(part, dict) and part.get("type") == "text"
                    )
                history_text += f"{role}: {content}\n"
            history_text += "Assistant:"

            response = self.gemini_model.generate_content(history_text)

            # Wrap in a Groq-compatible response shape
            class _GeminiResp:
                class _Choice:
                    class _Msg:
                        def __init__(self, text):
                            self.content = text
                    def __init__(self, text):
                        self.message = self._Msg(text)
                def __init__(self, text):
                    self.choices = [self._Choice(text)]

            return _GeminiResp(response.text)
        except Exception:
            return None

    def chat(self, messages, user_profile=None, stream=False, use_vision=False):
        system_prompt = self.get_system_prompt(user_profile)
        system_msg = {"role": "system", "content": system_prompt}
        model_to_use = self.vision_model if use_vision else self.model

        # Keep last 5 messages to manage token usage
        if len(messages) > 5:
            messages = messages[-5:]

        # Format messages: convert 'image' key into Groq multimodal format
        formatted_messages = [system_msg]
        for msg in messages:
            if "image" in msg and use_vision:
                content = []
                if msg.get("content"):
                    content.append({"type": "text", "text": msg["content"]})
                content.append({
                    "type": "image_url",
                    "image_url": {"url": msg["image"]}
                })
                formatted_messages.append({"role": msg["role"], "content": content})
            else:
                clean = {"role": msg["role"], "content": msg.get("content", "")}
                formatted_messages.append(clean)

        # ── 1. Try primary Groq model ───────────────────────────────────────
        err_str = ""
        try:
            return self.client.chat.completions.create(
                model=model_to_use,
                messages=formatted_messages,
                temperature=0.7,
                max_completion_tokens=2048,
                stream=stream
            )
        except Exception as e:
            err_str = str(e).lower()

        # ── 2. Try Groq fallback models ────────────────────────────────────
        if "429" in err_str or "rate" in err_str or "limit" in err_str or "503" in err_str:
            for fallback in self.groq_fallbacks:
                try:
                    return self.client.chat.completions.create(
                        model=fallback,
                        messages=formatted_messages,
                        temperature=0.7,
                        max_completion_tokens=1024
                    )
                except Exception:
                    continue

            # ── 3. Try Gemini as final fallback ────────────────────────────
            if self.gemini_available:
                result = self._call_gemini(messages, system_prompt)
                if result:
                    return result

            st.warning("⏳ **AI is temporarily at capacity.** All models are busy. Please wait 1–2 minutes and try again.")

        elif "service unavailable" in err_str or "overloaded" in err_str:
            if self.gemini_available:
                result = self._call_gemini(messages, system_prompt)
                if result:
                    return result
            st.warning("🔧 **AI service is temporarily overloaded.** Please try again in a moment.")

        elif "401" in err_str or "invalid_api_key" in err_str or "authentication" in err_str:
            st.error("🔑 **API Key Error.** The AI service key is invalid or expired.")

        elif "400" in err_str and "image" in err_str:
            st.error("🖼️ **Image not supported by this model.** Please describe your question in text instead.")

        elif "413" in err_str or "too large" in err_str:
            st.warning("📦 **Message too long.** Please start a new chat or shorten your question.")

        elif "connection" in err_str or "timeout" in err_str or "network" in err_str:
            st.warning("🌐 **Connection issue.** Please check your internet and try again.")

        else:
            st.warning("🤖 **AI is temporarily unavailable.** Please try again in a moment.")

        return None

    def analyze_image(self, prompt, image_base64, user_profile=None):
        """Single-shot image analysis."""
        return self.chat(
            [{"role": "user", "content": prompt, "image": f"data:image/jpeg;base64,{image_base64}"}],
            user_profile, use_vision=True
        )


@st.cache_resource
def get_ai_agent():
    return EDUAIAgent()
