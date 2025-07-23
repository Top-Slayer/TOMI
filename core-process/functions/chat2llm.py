import requests
import time
import json
from . import tts


# model_name = "gemma3:1b-it-q4_K_M" # maximum
model_name = "gemma3:12b-it-q4_K_M"
system_prompt = """
You are a helpful and funny AI assistant. Your name is "ໂທມິ", and you always refer to yourself using the pronoun "ໂທມິ" instead of "ເຮົາ" or "ຂ້ອຍ".

[Behavior Rules]
- You must always respond in the **Lao language**, even if the input is in Thai.
- If the user writes in Thai, you must **translate and respond in Lao**.
- Only respond **Lao language**.
- Only say "ສະບາຍດີເຮົາຊື່ໂທມິ" **if the user greets you first** (e.g. "hello", "hi", "ສະບາຍດີ").
- Your tone should be **friendly and funny**.
"""



def _timer(choice: int):
    if choice == 1:
        start_time = time.time()
    elif choice == 0:
        end_time = time.time()
        print(end_time - start_time)

conversation = []

def chat(user_prompt: str, debug=False):
    global conversation

    conversation.append({"role": "user", "content": user_prompt})

    prompt_parts = [f"{system_prompt}"]
    for message in conversation:
        role = message["role"].capitalize()
        content = message["content"]
        prompt_parts.append(f"{role}: {content}")
    prompt_parts.append("Assistant:")

    full_prompt = "\n".join(prompt_parts)

    sentense = ""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": full_prompt,
                "num_predict": 100,
                "stream": True,
            },
            stream=True,
        )
    except Exception as e:
        print(f"--- Have Something wrong with ollama server [try to open server again] ---\n{e}")
        return

    assistant_reply = ""

    for line in response.iter_lines():
        if line:
            try:
                data = line.decode("utf-8")
                json_data = json.loads(data)
                token = json_data["response"]
                sentense += token
                assistant_reply += token

                print(token, end="", flush=True)

                if token in " ":
                    print()
                    tts.synthesize(sentense)
                    sentense = ""

            except json.JSONDecodeError as e:
                print(f"\nJSON Decode Error: {e}")

    if sentense != "":
        tts.synthesize(sentense)

    conversation.append({"role": "assistant", "content": assistant_reply})