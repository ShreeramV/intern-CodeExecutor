from typing import List, Optional
from pydantic import BaseModel

class GeneratedQuestionOut(BaseModel):
    id: int
    title: str
    description: str
    sample_input: str
    sample_output: str
    companies_asked: List[str]
    year_asked: Optional[int]
    difficulty: str

class GeneratedQuestionList(BaseModel):
    generated_questions: List[GeneratedQuestionOut]
