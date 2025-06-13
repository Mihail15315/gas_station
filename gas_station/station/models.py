from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
class FuelType(models.Model):
    name = models.CharField(max_length=50, verbose_name="Тип топлива")
    price = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Цена за литр")
    cost = models.DecimalField(max_digits=8, decimal_places=2, verbose_name="Себестоимость за литр")
    octane_number = models.IntegerField(verbose_name="Октановое число")
    available = models.BooleanField(default=True, verbose_name="Доступно")
    
    @property
    def profit_per_liter(self):
        return self.price - self.cost
    
    def __str__(self):
        return f"{self.name} ({self.octane_number}) - {self.price} руб/л"

    class Meta:
        verbose_name = "Тип топлива"
        verbose_name_plural = "Типы топлива"

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.CharField(max_length=100, verbose_name="Должность")
    hire_date = models.DateField(verbose_name="Дата приема")
    salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Зарплата")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.position}"

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

class Client(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя")
    phone = models.CharField(max_length=20, verbose_name="Телефон", unique=True)
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name="Скидка (%)")
    registration_date = models.DateField(auto_now_add=True, verbose_name="Дата регистрации")
    
    def __str__(self):
        return f"{self.name} ({self.phone})"

    class Meta:
        verbose_name = "Клиент"
        verbose_name_plural = "Клиенты"

class GasStation(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название АЗС")
    address = models.TextField(verbose_name="Адрес")
    opening_time = models.TimeField(verbose_name="Время открытия")
    closing_time = models.TimeField(verbose_name="Время закрытия")
    manager = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, verbose_name="Менеджер")
    
    def __str__(self):
        return f"{self.name} ({self.address})"

    class Meta:
        verbose_name = "Автозаправка"
        verbose_name_plural = "Автозаправки"

class Sale(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
        ('mobile', 'Мобильное приложение'),
    ]
    
    fuel = models.ForeignKey(FuelType, on_delete=models.PROTECT, verbose_name="Топливо")
    volume = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Объем (л)")
    total_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Общая стоимость")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата продажи")
    employee = models.ForeignKey(Employee, on_delete=models.PROTECT, verbose_name="Сотрудник")
    station = models.ForeignKey(GasStation, on_delete=models.PROTECT, verbose_name="АЗС")
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, verbose_name="Способ оплаты")
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Клиент")
    
    @property
    def profit(self):
        return (self.fuel.price - self.fuel.cost) * self.volume
    
    def save(self, *args, **kwargs):
        # Конвертируем discount в Decimal перед вычислениями
        discount = Decimal(self.client.discount if self.client else 0)
        self.total_price = self.fuel.price * self.volume * (Decimal('1') - discount / Decimal('100'))
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Продажа #{self.id} - {self.fuel.name} {self.volume}л"

    class Meta:
        verbose_name = "Продажа"
        verbose_name_plural = "Продажи"
        ordering = ['-date']