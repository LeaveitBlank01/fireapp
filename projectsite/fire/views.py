from django.shortcuts import render
from django.views.generic.list import ListView
from fire.models import Locations, Incident, FireStation

from django.db import connection
from django.http import JsonResponse
from django.db.models.functions import ExtractMonth

from django.db.models import Count
from datetime import datetime


class HomePageView(ListView):
    model = Locations
    context_object_name = 'home'
    template_name = "home.html"


class ChartView(ListView):
    template_name = 'chart.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    def get_queryset(self, *args, **kwargs):
        pass

def map_station(request):
    fireStations = FireStation.objects.values('name', 'latitude', 'longitude')

    for fs in fireStations:
        fs['latitude'] = float(fs['latitude'])
        fs['longitude'] = float(fs['longitude'])

    fireStations_list = list(fireStations)

    context = {
        'fireStations': fireStations_list,
    }

    return render(request, 'map_station.html', context)


def PieCountbySeverity(request):
    query = '''
    SELECT severity_level, COUNT(*) as count
    FROM fire_incident
    GROUP BY severity_level
    '''
    data = {}
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
    
    if rows:
        data = {severity: count for severity, count in rows}

    return JsonResponse(data)


def LineCountbyMonth(request):
    
    current_year = datetime.now().year
    
    result = {month: 0 for month in range(1, 13)}
    
    incidents_per_month = Incident.objects.filter(date_time__year=current_year) \
        .values_list('date_time', flat=True)
        
    for date in incidents_per_month:
        month = date.month
        result[month] += 1
    
    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    
    result_with_month_names = {
        month_names[int(month)]: count for month, count in result.items()
    }
    
    return JsonResponse(result_with_month_names)


def MultilineIncidentTop3Country(request):
    query = '''
    SELECT
        fl1.country,
        strftime('%m', fi.date_time) AS month,
        COUNT(fi.id) AS incident_count
    FROM 
        fire_incident fi
    JOIN
        fire_locations fl1 ON fi.location_id = fl1.id
    WHERE
        fl1.country IN (
            SELECT
                fl_top.country
            FROM
                fire_incident fi_top
            JOIN
                fire_locations fl_top ON fi_top.location_id = fl_top.id
            WHERE
                strftime('%Y', fi_top.date_time) = strftime('%Y', 'now')
            GROUP BY fl_top.country
            ORDER BY COUNT(fi_top.id) DESC
            LIMIT 3
        )
        AND strftime('%Y', fi.date_time) = strftime('%Y', 'now')
    GROUP BY fl1.country, month
    ORDER BY fl1.country, month;
    '''

    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    result = {}

    months = [str(i).zfill(2) for i in range(1, 13)]

    for row in rows:
        country = row[0]
        month = row[1]
        total_incidents = row[2]

        if country not in result:
            result[country] = {month: 0 for month in months}

        result[country][month] = total_incidents

    while len(result) < 3:
        fake_country = f"Country {len(result) + 1}"
        result[fake_country] = {month: 0 for month in months}

    for country in result:
        result[country] = dict(sorted(result[country].items()))

    return JsonResponse(result)


def multipleBarBySeverity(request):
    query = '''
        SELECT
            fi.severity_level,
            strftime('%m', fi.date_time) AS month,
            COUNT(fi.id) AS incident_count
        FROM
            fire_incident fi
        GROUP BY fi.severity_level, month
    '''
    
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    result = {}
    months = set(str(i).zfill(2) for i in range(1, 13))

    for row in rows:
        level = str(row[0])  # Ensure the severity level is a string
        month = row[1]
        total_incidents = row[2]

        if level not in result:
            result[level] = {month: 0 for month in months}

        result[level][month] = total_incidents

    # Sort months within each severity level
    for level in result:
        result[level] = dict(sorted(result[level].items()))

    return JsonResponse(result)

def map_incident(request):
     incidents = Incident.objects.select_related('location').values(
         'location__latitude', 'location__longitude', 'severity_level', 'description')
 
     incident_data = []
     for i in incidents:
         incident_data.append({
             'latitude': float(i['location__latitude']),
             'longitude': float(i['location__longitude']),
             'severity': i['severity_level'],
             'description': i['description'],
         })
 
     context = {'incidents': incident_data}
     return render(request, 'map_incident.html', context)
