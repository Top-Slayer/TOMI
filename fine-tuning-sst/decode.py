import json

# sentence = [45, 18, 33, 16, 29, 11, 33, 8, 45, 31, 42, 34, 13, 51, 30, 8, 18, 44, 17, 15, 44, 17, 13, 42, 16, 45, 30, 8, 5, 33, 17, 19, 41, 51, 30, 39, 50, 16, 4]
sentence = [27, 36, 15, 37, 50, 49, 12, 45, 30, 33, 12, 13, 34, 23, 5, 40, 52, 17, 45, 26, 39, 30, 12, 0, 5, 36, 16, 46, 17, 17, 48, 12, 45, 14, 37, 8, 9, 32, 28, 27, 11, 19, 30, 23]

with open("vocab.json", "r") as f:
    json_datas = json.load(f)
    num_to_char = {v: k for k, v in json_datas.items()}
    decoded_text = ''.join(num_to_char.get(n, '?') for n in sentence)
    print(decoded_text)
