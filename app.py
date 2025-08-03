import streamlit as st
import requests
import time

# ---------------------- Auto-reset Logic ----------------------
if "initialized" not in st.session_state:
    st.session_state["rewritten_text"] = ""
    st.session_state["feedback"] = ""
    st.session_state["initialized"] = True

# ---------------------- App Config ----------------------
st.set_page_config(page_title="Feedback Rewriter Assistant", page_icon="✍️", layout="centered")

# ---------------------- Header ----------------------
st.markdown("""
<h1 style='text-align: center;'>✍️ Feedback Rewriter Assistant</h1>
<p style='text-align: center; font-size: 18px;'>🔄 Rewrite your workplace or professional feedback into <b>polished, clear, and impactful</b> messages.</p>
<p style='text-align: center; font-size: 16px;'>🌟 Choose tone, format as email, and optionally translate output to any language.</p>
""", unsafe_allow_html=True)

# ---------------------- Tone Options & Tooltips ----------------------
tone_labels = {
    "managerial": "🧭 Managerial - Balanced and leadership-oriented",
    "empathetic": "💖 Empathetic - Supportive and understanding",
    "formal": "🧾 Formal - Polished and businesslike",
    "friendly": "😊 Friendly - Warm and casual",
    "assertive": "💼 Assertive - Clear and direct"
}

# ---------------------- Input Section ----------------------
st.markdown("### ✏️ Enter Feedback Below")
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🎯 Try Example Feedback"):
        st.session_state.user_input = (
            "You’re always missing deadlines. I can’t keep covering for your delays. It’s affecting the whole project."
        )
with col2:
    if st.button("🔁 Clear All"):
        st.session_state.user_input = ""
        st.session_state.rewritten_text = ""

user_input = st.text_area("", key="user_input", height=200,
                          placeholder="e.g. You're always late submitting your work. This is unacceptable.")

# ---------------------- Tone, Email, Language ----------------------
if user_input.strip():
    st.markdown("### 🎨 Customize Tone and Output")
    selected_tone = st.selectbox("Select Desired Tone:", list(tone_labels.values()))
    format_as_email = st.checkbox("📧 Format as Email")
    enable_translation = st.checkbox("🌍 Translate output into another language")
    if enable_translation:
        selected_language = st.text_input("Which language? (e.g. Hindi, Spanish, Tamil, German)", value="Hindi")
    else:
        selected_language = "English"

    if st.button("🚀 Rewrite Feedback"):
        st.session_state.rewritten_text = ""
        with st.spinner("Rewriting in progress..."):
            try:
                if "OPENROUTER_API_KEY" not in st.secrets:
                    st.error("⚠️ OPENROUTER_API_KEY is missing in Streamlit secrets.")
                    st.stop()

                api_key = st.secrets["OPENROUTER_API_KEY"]
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                tone = selected_tone.split("-")[0].strip().lower()
                lang = selected_language

                if format_as_email:
                    system_prompt = (
    f"You are an expert in writing professional emails. Convert the given workplace feedback into a polite, well-structured email using a {tone} tone. "
    f"Write the final email entirely in {lang} language. Do not include any English explanation or translation. Include a suitable greeting and closing."
)
                else:
                    system_prompt = (
    f"You are an expert in rewriting workplace feedback. Rephrase the given message to sound more {tone} while keeping the original meaning. "
    f"Do not format as an email. Return ONLY the rewritten feedback in {lang} language. Do not include any English explanation or translation."
)

                data = {
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ]
                }

                model_fallbacks = [
                    "mistral/mistral-7b-instruct",
                    "mistralai/mixtral-8x7b-instruct",
                    "nousresearch/nous-capybara-7b",
                    "gryphe/mythomax-l2-13b",
                    "nousresearch/nous-hermes-2-mixtral"
                ]

                for model in model_fallbacks:
                    try:
                        data["model"] = model
                        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
                        if response.status_code == 200:
                            result = response.json()
                            rewritten = result["choices"][0]["message"]["content"].strip()
                            st.session_state.rewritten_text = rewritten
                            break
                        else:
                            time.sleep(1)
                    except Exception:
                        time.sleep(1)

                if not st.session_state.rewritten_text:
                    st.error("⚠️ Could not rewrite the feedback at this time. Please try again.")

            except Exception:
                st.error("⚠️ Unexpected error. Please try again.")

# ---------------------- Display Output ----------------------
if st.session_state.rewritten_text:
    st.markdown("### ✅ Here's Your Refined Feedback:")
    st.success(st.session_state.rewritten_text)
    st.download_button("📋 Download Rewritten Feedback", st.session_state.rewritten_text, file_name="rewritten_feedback.txt", use_container_width=True)

# ---------------------- Optional User Feedback ----------------------
st.markdown("---")
st.text_area("📬 Got suggestions for this tool? We'd love your feedback:", key="feedback", height=100)

# ---------------------- Footer ----------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align: center; font-size: 14px;'>"
    "🛠️ Created by <b>Devi Mudhanagiri</b> · v1.4 · Powered by <a href='https://openrouter.ai' target='_blank'>OpenRouter</a>"
    "</div>",
    unsafe_allow_html=True
)
