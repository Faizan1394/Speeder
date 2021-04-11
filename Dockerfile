FROM python:3.8.8

WORKDIR /opt/ml_api

ENV FLSK_APP speeder_api.py

#install requirements
COPY ./WebApp /opt/ml_api/
RUN pip install --upgrade pip
RUN pip install -r /opt/ml_api/Requirements.txt
RUN pip install -r /opt/ml_api/Requirements.txt

EXPOSE 80

CMD ["python","./speeder_api.py"]
