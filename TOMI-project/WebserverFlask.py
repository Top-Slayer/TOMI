import csv
import itertools
import cv2 as cv
import numpy as np
import mediapipe as mp
from model import KeyPointClassifier
from flask import Flask, request, render_template
import base64
from flask_cors import CORS
from datetime import datetime
import gc
import os

app = Flask(__name__)
CORS(app)

# Initialize MediaPipe FaceMesh and KeyPointClassifier once
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

keypoint_classifier = KeyPointClassifier()

with open("model/keypoint_classifier/keypoint_classifier_label.csv", encoding="utf-8-sig") as f:
    keypoint_classifier_labels = [row[0] for row in csv.reader(f)]

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/video_feed', methods=['POST'])
def video_feed():
    try:
        if not request.json or 'image' not in request.json:
            return {'error': 'Invalid request, no image provided'}, 400

        data = request.json['image']
        data = data.split(',')[1]  # Remove the data URL part
        image_data = base64.b64decode(data)
        np_arr = np.frombuffer(image_data, np.uint8)
        frame = cv.imdecode(np_arr, cv.IMREAD_COLOR)

        if frame is None:
            return {'error': 'Could not decode image'}, 400

        # Process the frame (e.g., detect emotion)
        frame, facial_text = addEmotionToImg(frame)

        save_image(frame)

        # Encode the frame back to JPEG
        _, buffer = cv.imencode('.jpg', frame)
        response = base64.b64encode(buffer).decode('utf-8')
        
        # Explicitly delete large objects
        del data, image_data, np_arr, frame, buffer
        gc.collect()

        # Text response based on emotion
        response_text = get_emotion_response(facial_text)
        
        return {'image': response, 'text': response_text}, 200
    except Exception as e:
        print(e)
        return {'error': str(e)}, 500

def save_image(image):
    # Define the directory to save images
    save_dir = "images"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Define the filename with the current datetime
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".jpg"
    save_path = os.path.join(save_dir, filename)
    
    # Save the image
    cv.imwrite(save_path, image)

def get_emotion_response(emotion):
    responses = {
        "Neutral": "You have to smile more cause you're so cute when smiling",
        "Sad": "Dear me, you are the best",
        "Angry": "Claim down you know violent isn't a good way",
        "Happy": "The world is more beautiful because your smile you know~~",
        "Surprise": "Yeah!! congratulation~~"
    }
    return responses.get(emotion, "")

def calc_landmark_list(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]
    return [
        [min(int(landmark.x * image_width), image_width - 1),
         min(int(landmark.y * image_height), image_height - 1)]
        for landmark in landmarks.landmark
    ]

def pre_process_landmark(landmark_list):
    base_x, base_y = landmark_list[0]
    temp_landmark_list = [
        [x - base_x, y - base_y] for x, y in landmark_list
    ]
    max_value = max(map(abs, itertools.chain(*temp_landmark_list)))
    return [n / max_value for n in itertools.chain(*temp_landmark_list)]

def draw_bounding_rect(use_brect, image, brect):
    if use_brect:
        cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[3]), (0, 0, 0), 1)
    return image

def calc_bounding_rect(image, landmarks):
    image_width, image_height = image.shape[1], image.shape[0]
    landmark_array = np.array([
        [int(landmark.x * image_width), int(landmark.y * image_height)]
        for landmark in landmarks.landmark
    ], dtype=int)
    x, y, w, h = cv.boundingRect(landmark_array)
    return [x, y, x + w, y + h]

def draw_info_text(image, brect, facial_text):
    info_text = f"Emotion: {facial_text}"
    cv.rectangle(image, (brect[0], brect[1]), (brect[2], brect[1] - 22), (0, 0, 0), -1)
    if facial_text:
        cv.putText(image, info_text, (brect[0] + 5, brect[1] - 4),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv.LINE_AA)
    return image

def addEmotionToImg(image):
    debug_image = image.copy()
    image_rgb = cv.cvtColor(image, cv.COLOR_BGR2RGB)
    image_rgb.flags.writeable = False
    results = face_mesh.process(image_rgb)
    image_rgb.flags.writeable = True

    facial_text = "Unknown"
    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            brect = calc_bounding_rect(debug_image, face_landmarks)
            landmark_list = calc_landmark_list(debug_image, face_landmarks)
            pre_processed_landmark_list = pre_process_landmark(landmark_list)
            facial_emotion_id = keypoint_classifier(pre_processed_landmark_list)
            facial_text = keypoint_classifier_labels[facial_emotion_id]
            debug_image = draw_bounding_rect(True, debug_image, brect)
            debug_image = draw_info_text(debug_image, brect, facial_text)

    return debug_image, facial_text

if __name__ == '__main__':
    app.run(port=5000)
