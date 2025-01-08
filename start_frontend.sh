# start_frontend.sh
#!/bin/bash

# Start Streamlit on a different port, e.g., PORT + 1
streamlit run Echo.py --server.port 8001 --server.address 0.0.0.0 > frontend_logs.log 2>&1