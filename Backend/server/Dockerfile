FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
# Install boto3 for S3 interaction
RUN pip install boto3
COPY . .
CMD ["python", "run.py"]
ENV PYTHONUNBUFFERED=1