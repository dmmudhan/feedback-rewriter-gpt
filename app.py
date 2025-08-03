import streamlit as st
import requests

# --- Page Config ---
st.set_page_config(
    page_title="Feedback Rewriter Assistant",
    page_icon="✍️",
    layout="centered"
)

# --- Header ---
st.markdown("<h1 style='text-align: center;'>✍️ Feedback Rewriter Assistant</h1>", unsafe_allow_html=True)

# --- Tagline with Better Icons ---
st.markdown("""
<div style='text-align: center; font-size: 17px; line-height: 1.6; padding-top: 5px;'>
💬 Got rough feedback?<br>
🎯 Let AI help you rewrite it to be:<br>
✅ <strong>Professional</strong> &nbsp; 🤝 <strong>Friendly</strong> &nbsp; 💼 <strong>Assertive</strong>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# --- Prompt Template ---
def generate_prompt(text, tone):
    return f"""Rewrite the following workplace feedback in a {tone.lower()} tone, keeping the core message intact:

### Feedback:
{text}

### {tone} Rewrite:"""

# --- API Call Function ---
def rewrite_feedback(user_input, tone):
    try:
        headers = {
            "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "openchat/openchat-7b:free",
            "messages": [
                {"role": "user", "content": generate_prompt(user_input, tone)}
            ]
        }

        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            return f"⚠️ API Error {response.status_code}: {response.text}"

    except Exception as e:
        return f"⚠️ An error occurred: {str(e)}"

# --- UI Components ---
feedback_text = st.text_area("📥 Paste your raw feedback here 👇", height=150)

if feedback_text:
    selected_tone = st.selectbox("🎯 Choose your desired tone:", ["Formal", "Friendly", "Assertive"])

    if st.button("🔁 Rewrite Feedback"):
        with st.spinner("🤖 Rewriting your message..."):
            rewritten = rewrite_feedback(feedback_text, selected_tone)
            st.markdown("#### ✍️ Rewritten Feedback:")
            st.success(rewritten)
