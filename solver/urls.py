# core/urls.py

from django.urls import path
from .views import api_solve_math_problem,math_solver_view,login_view,logout_view,api_login,api_logout,api_profile,api_register,user_math_problems


urlpatterns = [

    path('api/solve/', api_solve_math_problem, name='api_solve_math'),
    path('api/user/problems/', user_math_problems, name='user_math_problems'),
    path('api/login/', api_login, name='api_login'),
    path('api/logout/', api_logout, name='api_logout'),
    path('api/register/', api_register, name='api_register'),
    path('api/profile/', api_profile, name='api_profile'),
    path('solver/', math_solver_view, name='math_solver'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
]
