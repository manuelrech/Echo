#!/bin/bash

# Imposta il PYTHONPATH e avvia uvicorn con redirect dei log
PYTHONPATH=$PYTHONPATH:. uvicorn src.backend.main:app --reload > backend_logs.log 2>&1