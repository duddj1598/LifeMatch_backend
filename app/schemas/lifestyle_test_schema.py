from pydantic import BaseModel
from typing import List, Optional, Dict


class QuestionOption(BaseModel):
    option_id: int
    text: str

class Question(BaseModel):
    question_id: int
    question_text: str
    options: List[QuestionOption]

class QuestionParts(BaseModel):
    part1: List[Question]
    part2: List[Question]
    part3: List[Question]
    part4: List[Question]

class LifestyleQuestionsResponse(BaseModel):
    status: int
    data: QuestionParts


class LifestyleTypeDetail(BaseModel):
    type_name: str
    keywords: str
    description: str

class LifestyleTypesResponse(BaseModel):
    status: int
    data: List[LifestyleTypeDetail]


class LifestyleTestSubmission(BaseModel):
    user_id: str
    selected_option_ids: List[int]


class LifestyleTestResultDetail(BaseModel):
    type_name: str
    keywords: str
    description: str

class LifestyleTestResultResponse(BaseModel):
    status: int
    user_id: str
    result: LifestyleTestResultDetail