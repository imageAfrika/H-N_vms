from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView

urlpatterns = [
    # Default admin urls
    path('admin/', admin.site.urls),
    
<<<<<<< HEAD
    # First page to open
=======
    # First page
>>>>>>> 9c75cf918a8d11a6d86766f04aa5a442974bdf76
    path('', RedirectView.as_view(url='/users/auth/login/', permanent=False)),

    # urlpatterns for users
    path('users/', include('users.urls')),

    # urlpatterns for services
    path('services/', include('services.urls')),
    
    

]


