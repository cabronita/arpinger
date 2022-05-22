#!/usr/bin/env bash

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

docker build -t cabronita/arping:${TIMESTAMP} .

docker push cabronita/arping:${TIMESTAMP}