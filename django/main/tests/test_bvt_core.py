from django.conf import settings
from django.test import SimpleTestCase, Client
from django.urls import reverse
from unittest.mock import patch
from main.cache import CACHE_STORE
import os

@patch('main.views.services.openAI_translate')
class BVTCoreTest(SimpleTestCase):
    """Business Validation Tests for core translation functionality with mocked dependencies"""
    
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
    
    def test_index_page_get(self, mock_translate):
        """BVT: Index page should load successfully"""
        response = self.client.get(reverse('main'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertIn('form', response.context)
    
    def test_translation_workflow_success(self, mock_translate):
        """BVT: Complete translation workflow should work end-to-end"""
        mock_translate.return_value = self.test_en_translation
        
        response = self.client.post(reverse('main'), {
            'jp_text': self.test_jp_text
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'translate.html')
        self.assertContains(response, self.test_jp_text)
        self.assertContains(response, self.test_en_translation)
        
        # Verify the translation was cached
        key = CACHE_STORE.get_key(self.test_jp_text)
        self.assertTrue(CACHE_STORE.has_translation(key))
        self.assertEqual(CACHE_STORE.get_translation(key), self.test_en_translation)
    
    def test_translation_with_cache_hit(self, mock_translate):
        """BVT: Translation should use cached result when available"""
        # First request - should call the API
        mock_translate.return_value = self.test_en_translation
        self.client.post(reverse('main'), {'jp_text': self.test_jp_text})
        
        # Reset mock to verify it's not called again
        mock_translate.reset_mock()
        
        # Second request with same text - should use cache
        response = self.client.post(reverse('main'), {'jp_text': self.test_jp_text})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'translate.html')
        mock_translate.assert_not_called()  # Should not call API again
    
    def test_translation_api_failure(self, mock_translate):
        """BVT: System should handle translation API failures gracefully"""
        mock_translate.return_value = None
        
        response = self.client.post(reverse('main'), {
            'jp_text': self.test_jp_text
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        # The actual error message may vary based on the API response
        self.assertContains(response, 'Unable to process request')
    
    def test_translation_empty_input(self, mock_translate):
        """BVT: System should handle empty input validation"""
        response = self.client.post(reverse('main'), {
            'jp_text': ''
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'Please enter Japanese text or upload an image')
    
    def test_translation_long_text_truncation(self, mock_translate):
        """BVT: System should handle text longer than 200 characters"""
        long_text = "あ" * 250  # 250 characters
        mock_translate.return_value = self.test_en_translation
        
        response = self.client.post(reverse('main'), {
            'jp_text': long_text
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'Invalid input')
    
    # Helper function to read file 
    def _read_file_content(self, filename):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            json_result = file.read() 
            
        return json_result
    
    @patch('main.views.services.openAI_analyze')
    def test_analysis_workflow_success(self, mock_analyze, mock_translate):
        """BVT: Complete analysis workflow should work end-to-end"""
        json_response = self._read_file_content("test_data_valid_response.json")
        mock_analyze.return_value = json_response
        
        # First, create a translation to get a key
        with patch('main.views.services.openAI_translate') as mock_translate:
            mock_translate.return_value = self.test_en_translation
            response = self.client.post(reverse('main'), {
                'jp_text': self.test_jp_text
            })
            
        # Extract key from response context
        key = response.context['key']
        
        # Now test analysis
        response = self.client.get(reverse('analyze') + f'?key={key}')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        
        # Verify analysis was cached
        self.assertTrue(CACHE_STORE.has_analysis(key))
        # The actual response will be different due to JsonResponse processing
        self.assertIn(response.content.decode(), json_response)
    
    @patch('main.views.services.openAI_analyze')
    def test_analysis_with_cache_hit(self, mock_analyze, mock_translate):
        """BVT: Analysis should use cached result when available"""
        mock_analyze.return_value = self._read_file_content("test_data_valid_response.json")
        
        # First request - should call the API
        with patch('main.views.services.openAI_translate') as mock_translate:
            mock_translate.return_value = self.test_en_translation
            response = self.client.post(reverse('main'), {
                'jp_text': self.test_jp_text
            })
        
        key = response.context['key']
        self.client.get(reverse('analyze') + f'?key={key}')
        
        # Reset mock to verify it's not called again
        mock_analyze.reset_mock()
        
        # Second request with same key - should use cache
        response = self.client.get(reverse('analyze') + f'?key={key}')
        
        self.assertEqual(response.status_code, 200)
        mock_analyze.assert_not_called()  # Should not call API again
    
    @patch('main.views.services.openAI_analyze')
    def test_analysis_invalid_json_handling(self, mock_analyze, mock_translate):
        """BVT: System should handle invalid JSON from analysis API"""
        mock_analyze.return_value = self._read_file_content("test_data_invalid_response.json")
        
        with patch('main.views.services.openAI_translate') as mock_translate:
            mock_translate.return_value = self.test_en_translation
            response = self.client.post(reverse('main'), {
                'jp_text': self.test_jp_text
            })
        
        key = response.context['key']
        response = self.client.get(reverse('analyze') + f'?key={key}')
        
        self.assertEqual(response.status_code, 200)
        # Empty json is expected to return
        self.assertEquals(response.content.decode(), '{}')
    
    def test_cache_size_limit(self, mock_translate):
        """BVT: System should handle cache size limits correctly"""
        mock_translate.return_value = self.test_en_translation
        
        # Fill cache to limit
        cache_size = settings.CACHE_SIZE
        for i in range(cache_size + 2):  # Add 2 more than limit
            test_text = f"Test text {i}"
            self.client.post(reverse('main'), {
                'jp_text': test_text
            })
        
        # Should still work for recent entries
        response = self.client.post(reverse('main'), {
            'jp_text': f"Test text {cache_size + 1}"
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'translate.html')
        self.assertContains(response, f"Test text {cache_size + 1}")
        self.assertContains(response, self.test_en_translation)
    
    def test_form_validation_max_length(self, mock_translate):
        """BVT: Form should validate maximum text length"""
        # Create text longer than MAX_TEXT_LENGTH (200)
        long_text = "あ" * (settings.MAX_TEXT_LENGTH + 1)
        
        response = self.client.post(reverse('main'), {
            'jp_text': long_text
        })
        
        # extra text will be truncated and translation for truncated text is returned
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        # Should contain form errors
        self.assertContains(response, 'Invalid input')
    
    def test_debug_mode_time_tracking(self, mock_translate):
        """BVT: Debug mode should show time tracking information"""
        with self.settings(DEBUG=True):
            mock_translate.return_value = self.test_en_translation
            
            response = self.client.post(reverse('main'), {
                'jp_text': self.test_jp_text
            })
            
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'translate.html')
            # Should contain debug mode indicators
            self.assertIn('mode', response.context)
            self.assertEqual(response.context['mode'], 'debug')
            self.assertIsNotNone(response.context['time_taken'])
    
    def test_concurrent_requests_handling(self, mock_translate):
        """BVT: System should handle multiple concurrent requests"""
        mock_translate.return_value = self.test_en_translation
        
        # Simulate multiple requests
        responses = []
        for i in range(3):
            response = self.client.post(reverse('main'), {
                'jp_text': f"Test text {i}"
            })
            responses.append(response)
        
        # All should succeed
        for response in responses:
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'translate.html')
    
    def test_invalid_http_method(self, mock_translate):
        """BVT: System should handle invalid HTTP methods gracefully"""
        response = self.client.put(reverse('main'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'Something went wrong')