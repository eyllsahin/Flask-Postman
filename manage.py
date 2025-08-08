
"""
Environment Management Script for Flask Chatbot
"""
import os
import subprocess
import sys
import time

def run_command(command, shell=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(command, shell=shell, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_docker():
    """Check if Docker is running"""
    success, stdout, stderr = run_command("docker --version")
    if not success:
        print("❌ Docker is not installed or not in PATH")
        return False
    
    success, stdout, stderr = run_command("docker ps")
    if not success:
        print("❌ Docker daemon is not running")
        return False
    
    print("✅ Docker is running")
    return True

def check_ports():
    """Check if ports are available"""
    import socket
    
    ports_to_check = {
        8080: "Flask App (Docker)",
        3307: "MySQL (Docker)", 
        5001: "Flask App (Local)"
    }
    
    for port, service in ports_to_check.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        
        if result == 0:
            print(f"⚠️  Port {port} is in use ({service})")
        else:
            print(f"✅ Port {port} is available ({service})")

def show_status():
    """Show current status of containers"""
    print("\n📊 Container Status:")
    success, stdout, stderr = run_command("docker-compose ps")
    if success:
        print(stdout)
    else:
        print("❌ Could not get container status")

def start_docker():
    """Start Docker containers"""
    print("\n🚀 Starting Docker containers...")
    success, stdout, stderr = run_command("docker-compose up -d")
    if success:
        print("✅ Containers started successfully")
        time.sleep(5)  
        show_status()
        print("\n🌍 Application URLs:")
        print("   Docker: http://localhost:8080")
        print("   Health: http://localhost:8080/health")
    else:
        print(f"❌ Failed to start containers: {stderr}")

def stop_docker():
    """Stop Docker containers"""
    print("\n🛑 Stopping Docker containers...")
    success, stdout, stderr = run_command("docker-compose down")
    if success:
        print("✅ Containers stopped successfully")
    else:
        print(f"❌ Failed to stop containers: {stderr}")

def start_local():
    """Start local Flask application"""
    print("\n🚀 Starting local Flask application...")
    print("🌍 Will be available at: http://localhost:5001")
    print("💡 Make sure to set DB_HOST=localhost and DB_PORT=3307 in .env for Docker MySQL")
    print("⚠️  Press Ctrl+C to stop\n")
    
    os.environ['FLASK_DEBUG'] = 'True'
    os.environ['FLASK_HOST'] = '127.0.0.1'
    os.environ['FLASK_PORT'] = '5001'
    
    try:
        subprocess.run([sys.executable, "run.py"])
    except KeyboardInterrupt:
        print("\n👋 Local Flask application stopped")

def show_logs():
    """Show Docker container logs"""
    print("\n📋 Container Logs:")
    success, stdout, stderr = run_command("docker-compose logs --tail=50")
    if success:
        print(stdout)
    else:
        print(f"❌ Could not get logs: {stderr}")

def main():
    """Main menu"""
    print("=" * 60)
    print("🐳 Flask Chatbot Environment Manager")
    print("=" * 60)
    
    while True:
        print("\nChoose an option:")
        print("1. 🚀 Start Docker containers")
        print("2. 🛑 Stop Docker containers") 
        print("3. 📊 Show container status")
        print("4. 📋 Show logs")
        print("5. 🏠 Start local Flask app")
        print("6. 🔍 Check system status")
        print("7. 🚪 Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == "1":
            if check_docker():
                start_docker()
        elif choice == "2":
            stop_docker()
        elif choice == "3":
            show_status()
        elif choice == "4":
            show_logs()
        elif choice == "5":
            start_local()
        elif choice == "6":
            print("\n🔍 System Status Check:")
            check_docker()
            check_ports()
        elif choice == "7":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-7.")

if __name__ == "__main__":
    main()
