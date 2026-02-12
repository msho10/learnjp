from django.conf import settings
from django.test import SimpleTestCase, Client
from django.urls import reverse
from unittest.mock import patch
from main.cache import CACHE_STORE
import os

@patch('main.views.services.openAI_translate')
class BVTCacheTest(SimpleTestCase):
    """Business Validation Tests for cache functionality with mocked dependencies"""
    
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
    
    
    def test_translation_with_cache_corruption(self, mock_translate):
        """BVT: System should handle corrupted cache entries"""
        mock_translate.return_value = self.test_en_translation
        
        # Create a translation to get a key
        response = self.client.post(reverse('main'), {
            'jp_text': self.test_jp_text
        })
        
        key = response.context['key']
        
        # Corrupt the cache entry
        CACHE_STORE._translation_cache[key] = None
        
        # Should handle gracefully and re-translate
        response = self.client.post(reverse('main'), {
            'jp_text': self.test_jp_text
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.test_jp_text)
        self.assertContains(response, self.test_en_translation)

    # Helper function to read file 
    def _read_file_content(self, filename):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            json_result = file.read() 
            
        return json_result
    
    @patch('main.views.services.openAI_analyze')
    def test_analysis_with_cache_corruption(self, mock_analysis, mock_translate):
        """BVT: System should handle corrupted cache entries"""
        mock_translate.return_value = self.test_en_translation
        analysis_response = self._read_file_content("test_data_valid_response.json")
        mock_analysis.return_value = analysis_response
        
        # Create a translation to get a key
        response = self.client.post(reverse('main'), {
            'jp_text': self.test_jp_text
        })
        
        key = response.context['key']
        response = self.client.get(reverse('analyze') + f'?key={key}')

        # Corrupt the cache entry
        CACHE_STORE._analysis_cache[key] = None
        
        # Should handle gracefully and get analysis again
        response = self.client.get(reverse('analyze') + f'?key={key}')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, analysis_response)
