import streamlit as st
import requests
import time
import pandas as pd
import json
from datetime import datetime
import random
import os
import csv

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
    """Complete reset to initial state"""
    # Clear everything except initialize fresh state
    st.session_state.clear()
    st.session_state["rewritten_text"] = ""
    st.session_state["user_input"] = ""
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
    page_title="🎯 REFRAME - A Communication Coach", 
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
    
    .result-box {
        background: linear-gradient(135deg, #e8f5e8 0%, #f0fff0 100%);
        padding: 2rem;
        border-radius: 20px;
        border: 3px solid #4CAF50;
        margin: 2rem 0;
        box-shadow: 0 15px 35px rgba(76, 175, 80, 0.3);
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
    
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 1.5rem;
        margin: 1.5rem 0;
        max-width: 100%;
    }
    
    .feature-card {
        background: white;
        padding: 1.8rem 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
        border: 2px solid #f0f0f0;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        position: relative;
        overflow: hidden;
        cursor: pointer;
        z-index: 1;
    }

    .feature-card:hover {
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 30px rgba(0, 0, 0, 0.15);
        border-color: #4A90E2;
        z-index: 2;
    }

    .feature-card h4 {
        margin: 0 0 0.8rem 0;
        font-size: 1.2rem;
        color: #333;
        font-weight: 600;
        transition: color 0.3s ease;
    }

    .feature-card p {
        margin: 0;
        color: #666;
        font-size: 0.95rem;
        line-height: 1.4;
        transition: color 0.3s ease;
    }

    .feature-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(135deg, rgba(74, 144, 226, 0.05), rgba(80, 200, 120, 0.05));
        opacity: 0;
        transition: opacity 0.4s ease;
        pointer-events: none;
        z-index: -1;
    }

    .feature-card:hover::before {
        opacity: 1;
    }

    .creator-footer {
        text-align: center; 
        padding: 2.5rem; 
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%); 
        border-radius: 20px; 
        margin: 2rem 0; 
        position: relative; 
        overflow: hidden;
        color: white;
    }
    
    .creator-footer::before {
        content: '';
        position: absolute; 
        top: 0; 
        left: 0; 
        right: 0; 
        bottom: 0; 
        background: rgba(255,255,255,0.1); 
        backdrop-filter: blur(10px);
    }
    
    .creator-content {
        position: relative; 
        z-index: 1;
    }
    
    .creator-title {
        color: white; 
        margin: 0; 
        font-weight: 800;
        font-size: 2rem;
    }
    
    .creator-subtitle {
        color: #f0f0f0; 
        margin: 1rem 0; 
        font-size: 1.1rem; 
        font-weight: 500;
    }
    
    .creator-tagline {
        color: #e0e0e0; 
        margin: 0; 
        font-size: 1rem;
    }
    
    .creator-box {
        background: rgba(255,255,255,0.2); 
        padding: 1rem; 
        border-radius: 15px; 
        margin-top: 1rem;
    }
    
    .creator-mission {
        color: white; 
        margin: 0; 
        font-weight: 600;
    }
    
    .creator-vision {
        color: #f0f0f0; 
        margin: 0.5rem 0 0 0; 
        font-size: 0.9rem;
    }

    /* === Dark Mode Specific CSS Fixes === */
    @media (prefers-color-scheme: dark) {
        .hero-tagline {
            color: #ccc;
        }

        .tagline-sub {
            color: #bbb;
        }
    
        /* Fixes for Result Box */
        .result-box {
            background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
            border: 3px solid #1abc9c;
            color: #ecf0f1;
            box-shadow: 0 15px 35px rgba(26, 188, 156, 0.3);
        }

        /* Fixes for Pro Tips */
        .st-emotion-cache-1g83y1x div[data-testid="stMarkdownContainer"] div {
            background: #34495e !important;
            border: 2px solid #f39c12 !important;
            color: #ecf0f1 !important;
        }

        /* Fixes for Magic Recipe */
        .st-emotion-cache-1g83y1x div[data-testid="stMarkdownContainer"] div {
            background: #2c3e50 !important;
            border: 1px solid #1abc9c !important;
            color: #ecf0f1 !important;
        }

        /* Fixes for Stats Banner */
        .stats-banner {
            background: linear-gradient(135deg, #1f2e3d 0%, #2c3e50 100%) !important;
            color: #ecf0f1 !important;
        }
        
        /* Fixes for empty history state */
        .st-emotion-cache-1g83y1x div[data-testid="stMarkdownContainer"] div {
            background: #2c3e50 !important;
            border: 2px dashed #34495e !important;
            color: #ecf0f1 !important;
        }

        /* Fix for the feature cards */
        .feature-card {
            background: #2c3e50;
            border: 2px solid #34495e;
        }
        .feature-card h4 {
            color: #ecf0f1;
        }
        .feature-card p {
            color: #bdc3c7;
        }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------- VIRAL HERO SECTION ----------------------
st.markdown(
    """
    <style>
    @keyframes floatIn {
        from {
            opacity: 0;
            transform: translateY(30px) scale(0.95);
        }
        to {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    @keyframes pulseGlow {
        0% {
            text-shadow: 
                0 0 5px rgba(74, 144, 226, 0.2);
        }
        50% {
            text-shadow: 
                0 0 10px rgba(80, 200, 120, 0.3);
        }
        100% {
            text-shadow: 
                0 0 5px rgba(74, 144, 226, 0.2);
        }
    }

    .hero-main {
        text-align: center;
        margin: 1.5rem 0 1rem;
        animation: floatIn 1s ease-out forwards;
    }

    .hero-main h1 {
        font-size: 5rem;
        font-weight: 800;
        margin: 0;
        font-family: 'Poppins', sans-serif;
        background: linear-gradient(90deg, #1E40AF, #3B82F6); /* Vibrant yet clear blue gradient */
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
        position: relative;
        display: inline-block;
        transform: skew(-3deg);
        animation: pulseGlow 3s ease-in-out infinite alternate;
        filter: none; /* Removed shadow for clarity */
    }

    .hero-tagline {
        text-align: center;
        font-size: 2rem;
        font-family: 'Poppins', sans-serif;
        font-weight: 700;
        margin: 0.8rem auto;
        max-width: 700px;
        padding: 0 1rem;
        background: none;
        color: #222;
    }

    .tagline-focus {
        background: linear-gradient(90deg, #DC2626, #16A34A); /* Red to green gradient for contrast */
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.3rem;
        letter-spacing: -.5px;
        animation: pulseGlow 2.5s ease-in-out infinite alternate;
        filter: none; /* Removed shadow for clarity */
        display: block;
        margin: 0 auto;
    }

    .tagline-sub {
        display: block;
        font-size: 1.25rem;
        color: #555;
        font-weight: 500;
        margin: 0.4rem auto 0;
        opacity: 0.92;
        max-width: 600px;
    }

    .viral-cta {
        font-size: 1.9rem;
        font-weight: 600;
        color: #333;
        margin: 1rem auto;
        max-width: 750px;
        opacity: 0;
        animation: fadeIn 1.2s ease-in 0.8s forwards;
    }

    @media (max-width: 768px) {
        .hero-main h1 {
            font-size: 3.5rem;
            transform: skew(0deg);
        }
        .hero-tagline, .viral-cta {
            font-size: 1.3rem;
            padding: 0 1rem;
        }
        .tagline-focus {
            font-size: 1.5rem;
        }
        .tagline-sub {
            font-size: 1rem;
            max-width: 90%;
        }
    }
    </style>

    <div class="hero-main">
        <h1>Reframe</h1>
    </div>
    <p class="hero-tagline">
        <span class="tagline-focus">Turn Critique Into Connection</span>
        <span class="tagline-sub">Help your message land with empathy, clarity, and purpose</span>
    </p>
    """,
    unsafe_allow_html=True
)
# ---------------------- Social Proof Banner ----------------------
st.markdown("""
<div class="stats-banner">
    <h3 style="margin: 0; font-size: 1.4em;">✨ Reframe with Confidence, in Any Context</h3>
    <p style="margin: 0.5rem 0 0 0; font-size: 1.1em;">
        Turn harsh feedback into professional messages — instantly • Across languages • For every tone
    </p>
</div>
""", unsafe_allow_html=True)

# ---------------------- IMPROVED Feature Showcase (6 cards) ----------------------
st.markdown("""
<div class="feature-grid">
    <div class="feature-card">
        <h4>🎭 Perfect Tone Every Time</h4>
        <p>From warm to direct — match your message to the moment</p>
    </div>
    <div class="feature-card">
        <h4>🌍 Speak Their Language</h4>
        <p>Communicate clearly in multiple languages, with cultural nuance</p>
    </div>
    <div class="feature-card">
        <h4>📧 Ready-to-Send Emails</h4>
        <p>Get full emails with greeting, body, and closing — no drafting needed</p>
    </div>
    <div class="feature-card">
        <h4>⚡ Instant Reframing</h4>
        <p>Transform awkward messages in seconds — faster than typing</p>
    </div>
    <div class="feature-card">
        <h4>🧠 Context-Aware Rewrites</h4>
        <p>Preserves intent while improving clarity, tone, and impact</p>
    </div>
    <div class="feature-card">
        <h4>📊 Track Your Growth</h4>
        <p>See how you’re improving — with history, stats, and exportable logs</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------- Motivational Block (New Top Position) ----------------------
st.markdown("""
<div class="social-proof">
    <h3>🎯 Ready to Transform Your Communication?</h3>
    <p><strong>Try it now:</strong> Paste any challenging feedback, and see your message transformed into a polished, professional version instantly!</p>
    <p style="font-size: 0.9rem; margin-top: 1rem;">💫 Join thousands who've already improved their workplace communication</p>
</div>
""", unsafe_allow_html=True)
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
if st.session_state.user_input and st.session_state.user_input.strip():
    st.markdown('<div class="step-pill">⚙️ STEP 2: Choose Your Communication Style</div>', unsafe_allow_html=True)
    
    # Clean layout without problematic containers
    col1, col2 = st.columns([2, 1])
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
        format_as_email = st.checkbox(
            "📧 Email Mode", 
            value=st.session_state.get("format_as_email", False),
            help="Complete email with greeting & closing",
            key="email_checkbox"
        )
        st.session_state.format_as_email = format_as_email
        
        # Magic Recipe aligned properly
        st.markdown("**🔮 Magic Recipe:**")
        preview_parts = [tone_options[selected_tone_key].split(" - ")[0]]
        if format_as_email:
            preview_parts.append("Email")
        if selected_language_key != "English":
            preview_parts.append(language_options[selected_language_key].split(" ")[1])
        
        st.markdown(f"""
        <div style="background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 0.6rem; border-radius: 8px; margin-top: 0.3rem; text-align: center; font-weight: 600; font-size: 0.9rem;">
            {" + ".join(preview_parts)}
        </div>
        """, unsafe_allow_html=True)
    
    # ---------------------- VIRAL TRANSFORM BUTTON ----------------------
    st.markdown('<div class="step-pill">🚀 STEP 3: Watch The Magic Happen</div>', unsafe_allow_html=True)
    
    # Add a clear instructional message
    st.markdown("<p style='text-align: center; font-size: 1.2rem; font-weight: 600; color: #555;'>Ready to transform your message? Click the button below!</p>", unsafe_allow_html=True)
    
    # Centered mega button
    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        if st.button(
            "✨  Reframe your message  ✨", 
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
                "🧠 Processing your feedback...", 
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
                            f"You are an expert workplace communication coach. "
                            f"Transform the following feedback into a professional, well-structured email written **by the user to a colleague, peer, or team member** — not as a self-reflection or response to feedback they received. "
                            f"Use a {selected_tone_key} tone: warm, constructive, and appropriate for workplace dynamics. "
                            f"Write everything in perfect {selected_language_key}. "
                            f"For non-English: Use native greetings, expressions, and cultural norms. No English words at all. "
                            f"Structure the email with a clear greeting, body (with context and suggestion), and professional closing that fits {selected_language_key} business culture. "
                            f"Never write from the perspective of someone apologizing for their own mistake unless explicitly stated. "
                            f"The goal is to help the recipient grow — kindly, clearly, and respectfully."
                        )
                    else:
                        system_prompt = (
                            f"You are a communication expert helping professionals deliver better feedback. "
                            f"Rewrite the following raw message into clear, professional language with a {selected_tone_key} tone. "
                            f"This feedback is **from the user to someone else** (e.g., a teammate or report), not about themselves. "
                            f"Do NOT turn it into a self-critique or apology. Do NOT use first-person if the original isn't about the user. "
                            f"Write entirely in {selected_language_key}, using natural, native expressions. No English words. "
                            f"Make the feedback constructive, specific, and actionable — kind but clear. Keep it concise and impactful. "
                            f"Preserve the core message, but elevate tone and clarity for healthy workplace communication."
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

# ---------------------- CLEAN Results Section (NO ANIMATIONS) ----------------------
if st.session_state.rewritten_text and st.session_state.rewritten_text.strip():
    st.markdown('<div class="step-pill">🎉 BOOM! Your Reframed Message is Ready!</div>', unsafe_allow_html=True)
    
    # Simple, clean result display without animations
    st.markdown(f"""<div class="result-box"><h3>🎯 Your Words, Reimagined.</h3><p style="white-space: pre-wrap;">{st.session_state.rewritten_text}</p></div>""", unsafe_allow_html=True)
    
    # Viral sharing section
    st.markdown("""
    <div class="social-proof">
        <h4>🔥 That’s the magic of REFRAME—your personal communication coach, helping you craft impactful messages effortlessly!</h4>
        <p>Share this transformation with your team and watch communication improve across your organization</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.download_button(
            "💾 Download", 
            st.session_state.rewritten_text, 
            file_name=f"REFRAME_Transform_{datetime.now().strftime('%m%d_%H%M')}.txt",
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

# ---------------------- Bottom Actions ----------------------
st.markdown("---")
st.markdown('<h3 style="text-align: center; color: #666; margin: 2rem 0;">🛠️ Explore More Features</h3>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("⭐ Rate This Tool", use_container_width=True, help="Share your experience with REFRAME", key="feedback_toggle_btn"):
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
    st.markdown("### 🌟 Help Make REFRAME Even Better!")
    st.markdown("*Your feedback helps thousands of professionals communicate better*")

    with st.form("feedback_form", clear_on_submit=True):
        ff_text = st.text_area("💭 What's your experience with REFRAME?", height=100, placeholder="This tool saved me from so many awkward conversations...")
        ff_rating = st.slider("⭐ Rate your experience", 1, 5, 4, help="1 = Needs work, 5 = Mind-blowing!")
        ff_like = st.radio("🚀 Would you recommend REFRAME?", 
                          ["👍 Absolutely! I'd recommend it", "🙂 Yes, with a few suggestions", 
                           "😐 Neutral – it's okay", "👎 Not right now"], index=0)
        ff_improve = st.multiselect("🎯 What should we enhance?", 
                                   ["⚡ Speed", "🎯 Accuracy", "🌍 More Languages", 
                                    "🎭 More Tones", "📱 Mobile Experience", "🎨 Interface Design", 
                                    "📦 More Templates", "🔍 Context Awareness", "💡 Smarter Suggestions"])
        ff_suggestions = st.text_area("💡 Any brilliant suggestions?", placeholder="What would make this tool irresistible?")
        
        submit_col1, submit_col2, submit_col3 = st.columns([1, 0.2, 1])
        with submit_col1:
            if st.form_submit_button("❌ Close", use_container_width=True):
                st.session_state.show_feedback_form = False
                st.rerun()

        with submit_col3:
            submit_feedback = st.form_submit_button("🚀 Submit", use_container_width=True)
        
    if submit_feedback:
        # Generate ID and public link
        fb_id = str(int(time.time() * 1000))
        public_base = st.secrets.get("PUBLIC_BASE_URL", "")
        public_link = f"{public_base}?fb={fb_id}" if public_base else ""

        # Prepare row for Google Sheets and CSV
        timestamp = datetime.utcnow().isoformat()
        improvements_str = "; ".join(ff_improve) if ff_improve else ""
        row = [
            timestamp,
            ff_rating,
            ff_like,
            improvements_str,
            ff_suggestions,
            ff_text,          # original input
            "",               # rewritten (not used in feedback)
            "",               # user_email
            public_link
        ]

        # ✅ 1. Save to Google Sheets (primary)
        ok, msg = append_row_to_sheet(row)

        # ✅ 2. Always save to local CSV as fallback
        import os
        import csv

        csv_file = "feedback_local.csv"
        file_exists = os.path.isfile(csv_file)

        try:
            with open(csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Write header if file is new
                if not file_exists:
                    writer.writerow([
                        "timestamp", "rating", "like", "improvements", "suggestions",
                        "original", "rewritten", "user_email", "public_link"
                    ])
                # Write the feedback row
                writer.writerow(row)
        except Exception as e:
            # Log if needed, but don't break the flow
            pass  # Silent fallback — CSV is best-effort

        # ✅ 3. Success & Rerun
        st.balloons()
        if ok:
            st.success("🎉 Thank you! Your feedback makes REFRAME better for everyone!")
        else:
            st.success("🎉 Feedback recorded! Thanks for helping us improve!")

        st.session_state.show_feedback_form = False
        st.rerun()  # ← Right after state update

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
        # Get last 10 rewrites (most recent first)
        rewrites = st.session_state.rewrites[-10:]  # Last 10
        df = pd.DataFrame(rewrites)
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%m/%d %H:%M')
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📊 Export My Data", data=csv, file_name=f"REFRAME_History_{datetime.now().strftime('%Y%m%d')}.csv", use_container_width=True, key="export_history_btn")
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

# ---------------------- Public Feedback Viewer ----------------------
def show_public_feedback():
    rows = []

    # Try Google Sheets first
    try:
        client = gs_client_from_secrets()
        if client:
            sh = client.open("feedback_rewriter_history")
            worksheet = sh.sheet1
            sheet_data = worksheet.get_all_values()
            if len(sheet_data) > 1:
                rows = sheet_data[1:]  # skip header
    except Exception as e:
        st.write("🔍 Debug: Google Sheets failed — falling back to CSV.")  # Optional debug
        rows = []

    # Fallback to local CSV — only if Google Sheets failed OR no rows
    if not rows and os.path.isfile("feedback_local.csv"):
        try:
            with open("feedback_local.csv", newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                file_rows = list(reader)
                if file_rows:  # Only use if not empty
                    rows = file_rows
        except Exception:
            #st.write(f"🔍 Debug: CSV read failed: {e}")
            rows = []

    # ✅ Check if we have any rows
    if rows:
        df = pd.DataFrame(rows, columns=[
            "timestamp", "rating", "like", "improvements", "suggestions",
            "original", "rewritten", "user_email", "public_link"
        ])

        # Clean and convert
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        df = df.dropna(subset=['rating', 'timestamp'])  # Drop invalid

        if df.empty:
            st.info("No valid feedback found. Please share yours! 💌")
            return

        # Sort: highest rating first, then newest
        df = df.sort_values(by=['rating', 'timestamp'], ascending=[False, False]).reset_index(drop=True)

        st.markdown("### 🌟 What Others Are Saying")

        # Prepare display
        display_df = df[["timestamp", "rating", "suggestions"]].copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%b %d, %Y')
        display_df.rename(columns={
            "timestamp": "📅 Date",
            "rating": "⭐",
            "suggestions": "💬 Feedback"
        }, inplace=True)

        # Highlight 4–5 star feedback
        def highlight_row(row):
            try:
                if row["⭐"] >= 4:
                    return ['background-color: #f0fff0; color: #0a310a'] * len(row)
                return [''] * len(row)
            except:
                return [''] * len(row)

        st.dataframe(
            display_df.style.apply(highlight_row, axis=1),
            use_container_width=True,
            hide_index=True,
            column_config={
                "⭐": st.column_config.NumberColumn(format="%.1f ⭐"),
                "💬 Feedback": "Feedback",
                "📅 Date": "Date"
            }
        )

        # Spotlight top review
        top = df.iloc[0]
        if top['rating'] >= 4:
            with st.expander("✨ Featured Community Review", expanded=False):
                st.markdown(f"""
                > "{top['suggestions']}"
                > 
                > — Rated {top['rating']:.1f}⭐ on {top['timestamp'].strftime('%B %d')}"
                """)
    else:
        st.info("No feedback yet — be the first to share how REFRAME helped you craft better messages! 💌")
        

# Trigger Public Feedback Viewer
if st.button("💬 What Others Say", use_container_width=True, help="See real feedback from users like you"):
    show_public_feedback()


# ---------------------- FIXED FOOTER WITH PROPER HTML RENDERING ----------------------
st.markdown("---")
st.markdown("""
<div class="creator-footer">
    <div class="creator-content">
        <h2 class="creator-title">🚀 Created by Devi Mudhanagiri</h2>
        <p class="creator-subtitle">REFRAME v2.0 | Powered by OpenRouter AI</p>
        <p class="creator-tagline">💫 "Making every conversation a catalyst for growth"</p>
        <div class="creator-box">
            <p class="creator-mission">🎯 Built for leaders who care about communication</p>
            <p class="creator-vision">Transform. Connect. Succeed.</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)