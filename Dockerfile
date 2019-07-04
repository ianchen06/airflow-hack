FROM python:3.7
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
ENV C_FORCE_ROOT true
COPY . .
