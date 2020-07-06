REM TODO: Заменить путь на относительный (? %cd% ?)
docker rm horizon-web -fv
docker run --rm --name horizon-web -d -v D:\projs\horizon\web\data:/horizon-web/data/ -p 80:8000  horizon-web:dev