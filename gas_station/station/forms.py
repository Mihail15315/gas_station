from django import forms
from .models import *

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['fuel', 'volume', 'station', 'payment_method', 'client']
        widgets = {
            'volume': forms.NumberInput(attrs={'step': '0.1'}),
        }

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'phone', 'email', 'discount']
        widgets = {
            'discount': forms.NumberInput(attrs={'min': '0', 'max': '20', 'step': '0.5'}),
        }

class FuelTypeForm(forms.ModelForm):
    class Meta:
        model = FuelType
        fields = ['name', 'price', 'cost', 'octane_number', 'available']
        widgets = {
            'price': forms.NumberInput(attrs={'step': '0.01'}),
            'cost': forms.NumberInput(attrs={'step': '0.01'}),
        }