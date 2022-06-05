#!/usr/bin/env bash

docker build -t cabronita/arping:$1 .
docker push cabronita/arping:$1
