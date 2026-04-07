from django.urls import path
from .views import (
    CreateOrderView, OrderStatusView,
    ConfirmPaymentView, KitchenOrdersView, CashierOrdersView
)

urlpatterns = [
    path('',                               CreateOrderView.as_view(),    name='order-create'),
    path('<int:pk>/',                      OrderStatusView.as_view(),    name='order-status'),
    path('<uuid:codigo>/confirm-payment/', ConfirmPaymentView.as_view(), name='order-confirm-payment'),
    path('kitchen/',                       KitchenOrdersView.as_view(),  name='kitchen-orders'),
    path('kitchen/<int:pk>/ready/',        KitchenOrdersView.as_view(),  name='kitchen-ready'),
    path('cashier/',                       CashierOrdersView.as_view(),  name='cashier-orders'),
    path('cashier/<int:pk>/deliver/',      CashierOrdersView.as_view(),  name='cashier-deliver'),
]