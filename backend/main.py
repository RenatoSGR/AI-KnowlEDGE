from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

app = FastAPI()  

class Question(BaseModel):
    question: str

@app.post("/analyze/")  
async def analyze_document(file: UploadFile = File(...)):  
    content = await file.read()
    try:
        text = content.decode('utf-8')[:300]
    except UnicodeDecodeError:
        text = content.decode('latin-1')[:300]
    return {"text": text}  
  
  
@app.post("/chat")  
async def chat(question: Question):  
    reversed_question = question.question[::-1]  
    return {"response": reversed_question} 