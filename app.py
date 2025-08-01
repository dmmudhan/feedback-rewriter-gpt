import streamlit as st
from prompts import rewrite_feedback

st.set_page_config(page_title="Feedback Rewriter Assistant", page_icon="✍️")

st.title("✍️ Feedback Rewriter Assistant")
st.markdown("Rewrite feedback in different tones: *Empathetic*, *Constructive*, or *Managerial*.")

# User input
feedback = st.text_area("Enter your raw feedback here:", height=150)
tone = st.selectbox("Select the tone you want:", ["Empathetic", "Constructive", "Managerial"])

if st.button("Rewrite Feedback"):
    if not feedback.strip():
        st.warning("Please enter some feedback to rewrite.")
    else:
        with st.spinner("Rewriting in progress..."):
            api_key = st.secrets["OPENROUTER_API_KEY"]
            result = rewrite_feedback(feedback, tone, api_key)
            st.success("Done! Here's your rewritten feedback:")
            st.text_area("Rewritten Feedback", result, height=150)
