# ICQ Backend

## Quickstart

```
docker run --name pg -e POSTGRES_HOST_AUTH_METHOD=trust -p 5432:5432 -d postgis/postgis
poetry install
poetry run python manage.py migrate
poetry run python manage.py runserver
```

## Core Dependencies

- Selenium driver for Google Chrome
- Poetry for Python
- PostgreSQL
- GDAL
  - This needs to be set up outside of our Poetry environment, and generally boils down to the steps at [this site](https://mothergeo-py.readthedocs.io/en/latest/development/how-to/gdal-ubuntu-pkg.html).
  ```
  sudo add-apt-repository -y ppa:ubuntugis/ppa
  sudo apt update
  sudo apt install gdal-bin libgdal-dev
  ```

## Django

We use Django to run and manage the web application.

### Examples

**Apply migrations:** `poetry run python manage.py migrate`

## Dependency Management

We use Poetry to manage our Python dependencies. See the [basic usage](https://python-poetry.org/docs/basic-usage/) page for details.

### Examples

**Install dependencies:** `poetry install`
**Add new dependency:** `poetry add selenium`
**Run a script:** `poetry run python your_script.py`
**Start a shell:** `poetry shell`
