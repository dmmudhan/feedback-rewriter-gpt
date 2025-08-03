import streamlit as st
import requests
import time

# ---------------------- Streamlit UI Config ----------------------
st.set_page_config(page_title="Feedback Rewriter Assistant", page_icon="✍️", layout="centered")

# ---------------------- Main Header ----------------------
st.markdown("""
<h1 style='text-align: center;'>✍️ Feedback Rewriter Assistant</h1>
<p style='text-align: center; font-size: 18px;'>🔄 Rewrite your workplace or professional feedback into <b>polished, clear, and impactful</b> messages.</p>
<p style='text-align: center; font-size: 16px;'>🌟 Perfect for anyone looking to refine tone, improve clarity, and ensure constructive communication.</p>
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
selected_model = None
if user_input.strip():
    selected_tone = st.selectbox("🎨 Select Desired Tone", list(tone_labels.values()), index=0)
    selected_model = st.selectbox("🧠 Choose Model", [
        "mistral/mistral-7b-instruct",
        "openchat/openchat-3.5-0106",
        "nous-hermes/nous-hermes-2-mistral"
    ])

# ---------------------- Rewrite Button ----------------------
if user_input and selected_tone and selected_model:
    if st.button("🚀 Rewrite Feedback"):
        st.session_state.rewritten_text = ""
        with st.spinner("Rewriting in progress..."):
            try:
                # Check API key
                if "OPENROUTER_API_KEY" not in st.secrets:
                    st.error("⚠️ OPENROUTER_API_KEY is missing. Please set it in Streamlit secrets.")
                    st.stop()

                api_key = st.secrets["OPENROUTER_API_KEY"]
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
                    "model": selected_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_input}
                    ]
                }

                retries = 3
                success = False
                for attempt in range(retries):
                    try:
                        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
                        if response.status_code == 200:
                            success = True
                            break
                        else:
                            st.warning(f"Attempt {attempt+1} failed: {response.status_code} - {response.text}")
                            time.sleep(2)
                    except requests.exceptions.RequestException as e:
                        st.warning(f"Attempt {attempt+1} failed: {e}")
                        time.sleep(2)

                if not success:
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
