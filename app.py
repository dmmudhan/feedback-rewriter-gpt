import streamlit as st
import requests
import time

# ---------------------- Soft Reset on First Load ----------------------
if "initialized" not in st.session_state:
    st.session_state["rewritten_text"] = ""
    st.session_state["initialized"] = True

# ---------------------- Streamlit UI Config ----------------------
st.set_page_config(page_title="Feedback Rewriter Assistant", page_icon="✍️", layout="centered")

# ---------------------- Main Header ----------------------
st.markdown("""
<h1 style='text-align: center;'>✍️ Feedback Rewriter Assistant</h1>
<p style='text-align: center; font-size: 18px;'>🔄 Rewrite your workplace or professional feedback into <b>polished, clear, and impactful</b> messages.</p>
<p style='text-align: center; font-size: 16px;'>🌟 Perfect for anyone looking to refine tone, improve clarity, and ensure constructive communication.</p>
""", unsafe_allow_html=True)

# Add spacing before input
st.markdown("<br>", unsafe_allow_html=True)

# ---------------------- Session State Init ----------------------
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

# Show tone + email toggle only after input
selected_tone = None
format_as_email = False

if user_input.strip():
    selected_tone = st.selectbox("🎨 Select Desired Tone", list(tone_labels.values()), index=0)
    format_as_email = st.checkbox("📧 Format output as email", value=False)

# ---------------------- Rewrite Button ----------------------
if user_input and selected_tone is not None:
    if st.button("🚀 Rewrite Feedback"):
        st.session_state.rewritten_text = ""
        with st.spinner("Rewriting in progress..."):
            try:
                if "OPENROUTER_API_KEY" not in st.secrets:
                    st.error("⚠️ OPENROUTER_API_KEY is missing. Please set it in Streamlit secrets.")
                    st.stop()

                api_key = st.secrets["OPENROUTER_API_KEY"]
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                # Adjust prompt based on checkbox
                if format_as_email:
                    system_prompt = (
                        f"You are an expert in writing professional emails. "
                        f"Convert the given workplace feedback into a polite, well-structured email using a {selected_tone.lower()} tone. "
                        f"Preserve the original intent. Include a suitable greeting and closing."
                    )
                else:
                    system_prompt = (
                        f"You are an expert in rewriting workplace feedback. "
                        f"Rephrase the given message to sound more {selected_tone.lower()} while keeping the original meaning. "
                        f"Do not format the response as an email. Just return the improved version in a clear, professional paragraph."
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

                success = False
                for model in model_fallbacks:
                    try:
                        data["model"] = model
                        response = requests.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            json=data,
                            timeout=30
                        )

                        if response.status_code == 200:
                            result = response.json()
                            rewritten = result["choices"][0]["message"]["content"]
                            st.session_state.rewritten_text = rewritten.strip()
                            success = True
                            break
                        else:
                            time.sleep(1)

                    except Exception:
                        time.sleep(1)

                if not success:
                    st.error("⚠️ Could not rewrite the feedback at this time. Please try again shortly.")

            except Exception:
                st.error("⚠️ Unexpected error. Please refresh and try again.")

# ---------------------- Display Output ----------------------
if st.session_state.rewritten_text:
    st.markdown("### ✅ Here's Your Refined Feedback:")
    st.success(st.session_state.rewritten_text)

    # Copy to clipboard using st.code component (streamlit-safe)
    st.code(st.session_state.rewritten_text, language="markdown")

# ---------------------- Footer ----------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align: center; font-size: 14px;'>"
    "🛠️ Created by <b>Devi M</b> · v1.3 · Powered by <a href='https://openrouter.ai' target='_blank'>OpenRouter</a>"
    "</div>",
    unsafe_allow_html=True
)
