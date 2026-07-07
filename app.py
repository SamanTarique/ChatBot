from flask import Flask, request, jsonify
from Chatbot import get_answer

app = Flask(__name__)

@app.route("/")
def home():
    return "SafeX AI Chatbot API is Running!"

@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    user_question = data["message"]

    result = get_answer(user_question)

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)