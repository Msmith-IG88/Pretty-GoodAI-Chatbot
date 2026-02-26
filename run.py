import subprocess

subprocess.Popen(["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])
subprocess.run(["ngrok", "http", "8000"])