const video = document.getElementById('video');
const captureButton = document.getElementById('capture');

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

    // Convert the canvas to a Blob
    canvas.toBlob(blob => {
        sendData(blob);
    }, 'image/jpeg');
  });

  function sendData(blob) {
    const formData = new FormData();
    formData.append('file', blob, 'capture.jpg');

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
    })
    .catch(error => {
        console.error('Error:', error);
    });
  }
