from django.contrib import admin
from django.urls import path, include
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), 
    path('', include('billing.urls')), # include copia todo los url de la urls  de billing  - aplica para los tres include
]

