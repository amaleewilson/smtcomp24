#!/bin/sh
cd common
docker build --platform linux/amd64 --no-cache -t cvc5-cloud:common .
cd ..

cd leader
docker build --platform linux/amd64 --no-cache -t cvc5-cloud:leader .
cd ..

cd worker
docker build --platform linux/amd64 --no-cache -t cvc5-cloud:worker .
cd ..
