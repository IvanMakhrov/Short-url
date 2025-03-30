#!/bin/bash

while ! nc -z db 5432; do sleep 1; done
while ! nc -z redis 6379; do sleep 1; done

alembic upgrade head
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload