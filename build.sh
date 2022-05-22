#!/usr/bin/env bash

docker build -t cabronita/arping:$(git rev-parse --short HEAD) .
docker push cabronita/arping:$(git rev-parse --short HEAD)