from django.urls import path
from . import views

urlpatterns = [
    path("", views.session_list, name="report_session_list"),
    path("new/", views.create_session, name="create_report_session"),
    path("<uuid:pk>/", views.report_chat, name="report_chat"),
    path("<uuid:pk>/send/", views.send_message, name="send_chat_message"),
    path("<uuid:pk>/stream/", views.stream_response, name="stream_chat_response"),
    path("<uuid:pk>/delete/", views.delete_session, name="delete_report_session"),
    path("<uuid:pk>/rename/", views.rename_session, name="rename_report_session"),
]
