FROM python:3.10-slim


WORKDIR /code


COPY ./requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app
COPY ./guardian /code/guardian

# exit code 137 out of memory
# RUN python /code/guardian/download_model.py



CMD ["fastapi", "run", "app/main.py", "--port", "8000"]