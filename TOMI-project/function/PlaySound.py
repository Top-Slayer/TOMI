import pygame
from gtts import gTTS
from threading import Thread
from function import DetectFace

pygame.mixer.init()

def playSound(text):
    print(f"--> AI thinking: {text}")
    myobj = gTTS(text=text, lang="th", slow=False)
    myobj.save(r'output.wav')

    print("--> AI talking...")
    my_sound = pygame.mixer.Sound('output.wav')
    my_sound.play()

    pygame.time.wait(int(my_sound.get_length() * 1000))

    DetectFace.state = True
