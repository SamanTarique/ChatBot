import re
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

CSV_PATH = "FAQ_(1).csv"
MODEL_NAME = "all-MiniLM-L6-v2"
THRESHOLD = 0.40
WHATSAPP_LINK = "https://wa.me/923495614170"


# ---------------- Text Cleaning ----------------
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------- Load Dataset ----------------
print("Loading dataset...")
df = pd.read_csv(CSV_PATH)
df["Question"] = df["Question"].apply(clean_text)

print("Loading Sentence Transformer Model...")
model = SentenceTransformer(MODEL_NAME)

print("Creating Question Embeddings...")
question_embeddings = model.encode(
    df["Question"].tolist(),
    convert_to_numpy=True,
    show_progress_bar=False
)

print("Chatbot Ready!")


# ---------------- Chatbot Function ----------------
def get_answer(user_question):

    cleaned_question = clean_text(user_question)

    user_embedding = model.encode(
        cleaned_question,
        convert_to_numpy=True
    )

    similarity_scores = cosine_similarity(
        [user_embedding],
        question_embeddings
    )

    best_index = int(np.argmax(similarity_scores))

    # Convert NumPy float32 to normal Python float
    best_score = float(similarity_scores[0][best_index])

    if best_score >= THRESHOLD:

        return {
            "answer": str(df.iloc[best_index]["Answer"]),
            "matched_question": str(df.iloc[best_index]["Question"]),
            "confidence": round(best_score * 100, 2)
        }

    else:

        return {
            "answer": "Sorry, I couldn't find a suitable answer.\nFor further help contact SafeX Solutions:\nhttps://wa.me/923495614170",
            "matched_question": None,
            "confidence": round(best_score * 100, 2)
        }


# ---------------- Test ----------------
if __name__ == "__main__":

    while True:

        user_question = input("You : ")

        if user_question.lower() in ["exit", "quit"]:
            break

        result = get_answer(user_question)

        print("\nBot :", result["answer"])
        print("Matched Question :", result["matched_question"])
        print("Confidence :", result["confidence"], "%")
        
