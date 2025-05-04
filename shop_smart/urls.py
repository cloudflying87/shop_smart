from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from shopping import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.LandingPageView.as_view(), name='landing'),
    path('app/', include('shopping.urls')),
    
    # API endpoints that need to be at the root level
    path('api/items/search/', views.GroceryItemSearchView.as_view(), name='item_search'),
    path('api/items/barcode/<str:barcode>/', views.BarcodeSearchView.as_view(), name='barcode_search'),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='groceries/auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('password-reset/', 
         auth_views.PasswordResetView.as_view(template_name='groceries/auth/password_reset.html'), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='groceries/auth/password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(template_name='groceries/auth/password_reset_confirm.html'), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='groceries/auth/password_reset_complete.html'), 
         name='password_reset_complete'),
     
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
