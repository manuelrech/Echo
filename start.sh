#!/bin/bash

# Avvia il backend in background e salva i log
./start_backend.sh &

# Avvia il frontend in background e salva i log
./start_frontend.sh &