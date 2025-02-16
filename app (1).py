import requests
import re
from flask import Flask, request, jsonify, session
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.secret_key = "a3f8d6c79b2f4e8b9c1d2e5f6a7b8c9d10e11f12a13b14c15d16e17f18g19h"

OPENROUTER_API_KEY = "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"

CATEGORIES = {
    "funding": ["funding", "investment", "venture capital", "raise money", "seed round"],
    "idea_validation": ["validate", "idea", "market research", "customer feedback"],
    "cofounder": ["co-founder", "partner", "team building", "find co-founder"],
    "growth": ["growth", "marketing", "scale", "customers", "traction"]
}

FOLLOW_UP_QUESTIONS = {
    "funding": "Do you already have a pitch deck prepared? (Yes/No)",
    "idea_validation": "Have you tested your idea with real customers? (Yes/No)",
    "cofounder": "Do you need a technical or business-oriented co-founder?",
    "growth": "What is your main growth challenge right now? (Marketing/Sales/Retention)"
}

FOLLOW_UP_RESPONSES = {
    "funding_yes": "Great! Now, focus on refining your pitch and researching investors.",
    "funding_no": "No worries! Start by creating a compelling pitch deck covering problem, solution, and business model.",
    "idea_validation_yes": "Awesome! Now, refine your idea based on customer feedback.",
    "idea_validation_no": "You should conduct customer interviews or surveys to validate your idea.",
    "cofounder_technical": "A technical co-founder can be found on platforms like Indie Hackers or AngelList.",
    "cofounder_business": "For business-oriented co-founders, try LinkedIn or startup networking events.",
    "growth_marketing": "Marketing strategies include SEO, social media ads, and influencer partnerships.",
    "growth_sales": "For sales, focus on cold outreach, partnerships, and CRM tools.",
    "growth_retention": "To improve retention, focus on customer support, loyalty programs, and product improvements."
}

def get_chat_history():
    return session.get("chat_history", [])

def update_chat_history(user_message, bot_response):
    history = session.get("chat_history", [])
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": bot_response})

    session["chat_history"] = history[-10:]
    session.modified = True  

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip().lower()
    chat_history = get_chat_history()

    # Check if the user is responding to a follow-up
    last_follow_up = session.get("last_follow_up")

    if last_follow_up:
        session.pop("last_follow_up")  # Clear stored follow-up after response
        if user_message in ["yes", "no"]:
            follow_up_key = f"{last_follow_up}_{user_message}"
            bot_response = FOLLOW_UP_RESPONSES.get(follow_up_key, "Thanks for your response! Let's move forward.")
            update_chat_history(user_message, bot_response)
            return jsonify({"response": bot_response})
        elif last_follow_up == "cofounder" and user_message in ["technical", "business"]:
            bot_response = FOLLOW_UP_RESPONSES.get(f"cofounder_{user_message}", "Great choice! Let’s proceed.")
            update_chat_history(user_message, bot_response)
            return jsonify({"response": bot_response})

    # Detect category if not a follow-up response
    category = "general"
    for cat, keywords in CATEGORIES.items():
        if any(keyword in user_message for keyword in keywords):
            category = cat
            break

    SYSTEM_PROMPTS = {
        "funding": "You are an expert in startup fundraising...",
        "idea_validation": "You are a startup mentor specializing in idea validation...",
        "cofounder": "You are a startup advisor helping solo founders...",
        "growth": "You are a growth strategist for startups...",
        "general": "You are an AI mentor for entrepreneurs..."
    }

    system_prompt = SYSTEM_PROMPTS[category]

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": chat_history + [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            }
        )

        response_json = response.json()
        
        def format_ai_response(response_text):
            response_text = re.sub(r"(\d+)\.\s\*\*(.*?)\*\*", r"\n**\1. \2**", response_text)
            response_text = re.sub(r"(?<!\n)- ", r"\n- ", response_text)
            response_text = re.sub(r"\n{3,}", "\n", response_text)  
            response_text = response_text.replace("**", "")
            response_text = response_text.replace(". ", ".\n")
            return response_text.strip()

        bot_response = format_ai_response(response_json["choices"][0]["message"]["content"])

        # Add follow-up question
        follow_up = FOLLOW_UP_QUESTIONS.get(category)
        if follow_up:
            bot_response += f"\n\n💡 **Follow-up:** {follow_up}"
            session["last_follow_up"] = category  # Store follow-up question category

        update_chat_history(user_message, bot_response)

    except Exception as e:
        print(f"❌ OpenRouter API Error: {e}")
        bot_response = "Error: Could not connect to AI service."

    return jsonify({"response": bot_response})

if __name__ == '__main__':
    app.run(debug=True)
