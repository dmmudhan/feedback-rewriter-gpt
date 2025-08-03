import streamlit as st
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

st.set_page_config(page_title="Feedback Rewriter Assistant", page_icon="✍️")

st.markdown(
    """
    <div style='text-align: center; margin-top: -50px;'>
        <h1>✍️ Feedback Rewriter Assistant</h1>
        <p style='font-size: 18px;'>
            🧠 Transform raw feedback into professional, constructive messages.<br>
            🎯 Tailored for workplace communication across roles and contexts.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# Session state for user input
if "raw_feedback" not in st.session_state:
    st.session_state.raw_feedback = ""
if "tone_selected" not in st.session_state:
    st.session_state.tone_selected = None
if "rewritten_feedback" not in st.session_state:
    st.session_state.rewritten_feedback = ""

# Input text
st.text_area(
    label="Enter your raw feedback message",
    key="raw_feedback",
    height=150,
    placeholder="E.g., This report was full of mistakes and poorly written."
)

# Show tone selector only if input is present
if st.session_state.raw_feedback.strip():
    st.selectbox(
        label="Select Desired Tone",
        options=[
            "Formal",
            "Friendly",
            "Empathetic",
            "Assertive",
            "Managerial",
            "Supportive"
        ],
        key="tone_selected"
    )

    if st.button("✍️ Rewrite Feedback"):
        with st.spinner("Rewriting in progress..."):
            try:
                prompt = f"""You are a feedback rewriting assistant.

Given the raw feedback: "{st.session_state.raw_feedback}",

Rewrite it in a {st.session_state.tone_selected} tone. 
Make sure the message is professional, constructive, and workplace-appropriate.
Avoid harsh language or sounding robotic. Maintain the original intent, and ensure clarity."""

                headers = {
                    "Authorization": f"Bearer {st.secrets['OPENROUTER_API_KEY']}",
                    "Content-Type": "application/json"
                }

                data = {
                    "model": "openrouter/mistral-7b-instruct",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant that rewrites feedback professionally."},
                        {"role": "user", "content": prompt}
                    ]
                }

                response = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    data=json.dumps(data),
                    timeout=30
                )

                response.raise_for_status()
                result = response.json()
                rewritten = result['choices'][0]['message']['content']
                st.session_state.rewritten_feedback = rewritten.strip()

            except Exception as e:
                st.error(f"⚠️ An error occurred: {str(e)}")

# Output section
if st.session_state.rewritten_feedback:
    st.markdown("### ✅ Rewritten Feedback")
    st.success(st.session_state.rewritten_feedback)

# Footer
st.markdown(
    """
    <hr style="margin-top: 40px;"/>
    <div style="text-align: center; font-size: 14px; color: gray;">
        Developed as part of a Prompt Engineering Project • Version 1.2
    </div>
    """,
    unsafe_allow_html=True
)
