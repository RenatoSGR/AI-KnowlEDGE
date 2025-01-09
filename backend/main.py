# backend/main.py

import os
import asyncio
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .helpers.doc_helper import get_result


app = FastAPI()  

class Question(BaseModel):
    question: str

@app.post("/analyze/")  
async def analyze_document_content(file: UploadFile = File(...)):  
    content = await file.read()
    try:
        text = get_result(content)
    except UnicodeDecodeError:
        text = content.decode('latin-1')[:300]
    return {"text": text}  

@app.post("/summarize")
async def chat(question: Question):
    async def generate_response():
        response = """
        Elian was no ordinary boy. He lived in the quiet village of Oakhaven, nestled beside the Whispering Woods, a place most villagers avoided. Elian, however, was drawn to it. He felt a hum beneath the forest floor, a thrumming energy that resonated deep within him.
        """
        for chunk in response.split():
            yield chunk + " "
            await asyncio.sleep(0.1)  # simulate delay

    return StreamingResponse(generate_response(), media_type="text/plain")


@app.post("/chat")
async def chat(question: Question):
    async def generate_response():
        response = """
        Elian was no ordinary boy. He lived in the quiet village of Oakhaven, nestled beside the Whispering Woods, a place most villagers avoided. Elian, however, was drawn to it. He felt a hum beneath the forest floor, a thrumming energy that resonated deep within him.
        """
        for chunk in response.split():
            yield chunk + " "
            await asyncio.sleep(0.1)  # simulate delay

    return StreamingResponse(generate_response(), media_type="text/plain")