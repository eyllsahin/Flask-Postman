from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() in ['true', '1', 'yes']
    host = os.getenv('FLASK_HOST', '127.0.0.1')  
    port = int(os.getenv('FLASK_PORT', 5001))  
    
    print(f"🚀 Starting Flask application...")
    print(f"🔧 Debug mode: {debug_mode}")
    print(f"🌐 Host: {host}")
    print(f"🔌 Port: {port}")
    print(f"🌍 Access your app at: http://{host}:{port}")
    print(f"📊 Docker container runs on: http://localhost:8080")
    print("-" * 50)
    
    app.run(
        debug=debug_mode,
        host=host,
        port=port,
        threaded=True,  
        use_reloader=debug_mode  
    )

