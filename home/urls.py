from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from home import views
urlpatterns = [
    path("logins",views.logins,name='logins'),
    path("",views.index,name='home'),
    path("about",views.about,name='about'),
    path("services",views.services,name='services'),
    path("contact",views.contact,name='contact'),
    path("video",views.video,name='video'),
    path('admin-portal', views.admin_portal, name='admin_portal'),
    path('login/', views.logins, name='logins'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('delete-student/<int:student_id>/', views.delete_student, name='delete_student'),
    path('signup/', views.signup, name='signup')
]