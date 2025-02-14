FROM python:3.12


WORKDIR /app


COPY ./app/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./app/py /app/py


CMD ["fastapi", "run", "py/main.py", "--port", "8000"]

