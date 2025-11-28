from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from deep_translator import GoogleTranslator
import fitz
import pdfplumber
from gtts import gTTS
import os
import uuid
import whisper
import pyttsx3
import subprocess



app = Flask(__name__)
CORS(app)

model = whisper.load_model("base")

# Folders
UPLOAD_FOLDER = "uploads"
AUDIO_FOLDER = "tts_audio"
UPLOAD_AUDIO = "audio_uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_AUDIO, exist_ok=True)

# -------------------------------------------
# 1) PDF → TEXT
# -------------------------------------------
@app.route("/extract-pdf", methods=["POST"])
def extract_pdf():
    try:
        if "pdf" not in request.files:
            return jsonify({"error": "No PDF uploaded"}), 400

        pdf_file = request.files["pdf"]

        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        extracted = ""

        for page in doc:
            extracted += page.get_text()

        if not extracted.strip():
            return jsonify({"text": "", "warning": "PDF has no text (maybe scanned)"}), 200

        return jsonify({"text": extracted})

    except Exception as e:
        return jsonify({"error": f"PDF extraction failed: {e}"}), 500


# -------------------------------------------
# 2) TRANSLATE
# -------------------------------------------
@app.route("/translate", methods=["POST"])
def translate_text():
    try:
        data = request.json
        text = data.get("text", "").strip()
        target = data.get("target_lang", "en")

        if not text:
            return jsonify({"error": "Text empty"}), 400

        translated = GoogleTranslator(source="auto", target=target).translate(text)
        return jsonify({"translated": translated})

    except Exception as e:
        return jsonify({"error": f"Translation failed: {e}"}), 500


# ---------------------------
# 3. TEXT → SPEECH (gTTS with Debug Logs)
# ---------------------------




@app.route("/tts", methods=["POST"])
def tts_offline():
    try:
        data = request.json
        text = data.get("text", "")
        lang = data.get("lang", "en")

        print("\n----------------------------")
        print("OFFLINE TTS REQUEST RECEIVED")
        print("LANG:", lang)
        print("TEXT LENGTH:", len(text))
        print("----------------------------\n")

        os.makedirs("tts_audio", exist_ok=True)

        filename = f"{uuid.uuid4()}"
        wav_path = os.path.join("tts_audio", f"{filename}.wav")
        mp3_path = os.path.join("tts_audio", f"{filename}.mp3")

        # Generate WAV using pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.save_to_file(text, wav_path)
        engine.runAndWait()

        # Convert WAV → MP3 using ffmpeg
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, mp3_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Debug ffmpeg errors
        if result.returncode != 0:
            print("FFMPEG ERROR:", result.stderr.decode())
            return jsonify({"error": "FFmpeg conversion failed"}), 500

        # Return only filename
        return jsonify({"audio_url": f"{filename}.mp3"})

    except Exception as e:
        print("TTS ERROR:", e)
        return jsonify({"error": str(e)}), 500



# ---------------------------
#  SPEECH → TEXT (Whisper)
# ---------------------------
@app.route("/speech-to-text", methods=["POST"])
def speech_to_text():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400

    audio_file = request.files["audio"]

    # Save uploaded file
    filename = f"{uuid.uuid4()}.wav"
    filepath = os.path.join(UPLOAD_AUDIO, filename)
    audio_file.save(filepath)

    try:
        # Whisper automatically converts formats
        result = model.transcribe(filepath)
        text = result["text"].strip()

        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": f"STT failed: {e}"}), 500


# Serve generated audio files
@app.route("/tts_audio/<path:filename>")
def serve_tts_audio(filename):
    return send_file(os.path.join("tts_audio", filename), mimetype="audio/mpeg")




## -------------------------------------------
# RUN SERVER
# -------------------------------------------
if __name__ == "__main__":
    print("\n🚀 Backend running at: http://127.0.0.1:5000\n")
    app.run(debug=True)
