FROM python:3.9.10

## Update all apps and install dependecies for cv2
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

## Pip dependencies
# Upgrade pip
RUN pip install --upgrade pip
# Copy files
COPY . . 
RUN pip install -r requirements.txt

RUN echo "export TERM=xterm"  >> ~/.bashrc

CMD python main.py
