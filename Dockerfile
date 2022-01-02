FROM python:alpine3.9

COPY basic_cli.py .

RUN pip install websockets

CMD ["python3", "basic_cli.py"]
