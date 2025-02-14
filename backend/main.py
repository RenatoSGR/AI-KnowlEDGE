# backend/main.py

import os
import asyncio
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .helpers.doc_helper import get_result
from .helpers.language_helper import get_extractive_summary
from .helpers.ollama_helper import get_nb_tokens, get_available_models 
from .helpers.ollama_helper import generate_questions, generate_answer


app = FastAPI()  


class TextContent(BaseModel):
    content: str


class SummaryContent(BaseModel):
    content: str
    model_name: str


class QuestionContent(BaseModel):
    question: str
    relevant_chunks: list
    model_name: str


@app.post("/analyze/")  
async def analyze_document_content(file: UploadFile = File(...)):  
    content = await file.read()
    try:
        text = get_result(content)
    except UnicodeDecodeError:
        text = "Error reading file contents. Please upload a valid file."
    return {"text": text}  


@app.post("/summarize/")
async def chat(text_content: TextContent):
    summary = get_extractive_summary(text_content.content, num_sentences=4)
    return {"summary": summary}


@app.post("/estimate_tokens/")
async def estimate_tokens(text_content: TextContent):
    nb_tokens = get_nb_tokens(text_content.content)
    return {"nb_tokens": nb_tokens}


@app.get("/get_models/")
async def get_models():
    return {"available_models": get_available_models()}


@app.post("/generate_questions/")
async def get_ollama_questions(summary_content: SummaryContent):
    questions = generate_questions(summary_content.model_name, summary_content.content)
    return {"questions": questions}


@app.post("/generate_answer/")
async def get_ollama_answer(question_content: QuestionContent):
    answer = generate_answer(question_content.question, question_content.relevant_chunks, question_content.model_name)
    return {"answer": answer}