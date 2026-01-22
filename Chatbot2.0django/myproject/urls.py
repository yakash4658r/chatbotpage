from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views # Itha marakaama import pannunga

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Intha rendu line thaan mukkiyam - 'name' correct-ah irukanum
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    path('', include('chatbot.urls')),
]
