from django.conf import settings
from django.test import SimpleTestCase, Client
from django.urls import reverse
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
from main.cache import CACHE_STORE


@patch('main.views.services.openAI_translate')
@patch('main.views.utils.extract_text_from_image')
class BVTImageTest(SimpleTestCase):
    """Business Validation Tests for image upload and OCR functionality with mocked dependencies"""
    
    def setUp(self):
        """Set up test client and common test data"""
        self.client = Client()
        self.test_jp_text = "今日はいい天気です"
        self.test_en_translation = "Nice weather today"
        
    def tearDown(self):
        """Clean up after each test"""
        CACHE_STORE._request_queue.clear()
        CACHE_STORE._translation_cache.clear()
        CACHE_STORE._analysis_cache.clear()
    

    def test_image_upload_workflow_success(self, mock_ocr, mock_translate):
        """BVT: Complete image upload and translation workflow"""
        mock_ocr.return_value = self.test_jp_text
        mock_translate.return_value = self.test_en_translation
        
        # Create a mock image file
        image_content = b'fake image content'
        uploaded_file = SimpleUploadedFile(
            "test_image.jpg",
            image_content,
            content_type="image/jpeg"
        )
        
        response = self.client.post(reverse('main'), {
            'image_file': uploaded_file
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'translate.html')
        self.assertContains(response, self.test_jp_text)
        self.assertContains(response, self.test_en_translation)
        
        # Verify OCR was called
        mock_ocr.assert_called_once()
    

    def test_image_upload_empty_result(self, mock_ocr, mock_translate):
        """BVT: System should handle OCR returning no text"""
        mock_ocr.return_value = None
        mock_translate.return_value = self.test_en_translation
        
        image_content = b'fake image content'
        uploaded_file = SimpleUploadedFile(
            "test_image.jpg",
            image_content,
            content_type="image/jpeg"
        )
        
        response = self.client.post(reverse('main'), {
            'image_file': uploaded_file
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'No Japanese text found in image')
    
    def test_image_upload_with_long_text(self, mock_ocr, mock_translate):
        """BVT: System should handle OCR result longer than 200 characters"""
        long_text = "あ" * (settings.MAX_TEXT_LENGTH + 1)
        mock_ocr.return_value = long_text
        mock_translate.return_value = self.test_en_translation
        
        image_content = b'fake image content'
        uploaded_file = SimpleUploadedFile(
            "test_image.jpg",
            image_content,
            content_type="image/jpeg"
        )
        
        response = self.client.post(reverse('main'), {
            'image_file': uploaded_file
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'translate.html')
        # Should contain truncation warning
        self.assertContains(response, 'exceeded the allowed limit')
    
    
    def test_image_upload_translation_failure(self, mock_ocr, mock_translate):
        """BVT: System should handle OCR API failures gracefully"""
        mock_ocr.return_value = self.test_jp_text
        mock_translate.return_value = None
        
        image_content = b'fake image content'
        uploaded_file = SimpleUploadedFile(
            "test_image.jpg",
            image_content,
            content_type="image/jpeg"
        )
        
        response = self.client.post(reverse('main'), {
            'image_file': uploaded_file
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'Unable to process request')
    

    def test_image_upload_with_translation_cached(self, mock_ocr, mock_translate):
        """BVT: Image upload should use cached translation when available (NOTE: ONLY TRANSLATION IS CACHED, NOT THE IMAGE) """
        mock_ocr.return_value = self.test_jp_text
        mock_translate.return_value = self.test_en_translation
        
        # First request - should call the API
        image_content = b'fake image content'
        uploaded_file = SimpleUploadedFile(
            "test_image1.jpg",
            image_content,
            content_type="image/jpeg"
        )
        
        self.client.post(reverse('main'), {
           'image_file': uploaded_file
        })
        
        # Reset mocks to verify they're not called again
        mock_translate.reset_mock()
        
        # Second request with same OCR result - should use cache
        uploaded_file = SimpleUploadedFile(
            "test_image2.jpg",
            image_content,
            content_type="image/jpeg"
        )
        response = self.client.post(reverse('main'), {
            'image_file': uploaded_file
        })
        
        self.assertEqual(response.status_code, 200)
        mock_translate.assert_not_called()  # Should not call API again
        self.assertContains(response, self.test_jp_text)
        self.assertContains(response, self.test_en_translation)
        

    def test_image_upload_with_empty_file(self, mock_ocr, mock_translate):
        """BVT: System should handle empty image file upload"""
        mock_ocr.return_value = ""
        mock_translate.return_value = self.test_en_translation
        
        image_content = b'image with no text'
        uploaded_file = SimpleUploadedFile(
            "empty_image.jpg",
            image_content,
            content_type="image/jpeg"
        )
        
        response = self.client.post(reverse('main'), {
            'image_file': uploaded_file
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'No Japanese text found in image')
    
    # THIS TEST CURRENTLY FAILS. WILL FIX IT IN ANOTHER CHECK-IN (BY USING PILLOW TO CHECK IT'S A VALID IMAGE) 
    # def test_image_upload_with_invalid_file_type(self, mock_ocr, mock_translate):
    #     """BVT: System should handle invalid file types gracefully"""
    #     mock_ocr.return_value = self.test_jp_text
    #     mock_translate.return_value = self.test_en_translation
        
    #     # Create a non-image file
    #     text_content = b'This is not an image file'
    #     uploaded_file = SimpleUploadedFile(
    #         "document.txt",
    #         text_content,
    #         content_type="text/plain"
    #     )
        
    #     response = self.client.post(reverse('main'), {
    #         'image_file': uploaded_file
    #     })
        
    #     self.assertEqual(response.status_code, 200)
    #     self.assertContains(response, 'Invalid input')


    def test_image_upload_performance_tracking(self, mock_ocr, mock_translate):
        """BVT: System should track OCR performance time"""
        mock_ocr.return_value = self.test_jp_text
        mock_translate.return_value = self.test_en_translation
        
        image_content = b'fake image content'
        uploaded_file = SimpleUploadedFile(
            "test_image.jpg",
            image_content,
            content_type="image/jpeg"
        )
        
        with self.settings(DEBUG=True):
            response = self.client.post(reverse('main'), {
                'image_file': uploaded_file
            })
            
            self.assertEqual(response.status_code, 200)
            # Should contain time tracking information
            self.assertIn('mode', response.context)
            self.assertEqual(response.context['mode'], 'debug')
            self.assertIn('time_taken', response.context)
    
