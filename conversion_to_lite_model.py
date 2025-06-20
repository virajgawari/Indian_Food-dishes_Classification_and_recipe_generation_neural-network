import tensorflow as tf

# Path to your saved Keras model
KERAS_MODEL_PATH = 'indian_food_classifier.h5'
# Path where you want to save the TFLite model
TFLITE_MODEL_PATH = 'model.tflite'

print(f"Loading Keras model from: {KERAS_MODEL_PATH}")
# Load the model
model = tf.keras.models.load_model(KERAS_MODEL_PATH)

# Create a TFLite converter
converter = tf.lite.TFLiteConverter.from_keras_model(model)

# Optional: Add optimizations
converter.optimizations = [tf.lite.Optimize.DEFAULT]

# Convert the model
tflite_model = converter.convert()

print(f"Saving TFLite model to: {TFLITE_MODEL_PATH}")
# Save the model to a file
with open(TFLITE_MODEL_PATH, 'wb') as f:
    f.write(tflite_model)

print("Conversion successful!")