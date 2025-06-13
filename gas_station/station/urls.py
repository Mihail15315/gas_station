from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Продажи
    path('sales/', views.SaleListView.as_view(), name='sale-list'),
    path('sales/<int:pk>/', views.SaleDetailView.as_view(), name='sale-detail'),
    path('sales/add/', views.SaleCreateView.as_view(), name='sale-create'),
    path('sales/<int:pk>/edit/', views.SaleUpdateView.as_view(), name='sale-update'),
    path('sales/<int:pk>/delete/', views.SaleDeleteView.as_view(), name='sale-delete'),
    
    # Клиенты
    path('clients/', views.ClientListView.as_view(), name='client-list'),
    
    # Отчеты
    path('reports/daily/', views.daily_report_pdf, name='daily-report-pdf'),
    path('reports/fuel-popularity/', views.fuel_popularity_report_pdf, name='fuel-popularity-report-pdf'),
]