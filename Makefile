venv:
	@python -m venv ./venv

activate:
	@source ./venv/bin/activate

initdb:
	@python manage.py migrate
	@python manage.py createsuperuser

run:
	@python manage.py runserver