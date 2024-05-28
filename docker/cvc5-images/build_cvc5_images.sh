#!/bin/sh
cd common
docker build -t cloud-cvc5:common .
cd ..

cd leader
docker build -t cloud-cvc5:leader .
cd ..

cd worker
docker build -t cloud-cvc5:worker .
cd ..