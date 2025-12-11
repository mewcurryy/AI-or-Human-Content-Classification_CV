import tensorflow as tf
from PIL import Image
import numpy as np
import instaloader
import requests
from io import BytesIO
from flask import Flask, request, jsonify, render_template
import os
import base64
from werkzeug.utils import secure_filename

def load_keras_model(model_path):
    try:
        model = tf.keras.models.load_model(model_path)
        return model
    except Exception as e:
        print(f"Error saat memuat model: {e}")
        return None

def preprocess_image(image, target_size=(512, 512)):
    if image.mode != "RGB":
        image = image.convert("RGB")
    
    img = image.resize(target_size)
    
    img_array = np.array(img)
    img_array = np.expand_dims(img_array, axis=0) 
    
    img_array = img_array / 255.0
    
    darkening_factor = 0.6
    darkened_image_array = img_array * darkening_factor
    
    return darkened_image_array

def getLinkPost(link):
    shortcode = link.split("/p/")[1].split("/")[0]
    print(shortcode)
    return shortcode

def classify_image(image):
    if model is None:
        return {"error": "Model tidak dapat dimuat. Pastikan file model ada di direktori yang sama."}
    
    processed_image = preprocess_image(image)
    prediction = model.predict(processed_image)
    
    prob_ai = float(prediction[0][0])
    prob_human = 1 - prob_ai
    hasil_prediksi = "Manusia" if prob_human > prob_ai else "AI"
    confidence = max(prob_human, prob_ai)
    
    return {
        "prediction": hasil_prediksi,
        "confidence": confidence,
        "prob_ai": prob_ai,
        "prob_human": prob_human
    }

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create uploads directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Load the model at startup
model = load_keras_model('./models/ResNet50V2-AIvsHumanGenImages-Final.keras')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file:
        image = Image.open(file)
        result = classify_image(image)
        return jsonify(result)

@app.route('/instagram', methods=['POST'])
def instagram_fetch():
    data = request.get_json()
    ig_url = data.get('url', '')
    
    if not ig_url:
        return jsonify({"error": "No URL provided"}), 400
    
    if "instagram.com" not in ig_url:
        return jsonify({"error": "Link tidak valid. Pastikan itu link Instagram."}), 400
    
    if "/reel/" in ig_url:
        return jsonify({"error": "Post ini berupa reels. Hanya gambar yang bisa diproses."}), 400
    
    try:
        shortcode = getLinkPost(ig_url)
        L = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(L.context, shortcode)
    except instaloader.exceptions.BadResponseException:
        return jsonify({"error": "Post tidak bisa diakses. Kemungkinan akun private."}), 400
    except Exception as e:
        return jsonify({"error": f"Tidak dapat mengakses Instagram. Kemungkinan IP server diblokir IG. {str(e)}"}), 400
    
    if post.is_video:
        return jsonify({"error": "Post ini berupa video. Hanya gambar yang bisa diproses."}), 400
    
    try:
        image_url = post.url 
        response = requests.get(image_url)
        
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            result = classify_image(image)
            img_base64 = base64.b64encode(response.content).decode('utf-8')
            result['image_data'] = img_base64
            return jsonify(result)
        else:
            return jsonify({"error": "Gagal mengunduh gambar dari Instagram."}), 400
    except Exception as e:
        return jsonify({"error": f"Error processing image: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)