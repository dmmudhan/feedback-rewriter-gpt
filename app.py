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

# ---------------------- Deterministic fallback ----------------------
def deterministic_rewrite(text: str, tone: str, language: str) -> str:
    out = text.strip()
    if len(out) > 0:
        out = out[0].upper() + out[1:]
    replacements = {"cant": "can't", "dont": "don't", "wont": "won't"}
    for k, v in replacements.items():
        out = out.replace(k, v)
    return f"(Tone: {tone}) {out}"

# ---------------------- Session-state init with proper reset ----------------------
# Always start with a clean slate on page load
if "app_loaded" not in st.session_state:
    st.session_state.clear()
    st.session_state["rewritten_text"] = ""
    st.session_state["feedback"] = ""
    st.session_state["user_input"] = ""
    st.session_state["rewrites"] = []
    st.session_state["show_feedback_form"] = False
    st.session_state["show_history"] = False
    st.session_state["app_loaded"] = True

# ---------------------- App Config ----------------------
st.set_page_config(page_title="Feedback Rewriter Assistant", page_icon="✍️", layout="centered")

# ---------------------- Header, Tagline & Catchy Intro ----------------------
st.markdown("""
<h1 style='text-align: center; margin-bottom:8px;'>✍️ Feedback Rewriter Assistant</h1>
<p style='text-align: center; font-size: 16px; margin-top:4px; margin-bottom:12px; color:#666;'>🌟 Turn raw feedback into clear, confident, and impactful communication — customize the tone, format, and language to fit any situation.</p>
<h3 style='text-align:center; color:#4CAF50; margin-top:0px; margin-bottom:20px;'>Your words, perfectly refined in seconds 🚀</h3>
<h4 style='text-align:center; color:#333; margin-bottom:16px;'>✨ Get Started: Enter your feedback below</h4>
""", unsafe_allow_html=True)

# ---------------------- Tone Options ----------------------
tone_labels = {
    "managerial": "🧭 Managerial - Balanced and leadership-oriented",
    "empathetic": "💖 Empathetic - Supportive and understanding",
    "formal": "🧾 Formal - Polished and businesslike",
    "friendly": "😊 Friendly - Warm and casual",
    "assertive": "💼 Assertive - Clear and direct"
}

# ---------------------- Input Section ----------------------
user_input = st.text_area("", key="user_input", height=180,
                          placeholder="e.g. You're always late submitting your work. This is unacceptable.")

# ---------------------- Action Buttons (Moved below input) ----------------------
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("🎯 Add Sample Text", use_container_width=True):
        st.session_state.user_input = "You're always missing deadlines. I can't keep covering for your delays. It's affecting the whole project."
        st.session_state.rewritten_text = ""  # Clear any old results
        st.rerun()
with col2:
    if st.button("🔁 Clear All", use_container_width=True):
        st.session_state.user_input = ""
        st.session_state.rewritten_text = ""  # Explicitly clear results
        st.rerun()

# ---------------------- Controls (Only show if there's input) ----------------------
if user_input and user_input.strip():
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        selected_tone = st.selectbox("Tone", list(tone_labels.values()), index=0, key="tone_select")
    with c2:
        format_as_email = st.checkbox("📧 Email", key="format_email")
    with c3:
        translate_enable = st.checkbox("🌍 Translate", key="translate_enable")

    if translate_enable:
        lang = st.text_input("Language", value="English", key="lang_input")
    else:
        lang = "English"

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    if st.button("🚀 Rewrite", key="rewrite_btn", use_container_width=True):
        # Clear previous results immediately
        st.session_state.rewritten_text = ""
        
        with st.spinner("Rewriting your feedback..."):
            try:
                api_key = st.secrets.get("OPENROUTER_API_KEY", None)
                tone_short = selected_tone.split("-")[0].strip().lower()
                if format_as_email:
                    system_prompt = (
                        f"You are an expert in writing professional emails. Convert the given workplace feedback into a polite, well-structured email using a {tone_short} tone. "
                        f"Write the final email entirely in {lang} language. Do not include any English explanation or translation. Include a suitable greeting and closing."
                    )
                else:
                    system_prompt = (
                        f"You are an expert in rewriting workplace feedback. Rephrase the given message to sound more {tone_short} while keeping the original meaning. "
                        f"Do not format as an email. Return ONLY the rewritten feedback in {lang} language. Do not include any English explanation or translation."
                    )

                if api_key:
                    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                    data = {"messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}]}
                    model_fallbacks = [
                        "mistral/mistral-7b-instruct",
                        "mistralai/mixtral-8x7b-instruct",
                        "nousresearch/nous-capybara-7b",
                        "gryphe/mythomax-l2-13b",
                        "nousresearch/nous-hermes-2-mixtral"
                    ]
                    rewritten = None
                    for model in model_fallbacks:
                        try:
                            data["model"] = model
                            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
                            if resp.status_code == 200:
                                j = resp.json()
                                rewritten = j.get("choices", [])[0].get("message", {}).get("content", "").strip()
                                break
                            else:
                                time.sleep(0.5)
                        except Exception:
                            time.sleep(0.5)
                    if rewritten:
                        st.session_state.rewritten_text = rewritten
                        st.session_state.rewrites.insert(0, {"timestamp": datetime.utcnow().isoformat(), "original": user_input, "rewritten": rewritten})
                    else:
                        st.warning("Could not get AI rewrite — using deterministic fallback.")
                        fallback = deterministic_rewrite(user_input, tone_short, lang)
                        st.session_state.rewritten_text = fallback
                        st.session_state.rewrites.insert(0, {"timestamp": datetime.utcnow().isoformat(), "original": user_input, "rewritten": fallback})
                else:
                    fallback = deterministic_rewrite(user_input, selected_tone, lang)
                    st.session_state.rewritten_text = fallback
                    st.session_state.rewrites.insert(0, {"timestamp": datetime.utcnow().isoformat(), "original": user_input, "rewritten": fallback})

            except Exception as e:
                st.error(f"Unexpected error while rewriting: {str(e)}. Please try again.")
                st.session_state.rewritten_text = ""

# ---------------------- Output (Only show if we have results) ----------------------
if st.session_state.rewritten_text and st.session_state.rewritten_text.strip():
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    st.markdown("### ✅ Here's Your Refined Feedback:")
    st.success(st.session_state.rewritten_text)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.download_button("📋 Download", st.session_state.rewritten_text, 
                          file_name="rewritten_feedback.txt", use_container_width=True)
    with col2:
        if st.button("🔄 Try Another Tone", use_container_width=True):
            st.session_state.rewritten_text = ""
            st.rerun()

# ---------------------- Feedback & History Controls ----------------------
st.markdown("<div style='margin-top:32px;'></div>", unsafe_allow_html=True)
st.markdown("---")
col1, col2 = st.columns([1, 1])
with col1:
    if st.button("💬 Leave Feedback", use_container_width=True):
        st.session_state.show_feedback_form = not st.session_state.get("show_feedback_form", False)
with col2:
    if st.button("📜 View My Past Rewrites", use_container_width=True):
        st.session_state.show_history = not st.session_state.get("show_history", False)

# Feedback Form
if st.session_state.get("show_feedback_form", False):
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
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
            st.success(f"Thanks — your feedback is recorded! {public_link}")
        else:
            st.warning(f"Saved locally (Sheets not configured). Message: {msg}")
            st.session_state.rewrites.insert(0, {"timestamp": datetime.utcnow().isoformat(), "rating": ff_rating, "like": ff_like, "improvements": "; ".join(ff_improve), "suggestions": ff_suggestions, "original": ff_text, "rewritten": "", "public_link": public_link})
            st.balloons()
        st.session_state.show_feedback_form = False

# History
if st.session_state.get("show_history", False):
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    st.subheader("📜 Rewrite History")
    if st.session_state.rewrites:
        df = pd.DataFrame(st.session_state.rewrites)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Export History CSV", data=csv, file_name="rewrite_history.csv", use_container_width=True)
    else:
        st.info("No rewrites yet. Start by entering some feedback above!")

# Footer
st.markdown("<div style='margin-top:40px;'></div>", unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div style='text-align: center; font-size: 14px; margin-top:16px;'>🛠️ Created by <b>Devi Mudhanagiri</b> · v1.6 · Powered by <a href='https://openrouter.ai' target='_blank'>OpenRouter</a></div>", unsafe_allow_html=True)