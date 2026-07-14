# SmartFit

SmartFit is a comprehensive fitness and nutrition tracking application built with Flask.

## Project Structure
- `app/`: Contains the main application code (routes, models, templates, static files).
- `migrations/`: Database migration scripts.
- `requirements.txt`: Python package dependencies.
- `.env`: Environment variables configuration.
- `run.py`: Entry point to run the application.

## Setup
1. Clone the repository.
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment.
4. Install dependencies: `pip install -r requirements.txt`
5. Configure your `.env` file based on `.env.example`.
6. Run database migrations: `flask db upgrade`
7. Run the application: `python run.py`
