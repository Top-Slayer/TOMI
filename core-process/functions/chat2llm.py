import requests
import time
import json
from . import tts


model_name = "gemma3:27b"
system_prompt = """
      You are a helpful assistant specialized in Lao academic and historical knowledge.

      [System Instruction]
      - Only answer questions in the Lao language.
      - If asked about unrelated topics, politely refuse.
      - Respond in full sentences using formal language.
      - Your name is "ທູມິ"
"""


def _timer(choice: int):
    if choice == 1:
        start_time = time.time()
    elif choice == 0:
        end_time = time.time()
        print(end_time - start_time)


def chat(user_prompt: str, debug=False):
    prompt = f"""
      {system_prompt}
      [User Question]
      {user_prompt}
      """

    sentense = ""

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "num_predict": 100,
                "stream": True,
            },
            stream=True,
        )
    except Exception as e:
        print(f"--- Have Something wrong with ollama server [try to open server again] ---\n{e}")
        return

    for line in response.iter_lines():
        if line:
            try:
                data = line.decode("utf-8")
                json_data = json.loads(data)
                sentense += json_data["response"]

                print(json_data["response"], end="", flush=True)

                if json_data["response"] in " ":
                    tts.synthesize(sentense)
                    sentense = ""

            except json.JSONDecodeError as e:
                print(f"\nJSON Decode Error: {e}")

    if sentense != "":
        tts.synthesize(sentense)
