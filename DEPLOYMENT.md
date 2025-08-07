# Deployment Guide

This guide explains how to deploy the Flask Chatbot application using Docker.

## Prerequisites

- Docker and Docker Compose installed
- Your environment variables configured

## Method 1: Using DockerHub Image (Recommended)

### 1. Create environment file

Create a `.env` file with your configuration:

```bash
# Copy the example file
cp .env.example .env

# Edit with your actual values
SECRET_KEY=your-super-secret-key-here-change-this
GEMINI_API_KEY=your-gemini-api-key-here
DB_HOST=localhost
DB_PORT=3307
DB_USER=root
DB_PASSWORD=your-db-password
DB_NAME=your-database-name
MYSQL_ROOT_PASSWORD=your-mysql-root-password
```

### 2. Deploy using production compose file

```bash
# Pull latest image and start services
docker-compose -f docker-compose.prod.yml up -d

# Initialize database (first time only)
docker-compose -f docker-compose.prod.yml exec chatbot_web python init_db.py

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 3. Access the application

- Application: http://localhost:5000
- Admin Panel: http://localhost:5000/admin
- Health Check: http://localhost:5000/health

## Method 2: Building from Source

### 1. Clone repository

```bash
git clone https://github.com/eyllsahin/Flask-Postman.git
cd Flask-Postman
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Build and deploy

```bash
# Build and start services
docker-compose up -d

# Initialize database
docker-compose exec chatbot_web python init_db.py
```

## Method 3: Direct Docker Run

### Run with MySQL

```bash
# Start MySQL container
docker run -d \
  --name chatbot_mysql \
  -e MYSQL_ROOT_PASSWORD=your-password \
  -e MYSQL_DATABASE=chatbot_flask \
  -p 3307:3306 \
  mysql:8.0

# Start Flask app
docker run -d \
  --name chatbot_web \
  --link chatbot_mysql:mysql \
  -p 5000:5000 \
  -e SECRET_KEY=your-secret-key \
  -e GEMINI_API_KEY=your-api-key \
  -e DB_HOST=chatbot_mysql \
  -e DB_USER=root \
  -e DB_PASSWORD=your-password \
  -e DB_NAME=chatbot_flask \
  sept23/flask-chatbot:latest
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Flask session secret | `your-super-secret-key` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSy...` |
| `DB_HOST` | Database hostname | `localhost` or `chatbot_mysql` |
| `DB_USER` | Database username | `root` |
| `DB_PASSWORD` | Database password | `your-db-password` |
| `DB_NAME` | Database name | `chatbot_flask` |
| `MYSQL_ROOT_PASSWORD` | MySQL root password | `your-mysql-password` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_PORT` | Database port | `3306` |

## Troubleshooting

### Check container status
```bash
docker-compose ps
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f chatbot_web
```

### Database connection issues
```bash
# Test database connection
docker-compose exec chatbot_web python -c "from app.db_utils import get_db_connection; print('DB OK' if get_db_connection() else 'DB FAIL')"
```

### Reset database
```bash
# Stop services
docker-compose down

# Remove database volume
docker volume rm chatbot-flask_mysql_data

# Start and reinitialize
docker-compose up -d
docker-compose exec chatbot_web python init_db.py
```

## Security Considerations

1. **Never commit `.env` files**
2. **Use strong passwords** for production
3. **Regularly rotate API keys**
4. **Use HTTPS** in production
5. **Limit database access** to application only
6. **Monitor logs** for security issues

## Monitoring

### Health Check

The application includes a health check endpoint:

```bash
curl http://localhost:5000/health
```

Response format:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-01T12:00:00"
}
```

### Application Logs

Logs are stored in the `logs/` directory and include:
- Application startup/shutdown
- User authentication events
- Chat interactions
- Error messages

## Production Deployment

### 1. Use a reverse proxy (nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Enable SSL/TLS

Use Let's Encrypt or your preferred SSL provider.

### 3. Configure firewall

```bash
# Allow only necessary ports
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

### 4. Set up monitoring

Consider using:
- Docker health checks
- Application monitoring (New Relic, DataDog)
- Log aggregation (ELK stack)

## Backup

### Database backup
```bash
# Create backup
docker-compose exec chatbot_mysql mysqldump -u root -p chatbot_flask > backup.sql

# Restore backup
docker-compose exec -i chatbot_mysql mysql -u root -p chatbot_flask < backup.sql
```

### Application data backup
```bash
# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz logs/
```
