# backend/main.py

import os
import asyncio
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .helpers.doc_helper import get_result
from .helpers.language_helper import get_abstractive_summary


app = FastAPI()  

class TextContent(BaseModel):
    content: str

@app.post("/analyze/")  
async def analyze_document_content(file: UploadFile = File(...)):  
    content = await file.read()
    try:
        text = get_result(content)
    except UnicodeDecodeError:
        text = content.decode('latin-1')[:300]
    return {"text": text}  

@app.post("/summarize/")
async def chat(text_content: TextContent):
    summary = get_abstractive_summary(text_content.content)
    return {"summary": summary}