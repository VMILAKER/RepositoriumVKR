FROM python:latest

WORKDIR /Backend

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install python-dotenv

# RUN docker exec -it postgres-repositorium psql -U dynamo -d repositorium -c "ALTER DATABASE repositorium REFRESH COLLATION VERSION;"
# RUN docker exec -it postgres-repositorium psql -U dynamo -d postgres -c "ALTER DATABASE postgres REFRESH COLLATION VERSION;"

COPY ./ /Backend/

CMD ["python", "main.py"]