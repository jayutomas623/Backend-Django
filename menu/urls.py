from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryListView, ProductListView, GranelViewSet, ExtraViewSet, CategoryViewSet, ProductManageViewSet

router = DefaultRouter()
router.register(r'granel', GranelViewSet, basename='granel')
router.register(r'extras', ExtraViewSet, basename='extras')
router.register(r'categorias-admin', CategoryViewSet, basename='categorias-admin')
router.register(r'productos-admin', ProductManageViewSet, basename='productos-admin')

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='menu-categories'),
    path('products/',   ProductListView.as_view(),  name='menu-products'),
    
    path('manage/', include(router.urls)),
]