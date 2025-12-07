import os
import requests

HF_API = os.environ.get("HF_INFERENCE_API_KEY")  # optional key

def extractive_summary(text, max_sentences=5):
    sents = [s.strip() for s in text.replace("\n", " ").split('.') if s.strip()]
    return '. '.join(sents[:max_sentences]) + ('.' if len(sents[:max_sentences]) > 0 else '')

def hf_summarize(text):
    if not HF_API:
        return extractive_summary(text)
    try:
        url = "https://api-inference.huggingface.co/models/t5-small"
        headers = {"Authorization": f"Bearer {HF_API}"}
        payload = {"inputs": "summarize: " + text}
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and "summary_text" in data[0]:
                return data[0]["summary_text"]
        return extractive_summary(text)
    except:
        return extractive_summary(text)