FROM python:3

WORKDIR /usr/src/app

#COPY bridge_server.py ./
#RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 3100

COPY . .

ENTRYPOINT ["/bin/bash", "-c", "./start_server.sh"]
