up:
	docker compose up --build
down:
	docker compose down
migrate:
	docker compose exec web python manage.py migrate
makemigrations:
	docker compose exec web python manage.py makemigrations
test:
	docker compose exec web pytest
lint:
	ruff check .
format:
	ruff check . --fix && ruff format .
shell:
	docker compose exec web python manage.py shell
createsuperuser:
	docker compose exec web python manage.py createsuperuser
seed:
	docker compose exec web python manage.py seed_demo
