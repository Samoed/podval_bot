FROM python:3.10-slim

WORKDIR "/src"
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
ENV PYTHONPATH "${PYTHONPATH}:/src"
COPY . .
CMD ["python", "src/main.py"]
