FROM python:3.12

WORKDIR /Backend


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install python-dotenv


COPY ./ /Backend/

CMD ["python", "main.py"]