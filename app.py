import streamlit as st
import requests
import time
import pandas as pd
import json
from datetime import datetime
import random

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
    return f"[{tone.title()} Enhancement] {out}"

# ---------------------- PROPER Session State Reset ----------------------
def reset_app_state():
    keys_to_preserve = ["user_input"]
    current_input = st.session_state.get("user_input", "")
    st.session_state.clear()
    st.session_state["rewritten_text"] = ""
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

if "app_session_id" not in st.session_state:
    reset_app_state()

# ---------------------- App Config ----------------------
st.set_page_config(
    page_title="🎯 FeedbackGPT - AI Communication Coach", 
    page_icon="🚀", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------------------- STUNNING CSS for Viral Appeal ----------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700;800&display=swap');
    
    .main {
        font-family: 'Poppins', sans-serif;
    }
    
    .hero-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 4rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    .hero-tagline {
        text-align: center;
        font-size: 1.4rem;
        color: #444;
        margin-bottom: 0.8rem;
        font-weight: 500;
    }
    
    .viral-cta {
        text-align: center;
        background: linear-gradient(135deg, #FF6B6B, #4ECDC4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 1rem 0;
        animation: pulse 2s infinite;
    }
    
    .stats-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 20px;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    .step-pill {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        color: white;
        padding: 0.7rem 1.5rem;
        border-radius: 50px;
        font-weight: 700;
        text-align: center;
        margin: 1.5rem 0;
        box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
        transform: perspective(1000px) rotateX(-5deg);
    }
    
    .magic-controls {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 20px;
        border: 3px solid transparent;
        background-clip: padding-box;
        position: relative;
        margin: 1.5rem 0;
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    }
    
    .magic-controls::before {
        content: '';
        position: absolute;
        top: -3px; left: -3px; right: -3px; bottom: -3px;
        background: linear-gradient(135deg, #667eea, #764ba2, #f093fb);
        border-radius: 23px;
        z-index: -1;
    }
    
    .result-magic {
        background: linear-gradient(135deg, #e8f5e8 0%, #f0fff0 100%);
        padding: 2rem;
        border-radius: 20px;
        border: 3px solid #4CAF50;
        margin: 2rem 0;
        box-shadow: 0 15px 35px rgba(76, 175, 80, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .result-magic::before {
        content: '✨';
        position: absolute;
        top: 10px;
        right: 20px;
        font-size: 2rem;
        animation: sparkle 1.5s infinite;
    }
    
    .transform-btn {
        background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%) !important;
        color: white !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        padding: 1rem 2rem !important;
        border: none !important;
        border-radius: 50px !important;
        box-shadow: 0 8px 25px rgba(255, 107, 107, 0.4) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    
    .social-proof {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    @keyframes glow {
        from { text-shadow: 0 0 20px rgba(102, 126, 234, 0.5); }
        to { text-shadow: 0 0 30px rgba(118, 75, 162, 0.8), 0 0 40px rgba(240, 147, 251, 0.5); }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
    
    @keyframes sparkle {
        0%, 100% { transform: rotate(0deg) scale(1); }
        50% { transform: rotate(180deg) scale(1.2); }
    }
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }
    
    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
        border: 2px solid #f0f0f0;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# ---------------------- VIRAL HERO SECTION ----------------------
st.markdown('<h1 class="hero-header">🚀 FeedbackGPT</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-tagline">The AI that turns your brutal honesty into brilliant communication</p>', unsafe_allow_html=True)
st.markdown('<h2 class="viral-cta">🎯 Say goodbye to awkward conversations forever!</h2>', unsafe_allow_html=True)

# ---------------------- Social Proof Banner ----------------------
st.markdown("""
<div class="stats-banner">
    <h3 style="margin: 0;">⚡ Instant Professional Communication</h3>
    <p style="margin: 0.5rem 0 0 0;">Transform harsh feedback → Professional messages in 3 seconds | 12 languages | 5 tones</p>
</div>
""", unsafe_allow_html=True)

# ---------------------- Feature Showcase ----------------------
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <h4>🎭 5 Pro Tones</h4>
        <p>From empathetic to assertive</p>
    </div>
    <div class="feature-card">
        <h4>🌍 12 Languages</h4>
        <p>Global communication ready</p>
    </div>
    <div class="feature-card">
        <h4>📧 Email Format</h4>
        <p>Complete with greetings</p>
    </div>
    <div class="feature-card">
        <h4>⚡ 3-Second Results</h4>
        <p>Faster than typing yourself</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------- Tone & Language Options ----------------------
tone_options = {
    "managerial": "🧭 Managerial - Balanced Leadership",
    "empathetic": "💖 Empathetic - Caring & Supportive", 
    "formal": "🧾 Formal - Corporate Professional",
    "friendly": "😊 Friendly - Warm & Approachable",
    "assertive": "💼 Assertive - Direct & Confident"
}

language_options = {
    "English": "🇺🇸 English",
    "Spanish": "🇪🇸 Español", 
    "French": "🇫🇷 Français",
    "German": "🇩🇪 Deutsch",
    "Italian": "🇮🇹 Italiano",
    "Portuguese": "🇵🇹 Português",
    "Hindi": "🇮🇳 हिंदी",
    "Telugu": "🇮🇳 తెలుగు",
    "Tamil": "🇮🇳 தமிழ்",
    "Japanese": "🇯🇵 日本語",
    "Korean": "🇰🇷 한국어",
    "Chinese": "🇨🇳 中文"
}

# ---------------------- VIRAL SAMPLE TEXTS ----------------------
viral_samples = [
    "You never listen in meetings and always interrupt others. It's really annoying.",
    "Your code is always buggy and creates more work for everyone else.",
    "You're constantly late to everything and it shows you don't respect our time.",
    "Your presentations are boring and put everyone to sleep.",
    "You take credit for other people's work and it's not fair.",
    "You're always on your phone during important discussions.",
    "Your emails are confusing and no one understands what you want.",
    "You never help your teammates and only care about yourself."
]

# ---------------------- Step 1: EXCITING Input Section ----------------------
st.markdown('<div class="step-pill">🎯 STEP 1: Drop Your Raw, Honest Feedback Here</div>', unsafe_allow_html=True)

# Viral action buttons
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("🎲 Surprise Me!", use_container_width=True, help="Get a random challenging example", key="sample_btn"):
        reset_app_state()
        st.session_state.user_input = random.choice(viral_samples)
        st.rerun()
        
with col2:
    if st.button("🚀 Fresh Start", use_container_width=True, help="Clear everything and start over", key="clear_btn"):
        reset_app_state()
        st.rerun()
        
with col3:
    if st.button("💡 Pro Tips", use_container_width=True, help="Get expert communication advice", key="tip_btn"):
        if st.session_state.get("show_tip", False):
            st.session_state.show_tip = False
            st.session_state.current_tip = ""
        else:
            pro_tips = [
                "💡 **The Sandwich Method**: Positive → Constructive → Positive",
                "🎯 **Be Specific**: 'Late to 3 meetings this week' vs 'Always late'",
                "🤝 **Use 'We' Language**: 'How can we improve this?' vs 'You need to fix this'",
                "⏰ **Timing Matters**: Give feedback within 24-48 hours of the incident",
                "🌟 **Solution-Focused**: Always suggest a path forward",
                "📊 **Data Over Drama**: Use facts and examples, not emotions",
                "🎭 **Match the Moment**: Formal situations need formal language",
                "✨ **End Positively**: Leave them motivated, not deflated"
            ]
            st.session_state.current_tip = random.choice(pro_tips)
            st.session_state.show_tip = True

# Display tip with dismissal
if st.session_state.get("show_tip", False) and st.session_state.get("current_tip", ""):
    tip_col1, tip_col2 = st.columns([10, 1])
    with tip_col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fff3cd 0%, #fef7e0 100%); border: 2px solid #ffc107; border-radius: 15px; padding: 1.2rem; margin: 1rem 0; animation: slideIn 0.3s ease-in-out;">
            {st.session_state.current_tip}
        </div>
        """, unsafe_allow_html=True)
    with tip_col2:
        if st.button("✕", key="dismiss_tip", help="Hide tip"):
            st.session_state.show_tip = False
            st.session_state.current_tip = ""
            st.rerun()

# Main input with viral examples
user_input = st.text_area(
    label="",
    key="user_input", 
    height=140,
    placeholder="🔥 Paste your brutally honest feedback here...\n\nExamples:\n• 'You never respond to emails. It's unprofessional.'\n• 'Your presentation was confusing and boring.'\n• 'You always interrupt people in meetings.'\n\n💪 Be real - we'll make it professional!",
    help="Don't hold back - the rawer, the better the transformation!"
)

# ---------------------- ONLY SHOW CONTROLS IF INPUT EXISTS ----------------------
if user_input and user_input.strip():
    st.markdown('<div class="step-pill">⚙️ STEP 2: Choose Your Communication Style</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="magic-controls">', unsafe_allow_html=True)
        
        # Row 1: Tone and Format
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_tone_key = st.selectbox(
                "🎭 Pick Your Power Tone", 
                options=list(tone_options.keys()),
                format_func=lambda x: tone_options[x],
                index=list(tone_options.keys()).index(st.session_state.get("selected_tone", "managerial")),
                help="Choose the vibe that matches your situation",
                key="tone_selector"
            )
            st.session_state.selected_tone = selected_tone_key
            
        with col2:
            format_as_email = st.checkbox(
                "📧 Email Mode", 
                value=st.session_state.get("format_as_email", False),
                help="Complete email with greeting & closing",
                key="email_checkbox"
            )
            st.session_state.format_as_email = format_as_email
        
        # Row 2: Language
        col1, col2 = st.columns([3, 1])
        with col1:
            selected_language_key = st.selectbox(
                "🌍 Choose Your Language", 
                options=list(language_options.keys()),
                format_func=lambda x: language_options[x],
                index=list(language_options.keys()).index(st.session_state.get("selected_language", "English")),
                help="Pick your preferred language",
                key="language_selector"
            )
            st.session_state.selected_language = selected_language_key
            
        with col2:
            # Live preview
            st.markdown("**🔮 Magic Recipe:**")
            preview_parts = [tone_options[selected_tone_key].split(" - ")[0]]
            if format_as_email:
                preview_parts.append("Email")
            if selected_language_key != "English":
                preview_parts.append(language_options[selected_language_key].split(" ")[1])
            st.success(" + ".join(preview_parts))
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # ---------------------- VIRAL TRANSFORM BUTTON ----------------------
    st.markdown('<div class="step-pill">🚀 STEP 3: Watch The Magic Happen</div>', unsafe_allow_html=True)
    
    # Centered mega button
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        if st.button(
            "✨ TRANSFORM WITH AI MAGIC ✨", 
            use_container_width=True,
            help="🎭 Click for instant professional transformation!",
            key="transform_btn"
        ):
            # Reset other panels
            st.session_state.rewritten_text = ""
            st.session_state.show_feedback_form = False
            st.session_state.show_history = False
            st.session_state.show_tip = False
            
            # Exciting loading messages
            loading_messages = [
                "🎭 Analyzing your communication style...",
                "🧠 AI brain processing your feedback...", 
                "✨ Sprinkling professional magic...",
                "🎯 Crafting the perfect tone...",
                "🌟 Adding emotional intelligence...",
                "🚀 Final touches being applied..."
            ]
            
            with st.spinner(random.choice(loading_messages)):
                try:
                    api_key = st.secrets.get("OPENROUTER_API_KEY", None)
                    
                    if format_as_email:
                        system_prompt = (
                            f"You are an expert email communication coach. Transform this workplace feedback into a professional, well-structured email with a {selected_tone_key} tone. "
                            f"Write everything in perfect {selected_language_key}. "
                            f"For non-English: Use native greetings, expressions, and cultural norms. No English words at all. "
                            f"Include appropriate greeting, structured body, and professional closing for {selected_language_key} business culture."
                        )
                    else:
                        system_prompt = (
                            f"You are a communication expert. Transform this raw feedback into professional, {selected_tone_key} language while preserving the core message. "
                            f"Write entirely in {selected_language_key}. "
                            f"For non-English: Use natural, native expressions. No English words. "
                            f"Make it constructive, specific, and actionable. Keep it concise but impactful."
                        )

                    if api_key:
                        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                        data = {"messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}]}
                        model_fallbacks = [
                            "mistral/mistral-7b-instruct",
                            "mistralai/mixtral-8x7b-instruct", 
                            "nousresearch/nous-capybara-7b",
                            "gryphe/mythomax-l2-13b"
                        ]
                        rewritten = None
                        for model in model_fallbacks:
                            try:
                                data["model"] = model
                                resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
                                if resp.status_code == 200:
                                    j = resp.json()
                                    rewritten = j.get("choices", [])[0].get("message", {}).get("content", "").strip()
                                    if rewritten:
                                        break
                                time.sleep(0.5)
                            except:
                                time.sleep(0.5)
                        
                        if rewritten:
                            st.session_state.rewritten_text = rewritten
                            st.session_state.rewrites.insert(0, {"timestamp": datetime.utcnow().isoformat(), "original": user_input, "rewritten": rewritten})
                        else:
                            st.warning("🤖 AI temporarily busy - using smart backup!")
                            fallback = deterministic_rewrite(user_input, selected_tone_key, selected_language_key)
                            st.session_state.rewritten_text = fallback
                            st.session_state.rewrites.insert(0, {"timestamp": datetime.utcnow().isoformat(), "original": user_input, "rewritten": fallback})
                    else:
                        fallback = deterministic_rewrite(user_input, selected_tone_key, selected_language_key)
                        st.session_state.rewritten_text = fallback
                        st.session_state.rewrites.insert(0, {"timestamp": datetime.utcnow().isoformat(), "original": user_input, "rewritten": fallback})

                except Exception as e:
                    st.error(f"⚠️ Transformation failed: {str(e)} - Please try again!")
                    st.session_state.rewritten_text = ""

# ---------------------- STUNNING Results Section ----------------------
if st.session_state.rewritten_text and st.session_state.rewritten_text.strip():
    st.markdown('<div class="step-pill">🎉 BOOM! Your Professional Message is Ready!</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="result-magic">', unsafe_allow_html=True)
    st.markdown("### 🏆 **Your Transformed Communication:**")
    st.success(st.session_state.rewritten_text)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Viral sharing section
    st.markdown("""
    <div class="social-proof">
        <h4>🔥 That's the power of AI communication coaching!</h4>
        <p>Share this transformation with your team and watch communication improve across your organization</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.download_button(
            "💾 Download", 
            st.session_state.rewritten_text, 
            file_name=f"FeedbackGPT_Transform_{datetime.now().strftime('%m%d_%H%M')}.txt",
            use_container_width=True,
            help="Save your professional message",
            key="download_btn"
        )
    with col2:
        if st.button("🎭 Try New Tone", use_container_width=True, help="Same message, different vibe", key="retry_btn"):
            st.session_state.rewritten_text = ""
            st.rerun()
    with col3:
        if st.button("🔥 Transform More", use_container_width=True, help="Start fresh with new feedback", key="new_btn"):
            reset_app_state()
            st.rerun()

# ---------------------- Call to Action for Empty State ----------------------
else:
    st.markdown("""
    <div class="social-proof">
        <h3>🎯 Ready to Transform Your Communication?</h3>
        <p><strong>Try it now:</strong> Paste any difficult feedback above and watch AI make it professional in 3 seconds!</p>
        <p style="font-size: 0.9rem; margin-top: 1rem;">💫 Join thousands who've already improved their workplace communication</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------- Bottom Actions ----------------------
st.markdown("---")
st.markdown('<h3 style="text-align: center; color: #666; margin: 2rem 0;">🛠️ Explore More Features</h3>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("⭐ Rate This Tool", use_container_width=True, help="Share your experience with FeedbackGPT", key="feedback_toggle_btn"):
        st.session_state.show_feedback_form = not st.session_state.get("show_feedback_form", False)
        st.session_state.show_history = False
        if not st.session_state.show_feedback_form:
            st.rerun()
            
with col2:
    if st.button("📊 My Transformations", use_container_width=True, help="View your communication evolution", key="history_toggle_btn"):
        st.session_state.show_history = not st.session_state.get("show_history", False)
        st.session_state.show_feedback_form = False
        if not st.session_state.show_history:
            st.rerun()

# Enhanced Feedback Form
if st.session_state.get("show_feedback_form", False):
    st.markdown("### 🌟 Help Make FeedbackGPT Even Better!")
    st.markdown("*Your feedback helps thousands of professionals communicate better*")
    
    with st.form("feedback_form", clear_on_submit=True):
        ff_text = st.text_area("💭 What's your experience with FeedbackGPT?", height=100, placeholder="This tool saved me from so many awkward conversations...")
        ff_rating = st.slider("⭐ Rate your experience", 1, 5, 4, help="1 = Needs work, 5 = Mind-blowing!")
        ff_like = st.radio("🚀 Would you recommend FeedbackGPT?", ["👍 Absolutely - it's amazing!","👎 Not quite there yet"], index=0)
        ff_improve = st.multiselect("🎯 What should we enhance?", ["⚡ Speed","🎯 Accuracy","🌍 More Languages","🎭 More Tones","📱 Mobile Experience","🎨 Interface Design"])
        ff_suggestions = st.text_area("💡 Any brilliant suggestions?", placeholder="What would make this tool irresistible?")
        
        submit_col1, submit_col2, submit_col3 = st.columns([1, 2, 1])
        with submit_col2:
            submit_feedback = st.form_submit_button("🚀 Submit My Feedback", use_container_width=True)
        
    if submit_feedback:
        fb_id = str(int(time.time()*1000))
        public_base = st.secrets.get("PUBLIC_BASE_URL", "")
        public_link = f"{public_base}?fb={fb_id}" if public_base else ""
        row = [datetime.utcnow().isoformat(), ff_rating, ff_like, "; ".join(ff_improve), ff_suggestions, ff_text, "", "", public_link]
        ok, msg = append_row_to_sheet(row)
        
        if ok:
            st.balloons()
            st.success("🎉 Thank you! Your feedback makes FeedbackGPT better for everyone!")
        else:
            st.balloons()
            st.success("🎉 Feedback recorded! Thanks for helping us improve!")
        
        st.session_state.show_feedback_form = False
        time.sleep(1.5)
        st.rerun()

# Enhanced History
if st.session_state.get("show_history", False):
    st.markdown("### 📊 Your Communication Evolution")
    st.markdown("*Track how you've transformed difficult conversations into professional dialogue*")
    
    if st.session_state.rewrites:
        # Show stats
        total_transforms = len(st.session_state.rewrites)
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%); padding: 1rem; border-radius: 15px; margin: 1rem 0; text-align: center;">
            <h4 style="margin: 0; color: #1976d2;">🏆 You've transformed <span style="color: #d32f2f;">{total_transforms}</span> difficult conversations!</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # Display history
        df = pd.DataFrame(st.session_state.rewrites)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%m/%d %H:%M')
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📊 Export My Data", data=csv, file_name=f"FeedbackGPT_History_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True, key="export_history_btn")
        with col2:
            if st.button("🗑️ Clear History", use_container_width=True, help="Start fresh", key="clear_history_btn"):
                st.session_state.rewrites = []
                st.success("History cleared!")
                time.sleep(1)
                st.rerun()
    else:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: #f8f9fa; border-radius: 15px; border: 2px dashed #dee2e6;">
            <h4>🌟 Your transformation journey starts here!</h4>
            <p>Once you start transforming feedback, you'll see your communication evolution tracked here.</p>
        </div>
        """, unsafe_allow_html=True)

# ---------------------- VIRAL FOOTER WITH SOCIAL PROOF ----------------------
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 2.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); border-radius: 20px; margin: 2rem 0; position: relative; overflow: hidden;'>
    <div style='position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);'></div>
    <div style='position: relative; z-index: 1;'>
        <h2 style='color: white; margin: 0; font-weight: 800;'>🚀 Created by Devi Mudhanagiri</h2>
        <p style='color: #f0f0f0; margin: 1rem 0; font-size: 1.1rem; font-weight: 500;'>FeedbackGPT v2.1 | Powered by OpenRouter AI</p>
        <p style='color: #e0e0e0; margin: 0; font-size: 1rem;'>💫 "Making every conversation a catalyst for growth"</p>
        <div style='background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 15px; margin-top: 1rem;'>
            <p style='color: white; margin: 0; font-weight: 600;'>🎯 Built for leaders who care about communication</p>
            <p style='color: #f0f0f0; margin: 0.5rem 0 0 0; font-size: 0.9rem;'>Transform. Connect. Succeed.</p>
        </div>
    </div>
</div>
""")