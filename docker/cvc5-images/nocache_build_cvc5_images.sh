#!/bin/sh
cd common
docker build --no-cache -t cloud-cvc5:common .
cd ..

cd leader
docker build --no-cache -t cloud-cvc5:leader .
cd ..

cd worker
docker build --no-cache -t cloud-cvc5:worker .
cd ..
