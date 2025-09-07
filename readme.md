# Time Travel Image Transformer API

This project provides a FastAPI-based web service that transforms uploaded images to look as if they were taken in a specified year, using the Gemini API for image generation.

## Features

- Upload an image and specify a target year.
- The API returns a transformed image in PNG format, styled to match the requested year.
- CORS enabled for easy integration with web frontends.
- Health check endpoint (`/`).

## Requirements

- Python 3.11+
- [Google Gemini API access](https://ai.google.dev/)
- Gemini API Python SDK (`google-genai`)
- FastAPI
- Pillow
- python-dotenv

## Setup

1. **Clone the repository:**
   ```sh
   git clone <your-repo-url>
   cd nano_bannana_hackathon
   ```

2. **Create and activate a virtual environment:**
   ```sh
   python3 -m venv myvenv
   source myvenv/bin/activate
   ```

3. **Install dependencies:**
   ```sh
   pip install fastapi uvicorn pillow python-dotenv google-genai
   ```

4. **Set up your `.env` file:**
   Create a `.env` file in the project root with your Gemini API key:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

5. **Run the server:**
   ```sh
   uvicorn src.main:app --reload
   ```

## API Endpoints

### `POST /transform-image/`

Transform an uploaded image to look like it was taken in a specified year.

**Form Data:**
- `file`: Image file (PNG or JPEG recommended)
- `year`: Target year (integer)

**Response:**
- Returns the transformed image as a PNG file.

**Example using `curl`:**
```sh
curl -X POST "http://127.0.0.1:8000/transform-image/" \
  -F "file=@your_image.jpg" \
  -F "year=1980" \
  --output transformed.png
```

### `GET /`

Health check endpoint.

**Response:**
```json
{"message": "Time Travel Image Transformer API is running"}
```

## Notes

- Only PNG and JPEG images are supported. Other formats will be converted to PNG.
- The Gemini API must be accessible and the API key must be valid.
- The transformed image is returned as a downloadable PNG file.

## Troubleshooting

- If you see `GEMINI_API_KEY not found in .env file`, ensure your `.env` file is present and contains the correct key.
- For import errors, make sure you run `uvicorn` from the project root and that `src/__init__.py` exists.

## License

MIT License

---

**Enjoy time traveling