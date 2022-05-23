FROM centos/python-38-centos7

ENV TZ='Europe/London'

COPY requirements.txt arping.py ./

RUN python -m pip install --no-cache-dir -r requirements.txt

ENTRYPOINT [ "python", "./arping.py"]
CMD [ "--help" ]
