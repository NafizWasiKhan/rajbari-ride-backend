from django.urls import path
from .views import (
    FareEstimateView, RideCreateView, RideUpdateStatusView, RideDetailView, 
    DriverActionView, ScheduledRideCreateView, ScheduledRideListView,
    RequestSeatView, HandleSeatRequestView, MyScheduledRequestsView,
    AvailableRidesView, SendMessageView, ListMessagesView, UserChatsView,
    RideHistoryView, DriverStatsView, MyRideRequestsView, RideCancelView, RideUpdateView,
    CurrentRideView
)

urlpatterns = [
    path('current/', CurrentRideView.as_view(), name='current-ride'),
    path('fare-estimate/', FareEstimateView.as_view(), name='fare-estimate'),
    path('create/', RideCreateView.as_view(), name='ride-create'),
    path('<int:pk>/status/', RideUpdateStatusView.as_view(), name='ride-update-status'),
    path('<int:pk>/', RideDetailView.as_view(), name='ride-detail'),
    path('<int:pk>/action/', DriverActionView.as_view(), name='driver-action'),
    path('available/', AvailableRidesView.as_view(), name='available-rides'),
    path('my-requests/', MyRideRequestsView.as_view(), name='my-ride-requests'),
    path('<int:pk>/cancel/', RideCancelView.as_view(), name='ride-cancel'),
    path('<int:pk>/update/', RideUpdateView.as_view(), name='ride-update'),
    
    # Scheduled Rides
    path('scheduled/create/', ScheduledRideCreateView.as_view(), name='scheduled-create'),
    path('scheduled/list/', ScheduledRideListView.as_view(), name='scheduled-list'),
    path('scheduled/request-seat/', RequestSeatView.as_view(), name='request-seat'),
    path('scheduled/handle-request/<int:pk>/', HandleSeatRequestView.as_view(), name='handle-seat-request'),
    # Messaging
    path('messages/send/', SendMessageView.as_view(), name='send-message'),
    path('messages/', ListMessagesView.as_view(), name='list-messages'),
    path('chats/', UserChatsView.as_view(), name='user-chats'),
    path('history/', RideHistoryView.as_view(), name='ride-history'),
    path('stats/', DriverStatsView.as_view(), name='driver-stats'),
    path('scheduled/my-requests/', MyScheduledRequestsView.as_view(), name='my-scheduled-requests'),
]
