from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth import login
from .models import *
from .forms import (
    SignUpForm, BrandForm, ProductGroupForm, SupplierForm,
    ProductForm, CustomerForm, InvoiceForm, InvoiceDetailFormSet
)
from .mixins import ExportListMixin
from django.utils import timezone
from decimal import Decimal

# === REGISTRO ===
class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'registration/signup.html'  
    success_url = reverse_lazy('billing:brand_list')
    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

# === BRAND (FBV) ===
@login_required
def brand_list(request):
    brands = Brand.objects.all()
    return render(request, 'billing/brand_list.html', {'brands': brands})

@login_required
def brand_create(request):
    if request.method == 'POST':
        form = BrandForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Marca Creada exitosamente!')
            return redirect('billing:brand_list')
    else: form = BrandForm()
    return render(request, 'billing/brand_form.html', {'form':form, 'title':'Crear Marca'})

@login_required
def brand_update(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        form = BrandForm(request.POST, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(request, 'Marca actulizada exitosamente!')
            return redirect('billing:brand_list')
    else: form = BrandForm(instance=brand)
    return render(request, 'billing/brand_form.html', {'form':form, 'title':'Editar Marca'})

@login_required
def brand_delete(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        brand.delete()
        messages.success(request, 'Brand eliminada exitosamente!')
        return redirect('billing:brand_list')
    return render(request, 'billing/brand_confirm_delete.html', {'object': brand})

# === PRODUCTGROUP (CBV) ===
class ProductGroupListView(LoginRequiredMixin, ListView):
    model = ProductGroup; 
    template_name = 'billing/product_group_list.html'; 
    context_object_name = 'items'

class ProductGroupCreateView(LoginRequiredMixin, CreateView):
    model = ProductGroup; 
    form_class = ProductGroupForm; 
    template_name = 'billing/product_group_form.html'; 
    success_url = reverse_lazy('billing:productgroup_list')

class ProductGroupUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductGroup; 
    form_class = ProductGroupForm; 
    template_name = 'billing/product_group_form.html'; 
    success_url = reverse_lazy('billing:productgroup_list')

class ProductGroupDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductGroup; 
    template_name = 'billing/product_group_confirm_delete.html'; 
    success_url = reverse_lazy('billing:productgroup_list')

# === SUPPLIER (CBV) ===
class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier; template_name = 'billing/supplier_list.html'; context_object_name = 'items'
class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier; form_class = SupplierForm; template_name = 'billing/supplier_form.html'; success_url = reverse_lazy('billing:supplier_list')
class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier; form_class = SupplierForm; template_name = 'billing/supplier_form.html'; success_url = reverse_lazy('billing:supplier_list')
class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = Supplier; template_name = 'billing/supplier_confirm_delete.html'; success_url = reverse_lazy('billing:supplier_list')


# === PRODUCT (CBV) ===
class ProductListView(ExportListMixin, LoginRequiredMixin, ListView):
    model = Product
    template_name = 'billing/product_list.html'
    context_object_name = 'items'
    paginate_by = 3

    export_title = 'Productos'

    # === ÚNICA fuente de configuración de columnas ===
    # (key, etiqueta, accessor de exportación). La tabla, el PDF y el Excel
    # leen de aquí para mostrar/exportar exactamente la misma información.
    COLUMN_DEFS = [
        ('image',      'Imagen',         lambda o: 'Con imagen' if o.image else 'Sin imagen'),
        ('name',       'Nombre',         'name'),
        ('description', 'Descripción',   lambda o: o.description or '-'),
        ('brand',      'Marca',          'brand.name'),
        ('group',      'Grupo',          'group.name'),
        ('price',      'Precio',         lambda o: f'{o.unit_price:.2f}'),
        ('stock',      'Stock',          'stock'),
        ('balance',    'Balance',        lambda o: f'{o.balance:.2f}'),
        ('suppliers',  'Proveedores',    lambda o: ', '.join(s.name for s in o.suppliers.all()) or '-'),
        ('is_active',  'Estado',         lambda o: 'Activo' if o.is_active else 'Inactivo'),
        ('created_at', 'Fecha creación', lambda o: timezone.localtime(o.created_at).strftime('%d/%m/%Y %H:%M')),
    ]
    DEFAULT_COLUMNS = ['image', 'name', 'brand', 'group', 'price', 'stock', 'balance', 'suppliers', 'is_active']
    COLUMNS_SESSION_KEY = 'product_visible_columns'

    def get_visible_columns(self):
        """Devuelve la lista de keys de columnas visibles (orden canónico).

        Fuente de verdad persistida en sesión. Se actualiza cuando llegan
        parámetros ``columns`` (Aplicar) o ``reset_columns`` (Restablecer)."""
        all_keys = [c[0] for c in self.COLUMN_DEFS]
        session = self.request.session
        get = self.request.GET

        if 'reset_columns' in get:
            session.pop(self.COLUMNS_SESSION_KEY, None)
            return list(self.DEFAULT_COLUMNS)

        if 'columns' in get:
            selected = [k for k in get.getlist('columns') if k in all_keys]
            if not selected:                       # mínimo obligatorio: 1 columna
                selected = list(self.DEFAULT_COLUMNS)
            selected = [k for k in all_keys if k in selected]  # orden canónico
            session[self.COLUMNS_SESSION_KEY] = selected
            return selected

        saved = session.get(self.COLUMNS_SESSION_KEY)
        if saved:
            return [k for k in all_keys if k in saved]
        return list(self.DEFAULT_COLUMNS)

    def get_export_fields(self):
        """Solo las columnas visibles, en el mismo orden que el listado."""
        visible = self.get_visible_columns()
        return [(label, acc) for key, label, acc in self.COLUMN_DEFS if key in visible]

    def get_queryset(self):
        qs = Product.objects.select_related('brand', 'group').prefetch_related('suppliers')
        g = self.request.GET
        if name := g.get('name', '').strip():
            qs = qs.filter(name__icontains=name)
        if brand := g.get('brand', ''):
            qs = qs.filter(brand_id=brand)
        if group := g.get('group', ''):
            qs = qs.filter(group_id=group)
        if price_min := g.get('price_min', '').strip():
            qs = qs.filter(unit_price__gte=price_min)
        if price_max := g.get('price_max', '').strip():
            qs = qs.filter(unit_price__lte=price_max)
        if stock_min := g.get('stock_min', '').strip():
            qs = qs.filter(stock__gte=stock_min)
        if stock_max := g.get('stock_max', '').strip():
            qs = qs.filter(stock__lte=stock_max)
        if (is_active := g.get('is_active', '')) in ('0', '1'):
            qs = qs.filter(is_active=is_active == '1')
        if supplier := g.get('supplier', ''):
            qs = qs.filter(suppliers__id=supplier).distinct()
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['brands'] = Brand.objects.order_by('name')
        ctx['groups'] = ProductGroup.objects.order_by('name')
        ctx['suppliers'] = Supplier.objects.order_by('name')
        params = self.request.GET.copy()
        params.pop('page', None)
        params.pop('reset_columns', None)
        ctx['search_params'] = params.urlencode()

        # --- Configuración de columnas visibles (modal + tabla) ---
        visible = self.get_visible_columns()
        ctx['visible_columns'] = visible
        ctx['column_defs'] = [
            {'key': k, 'label': label, 'visible': k in visible}
            for k, label, _ in self.COLUMN_DEFS
        ]
        ctx['visible_count'] = len(visible)
        ctx['total_columns'] = len(self.COLUMN_DEFS)
        # Filtros activos (para conservarlos al aplicar columnas, sin page/columns)
        ctx['filter_items'] = [
            (k, v) for k, v in self.request.GET.items()
            if k not in ('columns', 'page', 'reset_columns')
        ]
        return ctx
class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'billing/product_detail.html'
    context_object_name = 'product'
    queryset = Product.objects.select_related('brand', 'group').prefetch_related('suppliers')
class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product; form_class = ProductForm; template_name = 'billing/product_form.html'; success_url = reverse_lazy('billing:product_list')
class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product; form_class = ProductForm; template_name = 'billing/product_form.html'; success_url = reverse_lazy('billing:product_list')
class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product; template_name = 'billing/product_confirm_delete.html'; success_url = reverse_lazy('billing:product_list')


# === CUSTOMER (CBV) ===
class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer; template_name = 'billing/customer_list.html'; context_object_name = 'items'
class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer; form_class = CustomerForm; template_name = 'billing/customer_form.html'; success_url = reverse_lazy('billing:customer_list')
class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer; form_class = CustomerForm; template_name = 'billing/customer_form.html'; success_url = reverse_lazy('billing:customer_list')
class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer; template_name = 'billing/customer_confirm_delete.html'; success_url = reverse_lazy('billing:customer_list')


# === INVOICE (CBV) ===
class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice; template_name = 'billing/invoice_list.html'; context_object_name = 'items'
@login_required
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceDetailFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            formset.instance = invoice
            formset.save()

            subtotal = sum(d.subtotal for d in invoice.details.all())
            invoice.subtotal = subtotal
            invoice.tax = subtotal * Decimal('0.15')
            invoice.total = invoice.subtotal + invoice.tax
            invoice.save()

            messages.success(request, f'Factura #{invoice.id} creada! Total: ${invoice.total}')
            return redirect('billing:invoice_list')
    else:
        form = InvoiceForm()
        formset = InvoiceDetailFormSet()
    return render(request, 'billing/invoice_form.html', {
        'form': form, 'formset': formset, 'title': 'Nueva Factura'
    })
class InvoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = Invoice; template_name = 'billing/invoice_confirm_delete.html'; success_url = reverse_lazy('billing:invoice_list')