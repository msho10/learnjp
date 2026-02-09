from django.test import SimpleTestCase
from django.urls import reverse
from unittest import mock

class IndexPageTest(SimpleTestCase):
    
    def test_get(self):
        response = self.client.get(reverse('main'))
        # Assert the response status code is 200 (OK)
        self.assertEqual(response.status_code, 200)
        # Assert a specific template was used
        self.assertTemplateUsed(response, 'index.html')

    @mock.patch('main.services.openAI_translate')
    def test_post(self, mock_translate):

        test_input = 'input from post test'
        expected_output = None
        mock_translate.return_value = expected_output
        
        url = reverse('main')
        
        data = {
            'jp_text': test_input
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'translate.html')

        
        