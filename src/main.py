from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
from google import genai
import logging
import base64

# ----------------------------
# Logging setup
# ----------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("time_travel_api")

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    logger.error("GEMINI_API_KEY not found in .env")
    raise RuntimeError("GEMINI_API_KEY not found in .env file")

# ----------------------------
# Initialize FastAPI
# ----------------------------
app = FastAPI(title="Time Travel Image Transformer")

# ----------------------------
# Add CORS middleware
# ----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------
# Initialize Gemini client
# ----------------------------
client = genai.Client(api_key=API_KEY)

# ----------------------------
# Health check
# ----------------------------
@app.get("/")
async def root():
    return {"message": "Time Travel Image Transformer API is running"}

# ----------------------------
# Transform image endpoint
# ----------------------------
@app.post("/transform-image/")
async def transform_image(file: UploadFile = File(...), year: int = Form(...)):
    try:
        # 1️⃣ Validate file type
        if not file.content_type.startswith("image/"):
            logger.error(f"Invalid file type uploaded: {file.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image")

        # 2️⃣ Read uploaded file
        image_data = await file.read()
        if not image_data:
            logger.error("Uploaded file is empty")
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
        logger.info(f"Uploaded file size: {len(image_data)} bytes, type: {file.content_type}")

        # 3️⃣ Validate with PIL
        try:
            original_img = Image.open(BytesIO(image_data))
            original_img.verify()
            original_img = Image.open(BytesIO(image_data))
        except Exception as e:
            logger.error(f"PIL failed to open uploaded image: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

        # 4️⃣ Convert to PNG for Gemini API
        buffer = BytesIO()
        original_img.convert("RGB").save(buffer, format="PNG")
        image_data = buffer.getvalue()
        mime_type = "image/png"

        # 5️⃣ Prepare prompt
        prompt = f"Transform this image to look like it was in {year}, realistic style."
        logger.info(f"Sending request to Gemini API with prompt: {prompt}")

        # 6️⃣ Call Gemini API
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[{
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": mime_type, "data": image_data}},
                    {"text": prompt}
                ]
            }],
        )

        # 7️⃣ Extract image data from response
        image_parts = [
            part.inline_data.data
            for part in response.candidates[0].content.parts
            if part.inline_data
        ]

        if not image_parts:
            logger.error("No image data returned from Gemini API")
            raise HTTPException(status_code=500, detail="No image data found in Gemini API response")

        # Log raw response size
        logger.info(f"Raw Gemini API response size: {len(image_parts[0])} bytes")
        with open(f"debug_response_{year}.bin", "wb") as f:
            f.write(image_parts[0])
            logger.info(f"Saved raw response to debug_response_{year}.bin")

        # 8️⃣ Attempt to decode Base64 if needed
        transformed_data = image_parts[0]
        try:
            # Test if it's Base64 (common if decoding fails)
            transformed_data = base64.b64decode(transformed_data)
            logger.info(f"Decoded Base64 transformed image, size: {len(transformed_data)} bytes")
        except Exception:
            logger.info("Gemini response is raw bytes, skipping Base64 decode")

        # 9️⃣ Open transformed image with PIL
        try:
            new_img = Image.open(BytesIO(transformed_data))
            new_img.verify()
            new_img = Image.open(BytesIO(transformed_data))
        except Exception as e:
            logger.error(f"Failed to open transformed image: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing transformed image: {str(e)}")

        # 10️⃣ Save as PNG and return
        output_buffer = BytesIO()
        new_img.save(output_buffer, format="PNG")
        output_buffer.seek(0)

        logger.info(f"Returning transformed image for year {year}")
        return StreamingResponse(
            output_buffer,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=time_travel_{year}.png"}
        )

    except Exception as e:
        logger.error(f"Unexpected error in transform_image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
