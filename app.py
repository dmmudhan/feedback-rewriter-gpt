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
    return f"[{tone.title()} Tone] {out}"

# ---------------------- PROPER Session State Reset ----------------------
def reset_app_state():
    """Completely reset the app to initial state"""
    keys_to_preserve = ["user_input"]  # Only preserve the current input
    current_input = st.session_state.get("user_input", "")
    
    # Clear everything
    st.session_state.clear()
    
    # Reset to defaults
    st.session_state["rewritten_text"] = ""
    st.session_state["feedback"] = ""
    st.session_state["user_input"] = current_input
    st.session_state["rewrites"] = []
    st.session_state["show_feedback_form"] = False
    st.session_state["show_history"] = False
    st.session_state["show_tip"] = False
    st.session_state["current_tip"] = ""
    st.session_state["selected_tone"] = "managerial"
    st.session_state["selected_language"] = "English"
    st.session_state["format_as_email"] = False
    st.session_state["app_session_id"] = str(int(time.time() * 1000))

# Initialize session state properly
if "app_session_id" not in st.session_state:
    reset_app_state()

# ---------------------- App Config ----------------------
st.set_page_config(
    page_title="AI Feedback Rewriter | Transform Your Words", 
    page_icon="✨", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------------------- Custom CSS for Better UI ----------------------
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .tagline {
        text-align: center;
        font-size: 1.2rem;
        color: #555;
        margin-bottom: 1rem;
        line-height: 1.6;
    }
    
    .cta-header {
        text-align: center;
        color: #2E8B57;
        font-size: 1.8rem;
        font-weight: 600;
        margin: 1.5rem 0;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    .step-indicator {
        background: linear-gradient(90deg, #4CAF50, #45a049);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 25px;
        font-weight: 600;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .control-section {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #4CAF50;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .result-section {
        background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
        padding: 1.5rem;
        border-radius: 15px;
        border: 2px solid #4CAF50;
        margin: 1.5rem 0;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.2);
    }
    
    .tip-container {
        background: linear-gradient(135deg, #fff3cd 0%, #fef7e0 100%);
        border: 2px solid #ffc107;
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        animation: slideIn 0.3s ease-in-out;
    }
    
    @keyframes slideIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------- Stunning Header ----------------------
st.markdown('<h1 class="main-header">✨ AI Feedback Rewriter</h1>', unsafe_allow_html=True)
st.markdown('<p class="tagline">🎯 Transform harsh feedback into professional, empathetic communication<br>🚀 Perfect tone • Any language • Instant results</p>', unsafe_allow_html=True)
st.markdown('<h2 class="cta-header">💡 Turn awkward conversations into confident communications!</h2>', unsafe_allow_html=True)

# ---------------------- Tone Options (Fixed Logic) ----------------------
tone_options = {
    "managerial": "🧭 Managerial",
    "empathetic": "💖 Empathetic", 
    "formal": "🧾 Formal",
    "friendly": "😊 Friendly",
    "assertive": "💼 Assertive"
}

# ---------------------- Language Options (Predefined) ----------------------
language_options = {
    "English": "🇺🇸 English",
    "Spanish": "🇪🇸 Spanish", 
    "French": "🇫🇷 French",
    "German": "🇩🇪 German",
    "Italian": "🇮🇹 Italian",
    "Portuguese": "🇵🇹 Portuguese",
    "Hindi": "🇮🇳 Hindi",
    "Telugu": "🇮🇳 Telugu",
    "Tamil": "🇮🇳 Tamil",
    "Japanese": "🇯🇵 Japanese",
    "Korean": "🇰🇷 Korean",
    "Chinese": "🇨🇳 Chinese"
}

# ---------------------- Step 1: Input Section ----------------------
st.markdown('<div class="step-indicator">📝 Step 1: Enter Your Raw Feedback</div>', unsafe_allow_html=True)

# Quick action buttons
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("🎯 Try Sample Text", use_container_width=True, help="Load example feedback", key="sample_btn"):
        # Clear everything except set the sample text
        reset_app_state()
        st.session_state.user_input = "You're always missing deadlines. I can't keep covering for your delays. It's affecting the whole project."
        st.rerun()
        
with col2:
    if st.button("🔄 Clear All", use_container_width=True, help="Start fresh", key="clear_btn"):
        # Complete reset
        reset_app_state()
        st.rerun()
        
with col3:
    if st.button("🎲 Random Tip", use_container_width=True, help="Get writing tips", key="tip_btn"):
        if st.session_state.get("show_tip", False):
            # Hide tip if already showing
            st.session_state.show_tip = False
            st.session_state.current_tip = ""
        else:
            # Show new tip
            tips = [
                "💡 Be specific about behaviors, not personality",
                "🎯 Focus on impact and solutions", 
                "🤝 Use 'we' instead of 'you' when possible",
                "⏰ Give feedback soon after the event",
                "🌟 Balance criticism with recognition",
                "📝 Use concrete examples instead of generalizations",
                "🤔 Ask questions to encourage dialogue",
                "✨ End with positive expectations"
            ]
            st.session_state.current_tip = tips[int(time.time()) % len(tips)]
            st.session_state.show_tip = True

# Display tip if active
if st.session_state.get("show_tip", False) and st.session_state.get("current_tip", ""):
    st.markdown(f"""
    <div class="tip-container">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><strong>💡 Pro Tip:</strong> {st.session_state.current_tip}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add a small dismiss button
    if st.button("✕ Dismiss", key="dismiss_tip", help="Hide this tip"):
        st.session_state.show_tip = False
        st.session_state.current_tip = ""
        st.rerun()

# Main input area
user_input = st.text_area(
    "", 
    key="user_input", 
    height=150,
    placeholder="✏️ Paste your raw feedback here...\n\nExample: 'You never respond to emails on time. This is really frustrating and unprofessional.'\n\n💡 Pro tip: Be honest about what you really want to say - we'll make it professional!",
    help="Enter the feedback you want to refine - be authentic, we'll handle the rest!"
)

# ---------------------- Step 2: Customization Options ----------------------
if user_input and user_input.strip():
    st.markdown('<div class="step-indicator">⚙️ Step 2: Customize Your Message Style</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="control-section">', unsafe_allow_html=True)
        
        # Row 1: Tone and Format
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_tone_key = st.selectbox(
                "🎭 Choose Your Tone", 
                options=list(tone_options.keys()),
                format_func=lambda x: tone_options[x],
                index=list(tone_options.keys()).index(st.session_state.get("selected_tone", "managerial")),
                help="Select the professional tone that best fits your situation",
                key="tone_selector"
            )
            st.session_state.selected_tone = selected_tone_key
            
        with col2:
            format_as_email = st.checkbox(
                "📧 Format as Email", 
                value=st.session_state.get("format_as_email", False),
                help="Add greeting, structure, and professional closing",
                key="email_checkbox"
            )
            st.session_state.format_as_email = format_as_email
        
        # Row 2: Language Selection
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_language_key = st.selectbox(
                "🌍 Select Language", 
                options=list(language_options.keys()),
                format_func=lambda x: language_options[x],
                index=list(language_options.keys()).index(st.session_state.get("selected_language", "English")),
                help="Choose your preferred language for the output",
                key="language_selector"
            )
            st.session_state.selected_language = selected_language_key
            
        with col2:
            # Preview section
            st.markdown("**🔍 Preview:**")
            preview_text = f"{tone_options[selected_tone_key]}"
            if format_as_email:
                preview_text += " + Email"
            if selected_language_key != "English":
                preview_text += f" + {language_options[selected_language_key]}"
            st.info(preview_text)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ---------------------- Step 3: Generate Button (Mobile Friendly) ----------------------
    st.markdown('<div class="step-indicator">🚀 Step 3: Transform Your Feedback</div>', unsafe_allow_html=True)
    
    # Big, attractive generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button(
            "✨ TRANSFORM MY FEEDBACK ✨", 
            use_container_width=True,
            help="Click to generate your refined, professional feedback",
            key="transform_btn"
        ):
            # Clear previous results and hide other sections
            st.session_state.rewritten_text = ""
            st.session_state.show_feedback_form = False
            st.session_state.show_history = False
            st.session_state.show_tip = False
            
            with st.spinner("🎭 Applying the perfect tone... 🌟 Crafting professional language... ⚡ Almost ready!"):
                try:
                    api_key = st.secrets.get("OPENROUTER_API_KEY", None)
                    
                    if format_as_email:
                        system_prompt = (
                            f"You are an expert in writing professional emails. Convert the given workplace feedback into a polite, well-structured email using a {selected_tone_key} tone. "
                            f"Write the final email entirely in {selected_language_key} language. "
                            f"Important: If the language is not English, write EVERYTHING in {selected_language_key} including greetings and closings. Use native expressions and natural phrasing. "
                            f"Do not include any English words or explanations. Include a suitable greeting and professional closing appropriate for {selected_language_key} culture."
                        )
                    else:
                        system_prompt = (
                            f"You are an expert in rewriting workplace feedback. Rephrase the given message to sound more {selected_tone_key} while keeping the original meaning. "
                            f"Write the response entirely in {selected_language_key} language. "
                            f"Important: If the language is not English, use natural, native expressions and phrasing. Do not include any English words. "
                            f"Do not format as an email. Return ONLY the rewritten feedback in perfect {selected_language_key}."
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
                            st.warning("🤖 AI services temporarily unavailable — using smart fallback.")
                            fallback = deterministic_rewrite(user_input, selected_tone_key, selected_language_key)
                            st.session_state.rewritten_text = fallback
                            st.session_state.rewrites.insert(0, {"timestamp": datetime.utcnow().isoformat(), "original": user_input, "rewritten": fallback})
                    else:
                        fallback = deterministic_rewrite(user_input, selected_tone_key, selected_language_key)
                        st.session_state.rewritten_text = fallback
                        st.session_state.rewrites.insert(0, {"timestamp": datetime.utcnow().isoformat(), "original": user_input, "rewritten": fallback})

                except Exception as e:
                    st.error(f"⚠️ Oops! Something went wrong: {str(e)}. Please try again!")
                    st.session_state.rewritten_text = ""

# ---------------------- Results Section ----------------------
if st.session_state.rewritten_text and st.session_state.rewritten_text.strip():
    st.markdown('<div class="step-indicator">🎉 Your Professional Message is Ready!</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="result-section">', unsafe_allow_html=True)
    st.markdown("### ✅ **Transformed Feedback:**")
    st.success(st.session_state.rewritten_text)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Action buttons for results
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.download_button(
            "📋 Download Text", 
            st.session_state.rewritten_text, 
            file_name=f"refined_feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            use_container_width=True,
            help="Save your refined feedback as a text file",
            key="download_btn"
        )
    with col2:
        if st.button("🔄 Try Different Tone", use_container_width=True, help="Keep the same text, try another tone", key="retry_btn"):
            st.session_state.rewritten_text = ""
            st.session_state.show_feedback_form = False
            st.session_state.show_history = False
            st.rerun()
    with col3:
        if st.button("✨ New Feedback", use_container_width=True, help="Start over with new feedback", key="new_btn"):
            reset_app_state()
            st.rerun()

# ---------------------- Bottom Actions ----------------------
st.markdown("---")
st.markdown('<h3 style="text-align: center; color: #666;">🛠️ More Options</h3>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("💬 Share Feedback", use_container_width=True, help="Help us improve this tool", key="feedback_toggle_btn"):
        st.session_state.show_feedback_form = not st.session_state.get("show_feedback_form", False)
        st.session_state.show_history = False  # Hide history when showing feedback
        if not st.session_state.show_feedback_form:
            # If hiding feedback form, make sure it's properly reset
            st.rerun()
            
with col2:
    if st.button("📜 My History", use_container_width=True, help="View your previous transformations", key="history_toggle_btn"):
        st.session_state.show_history = not st.session_state.get("show_history", False)
        st.session_state.show_feedback_form = False  # Hide feedback when showing history
        if not st.session_state.show_history:
            # If hiding history, make sure it's properly reset
            st.rerun()

# Feedback Form
if st.session_state.get("show_feedback_form", False):
    st.markdown("### 📬 Help Us Make This Better!")
    with st.form("feedback_form", clear_on_submit=True):
        ff_text = st.text_area("What do you think about this tool?", height=100)
        ff_rating = st.slider("Rate your experience (1=poor, 5=amazing)", 1, 5, 4)
        ff_like = st.radio("Would you recommend this to colleagues?", ["👍 Absolutely","👎 Not really"], index=0)
        ff_improve = st.multiselect("What should we improve?", ["Speed","Accuracy","Languages","Tones","Interface","Mobile Experience"])
        ff_suggestions = st.text_area("Any specific suggestions?")
        submit_feedback = st.form_submit_button("🚀 Submit Feedback")
        
    if submit_feedback:
        fb_id = str(int(time.time()*1000))
        public_base = st.secrets.get("PUBLIC_BASE_URL", "")
        public_link = f"{public_base}?fb={fb_id}" if public_base else ""
        row = [datetime.utcnow().isoformat(), ff_rating, ff_like, "; ".join(ff_improve), ff_suggestions, ff_text, "", "", public_link]
        ok, msg = append_row_to_sheet(row)
        if ok:
            st.balloons()
            st.success("🎉 Thank you! Your feedback helps us improve!")
        else:
            st.warning(f"Feedback saved locally. {msg}")
            st.session_state.rewrites.insert(0, {"timestamp": datetime.utcnow().isoformat(), "rating": ff_rating, "like": ff_like, "improvements": "; ".join(ff_improve), "suggestions": ff_suggestions, "original": ff_text, "rewritten": "", "public_link": public_link})
            st.balloons()
        
        # Hide feedback form after successful submission
        st.session_state.show_feedback_form = False
        time.sleep(2)  # Brief pause before rerun
        st.rerun()

# History
if st.session_state.get("show_history", False):
    st.markdown("### 📜 Your Transformation History")
    if st.session_state.rewrites:
        df = pd.DataFrame(st.session_state.rewrites)
        st.dataframe(df, use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("💾 Export History", data=csv, file_name="feedback_history.csv", use_container_width=True, key="export_history_btn")
    else:
        st.info("🌟 No transformations yet. Start by entering some feedback above!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin: 2rem 0;'>
    <h3 style='color: white; margin: 0;'>🚀 Built by Devi Mudhanagiri</h3>
    <p style='color: #f0f0f0; margin: 0.5rem 0;'>v2.1 | Powered by OpenRouter AI | Made with ❤️ for better communication</p>
    <p style='color: #e0e0e0; margin: 0; font-size: 0.9rem;'>Transform every conversation into an opportunity 💫</p>
</div>
""", unsafe_allow_html=True)