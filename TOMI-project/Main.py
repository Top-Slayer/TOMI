import threading
from function import EmotionalRecognition
from function import PlaySound

threading.Thread(target=EmotionalRecognition.openCamera).start()

while 1:
    # print(
    #     f"{EmotionalRecognition.play_sound_key} && {PlaySound.enabled} | Emotional: {EmotionalRecognition.text}"
    # )

    if EmotionalRecognition.play_sound_key and PlaySound.enabled:
        threading.Thread(
            target=PlaySound.playSound, args=(EmotionalRecognition.text,)
        ).start()
