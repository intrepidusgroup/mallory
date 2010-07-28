#!/bin/sh

rm -f ../db/*
rm -f ../certs/*
rm -f certs/*
find . -name "*.pyc" -exec rm -f {} \;
rm -f mallory.log
