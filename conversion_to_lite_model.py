import tensorflow as tf


KERAS_MODEL_PATH = 'indian_food_classifier.h5'
TFLITE_MODEL_PATH = 'model.tflite'

print(f"Loading Keras model from: {KERAS_MODEL_PATH}")

model = tf.keras.models.load_model(KERAS_MODEL_PATH)
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

print(f"Saving TFLite model to: {TFLITE_MODEL_PATH}")
with open(TFLITE_MODEL_PATH, 'wb') as f:
    f.write(tflite_model)

print("Conversion successful!")
