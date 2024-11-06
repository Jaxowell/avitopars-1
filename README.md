# avitopars-1

...
pip freeze > requirements.txt - Сохранение зависимостей

Команды git:
git fetch origin - загрузка удалённых репозиториев
- Для слияния с основной веткой:
    git checkout main ... git pull origin main (обновление)
    git merge main (origin/main)


Часть I - Подготовка
1) myenv\Scripts\activate - Активация вирт. окр.
2) Проверяем python --version, когда активируется вирт. окр. Должна быть "3.11.9"
3) Устанавливаем новый pip: python.exe -m pip install --upgrade pip

Часть II - Установка зависимостей (плагинов)
1) pip install -r requirements.txt - Установка (обязательно в вирт. окр.)
2) playwright install

