from django.conf import settings
from django.test import SimpleTestCase, Client
from django.urls import reverse
from unittest.mock import patch
from main.cache import CACHE_STORE
import os

@patch('main.views.services.openAI_translate')
class BVTTranslationTest(SimpleTestCase):
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
        response = self.client.post(reverse('main'), {})
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'Please enter Japanese text or upload an image')
    
    def test_translation_text_exceeding_limit(self, mock_translate):
        """BVT: System should handle text longer than 200 characters"""
        long_text = "あ" * (settings.MAX_TEXT_LENGTH + 1)
        mock_translate.return_value = self.test_en_translation
        
        response = self.client.post(reverse('main'), {
            'jp_text': long_text
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'Invalid input')
        
    def test_debug_mode_time_tracking(self, mock_translate):
        """BVT: Debug mode should show time tracking information"""
        with self.settings(DEBUG=True):
            mock_translate.return_value = self.test_en_translation
            
            response = self.client.post(reverse('main'), {
                'jp_text': self.test_jp_text
            })
            
            self.assertEqual(response.status_code, 200)
            # Should contain debug mode indicators
            self.assertIn('mode', response.context)
            self.assertEqual(response.context['mode'], 'debug')
            self.assertIsNotNone(response.context['time_taken'])
    
    def test_invalid_http_method(self, mock_translate):
        """BVT: System should handle invalid HTTP methods gracefully"""
        response = self.client.put(reverse('main'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'Something went wrong')