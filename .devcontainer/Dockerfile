FROM python:3.9.10

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
## Pip dependencies
# Upgrade pip
RUN pip install --upgrade pip
# Copy dependencies
COPY ../requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt


