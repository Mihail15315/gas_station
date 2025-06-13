import random
# from datetime import datetime, timedelta
from datetime import time
from django.utils import timezone
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from station.models import *
from decimal import Decimal
def create_fuel_types():
    fuels = [
        {'name': 'АИ-92', 'price': 45.50, 'cost': 40.20, 'octane_number': 92},
        {'name': 'АИ-95', 'price': 48.90, 'cost': 43.50, 'octane_number': 95},
        {'name': 'АИ-98', 'price': 52.30, 'cost': 46.80, 'octane_number': 98},
        {'name': 'Дизель', 'price': 47.80, 'cost': 42.30, 'octane_number': 0},
        {'name': 'Газ', 'price': 28.40, 'cost': 24.10, 'octane_number': 0},
    ]
    for fuel in fuels:
        FuelType.objects.create(**fuel)

def create_employees():
    positions = ['Кассир', 'Оператор', 'Менеджер', 'Администратор', 'Заправщик']
    first_names = ['Иван', 'Алексей', 'Сергей', 'Дмитрий', 'Андрей', 'Елена', 'Ольга', 'Наталья']
    last_names = ['Иванов', 'Петров', 'Сидоров', 'Смирнов', 'Кузнецов', 'Васильева', 'Николаева']
    
    for i in range(8):
        username = f'employee{i+1}'
        user = User.objects.create_user(
            username=username,
            password='password123',
            first_name=random.choice(first_names),
            last_name=random.choice(last_names),
            email=f'{username}@gasstation.ru')
        
        Employee.objects.create(
            user=user,
            position=random.choice(positions),
            hire_date=timezone.now() - timedelta(days=random.randint(100, 1000)),
            salary=random.randint(30000, 60000),
            phone=f'+7915{random.randint(1000000, 9999999)}'
        )

def create_clients():
    first_names = ['Александр', 'Михаил', 'Артем', 'Анна', 'Мария', 'Екатерина']
    last_names = ['Соколов', 'Орлов', 'Лебедев', 'Воробьева', 'Голубева', 'Соловьева']
    
    for i in range(20):
        Client.objects.create(
            name=f"{random.choice(first_names)} {random.choice(last_names)}",
            phone=f"+7916{random.randint(1000000, 9999999)}",
            email=f"client{i+1}@example.com",
            discount=random.choice([0, 0, 0, 0, 5, 5, 10])  # 60% без скидки, 20% 5%, 20% 10%
        )

def create_stations():
    addresses = [
        "ул. Ленина, 10",
        "пр. Мира, 25",
        "ул. Гагарина, 42",
        "ш. Московское, 15 км"
    ]
    
    employees = list(Employee.objects.all())
    for i, address in enumerate(addresses):
        GasStation.objects.create(
            name=f"АЗС #{i+1}",
            address=address,
            opening_time=time(8, 0), 
            closing_time=time(22, 0),
            manager=random.choice(employees)
        )

def create_sales():
    fuels = list(FuelType.objects.all())
    employees = list(Employee.objects.all())
    stations = list(GasStation.objects.all())
    clients = list(Client.objects.all())
    payment_methods = ['cash', 'card', 'mobile']
    
    for i in range(60):
        days_ago = random.randint(0, 30)
        sale_date = timezone.now() - timezone.timedelta(days=days_ago)
        
        fuel = random.choice(fuels)
        volume = Decimal(str(random.uniform(10, 60)))  # Конвертируем float в Decimal
        
        # Создаем объект без сохранения
        sale = Sale(
            fuel=fuel,
            volume=volume,
            date=sale_date,
            employee=random.choice(employees),
            station=random.choice(stations),
            payment_method=random.choice(payment_methods),
            client=random.choice(clients + [None])
        )
        # Вызов save() автоматически рассчитает total_price
        sale.save()

def run():
    print("Создание типов топлива...")
    create_fuel_types()
    
    print("Создание сотрудников...")
    create_employees()
    
    print("Создание клиентов...")
    create_clients()
    
    print("Создание АЗС...")
    create_stations()
    
    print("Создание продаж...")
    create_sales()
    
    print("База данных успешно заполнена!")