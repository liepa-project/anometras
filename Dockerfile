FROM python:3.12


WORKDIR /app


COPY ./requirements.txt /app/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt


COPY ./py /app/py


CMD ["fastapi", "run", "py/main.py", "--port", "8000"]

