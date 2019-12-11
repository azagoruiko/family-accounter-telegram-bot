FROM python:3.7
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt
COPY . /app

CMD ["python", "bot.py"]
