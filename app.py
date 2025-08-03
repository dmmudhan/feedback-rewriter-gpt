
import streamlit as st
import requests
import time

# ---------------------- Streamlit UI Config ----------------------
st.set_page_config(page_title="Feedback Rewriter Assistant", page_icon="✍️", layout="centered")

# ---------------------- Main Header ----------------------
st.markdown("""
<h1 style='text-align: center;'>✍️ Feedback Rewriter Assistant</h1>
<p style='text-align: center; font-size: 18px;'>🔄 Transform your workplace feedback into <b>professional, clear, and constructive</b> messages.</p>
<p style='text-align: center; font-size: 16px;'>🎯 Ideal for HR, managers, and team leads looking to refine tone and intent.</p>
""", unsafe_allow_html=True)

# ---------------------- Session State ----------------------
if "rewritten_text" not in st.session_state:
    st.session_state.rewritten_text = ""

# ---------------------- Tone Options ----------------------
tone_labels = {
    "managerial": "🧭 Managerial",
    "empathetic": "💖 Empathetic",
    "formal": "🧾 Formal",
    "friendly": "😊 Friendly",
    "assertive": "💼 Assertive"
}

# ---------------------- Input Text ----------------------
user_input = st.text_area("✏️ Enter your raw feedback text here:", height=200)

# Show tone dropdown only after input
selected_tone = None
if user_input.strip():
    selected_tone = st.selectbox("🎨 Select Desired Tone", list(tone_labels.values()), index=0)

# ---------------------- Rewrite Button ----------------------
if user_input and selected_tone:
    if st.button("🚀 Rewrite Feedback"):
        st.session_state.rewritten_text = ""
        with st.spinner("Rewriting in progress..."):
            try:
                api_key = st.secrets["OPENROUTER_API_KEY"]
                model = "mistral/mistral-7b-instruct"
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                system_prompt = (
                    f"You are an expert communication coach. "
                    f"Your job is to rewrite raw workplace feedback in a more {selected_tone.lower()} tone. "
                    f"Keep the message professional, clear, and concise. Remove any harsh or offensive wording. "
                    f"Preserve the original intent while improving tone and delivery."
                )

                data = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ]
                }

                retries = 2
                for attempt in range(retries):
                    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
                    if response.status_code == 200:
                        break
                    time.sleep(1)
                else:
                    st.error("⚠️ Failed after retries. Please try again later.")
                    st.stop()

                result = response.json()
                rewritten = result["choices"][0]["message"]["content"]
                st.session_state.rewritten_text = rewritten.strip()

            except requests.exceptions.Timeout:
                st.error("⏳ Request timed out. Please try again.")
            except Exception as e:
                st.error(f"⚠️ An error occurred: {e}")

# ---------------------- Display Output ----------------------
if st.session_state.rewritten_text:
    st.markdown("### ✅ Rewritten Feedback:")
    st.success(st.session_state.rewritten_text)
