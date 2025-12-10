import streamlit as st
import tensorflow as tf
from PIL import Image
import numpy as np
import instaloader
import tempfile
import os
import shutil
import requests
import cv2

st.set_page_config(
    page_title="Human vs AI Image Detector",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="auto",
)

@st.cache_resource
def load_keras_model(model_path):
    """Memuat model Keras dari path yang diberikan."""
    try:
        model = tf.keras.models.load_model(model_path)
        return model
    except Exception as e:
        st.error(f"Error saat memuat model: {e}")
        return None

def preprocess_image(image, target_size=(512, 512)):
    """
    Mengubah ukuran, menormalisasi, dan menggelapkan gambar agar sesuai
    dengan input model.
    """
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

def main():
    st.title("🤖 Detektor Gambar: AI vs Manusia")
    st.markdown("""
        Aplikasi ini bisa mendeteksi apakah gambar dibuat oleh **AI** atau oleh **Manusia** dengan menggunakan deep learning.
    """)
    st.divider()
    
    model = load_keras_model('./models/ResNet50V2-AIvsHumanGenImages-Final.keras')
    if model is None:
        st.warning("Model tidak dapat dimuat. Pastikan file model ada di direktori yang sama.")
        return


    st.header("📁 Deteksi dari Upload Gambar")

    uploaded_file = st.file_uploader(
        "Pilih sebuah gambar...",
        type=["jpg", "jpeg", "png"],
        help="Format: JPG, JPEG, PNG"
    )
        
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
            
        col1, col2 = st.columns(2)
        with col1:
            st.image(image, caption="Gambar yang Diunggah", use_container_width=True)
            
        with st.spinner('Menganalisis gambar...'):
            processed_image = preprocess_image(image)
            prediction = model.predict(processed_image)
            print(prediction)
            print(prediction[0][0])
            prob_ai = float(prediction[0][0])
            prob_human = 1 - prob_ai
            hasil_prediksi = "Manusia" if prob_human > prob_ai else "AI"
            confidence = max(prob_human, prob_ai)

        with col2:
            st.subheader("Hasil Prediksi:")
            if hasil_prediksi == "Manusia":
                st.success("✅ Gambar ini sepertinya dibuat oleh **Manusia**.")
            else:
                st.error("🤖 Gambar ini sepertinya dibuat oleh **AI**.")
                
            st.metric(label="Tingkat Keyakinan", value=f"{confidence:.2%}")
            st.write("Detail Probabilitas:")
            st.write(f"- Manusia: `{prob_human:.2%}`")
            st.write(f"- AI: `{prob_ai:.2%}`")

    st.divider()

    st.header("📸 Deteksi dari Link Instagram")

    ig_url = st.text_input(
        "Masukkan link Instagram (post/photo/profil):",
        placeholder="https://www.instagram.com/p/Cxxxx/"
    )

    if ig_url:
        if "instagram.com" not in ig_url:
            st.error("❌ Link tidak valid. Pastikan itu link Instagram.")
            return

        if "/reel/" in ig_url:
            st.error('🚫 Post ini berupa reels. Hanya gambar yang bisa diproses.')
            return
        
        shortcode = getLinkPost(ig_url)
        L = instaloader.Instaloader()
        
        # Download gambar
        try:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
        except instaloader.exceptions.BadResponseException:
            st.error("⚠️ Post tidak bisa diakses. Kemungkinan akun private.")
            return

        if post.is_video:
            st.error("🚫 Post ini berupa video. Hanya gambar yang bisa diproses.")
            return 
        
        st.success("🔓 Akun bersifat public — melanjutkan download.")

        image_url = post.url 
        response = requests.get(image_url)

        if response.status_code == 200:
            print("Gambar berhasil didownload ke memori.")

            image_array = np.frombuffer(response.content, dtype=np.uint8)
            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # ubah BGR → RGB
            image = Image.fromarray(image)
            
        col1, col2 = st.columns(2)
        with col1:
            st.image(image, caption="Gambar yang Diunggah", use_container_width=True)
            
        with st.spinner('Menganalisis gambar...'):
            processed_image = preprocess_image(image)
            prediction = model.predict(processed_image)
                
            prob_ai = float(prediction[0][0])
            prob_human = 1 - prob_ai
            hasil_prediksi = "Manusia" if prob_human > prob_ai else "AI"
            confidence = max(prob_human, prob_ai)

        with col2:
            st.subheader("Hasil Prediksi:")
            if hasil_prediksi == "Manusia":
                st.success("✅ Gambar ini sepertinya dibuat oleh **Manusia**.")
            else:
                st.error("🤖 Gambar ini sepertinya dibuat oleh **AI**.")
                
            st.metric(label="Tingkat Keyakinan", value=f"{confidence:.2%}")
            st.write("Detail Probabilitas:")
            st.write(f"- Manusia: `{prob_human:.2%}`")
            st.write(f"- AI: `{prob_ai:.2%}`")

            st.divider()

if __name__ == "__main__":
    main()