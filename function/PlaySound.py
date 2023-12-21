import pygame
from gtts import gTTS
from threading import Thread

pygame.mixer.init()

def setSound(text):
    myobj = gTTS(text=text, lang="th", slow=False)
    myobj.save("output.wav")

def playSound():
    print("--> Talking...")
    my_sound = pygame.mixer.Sound("output.wav")
    my_sound.play()
    pygame.time.wait(int(my_sound.get_length() * 1000))
    return True
