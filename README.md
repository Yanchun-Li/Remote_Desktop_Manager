# Remote Desktop Manager

A web-based remote desktop management system that allows you to manage and monitor remote desktop usage. This application helps you track and manage remote desktop sessions efficiently.

## Features

- Add, rename, and delete remote desktops
- Track desktop usage status in real-time
- User login/logout functionality
- Time remaining display for active sessions
- Database backup functionality
- Responsive design for all devices
- Session management and monitoring
- Environment-based configuration

## Prerequisites

- Python 3.7 or higher
- PostgreSQL (for production)
- SQLite (for development)

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd remotedesktop
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On Unix or MacOS
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:
   ```
   FLASK_APP=app.py
   FLASK_ENV=development
   DATABASE_URL=sqlite:///desktops.db
   SECRET_KEY=your-secret-key
   ```

5. Initialize the database:
   ```bash
   python init_db.py
   ```

6. Run the application:
   ```bash
   python app.py
   ```
   Or on Windows:
   ```bash
   start.bat
   ```

7. Open your browser and navigate to `http://localhost:5000`

## Database Management

- To backup the database:
  ```bash
  python backup_db.py
  ```

## Deployment

This project is configured for deployment on Render.com. The deployment process is automated through the `render.yaml` configuration file.

### Production Setup

1. Set up a PostgreSQL database on Render
2. Update the `DATABASE_URL` in your environment variables
3. Deploy the application using Render's web service

## Project Structure

- `app.py` - Main application file
- `models.py` - Database models
- `config.py` - Configuration settings
- `init_db.py` - Database initialization
- `backup_db.py` - Database backup utility
- `templates/` - HTML templates
- `static/` - Static assets (CSS, JavaScript, images)

## Technologies Used

- Python 3.7+
- Flask 2.0.1
- SQLAlchemy 1.4.23
- Flask-SQLAlchemy 2.5.1
- PostgreSQL/SQLite
- HTML/CSS/JavaScript

