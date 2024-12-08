# Остановить и удалить все контейнеры
docker stop $(docker ps -aq)
docker rm $(docker ps -aq)

# Удалить все образы
docker rmi $(docker images -q)

# Удалить все тома
docker volume rm $(docker volume ls -q)

# Перейти в директорию frontend и собрать Docker-образ
cd frontend
docker build -t vettspace/foodgram_frontend .

# Перейти в директорию backend и собрать Docker-образ
cd ../backend
docker build -t vettspace/foodgram_backend .

# Перейти в директорию infra 
# и запустить docker-local-compose для локального развертывания
cd ../infra
docker-compose -f docker-local-compose.yml up -d --build

# Выполнить миграции и другие команды Django
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py collectstatic --no-input
docker-compose exec backend python manage.py create_tags
docker-compose exec backend python manage.py load_ingredients data/ingredients.json
docker-compose exec backend python manage.py create_users
docker-compose exec backend python manage.py create_recipes
docker-compose exec backend python manage.py createsuperuser