FROM python:3.10-slim

COPY recipes /recipes
COPY phrases /phrases
WORKDIR "/src"
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "src/main.py"]
