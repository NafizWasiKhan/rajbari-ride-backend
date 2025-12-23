from django.urls import path
from .views import RegisterView, LoginView, LogoutView, UpdateLocationView, ProfileToggleOnlineView, UserProfileView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('location/', UpdateLocationView.as_view(), name='update-location'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/toggle-online/', ProfileToggleOnlineView.as_view(), name='toggle-online'),
]
