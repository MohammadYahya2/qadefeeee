# shoes/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language

# ==============================================================================
#                              مسارات URL الأساسية
# ==============================================================================
urlpatterns = [
    # مسار مخصص للوحة التحكم
    path('admin/custom/', include('shoes_view.admin_urls')),
    # المسار الرئيسي للوحة تحكم Django
    path('admin/', admin.site.urls),
    # مسار لتبديل اللغة
    path('i18n/setlang/', set_language, name='set_language'),
    # مسارات التطبيق الرئيسي (يجب أن يكون في النهاية)
    path('', include('shoes_view.urls')),
]

# ==============================================================================
#  إضافة مسارات لتقديم ملفات الميديا والملفات الثابتة
#  هذا الإعداد ضروري لتعمل الصور والملفات على استضافة cPanel
#  عندما يكون DEBUG = False
# ==============================================================================
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
