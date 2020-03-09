from django.urls import path, re_path
from django.contrib import admin
from . import views

app_name = 'mplate_decoder'
urlpatterns = [
    path('decode/', views.MplateCreate.as_view(),
         name='mplate_create'),

    re_path(r'^(?P<chassis_number_short>[0-9]{7,8})/$',
            views.MplateRetrieve.as_view(),
            name='mplate_retrieve'),
    re_path(r'^(?P<chassis_number_short>[0-9]{7,8})/update/$',
            views.MplateUpdate.as_view(),
            name='mplate_update'),
    re_path(r'^(?P<chassis_number_short>[0-9]{7,8})/delete/$',
            views.MplateDelete.as_view(),
            name='mplate_delete'),
    path('mine/', views.MplatesByUserListView.as_view(),
         name='mplate_mine'),
    path('', views.MplateIndex.as_view(),
         name='mplate_index'),
    path('about/', views.MplateAbout.as_view(),
         name='mplate_about'),
    path('search/', views.SearchResultsView.as_view(),
         name='search_results'),
]

SITE_NAME = "VW Type 2 ID"
admin.site.site_header = f"{SITE_NAME} Admin"
admin.site.site_title = f"{SITE_NAME} Admin Portal"
admin.site.index_title = f"Welcome to {SITE_NAME} Admin Portal"
