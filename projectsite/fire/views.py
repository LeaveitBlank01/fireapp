from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from fire.models import Locations, Incident, FireStation, FireTruck, Firefighters
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.db import connection
from django.http import JsonResponse
from django.db.models.functions import ExtractMonth

from django.db.models import Count
from datetime import datetime

from fire.forms import Incident_Form ,LocationForm, FireStationzForm, Firetruckform, FirefightersForm


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
        'location__latitude', 'location__longitude', 'severity_level', 'description', 'location__city'
    )

    incident_data = []
    cities = set()

    for i in incidents:
        city = i['location__city']
        cities.add(city)

        incident_data.append({
            'latitude': float(i['location__latitude']),
            'longitude': float(i['location__longitude']),
            'severity': i['severity_level'],
            'description': i['description'],
            'city': city
        })

    context = {
        'incidents': incident_data,
        'cities': sorted(cities)
    }

    return render(request, 'map_incident.html', context)



def dashboard1(request):
    return render(request, 'dashboard1.html')


# New API for Polar Area Chart
def polarAreaBySeverity(request):
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

# New API for Scatter Chart
def scatterLatLonIncidents(request):
    incidents = Incident.objects.select_related('location').values(
        'location__latitude', 'location__longitude'
    )

    points = []
    for i in incidents:
        points.append({
            'x': float(i['location__longitude']),
            'y': float(i['location__latitude']),
        })

    return JsonResponse(points, safe=False)

def dashboard2(request):
    return render(request, 'dash2.html')





def heatmapByHourDay(request):
    query = '''
    SELECT 
        CAST(strftime('%H', date_time) AS INTEGER) AS hour, 
        (CAST(strftime('%w', date_time) AS INTEGER) + 6) % 7 AS day,   -- Convert to 0=Monday
        COUNT(*) as count
    FROM fire_incident
    GROUP BY hour, day
    '''
    
    heatmap = [[0]*24 for _ in range(7)]
    
    with connection.cursor() as cursor:
        cursor.execute(query)
        for hour, day, count in cursor.fetchall():
            if hour is not None and day is not None:  
                if 0 <= hour < 24 and 0 <= day < 7: 
                    heatmap[day][hour] = count
                else:
                    print(f"Invalid hour/day: hour={hour}, day={day}")
            else:
                print(f"None value detected: hour={hour}, day={day}")
    
    return JsonResponse({'heatmap': heatmap})


# Stacked Bar View
def stackedBarIncidentTypeCountry(request):
    qs = Incident.objects.values('location__country', 'severity_level').annotate(count=Count('id'))
    data = {}
    for row in qs:
        country = row['location__country'] or "Unknown"
        severity = row['severity_level'] or "Unknown"
        if country not in data:
            data[country] = {}
        data[country][severity] = row['count']
    return JsonResponse(data)


# Donut Chart View
def donutResponseTimeDistribution(request):
    query = '''
    SELECT 
        CASE
            WHEN response_time < 5 THEN '<5 mins'
            WHEN response_time BETWEEN 5 AND 9 THEN '5-9 mins'
            WHEN response_time BETWEEN 10 AND 19 THEN '10-19 mins'
            WHEN response_time >= 20 THEN '20+ mins'
            ELSE 'Unknown'
        END AS bucket,
        COUNT(*) as count
    FROM fire_incident
    GROUP BY bucket
    '''
    data = {}
    with connection.cursor() as cursor:
        cursor.execute(query)
        for bucket, count in cursor.fetchall():
            data[bucket] = count
    return JsonResponse(data)

def dashboard3(request):
    return render(request, 'dashboard3.html')

def dashboard4(request):
    return render(request, 'dashboard4.html')

def dashboard5(request):
    return render(request, 'dashboard5.html')


# Incident: Create View
class IncidentCreateView(CreateView):
    model = Incident
    form_class = Incident_Form
    template_name = 'incident_add.html'
    success_url = reverse_lazy('incident-list')

    def form_valid(self, form):
        description = form.instance.description[:50] + "..." if len(form.instance.description) > 50 else form.instance.description
        messages.success(self.request, f'Incident "{description}" created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['incident_list'] = self.success_url
        return context


# Incident: Update View
class IncidentUpdateView(UpdateView):
    model = Incident
    form_class = Incident_Form
    template_name = 'incident_edit.html'
    success_url = reverse_lazy('incident-list')

    def form_valid(self, form):
        description = form.instance.description[:50] + "..." if len(form.instance.description) > 50 else form.instance.description
        messages.success(self.request, f'Incident "{description}" updated successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['incident_list'] = self.success_url
        return context


# Incident: Delete View
class IncidentDeleteView(DeleteView):
    model = Incident
    template_name = 'incident_del.html'
    success_url = reverse_lazy('incident-list')
    context_object_name = 'incident'

    def form_valid(self, form):
        response = super().form_valid(form)
        description = self.object.description[:50] + "..." if len(self.object.description) > 50 else self.object.description
        messages.success(self.request, f'Successfully deleted incident: "{description}"')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Delete Incident #{self.object.id}"
        context['incident_list'] = self.success_url
        return context


# Incident: List/Search View
class IncidentListView(ListView):
    model = Incident
    template_name = 'incident_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(
                Q(description__icontains=query) |
                Q(severity_level__icontains=query) |
                Q(location__name__icontains=query) |
                Q(date_time__icontains=query)
            )
        return qs
    

class LocationListView(ListView):
    model = Locations
    template_name = 'location_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(address__icontains=query) |
                Q(city__icontains=query) |
                Q(country__icontains=query)
            )
        return qs
class LocationCreateView(CreateView):
    model = Locations
    form_class = LocationForm
    template_name = 'location_add.html'
    success_url = reverse_lazy('location-list')

    def form_valid(self, form):
        name = form.instance.name
        messages.success(self.request, f'Location "{name}" created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['loc_list'] = self.success_url  
        return context

class LocationUpdateView(UpdateView):
    model = Locations
    form_class = LocationForm
    template_name = 'location_edit.html'
    success_url = reverse_lazy('location-list')

    def form_valid(self, form):
        name = form.instance.name
        messages.success(self.request, f'Location "{name}" updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['location_list'] = self.success_url  
        return context

class LocationDeleteView(DeleteView):
    model = Locations
    template_name = 'location_del.html'
    success_url = reverse_lazy('location-list')
    context_object_name = 'location'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Delete Location #{self.object.id}"
        return context

    def form_valid(self, form):
        name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, 
            f'Location "{name}" was successfully deleted.',
            extra_tags='danger'
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['loc_list'] = self.success_url
        return context

def some_view(request):
   
    messages.success(request, "Action completed successfully!")
   

# Boat: Create View
class BoatCreateView(CreateView):
    model = Incident  
    form_class = Incident_Form
    template_name = 'boat_add.html'
    success_url = reverse_lazy('incident-list')

    def post(self, request, *args, **kwargs):
       
        errors = []
     

        if errors:
            for error in errors:
                messages.error(request, error)
            return self.form_invalid(self.get_form())

        messages.success(request, "Boat added successfully!")
        return super().post(request, *args, **kwargs)

def multi_line_chart(request):
    data = {
        "CountryA": {"Jan": 10, "Feb": 20, "Mar": 30, "Apr": 40, "May": 50, "Jun": 60, "Jul": 70, "Aug": 80, "Sep": 90, "Oct": 100, "Nov": 110, "Dec": 120},
        "CountryB": {"Jan": 15, "Feb": 25, "Mar": 35, "Apr": 45, "May": 55, "Jun": 65, "Jul": 75, "Aug": 85, "Sep": 95, "Oct": 105, "Nov": 115, "Dec": 125},
        "CountryC": {"Jan": 12, "Feb": 22, "Mar": 32, "Apr": 42, "May": 52, "Jun": 62, "Jul": 72, "Aug": 82, "Sep": 92, "Oct": 102, "Nov": 112, "Dec": 122}
    }
    return JsonResponse(data)

def multi_bar_chart(request):

    data = {
        "Minor": {"Dec": 10, "Jan": 20, "Feb": 30, "Mar": 40, "Apr": 50, "May": 60, "Jun": 70, "Jul": 80, "Aug": 90, "Sep": 100, "Oct": 110, "Nov": 120},
        "Moderate": {"Dec": 15, "Jan": 25, "Feb": 35, "Mar": 45, "Apr": 55, "May": 65, "Jun": 75, "Jul": 85, "Aug": 95, "Sep": 105, "Oct": 115, "Nov": 125},
        "Major": {"Dec": 12, "Jan": 22, "Feb": 32, "Mar": 42, "Apr": 52, "May": 62, "Jun": 72, "Jul": 82, "Aug": 92, "Sep": 102, "Oct": 112, "Nov": 122}
    }
    return JsonResponse(data)

class FirestationListView(ListView):
    model = FireStation
    template_name = 'firestation_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(address__icontains=query) |
                Q(city__icontains=query) |
                Q(country__icontains=query)
            )
        return qs

class FirestationCreateView(CreateView):
    model = FireStation
    form_class = FireStationzForm
    template_name = 'firestation_add.html'
    success_url = reverse_lazy('firestation-list')

    def form_valid(self, form):
        name = form.instance.name
        messages.success(self.request, f'Fire Station "{name}" created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['firestation_list'] = self.success_url  
        return context
class FirestationUpdateView(UpdateView):
    model = FireStation
    form_class = FireStationzForm
    template_name = 'firestation_edit.html'
    success_url = reverse_lazy('firestation-list')

    def form_valid(self, form):
        name = form.instance.name
        messages.success(self.request, f'Fire Station "{name}" updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['firestation_list'] = self.success_url  
        return context
class FirestationDeleteView(DeleteView):
    model = FireStation
    template_name = 'firestation_del.html'
    success_url = reverse_lazy('firestation-list')
    context_object_name = 'firestation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Delete Fire Station #{self.object.id}"
        return context

    def form_valid(self, form):
        name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, 
            f'Fire Station "{name}" was successfully deleted.',
            extra_tags='danger'
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['firestation_list'] = self.success_url
        return context

class FireTruckListView(ListView):
    model = FireTruck
    template_name = 'firetruck_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(model__icontains=query) |
                Q(year__icontains=query)
            )
        return qs

class FireTruckCreateView(CreateView):
    model = FireTruck
    form_class = Firetruckform
    template_name = 'firetruck_add.html'
    success_url = reverse_lazy('firetruck-list')

    def form_valid(self, form):
        name = form.instance.name
        messages.success(self.request, f'Fire Truck "{name}" created successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['firetruck_list'] = self.success_url  
        return context

class FireTruckUpdateView(UpdateView):
    model = FireTruck
    form_class = Firetruckform
    template_name = 'firetruck_edit.html'
    success_url = reverse_lazy('firetruck-list')

    def form_valid(self, form):
        name = form.instance.name
        messages.success(self.request, f'Fire Truck "{name}" updated successfully!')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['firetruck_list'] = self.success_url  
        return context
    
class FireTruckDeleteView(DeleteView):
    model = FireTruck
    template_name = 'firetruck_del.html'
    success_url = reverse_lazy('firetruck-list')
    context_object_name = 'firetruck'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Delete Fire Truck #{self.object.id}"
        return context

    def form_valid(self, form):
        name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request, 
            f'Fire Truck "{name}" was successfully deleted.',
            extra_tags='danger'
        )
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['firetruck_list'] = self.success_url
        return context
    
class FirefightersCreateView(CreateView):
    model = Firefighters
    form_class = FirefightersForm
    template_name = 'firefighter_add.html'
    success_url = reverse_lazy('firefighters-list') # <<-- CHANGED TO PLURAL

    def form_valid(self, form):
        name = form.instance.name
        messages.success(self.request, f'Firefighter "{name}" created successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # This context variable is optional, success_url is handled internally
        context['firefighter_list'] = self.success_url
        return context
    
class FirefightersUpdateView(UpdateView):
    model = Firefighters
    form_class = FirefightersForm
    template_name = 'firefighter_edit.html'
    success_url = reverse_lazy('firefighters-list') # <<-- CHANGED TO PLURAL

    def form_valid(self, form):
        name = form.instance.name
        messages.success(self.request, f'Firefighter "{name}" updated successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # This context variable is optional
        context['firefighter_list'] = self.success_url
        return context
    
class FirefightersDeleteView(DeleteView):
    model = Firefighters
    template_name = 'firefighter_del.html'
    success_url = reverse_lazy('firefighters-list') # <<-- CHANGED TO PLURAL
    context_object_name = 'firefighter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Delete Firefighter #{self.object.id}"
        return context

    def form_valid(self, form):
        name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request,
            f'Firefighter "{name}" was successfully deleted.',
            extra_tags='danger'
        )
        return response

class FirefightersListView(ListView):
    model = Firefighters
    template_name = 'firefighter_list.html'
    context_object_name = 'object_list'
    paginate_by = 10

    def get_queryset(self, *args, **kwargs):
        qs = super().get_queryset(*args, **kwargs)
        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(rank__icontains=query) |
                Q(experience_level__icontains=query)
            )
        return qs
    
class FirefightersCreateView(CreateView):
    model = Firefighters
    form_class = FirefightersForm
    template_name = 'firefighter_add.html'
    success_url = reverse_lazy('firefighters-list')

    def form_valid(self, form):
        name = form.instance.name
        messages.success(self.request, f'Firefighter "{name}" created successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['firefighter_list'] = self.success_url
        return context
    
class FirefightersUpdateView(UpdateView):
    model = Firefighters
    form_class = FirefightersForm
    template_name = 'firefighter_edit.html'
    success_url = reverse_lazy('firefighters-list')

    def form_valid(self, form):
        name = form.instance.name
        messages.success(self.request, f'Firefighter "{name}" updated successfully!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['firefighter_list'] = self.success_url
        return context
    
class FirefightersDeleteView(DeleteView):
    model = Firefighters
    template_name = 'firefighter_del.html'
    success_url = reverse_lazy('firefighters-list')
    context_object_name = 'firefighter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f"Delete Firefighter #{self.object.id}"
        return context

    def form_valid(self, form):
        name = self.object.name
        response = super().form_valid(form)
        messages.success(self.request,
            f'Firefighter "{name}" was successfully deleted.',
            extra_tags='danger'
        )
        return response