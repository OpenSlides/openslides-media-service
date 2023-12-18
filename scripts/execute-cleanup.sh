#!/bin/bash

printf "Autoflake:\n"
autoflake --verbose --in-place --remove-all-unused-imports --ignore-init-module-imports --recursive src/ tests/
printf "\nBlack:\n"
black src/ tests/
printf "\nIsort:\n"
isort src/ tests/
printf "\nFlake8:\n"
flake8 src/ tests/
