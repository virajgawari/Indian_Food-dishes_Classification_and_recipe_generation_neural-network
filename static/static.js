document.addEventListener('DOMContentLoaded', () => {
    const imageUploadInput = document.getElementById('imageUpload');
    const resultDiv = document.getElementById('result');
    const recipeContainer = document.getElementById('recipe-container');
    const uploadedImage = document.getElementById('uploadedImage');
    const imagePreviewContainer = document.getElementById('image-preview-container');
    const predictButton = document.getElementById('predictButton');
    const resultsSection = document.getElementById('results-section');
    const spinner = document.getElementById('spinner');

    const showUploadBtn = document.getElementById('show-upload-btn');
    const showCameraBtn = document.getElementById('show-camera-btn');
    const uploadView = document.getElementById('upload-view');
    const cameraView = document.getElementById('camera-view');
    const videoFeed = document.getElementById('video-feed');
    const snapBtn = document.getElementById('snap-btn');
    const canvas = document.createElement('canvas');

    let cameraStream = null;

    showCameraBtn.addEventListener('click', () => {
        uploadView.style.display = 'none';
        cameraView.style.display = 'flex';
        imagePreviewContainer.style.display = 'none';
        resultsSection.style.display = 'none';
        showCameraBtn.classList.add('active');
        showUploadBtn.classList.remove('active');
        startCamera();
    });

    showUploadBtn.addEventListener('click', () => {
        cameraView.style.display = 'none';
        uploadView.style.display = 'block';
        imagePreviewContainer.style.display = 'none';
        resultsSection.style.display = 'none';
        showUploadBtn.classList.add('active');
        showCameraBtn.classList.remove('active');
        stopCamera();
    });

    async function startCamera() {
        if (cameraStream) return;
        try {
            cameraStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
            videoFeed.srcObject = cameraStream;
        } catch (error) {
            console.error("Error accessing camera:", error);
            alert("Could not access camera. Please check permissions and try again.");
        }
    }

    function stopCamera() {
        if (cameraStream) {
            cameraStream.getTracks().forEach(track => track.stop());
            cameraStream = null;
        }
    }

    imageUploadInput.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (e) => {
                if (uploadedImage.src) {
                    URL.revokeObjectURL(uploadedImage.src);
                }
                uploadedImage.src = e.target.result;
                imagePreviewContainer.style.display = 'flex';
                uploadView.style.display = 'none';
                resultsSection.style.display = 'none';
            };
            reader.readAsDataURL(file);
        }
    });

    predictButton.addEventListener('click', () => {
        const file = imageUploadInput.files[0];
        if (!file) {
            alert('Please upload an image first.');
            return;
        }
        sendPredictionRequest(file);
    });

    snapBtn.addEventListener('click', () => {
        if (!cameraStream) {
            alert('Camera is not active.');
            return;
        }

        const context = canvas.getContext('2d');
        canvas.width = videoFeed.videoWidth;
        canvas.height = videoFeed.videoHeight;
        context.drawImage(videoFeed, 0, 0, canvas.width, canvas.height);

        stopCamera();

        canvas.toBlob((blob) => {
            if (blob) {
                if (uploadedImage.src) {
                    URL.revokeObjectURL(uploadedImage.src);
                }
                uploadedImage.src = URL.createObjectURL(blob);

                sendPredictionRequest(blob);
            } else {
                console.error("Failed to create blob from canvas.");
                alert("Error capturing image. Please try again.");
            }
        }, 'image/jpeg');
    });

    async function sendPredictionRequest(fileOrBlob) {
        cameraView.style.display = 'none';
        uploadView.style.display = 'none';
        imagePreviewContainer.style.display = 'none';
        resultsSection.style.display = 'none';
        spinner.style.display = 'block';

        const formData = new FormData();
        formData.append('file', fileOrBlob, 'image.jpg');

        try {
            const response = await fetch('/predict', { method: 'POST', body: formData });
            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || `Server error: ${response.statusText}`);
            }

            const data = await response.json();

            spinner.style.display = 'none';
            imagePreviewContainer.style.display = 'flex';
            resultsSection.style.display = 'block';

            resultDiv.innerHTML = `<p>${data.prediction}</p>`;

            if (data.recipe) {
                const recipe = data.recipe;
                let ingredientsHTML = recipe.ingredients.map(ing => `<li>${ing.quantity || ''} ${ing.unit || ''} ${ing.name}</li>`.trim()).join('');
                let instructionsHTML = recipe.instructions.map(inst => `<li>${inst}</li>`).join('');
                recipeContainer.innerHTML = `
                    <h3>📖 Recipe for ${recipe.name}</h3>
                    <p class="description">${recipe.description}</p>
                    <div class="recipe-layout">
                        <div class="ingredients"><h4>Ingredients</h4><ul>${ingredientsHTML}</ul></div>
                        <div class="instructions"><h4>Instructions</h4><ol>${instructionsHTML}</ol></div>
                    </div>`;
            } else {
                recipeContainer.innerHTML = `<p>Sorry, a recipe for ${data.prediction} could not be found.</p>`;
            }
        } catch (error) {
            spinner.style.display = 'none';
            resultsSection.style.display = 'block';
            imagePreviewContainer.style.display = 'flex';
            console.error('Error:', error);
            resultDiv.innerHTML = `<p style="color: #e74c3c;">An error occurred: ${error.message}</p>`;
            recipeContainer.innerHTML = '';
        }
    }
});