import os
import io
import json
import logging
import sqlite3
from datetime import datetime
import tensorflow as tf
from PIL import Image, UnidentifiedImageError
import numpy as np
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MODEL_PATH = "indian_food_classifier.h5"
CLASS_NAMES_PATH = "class_names.txt"
RECIPES_PATH = "recipes.json"
DATABASE_PATH = "predictions.db"
UPLOADS_FOLDER = os.path.join('static', 'uploads')
IMAGE_SIZE = (224, 224)

os.makedirs(UPLOADS_FOLDER, exist_ok=True)


def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            predicted_class TEXT NOT NULL,
            timestamp DATETIME NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    app.logger.info(f"Database initialized at {DATABASE_PATH}")


try:
    app.logger.info(f"Loading model from: {MODEL_PATH}")
    model = tf.keras.models.load_model(MODEL_PATH)
    
    app.logger.info(f"Loading class names from: {CLASS_NAMES_PATH}")
    with open(CLASS_NAMES_PATH, "r") as f:
        class_names = [line.strip() for line in f.readlines()]

    app.logger.info(f"Loading recipes from: {RECIPES_PATH}")
    with open(RECIPES_PATH, "r", encoding="utf-8") as f:
        recipes_data = json.load(f)
    recipes_dict = {recipe['folderName']: recipe for recipe in recipes_data['recipes']}
    
    app.logger.info("All resources loaded successfully.")
    
except FileNotFoundError as e:
    app.logger.error(f"FATAL: A required file was not found: {e}. The application cannot start.")
    raise


def predict_image(image: Image.Image) -> str:
    img = image.resize(IMAGE_SIZE)
    img_array = np.array(img)
    if img_array.shape[2] == 4:
        img_array = img_array[:, :, :3]
    img_array = np.expand_dims(img_array, axis=0)
    predictions = model.predict(img_array)
    score = tf.nn.softmax(predictions[0])
    return class_names[np.argmax(score)]


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def handle_prediction():
    if 'file' not in request.files:
        return jsonify({'error': "Missing 'file' part in the request."}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': "No file selected."}), 400

    if file:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{file.filename}"
            image_path = os.path.join(UPLOADS_FOLDER, filename)
            
            image_bytes = file.read()
            image = Image.open(io.BytesIO(image_bytes))
            image.save(image_path)
            app.logger.info(f"Image saved to {image_path}")

            predicted_class_key = predict_image(image)
            
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO predictions (image_path, predicted_class, timestamp) VALUES (?, ?, ?)",
                (image_path, predicted_class_key, datetime.now())
            )
            conn.commit()
            conn.close()
            app.logger.info(f"Prediction for '{predicted_class_key}' saved to database.")

            recipe_details = recipes_dict.get(predicted_class_key)
            display_name = predicted_class_key.replace('_', ' ').title()
            
            return jsonify({
                'prediction': display_name,
                'recipe': recipe_details 
            }), 200

        except UnidentifiedImageError:
            app.logger.error(f"Uploaded file '{file.filename}' is not a valid image.")
            return jsonify({'error': "The uploaded file is not a valid image."}), 400
        except Exception as e:
            app.logger.error(f"An unexpected error occurred: {e}", exc_info=True)
            return jsonify({'error': "An internal server error occurred."}), 500

    return jsonify({'error': "An unknown error occurred."}), 500


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)