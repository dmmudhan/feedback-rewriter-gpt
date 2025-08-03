
import streamlit as st
import requests
import json
import os

st.set_page_config(page_title="Feedback Rewriter Assistant", page_icon="✍️", layout="centered")

st.title("✍️ Feedback Rewriter Assistant")
st.markdown("Transform raw feedback into clear, respectful communication.")

st.markdown("#### 🧭 Choose the Tone of Your Message")
tone = st.selectbox("Select tone", ["Friendly", "Formal", "Assertive", "Empathetic", "Managerial"])

st.markdown("#### 📝 Enter Your Raw Feedback")
user_input = st.text_area("Your raw message", height=200)

if st.button("✍️ Rewrite Feedback"):
    if not user_input:
        st.warning("Please enter your feedback first.")
    else:
        with st.spinner("Rewriting your feedback..."):
            try:
                prompt = f"""
You are a professional writing assistant. Rewrite the following feedback in a {tone.lower()} tone:
"""{user_input}"""

Ensure it sounds natural, respectful, and easy to understand.
"""

                headers = {
                    "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": "openrouter/mistral-7b-instruct",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7
                }

                # Retry logic
                retries = 1
                for attempt in range(retries + 1):
                    try:
                        response = requests.post(
                            "https://openrouter.ai/api/v1/chat/completions",
                            headers=headers,
                            data=json.dumps(payload),
                            timeout=60  # increased timeout
                        )
                        response.raise_for_status()
                        rewritten = response.json()["choices"][0]["message"]["content"]
                        break  # break if successful
                    except requests.exceptions.Timeout as e:
                        if attempt == retries:
                            raise e

                st.markdown("### ✨ Rewritten Feedback")
                st.success(rewritten.strip())

            except Exception as e:
                st.error(f"⚠️ An error occurred: {e}")
