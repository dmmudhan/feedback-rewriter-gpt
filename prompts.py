import requests

def rewrite_feedback(feedback: str, tone: str, api_key: str) -> str:
    system_prompt = (
        "You are an assistant that rewrites workplace feedback messages to improve tone and clarity. "
        "Depending on the selected tone, adjust the response accordingly:\n"
        "- Empathetic: Use gentle, understanding language.\n"
        "- Constructive: Focus on solutions and next steps.\n"
        "- Managerial: Be direct but professional and goal-oriented."
    )

    user_prompt = f"Rewrite the following feedback in a {tone} tone:\n\n\"{feedback}\""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://feedback-rewriter.streamlit.app",  # replace with your actual Streamlit app URL later
        "X-Title": "Feedback Rewriter Assistant"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    }

    response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"].strip()
    else:
        return f"Error: {response.status_code} - {response.text}"
