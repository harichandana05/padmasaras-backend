import json
import os

VOCAB_FILE = os.path.join(os.path.dirname(__file__), "vocabulary.json")

def load_vocabulary():
    with open(VOCAB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def translate_text(text, language):
    text = text.lower().strip()
    vocab = load_vocabulary()

    words = text.split()
    translated_words = []
    explanation = []

    for word in words:
        if word in vocab and language in vocab[word]:
            translated = vocab[word][language]
            translated_words.append(translated)
            explanation.append(f"{word} → {translated}")
        else:
            translated_words.append(word)
            explanation.append(f"{word} → (not learned yet)")

    final_translation = " ".join(translated_words)

    return {
        "translation": final_translation,
        "explanation": explanation
    }
