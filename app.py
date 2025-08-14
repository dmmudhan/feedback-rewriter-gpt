import streamlit as st
import requests
import time
import pandas as pd
import json
from datetime import datetime
from pytz import timezone
import random
import os
import csv
import logging

# Define the UTC timezone variable once and use it throughout the app.
UTC_TZ = timezone('UTC')

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

PUBLIC_URL = st.secrets.get("public_app_url", "https://feedback-rewriter-gpt-caht6hciagxykx52hz6xnh.streamlit.app/")

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
        logging.info("Successfully loaded GSS credentials.") 
        return gspread.authorize(creds)
    except Exception as e:
        logging.error(f"Google Sheets credential error: {e}")
        return None

def append_row_to_sheet(row, sheet_name="reframe_app_feedback"):
    client = gs_client_from_secrets()
    if not client:
        logging.error("Failed to authorize Google Sheets client.")
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
        st.success("Successfully appended row to Google Sheet.")
        return True, "OK"
    except Exception as e:
        logging.error(f"Failed to append row: {str(e)}")
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
# PROPER Session State Initialization
if "app_session_id" not in st.session_state:
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
    st.session_state["continue_btn_clicked"] = False
    
# The reset function is fine to be called from buttons, but should not be called globally.
def reset_app_state():
    """Complete reset to initial state"""
    st.session_state.clear()
    # The app will re-initialize with the defaults above on the next rerun
    st.rerun()

# ---------------------- App Config ----------------------
st.set_page_config(
    page_title="🎯 REFRAME - Elevate Your Message", 
    page_icon="🪄", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

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
    
    .pro-tip-box {
        background: linear-gradient(135deg, #d4edda 0%, #d4f0e0 100%); 
        border: 2px solid #28a745;
        border-radius: 15px; 
        padding: 1.2rem; 
        margin: 1rem 0; 
        animation: fadeIn 0.5s ease-in-out;
        box-shadow: 0 4px 12px rgba(40, 167, 69, 0.2);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
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
    
    /* FIXED SOCIAL ICONS CSS */
    .social-proof {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 2rem 0;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
    }
    
    .social-links-container {
        display: flex;
        justify-content: center;
        gap: 2rem;
        margin-top: 1.5rem;
        flex-wrap: wrap;
    }
    
    .social-link {
        display: inline-block;
        width: 60px;
        height: 60px;
        border-radius: 50%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        position: relative;
        overflow: hidden;
        text-decoration: none;
    }
    
    .social-link:hover {
        transform: translateY(-5px) scale(1.1);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    
    .social-icon {
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: 700;
        text-decoration: none;
        font-family: 'Poppins', sans-serif;
    }
    
    .linkedin-bg {
        background: linear-gradient(135deg, #0077B5, #005885);
    }
    
    .twitter-bg {
        background: linear-gradient(135deg, #1DA1F2, #0d8bd9);
    }
    
    .facebook-bg {
        background: linear-gradient(135deg, #1877F2, #166fe5);
    }
    
    /* Text-specific styling for each platform */
    .linkedin-text {
        font-size: 20px;
        font-weight: 700;
        letter-spacing: -1px;
    }
    
    .twitter-text {
        font-size: 18px;
        font-weight: 700;
    }
    
    .facebook-text {
        font-size: 24px;
        font-weight: 700;
    }
    
    /* Dark Mode specific styles for the result box */
    @media (prefers-color-scheme: dark) {
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
        .st-emotion-cache-1g83y1x div[data-testid="stMarkdownContainer"] div {
            background: linear-gradient(135deg, #1f2e3d 0%, #2c3e50 100%) !important;
            color: #ecf0f1 !important;
        }
        
        /* Fixes for empty history state */
        .st-emotion-cache-1g83y1x div[data-testid="stMarkdownContainer"] div {
            background: #2c3e50 !important;
            border: 2px dashed #34495e !important;
            color: #ecf0f1 !important;
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
        margin: 1.5rem 0 0.2rem;
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
        margin: 0.2rem auto;
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
        <span class="tagline-sub">Every word, refined. From praise to critique!</span>
    </p>
    """,
    unsafe_allow_html=True
)
# ---------------------- Social Proof Banner ----------------------
st.markdown("""
<div class="stats-banner">
    <h3 style="margin: 0; font-size: 1.4em;">✨ Communicate with Confidence, in Any Context</h3>
    <p style="margin: 0.5rem 0 0 0; font-size: 1.1em;">
        Turn critiques into conversations and praise into motivation — instantly • Across languages • For every tone
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

# Check if feedback was just submitted
if st.session_state.get("feedback_submitted"):
    st.balloons()
    st.success("🎉 Thank you! Your feedback makes REFRAME better for everyone!")
    st.session_state.feedback_submitted = False

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
    "You never help your teammates and only care about yourself.",
    "Why did you refactor working code that wasn’t even assigned to you?",
    "The project is way behind schedule because you didn't deliver your part on time.",
    "I disagree with your proposal, it's just not going to work.",
    "You're not a good fit for this team, your personality clashes with everyone.",
    "This report is useless. The data is all wrong and the conclusions don't make sense.",
    "You need to be more proactive. I shouldn't have to follow up with you all the time.",
    "I'm not happy with your performance. You've been making a lot of simple mistakes lately.",
    "We trust you to manage your time — but you must be online from 9–5.",
    "We need to let you go. This role is no longer a good fit for the company's direction.",
    "You are not meeting the performance expectations of your role. There's been no improvement since our last talk.",
    "Your behavior in meetings is unprofessional and is making your colleagues uncomfortable.",
    "You've been out of compliance with company policy regarding expense reports for three months.",
    "The last employee survey showed a high level of dissatisfaction with your department's leadership.",
    "You missed the sprint deadline again. This is impacting the entire team's velocity.",
    "Your user stories are consistently incomplete at the end of the sprint.",
    "You're not actively participating in our daily stand-ups and that's not what Scrum is about.",
    "Your task estimates are consistently inaccurate, making sprint planning impossible.",
    "You are not updating your tasks on the board, which makes it hard for the team to see what's a blocker.",
    "You're not responding to emails, only DMs and texts. That's not how we do professional communication here.",
    "Per my last email: I told you twice already.",
    "We value feedback — but don’t question leadership decisions.",
    "You committed directly to main again. We have a branch policy for a reason.",
    "Thanks for working weekends! We’ll 'keep it in mind during reviews'.",
    "You said the work was 'cringe' and not a good use of your time. This is part of the job.",
    "The way you handled that disagreement on LinkedIn violated our social media policy.",
    "You completely ignored the formal process for requesting time off and just messaged me directly.",
    "You're constantly missing team meetings or leaving early without warning. It's unprofessional.",
    "You haven't completed the mandatory compliance training, which is putting the team at risk.",
    "You've been taking days off without formally applying for leave through the HR system.",
    "You were out on long-term leave for a week and I had no idea until a colleague told me.",
    "Your promotion to Senior Developer is effective next Monday. Congrats.",
    "We expect you to be available after hours during 'critical releases'.",
    "I'm giving you a promotion. It comes with more responsibilities so get ready.",
    "We decided to promote you. You'll have a new title and salary.",
    "It's your fifth anniversary. Keep up the good work.",
    "Congrats on ten years. Your team couldn't have done it without you.",
    "Your salary increase request cannot be approved at this time. We need to stick to the budget.",
    "Your performance is below expectations. I need you to show more initiative and ownership.",
    "We're making changes and your position is being eliminated. We have to let you go.",
    "The feedback we've received indicates that you are not a team player.",
    "I’m resigning — not because of the pay, but because I’m doing 3 people’s jobs.",
    "Your current work is not meeting the quality standards we expect from a senior role.",
    "I'm resigning because I was promised growth but got stuck doing the same thing for a year.",
    "It's time for me to leave — I can't keep covering for your poor management.",
    "I'm stepping down because the team culture feels toxic and no one holds themselves accountable.",
    "I'm out — I gave my best, but my efforts were never recognized.",
    "I'm leaving because I found a place that values work-life balance — something we clearly don’t have here."
]

# ---------------------- Step 1: EXCITING Input Section ----------------------
st.markdown('<div class="step-pill">🎯 STEP 1: Drop Your Raw, Honest Feedback Here</div>', unsafe_allow_html=True)
  
# Viral action buttons
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    if st.button("💡 Instant Inspiration!", use_container_width=True, help="Get a random example to kickstart your reframe", key="sample_btn"):
        #reset_app_state()
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
                "💡 **The Feedback Sandwich:** Start with praise, deliver the critique, and end with a positive look forward. It makes tough conversations a little softer.",
                "🎯 **Speak in Data, Not Drama:** Instead of 'You're always late,' try 'I've noticed you've been late to our last three stand-ups.' Facts are less emotional.",
                "🤝 **Replace 'You' with 'We':** Turn 'You need to fix this' into 'How can we work together to solve this?' It shifts blame to collaboration.",
                "⏰ **The 24-Hour Rule:** Don't let feedback go stale. Deliver it within a day to keep the context fresh and the lesson impactful.",
                "🌟 **Always End with a Solution:** Your critique is only half the conversation. Finish with an actionable step or a path forward to make the feedback constructive, not just critical.",
                "📈 **Data Talks, Emotions Walk:** Ground your feedback in specific examples, not feelings. It makes your point indisputable.",
                "🎭 **Context is King:** The best feedback is tailored. Use a tone that matches the relationship and the situation.",
                "✨ **The Mirror Principle:** Before giving feedback, ask yourself: 'Am I saying this to help them, or to vent my frustration?'"
            ]
            st.session_state.current_tip = random.choice(pro_tips)
            st.session_state.show_tip = True

# Display tip with dismissal
if st.session_state.get("show_tip", False) and st.session_state.get("current_tip", ""):
    tip_col1, tip_col2 = st.columns([10, 1])
    with tip_col1:
        st.markdown(f"""
        <div class="pro-tip-box">
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
    label="Your Feedback",
    key="user_input", 
    height=140,
    placeholder="🔥 Paste your brutally honest feedback here...\n\nExamples:\n• 'You never respond to emails. It's unprofessional.'\n• 'Your presentation was confusing and boring.'\n• 'You always interrupt people in meetings.'\n\n💪 Be real - we'll make it professional!",
    help="Don't hold back - the rawer, the better the transformation!"
)

# ---------------------- Add a mobile-friendly "Continue" button ----------------------
if st.session_state.user_input and st.session_state.user_input.strip() and not st.session_state.continue_btn_clicked:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ Continue to Options", use_container_width=True, key="continue_btn_main", help="Click to proceed to the next step"):
            st.session_state.continue_btn_clicked = True
            st.rerun()

# ---------------------- ONLY SHOW CONTROLS IF INPUT EXISTS ----------------------
if st.session_state.user_input and st.session_state.user_input.strip() and st.session_state.continue_btn_clicked:
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
            
            api_key = st.secrets.get("OPENROUTER_API_KEY", None)
            
            if not api_key:
                st.error("⚠️ The service is currently undergoing maintenance and is unavailable. We apologize for the inconvenience! Please check back in a few minutes.")
                st.session_state.rewritten_text = ""
            else:
                rewritten = None
                                           
                with st.spinner(random.choice(loading_messages)):
                    try:                   
                        # This part of the code remains the same for defining system prompts
                        if format_as_email:
                            system_prompt = (
                                f"You are a seasoned workplace communication expert. Your task is to transform a user's raw feedback into a professional and well-structured email. "
                                f"The email is written by the user to a professional peer, manager, report, or team member. "
                                f"Use a {selected_tone_key} tone: warm, constructive, and solution-oriented. "
                                f"Write everything exclusively in perfect {selected_language_key}, using native greetings, expressions, and cultural norms without any English words."
                                f"The email must have a clear subject line, a respectful greeting, a body that provides specific and actionable feedback, and a professional closing."
                                f"The body of the email must be more than a simple sentence. It should provide a clear, positive context, explain the 'why' behind the feedback, and offer a forward-looking solution. "
                                f"Never write from the perspective of the sender apologizing for their own mistake unless they are explicitly stating they made one. "
                                f"Do not use any introductory conversational text like 'Here is the email:' before the email content. Start your response directly with the email's subject line."
                                f"The goal is to help the recipient grow, kindly, clearly, and respectfully."
                            )
                        else:
                            system_prompt = (
                                f"You are a seasoned and empathetic communication coach for professionals. "
                                f"Your task is to transform the user's raw feedback into a highly professional and constructive statement. "
                                f"The feedback is from the user to a professional peer, manager, report, or team member, not a self-critique. Never, under any circumstances, generate an apology from the user's perspective unless they are explicitly stating they made one."
                                f"Use a {selected_tone_key} tone and write exclusively in perfect {selected_language_key}. For non-English, use natural, culturally appropriate expressions without any English words."
                                f"Respond in **exactly this format**:\n\n"
                                f"The Reframe:\n"
                                f"<Insert your full reframe here. Start with a positive or neutral observation, explain the impact, and suggest a collaborative path forward. Be specific and solution-focused.>\n\n"
                                f"Bonus Tip:\n"
                                f"<Insert a short, practical suggestion for how to deliver this feedback effectively — e.g., suggest a private 1:1, a specific opening line, or ideal timing. Keep it to **1–2 clear sentences**. Do not add fluff, disclaimers, or generic advice.>\n\n"
                                f"Rules:\n\n"
                                f"- Start with 'The Reframe:' on its own line.\n"
                                f"- Put the reframe content on the next line — do not combine.\n"
                                f"- After a blank line, write 'Bonus Tip:' on its own line.\n"
                                f"- Write the tip content **below** 'Bonus Tip:', not on the same line.\n"
                                f"- The tip must be 1–2 sentences. No more.\n"
                                f"- Do not use markdown, quotes, asterisks, or formatting.\n"
                                f"- Do not add greetings, closings, or explanations.\n\n"
                                f"Example Output:\n"
                                f"The Reframe:\n"
                                f"I've noticed that sometimes in meetings, multiple people start speaking at once, which can make it hard to follow the discussion. To help us collaborate more effectively, it would be great if we could practice pausing briefly before responding. This small change can make a big difference in ensuring everyone feels heard.\n\n"
                                f"Bonus Tip:\n"
                                f"Bring this up in a private 1:1 and start with, 'I’ve been thinking about how we can make our meetings even better — would you be open to some feedback?'"
                            )

                        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                        data = {"messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_input}]}
                        model_fallbacks = [                           
                            "mistral/mistral-7b-instruct",
                            "mistralai/mixtral-8x7b-instruct",
                            "gryphe/mythomax-l2-13b",
                            "openchat/openchat-7b"
                            "qwen/qwen3-4b:free",
                            "google/gemma-3n-e2b-it:free",
                            "nousresearch/nous-capybara-7b",                            
                            "mistralai/mistral-small-3.2-24b-instruct:free",                                                      
                            "mistralai/devstral-small-2505:free",
                            "z-ai/glm-4.5-air:free",                            
                            "google/gemma-3n-e4b-it:free",
                            "openrouter/gpt-oss-20b:free",
                            "deepseek/deepseek-chat-v3-0324:free",
                            "deepseek/deepseek-r1:free",
                            "microsoft/mai-ds-r1:free",
                            "tngtech/deepseek-r1t-chimera:free",
                            "qwen/qwen3-coder:free",                           
                            "qwen/qwen3-8b:free",
                            "qwen/qwen3-14b:free",
                            "qwen/qwen3-30b-a3b:free",
                            "qwen/qwen3-235b-a22b:free",
                            "moonshotai/kimi-k2:free",
                            "sarvamai/sarvam-m:free",
                            "meta-llama/llama-2-70b-chat"                                                       
                        ]
                                                  
                        # Show a reassuring message to the user during the fallback process
                        st.info("💡 Your message is being rephrased. We're experimenting with several models to find the ideal reframing for you, if it takes a moment!")
                        
                        for model in model_fallbacks:
                            try:
                                data["model"] = model
                                resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=30)
                                
                                # Check for insufficient credits
                                if resp.status_code == 402:
                                    logging.error("😐 The service is currently experiencing high demand and is unable to process your request. Please try again in a few moments!")
                                # Check for general authentication errors
                                elif resp.status_code == 401:
                                    logging.error("⚠️ We're having trouble connecting to the service. Please try again in a few moments!")
                                elif resp.status_code == 200:
                                    #logging.info(f"Successfully called model: {model}")
                                    j = resp.json()
                                    rewritten = j.get("choices", [])[0].get("message", {}).get("content", "").strip()
                                    if rewritten:
                                        break # Break the loop if a successful response is received
                                else:
                                    logging.warning(f"API call to {model} failed with status code: {resp.status_code}")
                                    time.sleep(0.5) # Wait before trying the next model
                                    
                            except requests.exceptions.RequestException:
                                # Log the specific network error for debugging purposes
                                logging.error(f"⚠️ It looks like we're having trouble connecting to the internet. Please check your connection and try again 🙂")
                                time.sleep(0.5) # Wait before trying the next model
                                pass # Continue to the next model in the fallback list
                        
                        if rewritten and user_input:
                            st.session_state.rewritten_text = rewritten
                            # Modified timestamp format
                            formatted_timestamp = datetime.now(UTC_TZ).strftime("%Y-%m-%d %H:%M:%S")
                            st.session_state.rewrites.insert(0, {"timestamp": formatted_timestamp, "original": user_input, "rewritten": rewritten})
                        else:
                            # If the loop finishes and no model succeeded, set the rewritten text to empty and show a clear error.
                            st.error("⚠️ We were unable to reframe your message at the moment. Please try again 🙂")
                            st.session_state.rewritten_text = ""

                    except Exception as e:
                        # A final catch-all for any other unexpected errors
                        st.error(f"⚠️ An unexpected error occurred: {str(e)}. Please try again!")
                        st.session_state.rewritten_text = ""

# ---------------------- CLEAN Results Section (NO ANIMATIONS) ----------------------
if st.session_state.rewritten_text and st.session_state.rewritten_text.strip():
    st.markdown('<div class="step-pill">🎉 Your Reframed Message is Ready!</div>', unsafe_allow_html=True)
    
    # Simple, clean result display without animations
    st.markdown(f"""<div class="result-box"><h3>🎯 Your Words, Reimagined.</h3><p style="white-space: pre-wrap;">{st.session_state.rewritten_text}</p></div>""", unsafe_allow_html=True)
    
    # Viral sharing section
    # Font Awesome icons (requires CDN):
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="social-proof">
        <h4>🔥 REFRAME ⚡️ Elevate Your Message</h4>
        <p>If you found this useful, share the tool with your network:</p>
        <div class="social-links-container">
            <a href="https://www.linkedin.com/shareArticle?mini=true&url={PUBLIC_URL}&title=REFRAME%20⚡️%20Elevate%20Your%20Message&summary=Reframe%20is%20an%20amazing%20AI%20tool%20that%20helps%20you%20transform%20your%20words%20and%20deliver%20constructive%20feedback%20instantly.%20It's%20my%20new%20favorite%20communication%20coach!"
                target="_blank" class="social-link linkedin-bg">
                <div class="social-icon linkedin-text">in</div>
            </a>
            <a href="https://twitter.com/intent/tweet?text=REFRAME%20is%20an%20amazing%20AI%20tool%20that%20helps%20you%20transform%20your%20words%20and%20elevate%20your%20message.%20It%20turns%20awkward%20feedback%20into%20professional%20messages%20instantly.%20Check%20it%20out%20here%3A%20{PUBLIC_URL}"
                target="_blank" class="social-link twitter-bg">
                <div class="social-icon twitter-text">𝕏</div>
            </a>
            <a href="https://www.facebook.com/sharer/sharer.php?u={PUBLIC_URL}"
                target="_blank" class="social-link facebook-bg">
                <div class="social-icon facebook-text">f</div>
            </a>
        </div>
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

# ---------------------- Call to Action for Empty State ----------------------
else:
    # This block now correctly handles the initial empty state and all failure cases
    st.markdown("""
    <div class="social-proof">
        <h3>🎯 Ready to Transform Your Communication?</h3>
        <p><strong>Try it now:</strong> Give any challenging feedback, and see your message transformed into a polished, professional version instantly!</p>
        <p style="font-size: 0.9rem; margin-top: 1rem;">💫 Join thousands who've already improved their workplace communication</p>
    </div>
    """, unsafe_allow_html=True)

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
        # Modified timestamp format
        timestamp = datetime.now(UTC_TZ).strftime("%Y-%m-%d %H:%M:%S")
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
        st.session_state.feedback_submitted = True
        st.session_state.show_feedback_form = False
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
        # Get last 10 rewrites (most recent first)
        rewrites = st.session_state.rewrites[-10:] # Last 10
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
        <div style="text-align: center; padding: 2rem; border-radius: 15px; border: 2px dashed #dee2e6;">
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
            sh = client.open("reframe_app_feedback")
            worksheet = sh.sheet1
            sheet_data = worksheet.get_all_values()
            if len(sheet_data) > 1:
                rows = sheet_data[1:]  # skip header
    except Exception as e:
        st.write("🔍 Unable to open google feedback sheet — falling back to CSV.")
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
            st.write(f"🔍 CSV read failed: {e}")
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

        st.markdown("### 🔍 What Others Are Saying")

        # Prepare display
        display_df = df[["timestamp", "rating", "suggestions"]].copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%b %d, %Y')
        display_df.rename(columns={
            "timestamp": "📅 Date",
            "rating": "⭐ Rating",
            "suggestions": "💬 Feedback"
        }, inplace=True)

        # Highlight 4–5 star feedback
        def highlight_row(row):
            try:
                if row["⭐ Rating"] >= 4:
                    return ['background-color: #f0fff0; color: #0a310a'] * len(row)
                return [''] * len(row)
            except:
                return [''] * len(row)

        st.dataframe(
            display_df.style.apply(highlight_row, axis=1),
            use_container_width=True,
            hide_index=True,
            column_config={
                "⭐ Rating": st.column_config.NumberColumn(format="%.1f ⭐"),
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
        <p class="creator-subtitle">REFRAME v2.0 | 🎯 Empower your words</p>
        <p class="creator-tagline">"✨ Make every conversation a catalyst for growth and help your message land with empathy, clarity, and purpose ✨</p>
        <div class="creator-box">
            <p class="creator-mission">💫 Crafted for those who inspire.</p>
            <p class="creator-vision">Transform. Connect. Succeed.</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)