"""
URL configuration for AL-QATHIFI Men's Shoe Store
"""

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'shoes_view'

urlpatterns = [
    # Home and main pages
    path('', views.home, name='home'),
    path('products/', views.products, name='products'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('brand/<int:brand_id>/', views.brand_products, name='brand_products'),
    
    # Cart and checkout
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-quantity/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cancel-order/<uuid:order_id>/', views.cancel_order, name='cancel_order'),
    path('reorder/<uuid:order_id>/', views.reorder, name='reorder'),
    path('checkout/', views.checkout, name='checkout'),
    path('order-confirmation/<uuid:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('order-detail/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('print-order/<uuid:order_id>/', views.print_order, name='print_order'),
    
    # Wheel of Fortune
    path('wheel/', views.wheel_of_fortune, name='wheel'),
    path('wheel-api-v2/', views.wheel_api_v2, name='wheel_api_v2'),
    
    # User authentication and profile
    path('register/', views.user_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.user_profile, name='profile'),
    path('get-cart-content/', views.get_cart_content, name='get_cart_content'),
    
    # Password reset URLs
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             success_url='/password-reset-done/'
         ), 
         name='password_reset'),
    
    path('password-reset-done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url='/password-reset-complete/'
         ), 
         name='password_reset_confirm'),
    
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
    
    # Contact and information
    path('contact/', views.contact, name='contact'),
    
    # Language switching
    path('set-language/', views.set_language, name='set_language'),
    
    # AJAX endpoints
    path('search-suggestions/', views.search_suggestions, name='search_suggestions'),
    path('api/cart-count/', views.cart_count_api, name='cart_count_api'),
    
    # SEO and robots
    path('robots.txt', views.robots_txt, name='robots_txt'),
] 

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 