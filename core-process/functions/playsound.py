import pygame
from gtts import gTTS
import random

enabled = True
previous_text = str()

pygame.mixer.init()


def _randomSentence(word):
    sentences = str()
    happy_sentences = {"มีความสุขแบบนี้ก็ดีแล้วละโลกจะได้สดใส"}
    if word == "Happy":
        sentences = random.choice(happy_sentences)
    else:
        sentences = "Bruh"

    return sentences


def playSound(text):
    global enabled
    global previous_text

    enabled = False

    if previous_text != text:
        voice_sentences = text
        print(f"--> Text: {voice_sentences}")
        myobj = gTTS(text=voice_sentences, lang="ko", slow=False)
        myobj.save(r"output.wav")

        print("--> AI talking...")
        my_sound = pygame.mixer.Sound("output.wav")
        my_sound.play()

        pygame.time.wait(int(my_sound.get_length() * 1000))

    previous_text = text

    enabled = True
