from django.contrib import admin
from django.urls import path

from fire.views import HomePageView, ChartView, PieCountbySeverity, LineCountbyMonth, MultilineIncidentTop3Country, multipleBarBySeverity, polarAreaBySeverity, scatterLatLonIncidents, heatmapByHourDay, stackedBarIncidentTypeCountry, donutResponseTimeDistribution
from fire import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', HomePageView.as_view(), name='home'),
    path('stations', views.map_station, name='map-station'),
    path('dashboard_chart', ChartView.as_view(), name='dashboard-chart'),
    path('chart/', PieCountbySeverity, name='chart'),
    path('lineChart/', LineCountbyMonth, name='chart'),
    path('multilineChart/', MultilineIncidentTop3Country, name='chart'),
    path('multiBarchart/', multipleBarBySeverity, name='chart'),
    path('incident/', views.map_incident, name='map-incident'),
    path('dashboard1/', views.dashboard1, name='dashboard1'),
    path('polarAreaBySeverity/', polarAreaBySeverity, name='polarAreaBySeverity'),
    path('scatterLatLonIncidents/', scatterLatLonIncidents, name='scatterLatLonIncidents'),
    path('dashboard2/', views.dashboard2, name='dashboard2'),
    path('heatmap/', heatmapByHourDay, name='heatmap'),
    path('stacked-bar/', stackedBarIncidentTypeCountry, name='stacked-bar'),
    path('response-times/', donutResponseTimeDistribution, name='response-times'),
    path('dashboard3/', views.dashboard3, name='dashboard3'),
    path('dashboard4/', views.dashboard4, name='dashboard4'),
    path('dashboard5/', views.dashboard5, name='dashboard5'),

]
