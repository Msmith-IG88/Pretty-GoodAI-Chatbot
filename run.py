import subprocess

subprocess.Popen(["uvicorn", "server:app", "--port", "8000"])
subprocess.run(["ngrok", "http", "8000"])