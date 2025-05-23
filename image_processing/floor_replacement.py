import cv2
import numpy as np

def detect_floor(room_image_path):
    """
    Detects the floor in a room image.

    Args:
        room_image_path (str): Path to the room image.

    Returns:
        np.ndarray: A binary mask representing the detected floor area.
                    Returns None if the image cannot be loaded.
    """
    image = cv2.imread(room_image_path)
    if image is None:
        print(f"Error: Could not load image from {room_image_path}")
        return None

    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define a sample color range for common floor colors (e.g., browns)
    # These values might need significant tuning based on actual images.
    # Hue: 0-180, Saturation: 0-255, Value: 0-255
    lower_brown = np.array([10, 50, 50])  # Example lower bound for brown
    upper_brown = np.array([30, 255, 255]) # Example upper bound for brown
    
    # For grays/whites/blacks (low saturation)
    # lower_gray = np.array([0, 0, 50]) 
    # upper_gray = np.array([180, 40, 220])
    
    # Using brown for now
    mask = cv2.inRange(hsv_image, lower_brown, upper_brown)

    # Apply morphological operations to clean up the mask
    # Kernel for morphological operations
    kernel_size = 5 # Original value was 5
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    
    # Closing: Dilation followed by Erosion
    # Helps to fill small holes in the detected regions
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    
    # Optionally, opening (Erosion followed by Dilation) can remove small noise/objects
    # mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    print(f"Detected floor mask for {room_image_path} using color segmentation.")
    return mask

def prepare_tile(tile_image_path, floor_mask, room_image_shape):
    """
    Prepares (e.g., transforms) a tile image to fit the detected floor mask
    using perspective transformation.

    Args:
        tile_image_path (str): Path to the tile image.
        floor_mask (np.ndarray): Binary mask of the detected floor.
        room_image_shape (tuple): Shape of the original room image (height, width).
                                  Used for the output size of the warped tile.

    Returns:
        np.ndarray: The transformed tile image, warped to fit the floor.
                    Returns None if the tile image cannot be loaded, if no floor is detected,
                    or if no contours are found in the mask.
    """
    tile_image = cv2.imread(tile_image_path)
    if tile_image is None:
        print(f"Error: Could not load tile image from {tile_image_path}")
        return None

    if floor_mask is None:
        print("Error: Floor mask is None. Cannot prepare tile.")
        return None # Or return original tile_image, depending on desired behavior

    # Find contours in the floor mask
    contours, _ = cv2.findContours(floor_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        print("No contours found in the floor mask. Cannot determine floor shape.")
        # Optionally, resize tile to a default size or return as is
        return None 

    # Assume the largest contour corresponds to the main floor area
    largest_contour = max(contours, key=cv2.contourArea)

    # Get the four corner points of the largest contour using minAreaRect
    rect = cv2.minAreaRect(largest_contour)
    dst_pts = cv2.boxPoints(rect)
    
    # Order points: top-left, top-right, bottom-right, bottom-left
    # cv2.boxPoints returns them in a clockwise order, but starting point can vary.
    # We need a consistent order for getPerspectiveTransform.
    # Sort by sum (y+x) for top-left and bottom-right, and diff (y-x) for top-right and bottom-left.
    s = dst_pts.sum(axis=1)
    diff = np.diff(dst_pts, axis=1)
    
    ordered_dst_pts = np.zeros((4, 2), dtype="float32")
    ordered_dst_pts[0] = dst_pts[np.argmin(s)] # Top-left
    ordered_dst_pts[2] = dst_pts[np.argmax(s)] # Bottom-right
    ordered_dst_pts[1] = dst_pts[np.argmin(diff)] # Top-right
    ordered_dst_pts[3] = dst_pts[np.argmax(diff)] # Bottom-left
    
    dst_pts = np.array(ordered_dst_pts, dtype="float32")


    # Source points are the four corners of the tile image
    tile_h, tile_w = tile_image.shape[:2]
    src_pts = np.array([[0, 0], [tile_w - 1, 0], [tile_w - 1, tile_h - 1], [0, tile_h - 1]], dtype="float32")

    # Calculate the perspective transformation matrix
    transform_matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

    # Apply the perspective transformation
    # The output size (dsize) should be the size of the original room image
    warped_tile = cv2.warpPerspective(tile_image, transform_matrix, (room_image_shape[1], room_image_shape[0]))
    
    print(f"Prepared tile {tile_image_path} by warping it to fit the detected floor.")
    return warped_tile

def replace_floor(room_image_path, tile_image_path):
    """
    Replaces the floor in a room image with a new tile.

    Args:
        room_image_path (str): Path to the room image.
        tile_image_path (str): Path to the tile image.

    Returns:
        np.ndarray: The room image with the floor replaced.
                    Returns the original room image if any step fails (e.g., image loading,
                    floor detection, tile preparation). Returns None if the room image
                    itself cannot be loaded.
    """
    room_image = cv2.imread(room_image_path)
    if room_image is None:
        print(f"Error: Could not read room image at {room_image_path}")
        return None

    floor_mask = detect_floor(room_image_path)
    if floor_mask is None:
        print("Floor detection failed. Returning original room image.")
        return room_image

    prepared_tile = prepare_tile(tile_image_path, floor_mask, room_image.shape)
    if prepared_tile is None:
        print("Tile preparation failed. Returning original room image.")
        return room_image

    # Create a copy of the room image to modify
    output_image = room_image.copy()

    # Where the floor_mask is white (255), replace pixels in the output_image
    # with pixels from the prepared_tile.
    # Ensure prepared_tile and output_image have the same dimensions,
    # and floor_mask is a 2D mask for these dimensions.
    mask_condition = floor_mask == 255
    
    # Verify shapes if necessary (should be handled by prepare_tile output size)
    # print(f"output_image shape: {output_image.shape}")
    # print(f"prepared_tile shape: {prepared_tile.shape}")
    # print(f"floor_mask shape: {floor_mask.shape}")
    # print(f"Condition shape: {mask_condition.shape}")

    try:
        output_image[mask_condition] = prepared_tile[mask_condition]
        print(f"Successfully replaced floor in {room_image_path} with {tile_image_path}.")
    except IndexError as e:
        print(f"Error during pixel replacement: {e}. This might be due to shape mismatch.")
        print(f"Output image shape: {output_image.shape}, Prepared tile shape: {prepared_tile.shape}, Mask condition shape: {mask_condition.shape}")
        return room_image # Return original image in case of error

    return output_image

if __name__ == '__main__':
    # Example Usage (optional, for testing)
    # Create dummy images for testing if they don't exist
    # This part is more for local testing and might not be needed in the final script
    # For now, we'll assume images will be provided or handled by a different part of the app.
    pass
