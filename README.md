# Kausal Paths

## Installation

### Development

In the project root directory, create and activate a Python virtual environment:

```shell
python3 -m venv venv
source venv/bin/activate
```

Install the required Python packages:

```shell
pip install -r requirements.txt
```
Create a file called `local_settings.py` in your repo root with the following contents:

```python
from paths.settings import BASE_DIR

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': f'{BASE_DIR}/db.sqlite3',
        'ATOMIC_REQUESTS': True,
    }
}
```

Run migrations:

```shell
python manage.py migrate
```

Create a superuser:
> You might need the following translations during the createsuperuser operation: käyttäjätunnus = username, sähköpostiosoite = e-mail

```shell
python manage.py createsuperuser
```

Compile the translation files:

```shell
python manage.py compilemessages
```

You can now run the backend:

```shell
python manage.py runserver
```

The GraphQL API is now available at `http://127.0.0.1:8000/v1/graphql/`.