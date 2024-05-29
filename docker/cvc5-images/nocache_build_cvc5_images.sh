#!/bin/sh
cd common
docker build --platform linux/amd64 --no-cache -t cloud-cvc5:common .
cd ..

cd leader
docker build --platform linux/amd64 --no-cache -t cloud-cvc5:leader .
cd ..

cd worker
docker build --platform linux/amd64 --no-cache -t cloud-cvc5:worker .
cd ..
