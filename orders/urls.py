from django.urls import path
from .views import (
    CreateOrderView, OrderStatusView, ConfirmPaymentView, CancelOrderView,
    # Monitor general
    MonitorOrdersView,
    # Panel cajero
    CashierListView, CashierSearchView,
    # Sprint 4 stats
    DashboardStatsView, WeeklySalesView, HeatmapView, TopProductsView,
)

urlpatterns = [
    # ── Flujo base ──────────────────────────────────────────────────────────
    path('',                               CreateOrderView.as_view(),    name='order-create'),
    path('<int:pk>/',                      OrderStatusView.as_view(),    name='order-status'),
    path('<uuid:codigo>/confirm-payment/', ConfirmPaymentView.as_view(), name='order-confirm-payment'),
    path('kitchen/<int:pk>/cancel/',       CancelOrderView.as_view(),    name='kitchen-cancel'),

    # ── Monitor general (todos los roles) ───────────────────────────────────
    path('monitor/',             MonitorOrdersView.as_view(), name='monitor-list'),
    path('monitor/<int:pk>/action/', MonitorOrdersView.as_view(), name='monitor-action'),

    # ── Panel cajero ────────────────────────────────────────────────────────
    path('cashier-list/',   CashierListView.as_view(),   name='cashier-list'),
    path('cashier-search/', CashierSearchView.as_view(), name='cashier-search'),

    # ── Sprint 4 stats ──────────────────────────────────────────────────────
    path('stats/dashboard/',    DashboardStatsView.as_view(), name='stats-dashboard'),
    path('stats/weekly/',       WeeklySalesView.as_view(),    name='stats-weekly'),
    path('stats/heatmap/',      HeatmapView.as_view(),        name='stats-heatmap'),
    path('stats/top-products/', TopProductsView.as_view(),    name='stats-top-products'),
]