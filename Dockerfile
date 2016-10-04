FROM python:3

MAINTAINER Victor Hahn <victor.hahn@flexoptix.net>

ADD . /opt/atlassian_permissions
RUN pip install -r /opt/atlassian_permissions/requirements.txt

ENTRYPOINT ["/opt/atlassian_permissions/run.py"]
