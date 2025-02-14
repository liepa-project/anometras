FROM python:3.12


WORKDIR /app


COPY ./app /app

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt


CMD ["fastapi", "run", "py/main.py", "--port", "8000"]

