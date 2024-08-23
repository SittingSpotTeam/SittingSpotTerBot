FROM python:3.12.5-slim-bullseye

ADD main.py .
ADD requirements.txt .

RUN pip install -r ./requirements.txt

CMD ["python3", "./main.py"]