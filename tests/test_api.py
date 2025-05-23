import unittest
import os
import io
import sys
import shutil # For tearDownClass
import cv2 # For creating dummy images
import numpy as np # For creating dummy images

# Add the project root to the Python path to allow importing app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app # Your Flask application

class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_data_dir = "tests/TestData"
        os.makedirs(cls.test_data_dir, exist_ok=True)

        # Create dummy room image (300x300) - Consistent with TestImageProcessing
        cls.room_img_height, cls.room_img_width = 300, 300
        dummy_room_image = np.zeros((cls.room_img_height, cls.room_img_width, 3), dtype=np.uint8)
        # Floor color BGR: (40, 80, 120)
        floor_color_bgr = (40, 80, 120) 
        cv2.rectangle(dummy_room_image, 
                      (0, cls.room_img_height // 2), 
                      (cls.room_img_width -1, cls.room_img_height -1), 
                      floor_color_bgr, 
                      -1)
        cls.room_image_path = os.path.join(cls.test_data_dir, "dummy_room.png")
        cv2.imwrite(cls.room_image_path, dummy_room_image)

        # Create dummy tile image (100x100) - Consistent with TestImageProcessing
        dummy_tile_image = np.full((100, 100, 3), (255, 0, 0), dtype=np.uint8)  # Blue tile
        cls.tile_image_path = os.path.join(cls.test_data_dir, "dummy_tile.png")
        cv2.imwrite(cls.tile_image_path, dummy_tile_image)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_data_dir):
            shutil.rmtree(cls.test_data_dir)

    def setUp(self):
        app.testing = True
        self.client = app.test_client()
        # Paths are already defined in setUpClass, accessible via self.room_image_path etc.

    def test_replace_floor_success(self):
        with open(self.room_image_path, 'rb') as room_file, \
             open(self.tile_image_path, 'rb') as tile_file:
            
            data = {
                'room_image': (io.BytesIO(room_file.read()), 'dummy_room.png'),
                'tile_image': (io.BytesIO(tile_file.read()), 'dummy_tile.png')
            }
            
            response = self.client.post('/replace_floor', 
                                        content_type='multipart/form-data', 
                                        data=data)
        
        self.assertEqual(response.status_code, 200, "Response status code should be 200 for success.")
        self.assertEqual(response.content_type, 'image/jpeg', "Content type should be image/jpeg.")
        self.assertTrue('attachment' in response.headers['Content-Disposition'], 
                        "Content-Disposition should indicate an attachment.")
        # Check if response data is not empty
        self.assertTrue(response.data, "Response data should not be empty for a successful image replacement.")


    def test_replace_floor_missing_files(self):
        # Test with no files
        response_no_files = self.client.post('/replace_floor', content_type='multipart/form-data', data={})
        self.assertEqual(response_no_files.status_code, 400)
        self.assertEqual(response_no_files.content_type, 'application/json')
        json_response_no_files = response_no_files.get_json()
        self.assertIn('error', json_response_no_files)
        self.assertEqual(json_response_no_files['error'], "Both 'room_image' and 'tile_image' must be provided")

        # Test with only room_image
        with open(self.room_image_path, 'rb') as room_file:
            data_only_room = {
                'room_image': (io.BytesIO(room_file.read()), 'dummy_room.png')
            }
        response_only_room = self.client.post('/replace_floor', content_type='multipart/form-data', data=data_only_room)
        self.assertEqual(response_only_room.status_code, 400)
        self.assertEqual(response_only_room.content_type, 'application/json')
        json_response_only_room = response_only_room.get_json()
        self.assertIn('error', json_response_only_room)
        self.assertEqual(json_response_only_room['error'], "Both 'room_image' and 'tile_image' must be provided")

        # Test with only tile_image
        with open(self.tile_image_path, 'rb') as tile_file:
            data_only_tile = {
                'tile_image': (io.BytesIO(tile_file.read()), 'dummy_tile.png')
            }
        response_only_tile = self.client.post('/replace_floor', content_type='multipart/form-data', data=data_only_tile)
        self.assertEqual(response_only_tile.status_code, 400)
        self.assertEqual(response_only_tile.content_type, 'application/json')
        json_response_only_tile = response_only_tile.get_json()
        self.assertIn('error', json_response_only_tile)
        self.assertEqual(json_response_only_tile['error'], "Both 'room_image' and 'tile_image' must be provided")

if __name__ == '__main__':
    unittest.main()
