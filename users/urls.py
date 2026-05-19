from django.urls import path
from .views import (
    RegisterView, LoginView, LogoutView, MeView, CreateEmployeeView, 
    EmployeeListView, EmployeeDetailView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/',    LoginView.as_view(),    name='auth-login'),
    path('logout/',   LogoutView.as_view(),   name='auth-logout'),
    path('me/',       MeView.as_view(),       name='auth-me'),
    path('employee/', CreateEmployeeView.as_view(), name='auth-employee'),
    
    path('employees-list/', EmployeeListView.as_view(), name='employee-list'),
    path('employees/<int:pk>/', EmployeeDetailView.as_view(), name='employee-detail'),
]