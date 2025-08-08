import streamlit as st
import requests
import time
import pandas as pd
import json
from datetime import datetime

# ---------------------- Google Sheets Integration ----------------------
try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    GS_AVAILABLE = True
except ImportError:
    GS_AVAILABLE = False

def gs_client_from_secrets():
    if not GS_AVAILABLE:
        return None
    creds_str = st.secrets.get("gss_credentials", None)
    if not creds_str:
        return None
    try:
        creds_json = json.loads(creds_str)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Google Sheets credential error: {e}")
        return None

def append_row_to_sheet(row, sheet_name="feedback_rewriter_history"):
    client = gs_client_from_secrets()
    if not client:
        return False, "Google Sheets not configured"
    try:
        try:
            sh = client.open(sheet_name)
            worksheet = sh.sheet1
        except gspread.SpreadsheetNotFound:
            sh = client.create(sheet_name)
            worksheet = sh.sheet1
            worksheet.append_row(["timestamp","rating","like","improvements","suggestions","original","rewritten","user_email","public_link"])
        worksheet.append_row(row)
        return True, "OK"
    except Exception as e:
        return False, str(e)

# ---------------------- Auto-reset Logic ----------------------
if "initialized" not in st.session_state:
    st.session_state["rewritten_text"] = ""
    st.session_state["feedback"] = ""
    st.session_state["user_input"] = ""
    st.session_state["rewrites"] = []
    st.session_state["initialized"] = True

# ---------------------- App Config ----------------------
st.set_page_config(page_title="Feedback Rewriter Assistant", page_icon="✍️", layout="centered")

# ---------------------- Header ----------------------
st.markdown("""
<h1 style='text-align: center;'>✍️ Feedback Rewriter Assistant</h1>
<p style='text-align: center; font-size: 18px;'>🔄 Rewrite your workplace or professional feedback into <b>polished, clear, and impactful</b> messages.</p>
<p style='text-align: center; font-size: 16px;'>🌟 Choose tone, format as email, and optionally translate output to any language.</p>
""", unsafe_allow_html=True)

# ---------------------- Tone Options & Tooltips ----------------------
tone_labels = {
    "managerial": "🧭 Managerial - Balanced and leadership-oriented",
    "empathetic": "💖 Empathetic - Supportive and understanding",
    "formal": "🧾 Formal - Polished and businesslike",
    "friendly": "😊 Friendly - Warm and casual",
    "assertive": "💼 Assertive - Clear and direct"
}

# ---------------------- Input Section ----------------------
st.markdown("### ✏️ Enter Feedback Below")
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🎯 Try Example Feedback"):
        st.session_state.user_input = (
            "You’re always missing deadlines. I can’t keep covering for your delays. It’s affecting the whole project."
        )
with col2:
    if st.button("🔁 Clear All"):
        st.session_state.user_input = ""
        st.session_state.rewritten_text = ""

user_input = st.text_area("", key="user_input", height=200,
                          placeholder="e.g. You're always late submitting your work. This is unacceptable.")

# ---------------------- Tone, Email, Language ----------------------
if user_input.strip():
    st.markdown("### 🎨 Customize Tone and Output")
    selected_tone = st.selectbox("Select Desired Tone:", list(tone_labels.values()))
    format_as_email = st.checkbox("📧 Format as Email")
    enable_translation = st.checkbox("🌍 Translate output into another language")
    if enable_translation:
        selected_language = st.text_input("Which language? (e.g. Spanish, German, Hindi, Tamil... )", value="Spanish")
    else:
        selected_language = "English"

    if st.button("🚀 Rewrite Feedback"):
        st.session_state.rewritten_text = ""
        with st.spinner("Rewriting in progress..."):
            try:
                if "OPENROUTER_API_KEY" not in st.secrets:
                    st.error("⚠️ OPENROUTER_API_KEY is missing in Streamlit secrets.")
                    st.stop()

                api_key = st.secrets["OPENROUTER_API_KEY"]
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                tone = selected_tone.split("-")[0].strip().lower()
                lang = selected_language

                if format_as_email:
                    system_prompt = (
                        f"You are an expert in writing professional emails. Convert the given workplace feedback into a polite, well-structured email using a {tone} tone. "
                        f"Write the final email entirely in {lang} language. Do not include any English explanation or translation. Include a suitable greeting and closing."
                    )
                else:
                    system_prompt = (
                        f"You are an expert in rewriting workplace feedback. Rephrase the given message to sound more {tone} while keeping the original meaning. "
                        f"Do not format as an email. Return ONLY the rewritten feedback in {lang} language. Do not include any English explanation or translation."
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

                for model in model_fallbacks:
                    try:
                        data["model"] = model
                        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
                        if response.status_code == 200:
                            result = response.json()
                            rewritten = result["choices"][0]["message"]["content"].strip()
                            st.session_state.rewritten_text = rewritten
                            st.session_state.rewrites.insert(0, {
                                "timestamp": datetime.utcnow().isoformat(),
                                "original": user_input,
                                "rewritten": rewritten
                            })
                            break
                        else:
                            time.sleep(1)
                    except Exception:
                        time.sleep(1)

                if not st.session_state.rewritten_text:
                    st.error("⚠️ Could not rewrite the feedback at this time. Please try again.")

            except Exception:
                st.error("⚠️ Unexpected error. Please try again.")

# ---------------------- Display Output ----------------------
if st.session_state.rewritten_text:
    st.markdown("### ✅ Here's Your Refined Feedback:")
    st.success(st.session_state.rewritten_text)
    st.download_button("📋 Download Rewritten Feedback", st.session_state.rewritten_text, file_name="rewritten_feedback.txt", use_container_width=True)

# ---------------------- Feedback Form ----------------------
st.markdown("---")
st.subheader("📬 Share Your Feedback")
with st.form("feedback_form"):
    ff_text = st.text_area("Your feedback", height=100)
    ff_rating = st.slider("Rating (1=poor, 5=excellent)", 1, 5, 4)
    ff_like = st.radio("Do you like this tool?", ["👍 Yes","👎 No"], index=0)
    ff_improve = st.multiselect("What to improve?", ["Clarity","Brevity","Tone","Grammar","UX","Performance"])
    ff_suggestions = st.text_area("Any suggestions? (optional)")
    submit_feedback = st.form_submit_button("Submit Feedback")

if submit_feedback:
    fb_id = str(int(time.time()*1000))
    public_base = st.secrets.get("PUBLIC_BASE_URL", "")
    public_link = f"{public_base}?fb={fb_id}" if public_base else ""
    row = [datetime.utcnow().isoformat(), ff_rating, ff_like, "; ".join(ff_improve), ff_suggestions, ff_text, "", "", public_link]
    ok, msg = append_row_to_sheet(row)
    if ok:
        st.balloons()
        st.success(f"Thanks — your feedback is recorded. {public_link}")
    else:
        st.warning(f"Saved locally (Sheets not configured). Message: {msg}")
        st.session_state.rewrites.insert(0, {
            "timestamp": datetime.utcnow().isoformat(),
            "rating": ff_rating,
            "like": ff_like,
            "improvements": "; ".join(ff_improve),
            "suggestions": ff_suggestions,
            "original": ff_text,
            "rewritten": "",
            "public_link": public_link
        })
        st.balloons()

# ---------------------- Rewrite History ----------------------
st.markdown("---")
st.subheader("📜 Rewrite History")
if st.session_state.rewrites:
    df = pd.DataFrame(st.session_state.rewrites)
    st.dataframe(df)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Export History CSV", data=csv, file_name="rewrite_history.csv")
else:
    st.info("No rewrites yet.")

# ---------------------- Footer ----------------------
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    "<div style='text-align: center; font-size: 14px;'>"
    "🛠️ Created by <b>Devi Mudhanagiri</b> · v1.5 · Powered by <a href='https://openrouter.ai' target='_blank'>OpenRouter</a>"
    "</div>",
    unsafe_allow_html=True
)
