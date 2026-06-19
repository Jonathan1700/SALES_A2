from django import forms
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Brand, ProductGroup, Supplier, Product, Customer, Invoice, InvoiceDetail


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields:
            self.fields[f].widget.attrs['class'] = 'form-control'


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductGroupForm(forms.ModelForm):
    class Meta:
        model = ProductGroup
        fields = ['name', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'contact_name', 'email', 'phone', 'address', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductForm(forms.ModelForm):
    """Formulario centralizado de Producto: widgets, estilos, ayudas y validación.

    Toda la configuración visual y de validación vive aquí (no en las vistas),
    para que ProductCreateView y ProductUpdateView la reutilicen sin duplicar."""

    class Meta:
        model = Product
        fields = ['name', 'description', 'image', 'brand', 'group', 'suppliers', 'unit_price', 'stock', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 'placeholder': 'Ej. Teclado mecánico RGB',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Descripción opcional del producto...',
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'form-control', 'accept': 'image/*', 'id': 'id_image',
            }),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'group': forms.Select(attrs={'class': 'form-select'}),
            'suppliers': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control', 'step': '0.01', 'min': '0.01',
                'placeholder': '0.00', 'id': 'id_unit_price',
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control', 'min': '0', 'placeholder': '0', 'id': 'id_stock',
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'name': 'Nombre con el que se identifica el producto.',
            'image': 'Formatos de imagen (JPG, PNG, WEBP). Opcional.',
            'suppliers': 'Mantén Ctrl para seleccionar varios proveedores.',
            'unit_price': 'Debe ser mayor que cero. Ej. 10.50',
            'stock': 'Cantidad disponible en inventario.',
        }
        error_messages = {
            'name': {'required': 'El nombre del producto es obligatorio.'},
            'brand': {'required': 'Selecciona una marca.'},
            'group': {'required': 'Selecciona un grupo.'},
            'unit_price': {
                'required': 'El precio unitario es obligatorio.',
                'invalid': 'Ingresa un valor numérico válido.',
            },
            'stock': {'invalid': 'El stock debe ser un número entero.'},
        }

    def clean_unit_price(self):
        """Validación de servidor: precio estrictamente mayor que cero."""
        price = self.cleaned_data.get('unit_price')
        if price is not None and price <= 0:
            raise forms.ValidationError('El precio unitario debe ser mayor que cero.')
        return price

    def clean_stock(self):
        stock = self.cleaned_data.get('stock')
        if stock is not None and stock < 0:
            raise forms.ValidationError('El stock no puede ser negativo.')
        return stock


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['dni', 'first_name', 'last_name', 'email', 'phone', 'address', 'is_active']
        widgets = {
            'dni': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['customer']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
        }


InvoiceDetailFormSet = inlineformset_factory(
    Invoice,
    InvoiceDetail,
    fields=['product', 'quantity', 'unit_price'],
    extra=3,
    can_delete=True,
    widgets={
        'product': forms.Select(attrs={'class': 'form-select'}),
        'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
    }
)