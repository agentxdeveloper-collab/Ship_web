import pytest
from src.app import create_app
from db import db as _db

@pytest.fixture
def app(tmp_path):
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        _db.create_all()
    yield app

def test_index(client):
    rv = client.get('/')
    assert rv.status_code == 200

# To run the application, use the following commands:
# cd C:\Workspace\python_ship\fishing-boat-reservation-app
# python -m venv .venv
# .\.venv\Scripts\Activate.ps1
# python -m pip install --upgrade pip
# python -m pip install -r requirements.txt
# cd src
# python app.py
# Then open a browser and go to: http://127.0.0.1:5000