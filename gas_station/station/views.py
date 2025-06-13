from io import BytesIO
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, Count, F, ExpressionWrapper, DecimalField
from django.db.models.functions import TruncDay
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from datetime import datetime, timedelta
from django.db.models.functions import ExtractHour
from .models import *
from .forms import *
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from django.core.paginator import Paginator
from reportlab.pdfbase import pdfmetrics
from django.utils import timezone
from reportlab.pdfbase.ttfonts import TTFont
class SaleListView(ListView):
    model = Sale
    template_name = 'station/sale_list.html'
    paginate_by = 50  # Показывать 50 записей на странице
    ordering = ['-date']  # Сортировка по дате
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('fuel', 'employee', 'station', 'client')
        
        # Фильтрация по дате
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Фильтрация по типу топлива
        fuel_type = self.request.GET.get('fuel_type')
        if fuel_type:
            queryset = queryset.filter(fuel_id=fuel_type)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fuel_types'] = FuelType.objects.all()
        return context

class SaleDetailView(LoginRequiredMixin, DetailView):
    model = Sale
    template_name = 'station/sale_detail.html'
    context_object_name = 'sale'

class SaleCreateView(LoginRequiredMixin, CreateView):
    model = Sale
    form_class = SaleForm
    template_name = 'station/sale_form.html'
    success_url = reverse_lazy('sale-list')
    
    def form_valid(self, form):
        form.instance.employee = self.request.user.employee
        return super().form_valid(form)

class SaleUpdateView(LoginRequiredMixin, UpdateView):
    model = Sale
    form_class = SaleForm
    template_name = 'station/sale_form.html'
    success_url = reverse_lazy('sale-list')

class SaleDeleteView(LoginRequiredMixin, DeleteView):
    model = Sale
    template_name = 'station/sale_confirm_delete.html'
    success_url = reverse_lazy('sale-list')

class ClientListView(ListView):
    model = Client
    template_name = 'station/client_list.html'
    paginate_by = 20
    ordering = ['-id']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Поиск по имени
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(name__icontains=search_query)
        
        # Поиск по телефону
        phone_query = self.request.GET.get('phone')
        if phone_query:
            queryset = queryset.filter(phone__icontains=phone_query)
        
        return queryset

def dashboard(request):
    # Статистика за последние 7 дней
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # График 1: Динамика продаж по дням
    daily_sales = Sale.objects.filter(
        date__gte=start_date
    ).annotate(
        day=TruncDay('date')
    ).values('day').annotate(
        total_volume=Sum('volume'),
        total_sales=Sum('total_price'),
        total_profit=Sum(ExpressionWrapper(
            F('volume') * (F('fuel__price') - F('fuel__cost')),
            output_field=DecimalField()
        ))
    ).order_by('day')
    
    # График 2: Распределение продаж по типам топлива
    fuel_sales = Sale.objects.values(
        'fuel__name'
    ).annotate(
        total_volume=Sum('volume'),
        total_sales=Sum('total_price'),
        total_profit=Sum(ExpressionWrapper(
            F('volume') * (F('fuel__price') - F('fuel__cost')),
            output_field=DecimalField()
        ))
    ).order_by('-total_sales')
    
    # Рекомендации для увеличения прибыли
    recommendations = []
    
    # 1. Анализ популярности топлива
    most_profitable_fuel = max(fuel_sales, key=lambda x: x['total_profit'])
    least_profitable_fuel = min(fuel_sales, key=lambda x: x['total_profit'])
    
    recommendations.append(
        f"Самый прибыльный вид топлива: {most_profitable_fuel['fuel__name']} "
        f"(прибыль: {most_profitable_fuel['total_profit']:.2f} руб). "
        f"Рекомендуется увеличить его продвижение."
    )
    
    recommendations.append(
        f"Наименее прибыльный вид топлива: {least_profitable_fuel['fuel__name']}. "
        f"Рассмотрите возможность увеличения цены или снижения закупочной стоимости."
    )
    
    # 2. Анализ клиентов
    top_clients = Client.objects.annotate(
        total_purchases=Count('sale'),
        total_spent=Sum('sale__total_price')
    ).order_by('-total_spent')[:3]
    
    if top_clients:
        recommendations.append(
            "Топовые клиенты: " + ", ".join(
                f"{client.name} ({client.total_spent:.2f} руб)" 
                for client in top_clients
            ) + ". Рекомендуется предложить им персональные скидки или бонусы."
        )
    
    # 3. Анализ времени продаж
    hourly_sales = Sale.objects.annotate(
        hour=ExtractHour('date')
    ).values('hour').annotate(
        total_sales=Sum('total_price')
    ).order_by('hour')
    
    peak_hour = max(hourly_sales, key=lambda x: x['total_sales'])['hour']
    recommendations.append(
        f"Пиковый час продаж: {peak_hour}:00. "
        "Рекомендуется увеличить количество сотрудников в это время."
    )
    
    context = {
        'daily_sales': daily_sales,
        'fuel_sales': fuel_sales,
        'recommendations': recommendations,
    }
    
    return render(request, 'station/dashboard.html', context)

def daily_report_pdf(request):
    """
    PDF
    """
    try:
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.setFont("Helvetica", 12)
        
        today = timezone.now().date()
        p.drawString(100, 800, "Daily Sales Report")
        p.drawString(100, 785, f"Date: {today}")
        p.drawString(100, 770, f"Total sales: {Sale.objects.filter(date__date=today).count()}")
        p.line(100, 765, 500, 765)
        
        y = 750
        sales = Sale.objects.filter(date__date=today).select_related('fuel')
        for sale in sales:
            fuel_name = "AI-92" if "АИ-92" in sale.fuel.name else \
                      "AI-95" if "АИ-95" in sale.fuel.name else \
                      "AI-98" if "АИ-98" in sale.fuel.name else \
                      "Diesel" if "Дизель" in sale.fuel.name else "Gas"
            
            text = f"{fuel_name}: {sale.volume:.2f}L - {sale.total_price:.2f}RUB"
            p.drawString(100, y, text)
            y -= 15
            if y < 50:
                p.showPage()
                y = 800
                p.setFont("Helvetica", 12)
        
        p.save()
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'daily_report_{today}.pdf'
        return response
    except Exception as e:
        return HttpResponse(f"Error generating report: {str(e)}", status=500)


def fuel_popularity_report_pdf(request):
    """
    Генерация отчета по популярности топлива в PDF
    """
    try:
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.setFont("Helvetica", 14)
        p.drawString(100, 800, "Fuel Popularity Ranking Report")
        p.setFont("Helvetica", 10)
        p.drawString(100, 785, "Sorted by total sales volume")
        p.line(100, 780, 500, 780)
        
        p.setFont("Helvetica", 12)
        y = 760
        fuels = FuelType.objects.annotate(
            total_volume=Sum('sale__volume'),
            total_revenue=Sum('sale__total_price')
        ).order_by('-total_volume')
        
        for fuel in fuels:
            fuel_name = "AI-92" if "АИ-92" in fuel.name else \
                      "AI-95" if "АИ-95" in fuel.name else \
                      "AI-98" if "АИ-98" in fuel.name else \
                      "Diesel" if "Дизель" in fuel.name else "Gas"
            
            p.drawString(100, y, f"{fuel_name}:")
            p.drawString(220, y, f"{fuel.total_volume or 0:.2f}L sold")
            p.drawString(350, y, f"{fuel.total_revenue or 0:.2f}RUB revenue")
            y -= 20
            if y < 50:
                p.showPage()
                y = 800
                p.setFont("Helvetica", 12)
        
        p.save()
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'fuel_popularity_report.pdf'
        return response
    except Exception as e:
        return HttpResponse(f"Error generating report: {str(e)}", status=500)