from django.urls import path

from BuildCron.views import *
from rest_framework_simplejwt import views as jwt_views
urlpatterns = [
    path('token/obtain/', jwt_views.TokenObtainPairView.as_view(), name='token_create'),  # override sjwt stock token
    path('token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegistrationView.as_view(), name="user register"),
    # path('admin_register/', AdminRegistration.as_view(), name=" admin user register"),
    #
    # path('admin_login/', AdminLogin.as_view(), name="admin user login"),  # admin loging and change password
    path('checklist/', ChecklistView.as_view(), name="Checklist Data"),
    path('questions/', QuestionsView.as_view(), name="Question Data"),
    path('material/', MaterialsView.as_view(), name="Material Data"),
    path('queries/', QueriesView.as_view(), name="Queries Data"),

    path('login/', Login.as_view(), name="user login"),
    path('licenses/', LicensesView.as_view(), name="user Licenses"),
    #path('logout/', Logout.as_view(), name="user logout"),


]





