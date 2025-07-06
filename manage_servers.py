#!/usr/bin/env python3
import subprocess
import os
import sys
import time
import signal
import psutil

def find_process_by_port(port):
    """Find process using a specific port"""
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            try:
                return psutil.Process(conn.pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    return None

def kill_process_on_port(port, name):
    """Kill process running on specific port"""
    process = find_process_by_port(port)
    if process:
        print(f"🔴 Stopping {name} server (PID: {process.pid})...")
        process.terminate()
        try:
            process.wait(timeout=5)
        except psutil.TimeoutExpired:
            print(f"⚠️  Force killing {name} server...")
            process.kill()
        print(f"✅ {name} server stopped")
        return True
    return False

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting Backend server...")
    
    # Kill existing backend server
    kill_process_on_port(8000, "Backend")
    
    # Start backend
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    venv_python = os.path.join(os.path.dirname(__file__), 'venv', 'bin', 'python')
    
    if not os.path.exists(venv_python):
        print("❌ Virtual environment not found. Please create it first.")
        return None
    
    cmd = [venv_python, '-m', 'uvicorn', 'app:app', '--reload', '--port', '8000']
    process = subprocess.Popen(cmd, cwd=backend_path)
    print(f"✅ Backend server started (PID: {process.pid})")
    return process

def start_frontend():
    """Start the React frontend server"""
    print("🚀 Starting Frontend server...")
    
    # Kill existing frontend server
    kill_process_on_port(3000, "Frontend")
    
    # Start frontend
    frontend_path = os.path.join(os.path.dirname(__file__), 'frontend')
    
    # Check if node_modules exists
    if not os.path.exists(os.path.join(frontend_path, 'node_modules')):
        print("❌ node_modules not found. Running npm install...")
        subprocess.run(['npm', 'install'], cwd=frontend_path, check=True)
    
    env = os.environ.copy()
    env['NODE_OPTIONS'] = '--openssl-legacy-provider'
    
    cmd = ['npm', 'start']
    process = subprocess.Popen(cmd, cwd=frontend_path, env=env)
    print(f"✅ Frontend server started (PID: {process.pid})")
    return process

def stop_servers():
    """Stop both servers"""
    print("\n🛑 Stopping servers...")
    backend_stopped = kill_process_on_port(8000, "Backend")
    frontend_stopped = kill_process_on_port(3000, "Frontend")
    
    if not backend_stopped and not frontend_stopped:
        print("ℹ️  No servers were running")
    else:
        print("✅ All servers stopped")

def start_servers():
    """Start both servers"""
    try:
        # Start backend first
        backend_process = start_backend()
        if not backend_process:
            return
        
        # Wait a bit for backend to start
        print("⏳ Waiting for backend to initialize...")
        time.sleep(3)
        
        # Start frontend
        frontend_process = start_frontend()
        
        print("\n✅ Both servers are running!")
        print("📍 Backend:  http://localhost:8000")
        print("📍 Frontend: http://localhost:3000")
        print("\nPress Ctrl+C to stop both servers...\n")
        
        # Wait for Ctrl+C
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")
            stop_servers()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        stop_servers()

def main():
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == 'stop':
            stop_servers()
        elif command == 'start':
            start_servers()
        else:
            print("Usage: python manage_servers.py [start|stop]")
    else:
        # Default: start servers
        start_servers()

if __name__ == "__main__":
    # Install psutil if not available
    main()