# start_backend.sh
#!/bin/bash

# Set PYTHONPATH and start uvicorn on the specified PORT
PYTHONPATH=$PYTHONPATH:. uvicorn src.backend.main:app --reload --host 0.0.0.0 --port 8000 > backend_logs.log 2>&1