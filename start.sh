# start.sh
#!/bin/bash

# Start the backend in the background
./start_backend.sh &

# Start the frontend in the background (optional)
./start_frontend.sh &

# Wait for any process to exit (prevents the script from exiting)
wait -n

# Exit with status of the first process to exit
exit $?