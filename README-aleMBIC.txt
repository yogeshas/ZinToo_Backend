Alembic/Flask-Migrate Setup & Usage:

1. Create and activate your virtual environment:
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate

2. Install requirements:
   pip install -r requirements.txt

3. Initialize Alembic migrations (run once):
   flask db init

4. Generate migration after model changes:
   flask db migrate -m "Initial migration"

5. Apply migrations to the database:
   flask db upgrade

6. Run your Flask app:
   python app.py

# Make sure FLASK_APP=app.py is set in your environment if needed.
