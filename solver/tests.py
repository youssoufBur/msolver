# tests.py
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

class APITestCase(TestCase):
    def test_windows_paths(self):
        test_file = SimpleUploadedFile(
            "test_eq.png", 
            b"file_content", 
            content_type="image/png"
        )
        
        response = self.client.post('/api/resolve/', {'input_file': test_file})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('\\', response.data['original_input'])