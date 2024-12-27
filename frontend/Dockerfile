FROM python:3.9  
  
WORKDIR /app  
  
COPY . /app  
  
RUN pip install --no-cache-dir streamlit requests  
  
CMD ["streamlit", "run", "app.py", "--server.port=8501"]  