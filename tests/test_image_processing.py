import unittest
import cv2
import numpy as np
import os
import shutil # For tearDownClass

# Add the project root to the Python path to allow importing image_processing
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from image_processing.floor_replacement import detect_floor, prepare_tile, replace_floor

class TestImageProcessing(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_data_dir = "tests/TestData"
        os.makedirs(cls.test_data_dir, exist_ok=True)

        # Create dummy room image (300x300)
        cls.room_img_height, cls.room_img_width = 300, 300
        dummy_room_image = np.zeros((cls.room_img_height, cls.room_img_width, 3), dtype=np.uint8)
        # Draw a "floor" - a brown rectangle at the bottom half
        # HSV for brown: H: 10-30, S: 100-255, V: 50-200
        # For simplicity, using BGR: B:40, G:80, R:120 (a shade of brown)
        floor_color_bgr = (40, 80, 120) 
        cv2.rectangle(dummy_room_image, 
                      (0, cls.room_img_height // 2), 
                      (cls.room_img_width -1, cls.room_img_height -1), 
                      floor_color_bgr, 
                      -1) # Filled rectangle
        cls.room_image_path = os.path.join(cls.test_data_dir, "dummy_room.png")
        cv2.imwrite(cls.room_image_path, dummy_room_image)

        # Create dummy tile image (100x100)
        dummy_tile_image = np.full((100, 100, 3), (255, 0, 0), dtype=np.uint8)  # Blue tile
        cls.tile_image_path = os.path.join(cls.test_data_dir, "dummy_tile.png")
        cv2.imwrite(cls.tile_image_path, dummy_tile_image)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_data_dir):
            shutil.rmtree(cls.test_data_dir)

    def test_detect_floor(self):
        mask = detect_floor(self.room_image_path)
        self.assertIsNotNone(mask, "detect_floor should return a mask, not None.")
        self.assertTrue(isinstance(mask, np.ndarray), "detect_floor output should be a NumPy array.")
        # Check if mask is 2D
        self.assertEqual(mask.ndim, 2, "Mask should be 2-dimensional.")
        # Check if mask has same height and width as room image
        self.assertEqual(mask.shape[0], self.room_img_height, "Mask height should match room image height.")
        self.assertEqual(mask.shape[1], self.room_img_width, "Mask width should match room image width.")


    def test_prepare_tile(self):
        # 1. Get a mask first
        floor_mask = detect_floor(self.room_image_path)
        self.assertIsNotNone(floor_mask, "Failed to detect floor mask for prepare_tile test.")
        
        # 2. Get room image shape
        room_img = cv2.imread(self.room_image_path)
        self.assertIsNotNone(room_img, "Failed to load room image for shape.")
        room_shape = room_img.shape

        # 3. Call prepare_tile
        prepared_tile_img = prepare_tile(self.tile_image_path, floor_mask, room_shape)
        self.assertIsNotNone(prepared_tile_img, "prepare_tile should return an image, not None.")
        self.assertTrue(isinstance(prepared_tile_img, np.ndarray), "prepare_tile output should be a NumPy array.")
        self.assertEqual(prepared_tile_img.ndim, 3, "Prepared tile should be a 3-dimensional array (image).")
        self.assertEqual(prepared_tile_img.shape[0], room_shape[0], "Prepared tile height should match room image height.")
        self.assertEqual(prepared_tile_img.shape[1], room_shape[1], "Prepared tile width should match room image width.")


    def test_replace_floor(self):
        replaced_image = replace_floor(self.room_image_path, self.tile_image_path)
        self.assertIsNotNone(replaced_image, "replace_floor should return an image, not None.")
        self.assertTrue(isinstance(replaced_image, np.ndarray), "replace_floor output should be a NumPy array.")
        self.assertEqual(replaced_image.ndim, 3, "Replaced image should be a 3-dimensional array.")
        
        # Check if the output image has the same dimensions as the input room image
        room_img = cv2.imread(self.room_image_path)
        self.assertIsNotNone(room_img, "Failed to load room image for dimension check.")
        self.assertEqual(replaced_image.shape, room_img.shape, "Replaced image dimensions should match original room image.")

if __name__ == '__main__':
    unittest.main()
