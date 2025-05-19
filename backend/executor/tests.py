from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

class GradeCodeAPITests(APITestCase):
    def test_grade_code_with_valid_data(self):
        url = reverse('grade_code')
        data = {
            "code": "def add(a, b): return a + b",
            "question": "Write a function to add two numbers.",
            "sample_input": "add(2, 3)",
            "sample_output": "5",
            "user_output": "5"
        }

        response = self.client.post(url, data, format='json')

        # Debug print to inspect output if needed
        print(response.status_code, response.data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('final_score', response.data)
        self.assertIn('summary', response.data)
        self.assertIn('code_compiles', response.data)
