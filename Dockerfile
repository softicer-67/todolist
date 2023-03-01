FROM python:3.10

SHELL ["/bin/bash", "-c"]

WORKDIR /app

COPY requirements.txt /app

RUN pip install --upgrade pip

COPY . /app

RUN pip install -r /app/requirements.txt

CMD python manage.py runserver 0.0.0.0:8000
