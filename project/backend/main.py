from django.shortcuts import render, get_object_or_404, redirect
import psycopg2
from django.db import connection
def execute_query(query, params=None, fetchone=False, fetchall=False):
    # Подключение к базе данных
    conn = psycopg2.connect(
        host="localhost",
        database="vacancies",
        user="postgres",
        password="Takanashi_13"
    )

    # Создание курсора
    cursor = conn.cursor()

    # Выполнение SQL-запроса
    cursor.execute(query, params)

    # Получение результата
    result = None
    if fetchone:
        result = cursor.fetchone()
    elif fetchall:
        result = cursor.fetchall()

    # Подтверждение транзакции и закрытие соединения
    conn.commit()
    cursor.close()
    conn.close()

    return result



title = 'abuka'
duties = 'nothing'
conditions = 'prefect'
salary = 10000
active = False

# Запрос на вставку данных
insert_query = "INSERT INTO vacancy (title, duties, conditions, salary, active) VALUES (%s, %s, %s, %s, %s) RETURNING id"
insert_data = (title, duties, conditions, salary, active)

# Выполнение запроса на вставку и получение возвращаемого id
vacancy_id = execute_query(insert_query, params=insert_data, fetchone=True)[0]

print(f"Вакансия с ID {vacancy_id} успешно добавлена.")
