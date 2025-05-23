# Floor Replacement API

## Description
This project provides a REST API that takes an image of a room and an image of a floor tile, then replaces the detected floor in the room image with the provided tile pattern.

## Features
- Replaces the floor in room images with a user-provided tile image.
- Implements basic floor detection using HSV color segmentation (currently tuned for brown/grayish floors).
- Offers a simple REST API endpoint (`/replace_floor`) for integration.
- Includes unit and integration tests.

## Project Structure
```
.
├── app.py                      # Main Flask application, API endpoint definition
├── image_processing/
│   └── floor_replacement.py    # Core logic for floor detection and replacement
├── tests/
│   ├── TestData/               # Temporary directory for test images (created/deleted by tests)
│   ├── test_api.py             # Integration tests for the Flask API
│   └── test_image_processing.py # Unit tests for image processing functions
├── data/                       # Placeholder directory for potential future use (e.g., sample images)
├── temp_uploads/               # Temporary directory for uploaded files (created by app.py)
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Setup and Installation

### Prerequisites
- Python 3.7+

### Steps
1.  **Clone the repository (if applicable):**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    # venv\Scripts\activate
    # On macOS/Linux
    # source venv/bin/activate
    ```

3.  **Install dependencies:**
    The necessary libraries are listed in `requirements.txt`. Install them using pip:
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application
To start the Flask development server:
```bash
python app.py
```
The application will be accessible by default at `http://127.0.0.1:5000/` (or `http://localhost:5000/`).

### Accessing the Web Interface
Once the application is running, you can access a simple web interface by navigating to:
```
http://localhost:5000/
```
(or the configured host/port) in your web browser. This interface allows you to:
- Upload the room image directly from your computer.
- Upload the tile image directly from your computer.
- Submit the images and view the processed result directly on the page.
- Receive error messages on the page if something goes wrong (e.g., missing files, processing errors).

The web interface uses an HTML form that submits data to the `/replace_floor_html` endpoint, which then calls the core image processing logic.

## API Endpoint (for Machine-to-Machine Interaction)

### `POST /replace_floor`
Replaces the floor in a room image with a new tile image. This endpoint is suitable for programmatic access or integration with other services.

-   **Method:** `POST`
-   **Request Type:** `multipart/form-data`
-   **Parameters:**
    -   `room_image`: Image file (e.g., `.jpg`, `.png`) of the room.
    -   `tile_image`: Image file (e.g., `.jpg`, `.png`) of the floor tile.

-   **Success Response (`200 OK`):**
    -   **Content-Type:** `image/jpeg`
    -   **Body:** The resulting image file (JPEG format) with the floor replaced. The image is sent as an attachment.

-   **Error Responses:**
    -   **`400 Bad Request`:** Returned if `room_image` or `tile_image` is missing from the request.
        ```json
        {
            "error": "Both 'room_image' and 'tile_image' must be provided"
        }
        ```
    -   **`500 Internal Server Error`:** Returned if an unexpected error occurs during image processing or saving.
        ```json
        {
            "error": "Image processing failed. Check server logs." 
        }
        ```
        (The exact error message might vary, e.g., "Failed to save processed image." or "An internal server error occurred.")

The web interface mentioned above uses a separate endpoint (`/replace_floor_html`) internally but leverages the same core image processing logic.

## Running Tests
To discover and run all tests located in the `tests` directory, navigate to the project root and execute:
```bash
python -m unittest discover -s tests
```
Or, to run a specific test file:
```bash
python -m unittest tests.test_image_processing
python -m unittest tests.test_api
```

## Limitations and Future Improvements

### Current Limitations
-   **Floor Detection:** The current floor detection mechanism is based on simple HSV color segmentation. It is primarily tuned for brownish/grayish floors and may not perform well with:
    -   Complex floor patterns or multiple colors.
    -   Poor lighting conditions or strong shadows.
    -   Rooms with significant clutter on the floor.
    -   Floors that are not the most dominant color in the expected range.
-   **Perspective Correction:** While perspective transformation is applied, it relies on the accuracy of the contour detection of the floor. Complex floor shapes or occlusions can lead to imperfect warping.
-   **No User Interaction:** The floor area is detected automatically. There's no option for users to manually define or adjust the floor area.

### Potential Future Improvements
-   **Advanced Floor Segmentation:** Implement more robust segmentation techniques (e.g., using deep learning models like U-Net, or more advanced computer vision algorithms like GrabCut or watershed).
-   **Interactive Floor Definition:** Allow users to draw a polygon or provide points to define the floor area for more accurate results.
-   **Color Range Adjustment:** Allow users to specify or adjust the color range for floor detection via API parameters.
-   **Texture Tiling:** Improve how the tile image is applied to the floor, especially for larger areas, to ensure seamless tiling and realistic texture mapping.
-   **Support for More Image Formats:** Explicitly handle more input and output image formats.
-   **Enhanced Error Handling:** Provide more specific error messages for different failure modes.
-   **Asynchronous Processing:** For larger images or more complex processing, consider an asynchronous task queue (e.g., Celery) to prevent API timeouts.
-   **Configuration:** Allow configuration of parameters like the temporary upload folder.
```
