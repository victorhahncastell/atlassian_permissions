FROM python:3

MAINTAINER Victor Hahn <victor.hahn@flexoptix.net>

RUN pip install -r requirements.txt

ENTRYPOINT ["./run.py"]


