const url = 'http://localhost:5000/video_feed';
//const url = 'https://daring-swine-enabling.ngrok-free.app/video_feed';

const video = document.getElementById('video');
const img = document.getElementById('img');
const captureButton = document.getElementById('capture');

const state = document.getElementById("state");

// Request access to the webcam
navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
      video.srcObject = stream;
  })
  .catch(err => {
      console.error("Error accessing webcam: ", err);
  });

captureButton.addEventListener('click', () => {
  const canvas = document.createElement('canvas');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  const context = canvas.getContext('2d');
  context.drawImage(video, 0, 0, canvas.width, canvas.height);

  const imageData = canvas.toDataURL("image/jpeg")

  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ image: imageData })
  })
  .then(response => response.json())
  .then(data => {
    img.src = 'data:image/jpeg;base64,' + data.image;
    // state.style.display = 'none';
    // state.style.display = 'block';
    console.log('Success:', data);
  })
  .catch(error => {
    console.error('Error:', error);
    alert(error)
  });


});
