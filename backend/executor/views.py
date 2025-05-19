import os
import uuid
import subprocess
import json
import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Question, Topic, Company, TestCase
from .serializers import QuestionSerializer, GenerateQuestionInputSerializer
from .question_generator import generate_question_with_test_cases  # if used elsewhere
import google.generativeai as genai
from .models import Topic  
from decouple import config

logger = logging.getLogger(__name__)
GEMINI_API_KEY = config("GEMINI_API_KEY") 

genai.configure(api_key=GEMINI_API_KEY)

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

    print("🔹 Received code execution request.")
    print(f"🔸 Language: {language}")
    print(f"🔸 Code preview:\n{code[:100]}..." if code else "❌ No code provided")

    if not code or not language:
        print("❌ Code or language missing.")
        return Response({'error': 'Code and language are required.'}, status=400)

    if language not in LANGUAGES:
        print(f"❌ Unsupported language: {language}")
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
            print(f"🔧 Compiling C code: {' '.join(compile_cmd)}")
            subprocess.run(compile_cmd, check=True, stderr=subprocess.PIPE)
            cmd = [output_exe]

        elif language == 'cpp':
            output_exe = os.path.join(folder, f'{uuid.uuid4().hex}')
            compile_cmd = ['g++', filepath, '-o', output_exe]
            print(f"🔧 Compiling C++ code: {' '.join(compile_cmd)}")
            subprocess.run(compile_cmd, check=True, stderr=subprocess.PIPE)
            cmd = [output_exe]

        elif language == 'java':
            java_folder = os.path.abspath(folder)
            compile_cmd = ['javac', filepath]
            print(f"🔧 Compiling Java code: {' '.join(compile_cmd)}")
            subprocess.run(compile_cmd, cwd=java_folder, check=True, stderr=subprocess.PIPE)
            class_name = os.path.splitext(os.path.basename(filepath))[0]
            cmd = ['java', '-cp', java_folder, class_name]

        print(f"▶️ Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=True)

        print("✅ Execution successful.")
        if result.stdout:
            print("📤 Output:\n", result.stdout)
        if result.stderr:
            print("⚠️  Errors:\n", result.stderr)

        return Response({
            'stdout': result.stdout,
            'stderr': result.stderr
        })

    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e)
        print("❌ Execution failed with error:", stderr)
        return Response({'stdout': '', 'stderr': stderr}, status=400)

    except subprocess.TimeoutExpired:
        print("⏰ Execution timed out.")
        return Response({'stdout': '', 'stderr': 'Execution timed out'}, status=408)

    finally:
        print("🧹 Cleaning up temporary files...")
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
            logging.warning(f"⚠️ Cleanup failed: {cleanup_error}")

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
     # Fixed field names
    filterset_fields = ['difficulty', 'topics', 'companies', 'custom_id']  # Added custom_id
    
    # Support searching by related names and custom_id
    search_fields = ['title', 'topics__name', 'companies__name', 'difficulty', 'custom_id']  # Added custom_id


    
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
        f"Generate 5 coding questions on the topic '{topic_name}' with difficulty '{difficulty}'. "
        f"Each question should have:\n"
        f"- A title\n"
        f"- A detailed description\n"
        f"- A list of companies that have asked this question (key: 'companies_asked')\n"
        f"- The year this question was asked (key: 'year_asked')\n"
        f"- 2-3 test cases with input and output in JSON format\n"
        f"Respond only with a valid JSON array like:\n"
        f"{{'title': ..., 'description': ..., 'companies_asked': [...], 'year_asked': ..., 'test_cases': [{{'input': ..., 'output': ...}}]}}"
    )

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        content = response.text.strip()

        if not content:
            return Response({"error": "No content generated by Gemini."}, status=500)

        if content.startswith("```"):
            content = content.strip("```json").strip("```")

        try:
            questions_json = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("❌ Failed to parse JSON from Gemini: %s", str(e))
            return Response({'error': 'Failed to parse JSON from Gemini', 'details': str(e)}, status=500)

        topic_obj, _ = Topic.objects.get_or_create(name=topic_name)
        generated_questions = []

        for q in questions_json:
            logger.info(f"🔹 Processing Question: {q['title']}")

            companies_list = q.get('companies_asked', [])
            year_asked = q.get('year_asked', None)
            test_cases = q.get('test_cases', [])

            sample_input = str(test_cases[0]['input']) if test_cases else ""
            sample_output = str(test_cases[0]['output']) if test_cases else ""

            question = Question.objects.create(
                title=q['title'],
                description=q['description'],
                sample_input=sample_input,
                sample_output=sample_output,
                explanation="",
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
                    input_data=tc['input'],
                    expected_output=tc['output']
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

        return Response({'generated_questions': generated_questions}, status=201)

    except Exception as e:
        logger.error("❌ Exception occurred: %s", str(e))
        return Response({"error": str(e)}, status=500)

    
@api_view(['POST'])
def grade_code(request):
    logger.info("🔹 Received POST request to grade code.")

    # Validate input
    required_fields = ['code', 'question', 'sample_input', 'sample_output', 'user_output']
    if not all(request.data.get(field) for field in required_fields):
        logger.error("❌ Missing one or more required fields.")
        return Response({"error": "All fields are required."}, status=400)

    code = request.data['code']
    question = request.data['question']
    sample_input = request.data['sample_input']
    sample_output = request.data['sample_output']
    user_output = request.data['user_output']

    logger.info("🔹 Grading code for question.")

    # Construct prompt
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

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        content = response.text.strip()

        if not content:
            logger.error("❌ Empty response from Gemini.")
            return Response({"error": "No response from Gemini."}, status=500)

        if content.startswith("```"):
            content = content.strip("```json").strip("```")

        try:
            grade_json = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error("❌ Failed to parse JSON from Gemini: %s", str(e))
            return Response({'error': 'Failed to parse JSON from Gemini', 'raw': content}, status=500)

        logger.info("✅ Grading completed successfully.")
        return Response(grade_json, status=200)

    except Exception as e:
        logger.error("❌ Grade exception: %s", str(e))
        return Response({"error": str(e)}, status=500)




from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Question
from .serializers import QuestionSerializer

class QuestionDetailView(APIView):
    def get(self, request, pk):
        try:
            question = Question.objects.get(pk=pk)
        except Question.DoesNotExist:
            return Response({"error": "Question not found"}, status=404)
        serializer = QuestionSerializer(question)
        return Response(serializer.data)

class QuestionListView(APIView):
    def get(self, request):
        questions = Question.objects.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)
