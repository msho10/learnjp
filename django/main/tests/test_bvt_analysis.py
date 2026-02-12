from django.conf import settings
from django.test import SimpleTestCase, Client
from django.urls import reverse
from unittest.mock import patch
from main.cache import CACHE_STORE
import os

@patch('main.views.services.openAI_translate')
@patch('main.views.services.openAI_analyze')
class BVTAnalysisTest(SimpleTestCase):
    """Business Validation Tests for morphological analysis functionality with mocked dependencies"""
    
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
        
    # Helper function to read file 
    def _read_file_content(self, filename):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            json_result = file.read() 
            
        return json_result
    
    def test_analysis_workflow_success(self, mock_analyze, mock_translate):
        """BVT: Complete analysis workflow should work end-to-end"""
        json_response = self._read_file_content("test_data_valid_response.json")
        mock_analyze.return_value = json_response
        
        # First, create a translation to get a key
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
    
    def test_analysis_invalid_json_handling(self, mock_analyze, mock_translate):
        """BVT: System should handle invalid JSON from analysis API"""
        mock_analyze.return_value = self._read_file_content("test_data_invalid_response.json")
        
        mock_translate.return_value = self.test_en_translation
        response = self.client.post(reverse('main'), {
                'jp_text': self.test_jp_text
        })
        
        key = response.context['key']
        response = self.client.get(reverse('analyze') + f'?key={key}')
        
        self.assertEqual(response.status_code, 200)
        # Empty json is expected to return
        self.assertEquals(response.content.decode(), '{}')
    
    def test_analysis_api_failure(self, mock_analyze, mock_translate):
        """BVT: System should handle analysis API failures gracefully"""
        mock_analyze.return_value = None
        
        mock_translate.return_value = self.test_en_translation
        response = self.client.post(reverse('main'), {
                'jp_text': self.test_jp_text
        })
        
        key = response.context['key']
        response = self.client.get(reverse('analyze') + f'?key={key}')
        
        self.assertEqual(response.status_code, 200)
        # Should return empty JSON on failure
        self.assertEqual(response.content, b'{}')