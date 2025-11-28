# Copilot Instructions for Accessible Web

## Project Overview

**Accessible Web** is an assistive technology hub providing tools for users with accessibility needs (visual impairments, dyslexia, language barriers). The application is built as a **Flask backend + HTML/vanilla JS frontend** that integrates three core services:

1. **PDF Text Extraction** - Converts PDF files to text using PyMuPDF (fitz)
2. **Text Translation** - Multi-language translation via Google Translate API
3. **Text-to-Speech (TTS)** - Converts text to audio in 20+ languages using Microsoft Edge-TTS

## Architecture

### Backend (`backend/app.py`)
- **Framework**: Flask with CORS enabled for frontend communication
- **Port**: `http://127.0.0.1:5000` (hardcoded in frontend)
- **Key Dependencies**:
  - `flask-cors`: Cross-origin requests from frontend
  - `fitz` (PyMuPDF): PDF parsing
  - `deep_translator`: GoogleTranslator for translation
  - `edge_tts`: Async TTS audio generation (requires asyncio event loop management)

**API Endpoints**:
- `POST /extract-pdf` - Accepts multipart form data with PDF file; returns JSON `{"text": "..."}` or error
- `POST /translate` - JSON body `{"text": "...", "target_lang": "xx"}` (language code format: "en", "hi", "fr", etc.)
- `POST /tts` - JSON body `{"text": "...", "lang": "xx"}` - returns MP3 audio file; saves to `tts_audio/` directory

### Frontend (`frontend/index.html`)
- **Single-page vanilla JS** with inline styles and scripts (no build tool required)
- **Accessibility Features**:
  - High-contrast theme toggle (black background, yellow text)
  - Dyslexia-friendly font (Comic Sans MS with increased letter-spacing)
  - Voice guidance for blind users (browser Web Speech API) on file input focus/hover
- **UI Layout**: Toolbar buttons → text area → three feature sections (PDF extraction, translation, TTS)

## Critical Patterns & Conventions

### 1. Language Code Consistency
The app supports 20 languages. **Language codes must be identical across frontend, backend voice mapping, and translator**. Currently supported: `en`, `hi`, `mr`, `kn`, `ta`, `te`, `gu`, `bn`, `ml`, `pa`, `ur` (Indian languages) + `fr`, `es`, `de`, `ar`, `it`, `pt`, `ru`, `ja`, `ko`, `zh-cn` (international).

- Frontend has duplicate language dropdowns for translation and TTS - keep these synchronized
- Backend `voice_map` in `/tts` route defines available voices - any new language requires adding voice mapping

### 2. File I/O & Async Patterns
- **PDF extraction**: Reads uploaded file via `request.files["pdf"]`; extracts all pages into single text string
- **TTS audio generation**: Uses `asyncio` with `edge_tts.Communicate()` - requires proper event loop management (see `generate_audio()` function pattern)
- **File storage**: TTS outputs to `tts_audio/` directory with UUID filenames; frontend doesn't persist audio (browser-managed Blob URLs)

### 3. Data Flow
```
Frontend Form → Backend JSON/FormData → Processing → JSON response or Audio blob
                                         ↓
                                    GPU-less async TTS
                                    Google Translate API
                                    Local PDF parsing
```

### 4. Error Handling
- Backend returns `{"error": "message"}` with HTTP 4xx/5xx status codes
- Frontend uses simple `alert()` for user feedback - no error persistence
- PDF extraction fails silently (returns "Error extracting text." string)

## Developer Workflow

### Running the Application
1. **Backend**: `python app.py` from `backend/` directory (runs Flask dev server on port 5000 with debug enabled)
2. **Frontend**: Open `frontend/index.html` in browser directly (no build step needed)
3. **Testing**: Backend must be running for translation/TTS; PDF extraction works independently

### Adding a New Language
1. Add language option to both `<select id="targetLang">` and `<select id="ttsLang">` in `index.html`
2. Verify GoogleTranslator supports the language code (check `deep_translator` docs)
3. Add language + voice to backend `voice_map` in `/tts` route (check Microsoft Edge-TTS voice list)
4. Test translation and TTS endpoints with the new language code

### Common Pitfalls
- **Frontend/Backend mismatch**: `backendBase` URL must match running Flask server port
- **TTS async issues**: Edge-TTS requires proper event loop; test with longer text (>10 seconds) to catch timing bugs
- **CORS errors**: Frontend is CORS-enabled but ensure no 405 errors on OPTIONS requests
- **Language codes**: Google Translate may have different codes than Edge-TTS voices (e.g., `zh-cn` vs `zh-Hans`)

## Project-Specific Tools & Setup
- No build tool required (vanilla JS, CSS-in-HTML)
- No package.json; Flask `requirements.txt` needed (not visible in workspace - should exist in `backend/`)
- Audio player in frontend is initially hidden; shown on TTS request via `style.display = "block"`

## Key Files to Reference
- `frontend/index.html` - Main UI and JavaScript client logic
- `backend/app.py` - All three service endpoints; voice mapping for TTS
- `tts_audio/` directory - Where generated audio files are saved (not committed)
