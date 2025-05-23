import os
import uuid
import subprocess
import json
import logging
import random
import time
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from .models import Question, Topic, Company, TestCase
from .serializers import QuestionSerializer, GenerateQuestionInputSerializer
from .question_generator import generate_question_with_test_cases  # if used elsewhere
import google.generativeai as genai
from .models import Topic  
from decouple import config
import cohere
from dotenv import load_dotenv
from .pydantic_models import GeneratedQuestionOut, GeneratedQuestionList
from pydantic import TypeAdapter


load_dotenv()
logger = logging.getLogger(__name__)
GEMINI_API_KEY = config("GEMINI_API_KEY") 

genai.configure(api_key=GEMINI_API_KEY)

cohere_api_key = os.getenv('COHERE_API_KEY')
if not cohere_api_key:
    raise ValueError("COHERE_API_KEY not found in environment variables. Make sure it's set in your .env file.")

# Initialize Cohere client
cohere_client = cohere.Client(cohere_api_key)

LANGUAGES = {
    'python': '.py',
    'c': '.c',
    'cpp': '.cpp',
    'java': '.java',
}

@api_view(['POST'])
def run_code(request):
    code = request.data.get('code')
    language = request.data.get('language')

    logger.info("Code execution request received.")
    logger.info(f"Language: {language}")
    if code:
        logger.debug(f"Code preview:\n{code[:100]}...")
    else:
        logger.error("No code provided.")

    if not code or not language:
        logger.error("Code or language missing.")
        return Response({'error': 'Code and language are required.'}, status=400)

    if language not in LANGUAGES:
        logger.error(f"Unsupported language: {language}")
        return Response({'error': 'Unsupported language'}, status=400)

    ext = LANGUAGES[language]
    folder = 'temp_codes'
    os.makedirs(folder, exist_ok=True)

    filename = f'code_{uuid.uuid4().hex}{ext}'
    filepath = os.path.join(folder, filename)
    output_exe = None

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(code)

    try:
        if language == 'python':
            cmd = ['python', filepath]

        elif language == 'c':
            output_exe = os.path.join(folder, f'{uuid.uuid4().hex}')
            compile_cmd = ['gcc', filepath, '-o', output_exe]
            logger.info(f"Compiling C code: {' '.join(compile_cmd)}")
            subprocess.run(compile_cmd, check=True, stderr=subprocess.PIPE)
            cmd = [output_exe]

        elif language == 'cpp':
            output_exe = os.path.join(folder, f'{uuid.uuid4().hex}')
            compile_cmd = ['g++', filepath, '-o', output_exe]
            logger.info(f"Compiling C++ code: {' '.join(compile_cmd)}")
            subprocess.run(compile_cmd, check=True, stderr=subprocess.PIPE)
            cmd = [output_exe]

        elif language == 'java':
            java_folder = os.path.abspath(folder)
            compile_cmd = ['javac', filepath]
            logger.info(f"Compiling Java code: {' '.join(compile_cmd)}")
            subprocess.run(compile_cmd, cwd=java_folder, check=True, stderr=subprocess.PIPE)
            class_name = os.path.splitext(os.path.basename(filepath))[0]
            cmd = ['java', '-cp', java_folder, class_name]

        logger.info(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=True)

        logger.info("Execution successful.")
        if result.stdout:
            logger.debug(f"Execution output:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Execution warnings/errors:\n{result.stderr}")

        return Response({
            'stdout': result.stdout,
            'stderr': result.stderr
        })

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e)
        logger.error("Code execution failed", exc_info=True)
        return Response({'stdout': '', 'stderr': stderr}, status=400)

    except subprocess.TimeoutExpired:
        logger.error("Execution timed out.")
        return Response({'stdout': '', 'stderr': 'Execution timed out'}, status=408)

    finally:
        logger.info("Cleaning up temporary files...")
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
            if output_exe and os.path.exists(output_exe):
                os.remove(output_exe)
            if language == 'java':
                class_name = os.path.splitext(os.path.basename(filepath))[0]
                class_file = os.path.join(folder, f"{class_name}.class")
                if os.path.exists(class_file):
                    os.remove(class_file)
        except Exception as cleanup_error:
            logger.warning(f"Cleanup failed: {cleanup_error}")

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
     # Fixed field names
    filterset_fields = ['difficulty', 'topics', 'companies', 'custom_id']  # Added custom_id
    
    # Support searching by related names and custom_id
    search_fields = ['title', 'topics__name', 'companies__name', 'difficulty', 'custom_id']  # Added custom_id


    


def generate_with_model(model, prompt, retries=3):
    for attempt in range(1, retries + 1):
        try:
            logger.debug(f"Attempt {attempt}: Sending prompt to {model.__class__.__name__}.")
            response = model.generate_content(prompt)
            content = response.text.strip()
            logger.debug(f"Model response: {content[:200]}...")
            return content
        except Exception as e:
            logger.warning(f"{model.__class__.__name__} failed on attempt {attempt}: {e}")
            time.sleep(2 ** attempt + random.random())  # Exponential backoff
    return None



def generate_with_fallbacks(prompt):
    # Primary: Gemini 1.5 Flash
    content = generate_with_model(genai.GenerativeModel("gemini-1.5-flash"), prompt)
    if content:
        logger.info("✅ Response from Gemini 1.5 Flash")
        return content

    # Fallback 1: Gemini 1.5 Pro
    logger.info("🔁 Falling back to Gemini 1.5 Pro...")
    try:
        content = generate_with_model(genai.GenerativeModel("gemini-1.5-pro"), prompt)
        if content:
            logger.info("✅ Response from Gemini 1.5 Pro")
            return content
    except Exception as e:
        logger.warning(f"⚠️ Gemini 1.5 Pro fallback failed: {e}")

    # Fallback 2: Cohere
    logger.info("🔁 Falling back to Cohere...")
    try:
        co = cohere.Client("COHERE_API_KEY")
        response = co.generate(
            model="command",
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
        )
        content = response.generations[0].text.strip()
        logger.info("✅ Response from Cohere")
        return content
    except Exception as e:
        logger.error(f"❌ Cohere fallback failed: {e}")

    return None


@api_view(['POST'])
def generate_questions(request):
    logger.info("🔹 Received POST request to generate questions.")
    serializer = GenerateQuestionInputSerializer(data=request.data)

    if not serializer.is_valid():
        logger.error("❌ Invalid serializer input: %s", serializer.errors)
        return Response(serializer.errors, status=400)

    topic_name = serializer.validated_data['topic']
    difficulty = serializer.validated_data['difficulty']
    logger.info(f"🔹 Topic: {topic_name}, Difficulty: {difficulty}")

    prompt = (
    f"Generate 5 coding questions on the topic '{topic_name}' with difficulty '{difficulty}'.\n\n"
    "Each question must be a JSON object with the following keys:\n"
    '- "title": string\n'
    '- "description": string\n'
    '- "companies_asked": list of strings (company names)\n'
    '- "year_asked": integer or null\n'
    '- "explanation": string\n'
    '- "constraints": string\n'
    '- "sample_io": list of 3 objects, each with "input" and "output" keys as strings\n'
    '- "test_cases": list of 2 or 3 objects, each with "input" and "output" keys\n\n'
    "Return a JSON array containing exactly 5 such question objects.\n\n"
    "**Important:**\n"
    "- Respond ONLY with the JSON array.\n"
    "- Do NOT include any markdown formatting, text, or comments.\n"
    '- Ensure all property names and string values use double quotes.\n'
    "- The JSON must be valid and parseable.\n\n"
    "Example output:\n\n"
    "[\n"
    "  {\n"
    '    "title": "Example Question Title",\n'
    '    "description": "Detailed question description here...",\n'
    '    "companies_asked": ["Google", "Facebook"],\n'
    '    "year_asked": 2022,\n'
    '    "explanation": "Explanation with examples...",\n'
    '    "constraints": "Input constraints or time limits...",\n'
    '    "sample_io": [\n'
    '      {"input": "1 2", "output": "3"},\n'
    '      {"input": "4 5", "output": "9"},\n'
    '      {"input": "7 8", "output": "15"}\n'
    '    ],\n'
    '    "test_cases": [\n'
    '      {"input": "1 2", "output": "3"},\n'
    '      {"input": "4 5", "output": "9"}\n'
    '    ]\n'
    "  },\n"
    "  ...\n"
    "]"
    )




    content = generate_with_fallbacks(prompt)


    if not content:
        logger.error("❌ Gemini failed after retries. No fallback configured.")
        return Response({"error": "Gemini service is unavailable at the moment. Please try again later."}, status=503)

    if content.startswith("```"):
        content = content.strip("```json").strip("```")
        logger.debug("🧹 Stripped markdown code block formatting.")

    try:
        questions_json = json.loads(content)
        if not isinstance(questions_json, list):
            raise ValueError("Expected a list of questions.")
        logger.info(f"✅ Parsed {len(questions_json)} questions.")
    except Exception as e:
        logger.error("❌ Failed to parse JSON from Gemini: %s", str(e))
        return Response({'error': 'Invalid response format from Gemini', 'details': str(e)}, status=500)

    topic_obj, _ = Topic.objects.get_or_create(name=topic_name)
    generated_questions = []

    for q in questions_json:
        title = q.get('title')
        description = q.get('description')
        companies_list = q.get('companies_asked', [])
        year_asked = q.get('year_asked')
        test_cases = q.get('test_cases', [])
        constraints = q.get('constraints', '')
        testcase_description = q.get('testcase_description', '')
        explanation = q.get('explanation', '')

        if not title or not description:
            logger.warning(f"⚠️ Skipping question due to missing title/description: {q}")
            continue
        sample_ios = q.get('sample_io', [])
        sample_input = str(test_cases[0]['input']) if test_cases else ""
        sample_output = str(test_cases[0]['output']) if test_cases else ""

        try:
            question = Question.objects.create(
            title=title,
            description=description,
            sample_input=sample_input,
            sample_output=sample_output,
            explanation=explanation,
            constraints=constraints,
            testcase_description=testcase_description,
            difficulty=difficulty,
            year_asked=year_asked if isinstance(year_asked, int) else None,
        )

            question.topics.add(topic_obj)

            for company_name in companies_list:
                company_obj, _ = Company.objects.get_or_create(name=company_name)
                question.companies.add(company_obj)

            for tc in test_cases:
                TestCase.objects.create(
                    question=question,
                    input_data=tc.get('input'),
                    expected_output=tc.get('output')
                )

            generated_questions.append({
                'id': question.id,
                'title': question.title,
                'description': question.description,
                'sample_input': sample_input,
                'sample_output': sample_output,
                'companies_asked': companies_list,
                'year_asked': year_asked,
                'difficulty': difficulty,
            })

            logger.debug(f"✅ Saved question: {question.title}")

        except Exception as e:
            logger.error(f"❌ Failed to save question '{title}': {str(e)}")

    if not generated_questions:
        logger.warning("⚠️ No questions were saved to the database.")
        return Response({"error": "No valid questions generated."}, status=500)

    logger.info(f"✅ Successfully generated and saved {len(generated_questions)} questions.")
    response_model = GeneratedQuestionList(generated_questions=generated_questions)

    try:
        adapter = TypeAdapter(GeneratedQuestionList)
        json_output = adapter.dump_json(response_model, indent=2).decode()

        logger.debug("📦 Final response structured via Pydantic:\n%s", json_output)

        return Response(response_model.model_dump(), status=201)  # Use model_dump() instead of dict()
    except Exception as e:
        logger.error("❌ Failed to serialize Pydantic output: %s", str(e))
        return Response({"error": "Failed to serialize response"}, status=500)



def generate_grading_json(prompt):
    def try_parse_json(content):
        try:
            if content.startswith("```"):
                content = content.strip("```json").strip("```")
            return json.loads(content)
        except Exception as e:
            logger.warning(f"⚠️ Failed to parse JSON: {e}")
            return None

    # Primary: Gemini 1.5 Flash
    content = generate_with_model(genai.GenerativeModel("gemini-1.5-flash"), prompt)
    grade_json = try_parse_json(content) if content else None
    if grade_json:
        logger.info("✅ Grading response from Gemini 1.5 Flash")
        return grade_json

    # Fallback 1: Gemini 1.5 Pro
    logger.info("🔁 Falling back to Gemini 1.5 Pro...")
    content = generate_with_model(genai.GenerativeModel("gemini-1.5-pro"), prompt)
    grade_json = try_parse_json(content) if content else None
    if grade_json:
        logger.info("✅ Grading response from Gemini 1.5 Pro")
        return grade_json

    # Fallback 2: Cohere
    logger.info("🔁 Falling back to Cohere...")
    try:
        co = cohere.Client("YOUR_COHERE_API_KEY")
        response = co.generate(
            model="command",
            prompt=prompt,
            max_tokens=1000,
            temperature=0.7,
        )
        content = response.generations[0].text.strip()
        grade_json = try_parse_json(content)
        if grade_json:
            logger.info("✅ Grading response from Cohere")
            return grade_json
    except Exception as e:
        logger.error(f"❌ Cohere fallback failed: {e}")

    return None



@api_view(['POST'])
def grade_code(request):
    logger.info("🔹 Received POST request to grade code.")

    # Validate input
    required_fields = ['code', 'question', 'sample_input', 'sample_output', 'user_output']
    missing_fields = [field for field in required_fields if not request.data.get(field)]
    if missing_fields:
        logger.error(f"❌ Missing required fields: {', '.join(missing_fields)}")
        return Response({"error": f"Missing required fields: {', '.join(missing_fields)}"}, status=status.HTTP_400_BAD_REQUEST)

    code = request.data['code']
    question = request.data['question']
    sample_input = request.data['sample_input']
    sample_output = request.data['sample_output']
    user_output = request.data['user_output']

    logger.info("🔹 Constructing prompt for grading.")

    prompt = f"""
You are an AI code grader. Evaluate the following code submission based on the following **rubric (out of 10 marks)**:

1. **Code Compiles/Runs** (0–2): Does the code run without syntax/runtime errors?
2. **Correctness of Logic** (0–3): Does the logic implement the intended behavior and handle expected cases?
3. **Output Accuracy** (0–1): Does the output match the problem requirements exactly?
4. **Code Readability** (0–1): Clear indentation, meaningful naming, and good structure.
5. **Use of Language Features** (0–1): Proper use of constructs like loops, conditionals, functions, OOP, etc.
6. **Comments and Documentation** (0–1): Are important logic sections well explained?
7. **Error Handling / Edge Cases** (0–1): Does it handle invalid inputs or edge cases gracefully?

Return a JSON object with this structure:
{{
  "code_compiles": {{"score": int, "feedback": str}},
  "logic_correctness": {{"score": int, "feedback": str}},
  "output_accuracy": {{"score": int, "feedback": str}},
  "readability": {{"score": int, "feedback": str}},
  "language_features": {{"score": int, "feedback": str}},
  "documentation": {{"score": int, "feedback": str}},
  "error_handling": {{"score": int, "feedback": str}},
  "final_score": int,
  "summary": str,
  "strengths": str,
  "weaknesses": str
}}

### Question:
{question}

### Code:
{code}

### Sample Input:
{sample_input}

### Expected Output:
{sample_output}

### User Output:
{user_output}
"""

    logger.info("🔸 Sending prompt through fallback grading system.")
    grade_json = generate_grading_json(prompt)

    if not grade_json:
        logger.error("❌ All grading fallbacks failed.")
        return Response({"error": "All grading services failed. Please try again later."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    logger.info("✅ Grading completed successfully.")
    return Response(grade_json, status=status.HTTP_200_OK)




from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Question
from .serializers import QuestionSerializer


class QuestionDetailView(APIView):
    def get(self, request, pk):
        logger.info(f"Fetching question with ID: {pk}")
        try:
            question = Question.objects.get(pk=pk)
            logger.info(f"Question found: {question.title}")
        except Question.DoesNotExist:
            logger.warning(f"Question not found for ID: {pk}")
            return Response({"error": "Question not found"}, status=404)
        serializer = QuestionSerializer(question)
        return Response(serializer.data)



class QuestionListView(APIView):
    def get(self, request):
        questions = Question.objects.all()
        logger.info(f"Fetched all questions. Count: {questions.count()}")
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)
