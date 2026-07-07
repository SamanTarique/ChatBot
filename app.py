from flask import Flask, request, jsonify
from flask_cors import CORS
from Chatbot import get_answer

app = Flask(__name__)

# Enable CORS
CORS(app, resources={r"/chat": {"origins": "*"}})

@app.route("/")
def home():
    return "SafeX AI Chatbot API is Running!"

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()

        user_question = data.get("message", "")

        result = get_answer(user_question)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
