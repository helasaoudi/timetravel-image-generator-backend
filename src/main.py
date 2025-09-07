
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv
from google import genai
import io
import logging
import base64

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Time Travel Image Transformer")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini client
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise HTTPException(status_code=500, detail="GEMINI_API_KEY not found in .env file")
client = genai.Client(api_key=API_KEY)

@app.post("/transform-image/")
async def transform_image(file: UploadFile = File(...), year: int = Form(...)):
    """
    Endpoint to transform an image to look like it was from a specified year.
    Accepts an image file and a year, processes it with Gemini API, and returns the transformed image.
    """
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            logger.error(f"Invalid file type: {file.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image")

        # Read image data
        image_data = await file.read()
        if not image_data:
            logger.error("Uploaded file is empty")
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        # Log file size for debugging
        logger.info(f"Uploaded file size: {len(image_data)} bytes, content_type: {file.content_type}")

        # Validate image with PIL
        try:
            original_img = Image.open(BytesIO(image_data))
            original_img.verify()  # Verify image integrity
            # Reopen image after verification
            original_img = Image.open(BytesIO(image_data))
        except Exception as e:
            logger.error(f"Failed to open image with PIL: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")

        # Determine mime type for Gemini API
        mime_type = file.content_type
        if mime_type not in ["image/png", "image/jpeg"]:
            logger.warning(f"Unsupported mime type {mime_type}, converting to PNG")
            buffer = BytesIO()
            original_img.convert("RGB").save(buffer, format="PNG")
            image_data = buffer.getvalue()
            mime_type = "image/png"
        else:
            if original_img.format != "PNG":
                buffer = BytesIO()
                original_img.convert("RGB").save(buffer, format="PNG")
                image_data = buffer.getvalue()
                mime_type = "image/png"

        # Define the time-travel prompt
        prompt = f"Transform this image to look like it was in {year}, realistic style."
        logger.info(f"Processing image with prompt: {prompt}")

        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": image_data
                            }
                        },
                        {"text": prompt}
                    ],
                }
            ],
        )

        # Log the response structure for debugging
        logger.info(f"Gemini API response: {response.candidates[0].content.parts}")

        # Extract transformed image
        image_parts = [
            part.inline_data.data
            for part in response.candidates[0].content.parts
            if part.inline_data
        ]

        if not image_parts:
            logger.error("No image data found in Gemini API response")
            raise HTTPException(status_code=500, detail="No image data found in Gemini API response")

        # Log size of returned image data
        logger.info(f"Transformed image data size: {len(image_parts[0])} bytes")

        # Save raw response data for debugging
        with open(f"raw_response_{year}.bin", "wb") as f:
            f.write(image_parts[0])
        logger.info(f"Saved raw response data to raw_response_{year}.bin")

        # Try decoding as base64 in case the data is encoded
        try:
            image_data_decoded = base64.b64decode(image_parts[0])
            logger.info(f"Base64 decoded data size: {len(image_data_decoded)} bytes")
        except Exception as e:
            logger.warning(f"Base64 decoding failed: {str(e)}, using raw data")
            image_data_decoded = image_parts[0]

        # Try to open the transformed image
        try:
            new_img = Image.open(BytesIO(image_data_decoded))
            new_img.verify()  # Verify image integrity
            new_img = Image.open(BytesIO(image_data_decoded))  # Reopen after verify
        except Exception as e:
            logger.error(f"Failed to open transformed image: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error processing transformed image: {str(e)}")

        # Convert to PNG and return
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
        logger.error(f"Error in transform_image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {"message": "Time Travel Image Transformer API is running"}