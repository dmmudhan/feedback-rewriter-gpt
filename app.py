import streamlit as st
import requests

st.set_page_config(page_title="Feedback Rewriter Assistant v1.1")

st.title("📝 Feedback Rewriter Assistant")
st.markdown("Version **1.1** – Now detects tone and suggests improvements automatically 🎯")

OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
API_URL = "https://openrouter.ai/api/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://your-project.streamlit.app",  # Replace if deployed
    "X-Title": "FeedbackRewriterAssistant"
}

# Function to detect tone
def detect_tone(user_input):
    system_prompt = {
        "role": "system",
        "content": "Classify the tone of the following feedback as one of the following: Harsh, Polite, Empathetic, Casual, Passive-Aggressive. Only return the tone label."
    }
    user_prompt = {
        "role": "user",
        "content": user_input
    }
    payload = {
        "model": "mistralai/mixtral-8x7b-instruct",
        "messages": [system_prompt, user_prompt]
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    tone = response.json()['choices'][0]['message']['content'].strip()
    return tone

# Function to rewrite feedback
def rewrite_feedback(user_input, desired_tone):
    system_prompt = {
        "role": "system",
        "content": f"Rewrite the following feedback in a {desired_tone} tone. Keep it professional and meaningful."
    }
    user_prompt = {
        "role": "user",
        "content": user_input
    }
    payload = {
        "model": "mistralai/mixtral-8x7b-instruct",
        "messages": [system_prompt, user_prompt]
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    return response.json()['choices'][0]['message']['content'].strip()

# Main UI
user_input = st.text_area("Paste your raw feedback here 👇")

if user_input:
    with st.spinner("Detecting tone..."):
        detected_tone = detect_tone(user_input)
        st.success(f"Detected tone: **{detected_tone}**")

        st.markdown("### ✨ Choose a tone to rewrite the feedback:")
        tone_options = ["Empathetic", "Constructive", "Polite", "Managerial"]
        selected_tone = st.radio("Select a tone:", tone_options, horizontal=True)

        if st.button("🔁 Rewrite Feedback"):
            with st.spinner("Rewriting..."):
                rewritten = rewrite_feedback(user_input, selected_tone)
                st.markdown("### ✅ Rewritten Feedback")
                st.success(rewritten)
