import streamlit as st
import requests

st.set_page_config(page_title="Feedback Rewriter Assistant", page_icon="📝")

# 🚀 Smart Header
st.markdown("""
# ✨ Feedback Rewriter Assistant  
**Transform raw feedback into professional tone – in seconds.**  
Your go-to rewriting assistant for polished workplace communication.
""")

# 🎯 Prompt tone options
tone_options = ["Formal", "Friendly", "Assertive"]

# 🎛️ Sidebar tone selection
selected_tone = st.selectbox("Select Desired Tone", tone_options, index=0)

# 📝 Raw feedback input
raw_feedback = st.text_area("Paste your raw feedback here:", height=200)

# 🔁 Rewrite button
if st.button("Rewrite Feedback"):
    if not raw_feedback.strip():
        st.warning("Please enter some feedback to rewrite.")
    else:
        # 🌀 Show spinner while processing
        with st.spinner("Rewriting your feedback..."):
            prompt = f"""Rewrite the following feedback in a {selected_tone.lower()} tone:\n\n"{raw_feedback}"\n\nMake sure it sounds natural and professional."""
            try:
                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "openchat/openchat-3.5-1210",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ]
                    }
                )
                result = response.json()
                rewritten_text = result["choices"][0]["message"]["content"].strip()

                # 💬 Display rewritten feedback
                st.markdown("### ✍️ Rewritten Feedback")
                st.success(rewritten_text)

            except Exception as e:
                st.error(f"An error occurred: {e}")
