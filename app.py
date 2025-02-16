import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

OPENROUTER_API_KEY = "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"

# Define startup-related categories
CATEGORIES = {
    "funding": ["funding", "investment", "venture capital", "raise money", "seed round"],
    "idea_validation": ["validate", "idea", "market research", "customer feedback"],
    "cofounder": ["co-founder", "partner", "team building", "find co-founder"],
    "growth": ["growth", "marketing", "scale", "customers", "traction"]
}

def detect_category(user_message):
    """Detects the category of the user's query based on keywords."""
    for category, keywords in CATEGORIES.items():
        if any(keyword in user_message.lower() for keyword in keywords):
            return category
    return "general"  # Default if no category is detected

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '')

    # Detect category
    category = detect_category(user_message)

    # Define system prompt for each category
    SYSTEM_PROMPTS = {
        "funding": "You are an expert in startup fundraising. Provide detailed advice on securing investments, pitching to VCs, and bootstrapping.",
        "idea_validation": "You are a startup mentor specializing in idea validation. Provide structured advice on testing startup ideas and getting customer feedback.",
        "cofounder": "You are a startup advisor who helps solo founders find co-founders. Give tips on networking, choosing a good co-founder, and team building.",
        "growth": "You are a growth strategist for startups. Provide marketing and scaling strategies with actionable steps.",
        "general": "You are an AI mentor for entrepreneurs. Provide helpful startup advice on any topic."
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
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ]
            }
        )

        response_json = response.json()
        import re

        def format_ai_response(response_text):
            """Formats AI response for better readability with correct spacing."""
            
            # Ensure numbered points are bold and on a new line
            response_text = re.sub(r"(\d+)\.\s\*\*(.*?)\*\*", r"\n**\1. \2**", response_text)
            
            # Ensure bullet points are on new lines
            response_text = re.sub(r"(?<!\n)- ", r"\n- ", response_text)
            
            # Remove multiple consecutive line breaks (prevents excessive gaps)
            response_text = re.sub(r"\n{3,}", "\n", response_text)  
            
            # Remove unnecessary "**" (to fix any extra bold markers)
            response_text = response_text.replace("**", "")
            
            # Add line breaks after sentences for better readability
            response_text = response_text.replace(". ", ".\n")
            
            return response_text.strip()

        bot_response = format_ai_response(response_json["choices"][0]["message"]["content"])

    except Exception as e:
        print(f"❌ OpenRouter API Error: {e}")
        bot_response = "Error: Could not connect to AI service."

    return jsonify({"response": bot_response})

if __name__ == '__main__':
    app.run(debug=True)
