# start.sh
#!/bin/bash

# Start the backend in the background
./start_backend.sh &

# Start the frontend in the background (optional)
./start_frontend.sh &