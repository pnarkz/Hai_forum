
#forumprojesi\urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.permissions import IsAdminUser
# Swagger
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.contrib.auth.decorators import user_passes_test
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings
from django.conf.urls.static import static

schema_view = get_schema_view(
   openapi.Info(
      title="Forum API",
      default_version='v1',
      description="Forum uygulaması için API dokümantasyonu",
   ),
   public=True,
   permission_classes=[permissions.AllowAny],
)

urlpatterns = [
   path('admin/', admin.site.urls),
   path('', include('forum.urls')),  # Forum uygulaması ana sayfa
   # project/urls.py
   path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
   path('api/', include('forum.api.urls')),  # API endpointleri
   path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
   # Swagger Dokümantasyonu
   path('swagger/', user_passes_test(lambda u: u.is_staff)(schema_view.with_ui('swagger', cache_timeout=0)), name='schema-swagger-ui'),
   path('redoc/', user_passes_test(lambda u: u.is_staff)(schema_view.with_ui('redoc', cache_timeout=0)), name='schema-redoc'),

   # Ana sayfa yönlendirmesi
   path('', RedirectView.as_view(url='/topics/', permanent=False)),
   
]

if settings.DEBUG:
   urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)