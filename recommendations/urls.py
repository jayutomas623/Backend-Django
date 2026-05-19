from django.urls import path
from .views import ChatbotView, RecommendProductsView

urlpatterns = [
    path('chatbot/', ChatbotView.as_view(), name='chatbot'),
    path('suggest/<int:producto_id>/', RecommendProductsView.as_view(), name='recommender'),
]