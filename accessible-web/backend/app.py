from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from deep_translator import GoogleTranslator
import fitz
import os
import uuid
import asyncio
import edge_tts

app = Flask(__name__)
CORS(app)

# ---------------------------
# 1. PDF → TEXT
# ---------------------------
@app.route("/extract-pdf", methods=["POST"])
def extract_pdf():
    if "pdf" not in request.files:
        return jsonify({"error": "No PDF uploaded"}), 400

    pdf_file = request.files["pdf"]

    try:
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()

        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
# 2. TRANSLATION
# ---------------------------
@app.route("/translate", methods=["POST"])
def translate_text():
    data = request.json
    text = data.get("text")
    target = data.get("target_lang")

    try:
        translated_text = GoogleTranslator(source="auto", target=target).translate(text)
        return jsonify({"translated": translated_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------
# 3. TEXT TO SPEECH (EDGE-TTS)
# ---------------------------
@app.route("/tts", methods=["POST"])
def tts():
    data = request.json
    text = data.get("text")
    lang = data.get("lang")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Voice mapping
    voice_map = {
        "en": "en-US-AriaNeural",
        "hi": "hi-IN-SwaraNeural",
        "mr": "mr-IN-AarohiNeural",
        "kn": "kn-IN-SapnaNeural",
        "ta": "ta-IN-PallaviNeural",
        "te": "te-IN-ShrutiNeural",
        "ml": "ml-IN-SobhanaNeural",
        "gu": "gu-IN-DhwaniNeural",
        "bn": "bn-IN-TanishaNeural",
        "pa": "pa-IN-KomalNeural",
        "ur": "ur-PK-UzmaNeural",
        "fr": "fr-FR-DeniseNeural",
        "es": "es-ES-ElviraNeural",
        "de": "de-DE-KatjaNeural",
        "ar": "ar-AE-FatimaNeural",
        "ja": "ja-JP-NanamiNeural",
        "ko": "ko-KR-SunHiNeural",
        "zh-cn": "zh-CN-XiaoxiaoNeural",
    }

    voice = voice_map.get(lang)
    if not voice:
        return jsonify({"error": "Invalid language"}), 400

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join("tts_audio", filename)
    os.makedirs("tts_audio", exist_ok=True)

    # Proper async execution
    async def generate_audio():
        communicate = edge_tts.Communicate(text=text, voice=voice)
        await communicate.save(filepath)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(generate_audio())
    loop.close()

    return send_file(filepath, mimetype="audio/mpeg")


# ---------------------------
# RUN SERVER
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
