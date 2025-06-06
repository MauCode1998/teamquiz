import subprocess
import threading

bashscript = """
cd frontend
pwd
npm run build
"""

bashscript_2 = """
pkill -x Safari
pkill -x 'Google Chrome'
sleep 2
"""

bashscript_3 = """
open -a 'Safari' 'http://localhost:8000'
open -a 'Google Chrome' 'http://localhost:8000'
osascript -e 'tell application "Safari" to activate'
"""

bashscript_4 = """
lsof -t -i 8000 | xargs kill
cd backend 
uvicorn app:app --reload --port 8000
"""

def server_start():
    subprocess.run([bashscript_4],capture_output=True,shell=True)

scripts = [bashscript,bashscript_2]

uvicorn_thread = threading.Thread(target=server_start,daemon=True)

for script in scripts:
    process = subprocess.run([script],capture_output=True,shell=True)
    print(process.stdout.decode('utf-8'))

uvicorn_thread.start()

process = subprocess.run([bashscript_3],capture_output=True,shell=True)

uvicorn_thread.join()


