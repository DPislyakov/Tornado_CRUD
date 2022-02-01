FROM python:3.9

ADD api.py .

RUN pip install tornado

CMD ["python", "./api.py"]