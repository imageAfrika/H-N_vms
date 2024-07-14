from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    # Default admin urls
    path('admin/', admin.site.urls),
    
    # First page
    path('', RedirectView.as_view(url='/users/auth/login/', permanent=False)),

    # urlpatterns for users
    path('users/', include('users.urls')),

    # urlpatterns for services
    path('services/', include('services.urls')),
]
