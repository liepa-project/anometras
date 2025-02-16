FROM python:3.12


WORKDIR /app

COPY ./app/api_service/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app/common common/
COPY ./app/api_service /app/api_service/


CMD ["fastapi", "run", "api_service/main.py", "--port", "8000"]

