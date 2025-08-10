# ✍️ Feedback Rewriter Assistant

An AI-powered tool that rewrites workplace or professional feedback into more **clear, respectful, and human-friendly tones** — choose from styles like **Empathetic**, **Managerial**, **Formal**, **Friendly**, or **Assertive**.  
Optionally, generate the output in a **polished email format** — great for HRs, team leads, or anyone giving constructive input.

Built using [Streamlit](https://streamlit.io/) and free open-source LLMs via [OpenRouter](https://openrouter.ai) — powered by models like **Mistral**, **Mixtral**, and **MythoMax**.


## 🧠 What It Does

Rewrites raw or harsh feedback messages into:

- ✅ Friendly, Empathetic, Managerial, Formal, or Assertive tone
- ✅ Professional **email format** (optional toggle)
- ✅ Clear and polished paragraphs (default)
- ✅ Output in **multiple languages**

Built with:
- 🧠 OpenRouter API (free-tier friendly)
- ⚡ Automatic model fallback (no dropdowns)
- ✨ Responsive UI using Streamlit
- 🔒 No user data stored — safe to use


## 📆 Tech Stack

- Python 3
- Streamlit
- OpenRouter API
- Mistral 7B / Mixtral / Capybara / Mythomax fallback stack
- Markdown-based output display

## 📷 Preview

![Demo of Feedback Rewriter Assistant](Screenshot.png)

### 🎨 Available Tones

- 🧭 Managerial  
- 💖 Empathetic  
- 🧾 Formal  
- 😊 Friendly  
- 💼 Assertive

### 🛠️ Built With

- [Streamlit](https://streamlit.io/)
- [OpenRouter (Open Source LLM Gateway)](https://openrouter.ai/)
- Python + Requests


## 🛠️ Installation (Run Locally)

```bash
git clone https://github.com/dmmudhan/feedback-rewriter-gpt.git
cd feedback-rewriter-gpt
pip install -r requirements.txt
streamlit run app.py
```

## 🔐 Setup Your API Key

Create a file: `.streamlit/secrets.toml`

```toml
OPENROUTER_API_KEY = "sk-or-your-api-key-here"
```

Get your free key from: [https://openrouter.ai/keys](https://openrouter.ai/keys)


## 🧾 Version History

### ✅ v2.0 – Rebrand & Feedback-Powered Communication

- 🔄 Rebranded to "Reframe" – A name that reflects empathy, clarity, and intentional communication
- 💬 Smart feedback transformation – Rewrites tough messages into kind, clear, and professional versions in seconds
- 🎯 Tone Precision – 5 adaptive tones (Friendly, Firm, Empathetic, Professional, Enthusiastic) to match any workplace context
- 🌍 Multilingual Support – Write and reframe in 12+ languages with native expressions and cultural nuance
- 📧 Email Format Mode – Generate ready-to-send emails with proper greeting, body, and closing
- 📊 User History & Export – Track your communication evolution and export your rewrites
- 🌟 Social Proof Engine – “What Others Say” displays top-rated community feedback with sorting, styling, and fallbacks
- 🔁 Feedback Loop Built-In – Users can submit feedback that instantly appears in the public feed (CSV + Google Sheets sync)
- 🛠️ Robust Persistence – Dual storage: Google Sheets (cloud) + feedback_local.csv (fallback) for reliability
- 🎨 Premium UI Experience – Animated hero header, glowing "Reframe" logo, smooth hover effects, and modern layout
- ✨ Micro-Interactions – Subtle animations, fade-ins, and card lifts for a polished, high-end feel
- 🧩 Emotionally Intelligent Prompts – Ensures feedback is always directed to others, not self-apologies
- 🧑‍💼 User-Centric UX – Added neutral rating option, “Other” in enhancements, and close button in feedback form
- 📱 Mobile-Friendly Design – Responsive layout works seamlessly on all devices

[🔗 Live App](https://feedback-rewriter-gpt-caht6hciagxykx52hz6xnh.streamlit.app/)

### ✅ v1.3 – Email Format Toggle + UX Enhancements

- 📧 Added "Format as Email" option for professional email output
- 📋 Copy-friendly rewritten text using markdown display
- 🦶 Footer added with creator credit and version info
- ✨ Preserved clean UX and fallback logic from v1.2

[🔗 Live App](https://feedback-rewriter-gpt-ciwy4jjbnswedu3wgppmss.streamlit.app/)


### ✅ v1.2 (Latest)
- ✨ UI cleaned up with better spacing between sections
- 🧠 Improved system prompt to avoid unwanted email formatting
- 🔄 Built-in fallback logic for models — no user dropdown required
- 🎯 Auto-reset session on first app load after deploy (Streamlit Cloud safe)
- 🚫 Hides technical model failure messages from users
- 💬 Renamed output section: “Here's Your Refined Feedback”
- ✅ Clean, production-ready UX — no manual refresh needed by users

[🔗 Live App](https://feedback-rewriter-gpt-2epkjjin5zogy4mbdwhded.streamlit.app/) · [📂 Source Code](https://github.com/dmmudhan/feedback-rewriter-gpt)

### v1.1 – Tone Detection Update
- Added tone selection input (e.g., formal, friendly, assertive)
- Introduced `prompts.py` for modular prompt design
- Improved user experience with clearer outputs
- Updated Streamlit deployment

[🔗 Live App](https://feedback-rewriter-gpt-caht6hciagxykx52hz6xnh.streamlit.app/)

### v1.0 – Initial Version
- Basic Feedback Rewriting using LLM
- Accepts raw user feedback and rewrites it professionally


## 🤝 Contributing

Pull requests are welcome. Feel free to open an issue or suggest improvements!


## 🧑‍💼 Author

**Devi Mudhanagiri**
Prompt Engineering Enthusiast | AI Builder | Freelancing Learner
[LinkedIn](https://www.linkedin.com/in/devimuthyam/)

---

## 📝 License

MIT License
Copyright (c) 2025 Devi Mudhanagiri

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
