import re
import random
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

CSV_PATH = "FAQ_(1).csv"
MODEL_NAME = "all-MiniLM-L6-v2"
THRESHOLD = 0.40
SAMPLE_SIZE = 300
VARIANTS_PER_QUESTION = 2
RANDOM_SEED = 42
 
random.seed(RANDOM_SEED)
 
 
def clean_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
 
 
SYNONYM_MAP = {
    "what services do you offer": "what kind of work do you do",
    "do you offer": "you got any", "do you provide": "can i get",
    "can you help": "is it possible to assist", "can you": "is it possible to",
    "how do i": "what's the way to", "how can i": "what's the way to",
    "how much": "what's the cost", "services": "stuff you work on",
    "price": "cost", "pricing": "cost", "cost": "charges",
    "contact": "reach out to", "location": "address", "located": "based",
    "team": "staff members", "help": "assist", "website": "site",
    "company": "business", "information": "details", "provide": "give",
    "offer": "have", "tell me about": "give me details on",
    "what is": "what's", "who is": "who's", "experience": "background",
    "clients": "customers", "manage": "handle", "support": "assistance",
}
QUESTION_STARTERS_TO_DROP = ["what ", "how ", "do you ", "can you ", "is ", "are ", "where ", "who "]
FILLER_PREFIXES = ["hey ", "umm so ", "quick question, ", "hi, ", "yo ", ""]
FILLER_SUFFIXES = ["", " please", " thanks", " btw"]
 
 
def casual_paraphrase(question: str) -> str:
    q = question.lower().strip().rstrip("?")
    for original, replacement in SYNONYM_MAP.items():
        if original in q:
            q = q.replace(original, replacement)
    words = q.split()
    if len(words) > 3 and random.random() < 0.5:
        first, middle, last = words[0], words[1:-1], words[-1]
        random.shuffle(middle)
        q = " ".join([first] + middle + [last])
    if random.random() < 0.4:
        for starter in QUESTION_STARTERS_TO_DROP:
            if q.startswith(starter):
                q = q[len(starter):]
                break
    prefix = random.choice(FILLER_PREFIXES)
    suffix = random.choice(FILLER_SUFFIXES)
    return f"{prefix}{q}{suffix}".strip()
 
 
def main():
    print("Loading dataset...")
    df = pd.read_csv(CSV_PATH)
    print("Original rows:", len(df))
 
    # KEY DIFFERENCE: remove near-duplicate questions, keep 1 per unique answer
    df = df.drop_duplicates(subset="Answer", keep="first").reset_index(drop=True)
    print("After removing duplicate/near-identical questions:", len(df))
 
    df["Question_clean"] = df["Question"].apply(clean_text)
 
    print("\nLoading model (first run downloads ~80MB)...")
    model = SentenceTransformer(MODEL_NAME)
 
    question_embeddings = model.encode(
        df["Question_clean"].tolist(), convert_to_numpy=True, show_progress_bar=False
    )
    print("Embeddings ready:", question_embeddings.shape)
 
    sample_df = df.sample(n=min(SAMPLE_SIZE, len(df)), random_state=RANDOM_SEED)
    test_cases = []
    for _, row in sample_df.iterrows():
        for _ in range(VARIANTS_PER_QUESTION):
            test_cases.append((casual_paraphrase(row["Question"]), row["Answer"]))
 
    print(f"\nTesting on {len(test_cases)} paraphrased questions (harder, deduplicated corpus)...\n")
 
    correct = 0
    mistakes = []
    for paraphrased_q, expected_answer in test_cases:
        cleaned = clean_text(paraphrased_q)
        user_embedding = model.encode(cleaned, convert_to_numpy=True)
        similarity_scores = cosine_similarity([user_embedding], question_embeddings)
        best_index = int(np.argmax(similarity_scores))
        best_score = float(similarity_scores[0][best_index])
 
        predicted_answer = df.iloc[best_index]["Answer"] if best_score >= THRESHOLD else "NO_ANSWER_GIVEN"
 
        if predicted_answer.strip() == expected_answer.strip():
            correct += 1
        else:
            mistakes.append({
                "paraphrased_question": paraphrased_q,
                "expected_answer": expected_answer,
                "got_answer": predicted_answer,
                "score": round(best_score, 3),
            })
 
    accuracy = (correct / len(test_cases)) * 100
    print("=" * 55)
    print(f" HONEST (DEDUPLICATED) ACCURACY: {accuracy:.2f}%  ({correct}/{len(test_cases)})")
    print("=" * 55)
    print("\nThis number reflects the model's TRUE paraphrase-handling")
    print("ability, without help from near-duplicate questions already")
    print("sitting in the dataset.")
 
    if mistakes:
        pd.DataFrame(mistakes).to_csv("mistakes_dedup.csv", index=False)
        print(f"\n{len(mistakes)} mistakes saved to mistakes_dedup.csv")
 
 
if __name__ == "__main__":
    main()
