from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from home import views
urlpatterns = [
    path("logins",views.logins,name='logins'),
    path("",views.index,name='home'),
    path("admin/legacy/save/",views.save_legacy_record,name="save_legacy"),
    path("about",views.about,name='about'),
    path("instructor_login/", views.instructor_login, name="instructor_login"),
    path("admin-portal/", views.admin_portal, name="admin_portal"),
    path("logout/", views.instructor_logout, name="logout"),
    path("services",views.services,name='services'),
    path("api/attendance-data/", views.attendance_data_api, name="attendance_data_api"),
    path("contact",views.contact,name='contact'),
    path("video",views.video,name='video'),
    path('admin-portal/', views.admin_portal, name='admin_portal'),
    path('save-attendance/', views.save_attendance, name='save_attendance'),
    path('login/', views.logins, name='logins'),
    path("api/student/<int:student_id>/", views.admin_student_detail, name="admin_student_detail"),
    path("api/legacy/save/", views.api_save_legacy, name="api_save_legacy"),
    path('delete-attendance/<int:id>/', views.delete_attendance, name='delete_attendance'),
    path('get-students/', views.get_students, name='get_students'),
    path('signup/', views.signup, name='signup'),
    path("schedule",views.schedule,name='schedule'),
    path('get-logged-in-students/', views.get_logged_in_students, name='get_logged_in_students'),
    path('export-attendance/', views.export_attendance, name='export_attendance')
]