FROM python:3.12

WORKDIR /app

COPY ./app/elan_postprocessor/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt


COPY ./app/common/ common/
COPY ./app/__init__.py .
COPY ./app/elan_postprocessor/ elan_postprocessor/ 

ENTRYPOINT ["python", "-m", "elan_postprocessor.main"]