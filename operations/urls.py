from django.urls import path
from . import views

urlpatterns = [
    # Public Landing Page
    path("", views.home, name="home"),

    # Authentication
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Central Dashboard Dispatcher
    path("dashboard/", views.dashboard_redirect, name="dashboard"),
    path("dashboard/redirect/", views.dashboard_redirect, name="dashboard_redirect"),

    # Role-Specific Dashboards
    path("dashboard/inspector/", views.inspector_dashboard, name="inspector_dashboard"),
    path("dashboard/supervisor/", views.supervisor_dashboard, name="supervisor_dashboard"),
    path("dashboard/admin/", views.admin_dashboard, name="admin_dashboard"),

    # Feature 2: Inspection Management
    path("inspections/create/", views.inspection_create, name="inspection_create"),
    path("inspections/<int:pk>/", views.inspection_detail, name="inspection_detail"),

    # Feature 3: Supervisor Review
    path("inspections/<int:pk>/review/", views.inspection_review, name="inspection_review"),

    # Feature 4: Dispatch Clearance & Process Holds
    path("jobs/create/", views.job_create, name="job_create"),
    path("jobs/<int:pk>/", views.job_detail, name="job_detail"),
    path("jobs/<int:pk>/certificate/", views.job_certificate, name="job_certificate"),
    path("jobs/<int:pk>/clear-dispatch/", views.clear_dispatch, name="clear_dispatch"),
    path("jobs/<int:pk>/hold/", views.place_hold, name="place_hold"),
    path("holds/<int:pk>/release/", views.release_hold, name="release_hold"),

    # Enterprise Data Exports
    path("export/inspections/", views.export_inspections_csv, name="export_inspections_csv"),
    path("export/jobs/", views.export_jobs_csv, name="export_jobs_csv"),
]
