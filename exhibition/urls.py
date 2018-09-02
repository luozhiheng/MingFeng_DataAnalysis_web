from django.urls import path
from . import views

app_name = 'exhibition'
urlpatterns = [
    path('', views.index, name="index"),
    path('hg/', views.home_graph, name="home_graph"),
    path('detail_home/', views.detail_home, name="detail_home"),
    path('detail_home/chiller/',views.overview_chiller,name="overview_chiller")
]
