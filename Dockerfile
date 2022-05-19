FROM centos:7

RUN yum install -y \
    iproute \
    python3 \
    && yum clean all

WORKDIR /app

COPY requirements.txt ./
RUN python3 -m pip install --no-cache-dir -r requirements.txt

COPY arping.py .

ENTRYPOINT [ "python3", "./arping.py"]
CMD [ "--help" ]
