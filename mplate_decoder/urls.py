from django.urls import path

from . import views

app_name = 'mplate_decoder'
urlpatterns = [
     path('decode/', views.MplateCreate.as_view(),
          name='mplate_create'),
     path('<slug:chassis_number_short>', views.MplateRetrieve.as_view(),
          name='mplate_retrieve'),
     path('<slug:chassis_number_short>/update/', views.MplateUpdate.as_view(),
          name='mplate_update'),
     path('<slug:chassis_number_short>/delete/', views.MplateDelete.as_view(),
          name='mplate_delete'),
     path('', views.MplateIndex.as_view(),
          name='mplate_index'),
     path('about/', views.MplateAbout.as_view(),
          name='mplate_about'),
     path('search/', views.SearchResultsView.as_view(),
          name='search_results'),
]
