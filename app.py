import streamlit as st
import openai
from dotenv import load_dotenv
import os

# Load environment variables

load\_dotenv()

st.set\_page\_config(page\_title="Feedback Rewriter Assistant", page\_icon="✍️")
st.markdown(""" <h3 style='text-align: center;'>Got rough feedback?</h3> <h5 style='text-align: center;'>🎯 Reframe it for a more professional impact:</h5> <div style='text-align: center; font-size: 18px;'>
✅ <b>Managerial</b>  🤝 <b>Friendly</b>  🧠 <b>Constructive</b> </div> <hr style='margin-top: 20px;'>
""", unsafe\_allow\_html=True)

# Input text

user\_input = st.text\_area("📥 Paste your raw feedback here 👇", height=150)

# Show tone dropdown only if there's input

if user\_input.strip():
tone = st.selectbox("🎯 Choose your desired tone:", \["Managerial", "Friendly", "Constructive"])
else:
tone = None

# Submit button

submit = st.button("🔁 Rewrite Feedback")

# Secrets

api\_key = st.secrets.get("OPENROUTER\_API\_KEY", os.getenv("OPENROUTER\_API\_KEY"))

if submit and user\_input and tone:
try:
openai.api\_key = api\_key
openai.api\_base = "[https://openrouter.ai/api/v1](https://openrouter.ai/api/v1)"

```
    prompt = (
        f"You are a feedback rewriting assistant. Your job is to convert the user's raw workplace feedback "
        f"into a more {tone.lower()} and professional tone, while keeping the core message intact.\n\n"
        f"Raw feedback: {user_input}\n\n"
        f"Rewritten Feedback:"
    )

    response = openai.ChatCompletion.create(
        model="mistralai/mistral-7b-instruct",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        timeout=10  # Timeout added
    )

    rewritten = response.choices[0].message.content

    st.markdown("""
        <h4>📝 Rewritten Feedback:</h4>
    """, unsafe_allow_html=True)
    st.success(rewritten)

except openai.error.Timeout:
    st.error("⚠️ The request timed out. Please try again after a few seconds.")

except Exception as e:
    st.error(f"⚠️ An unexpected error occurred: {e}")
```

elif submit and not user\_input:
st.warning("Please enter feedback to rewrite.")
