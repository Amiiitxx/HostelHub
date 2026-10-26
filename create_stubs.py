import os, sys

os.chdir(r"c:\Users\LENOVO\OneDrive\Desktop\Applet logic\Hostel")
base = r"c:\Users\LENOVO\OneDrive\Desktop\Applet logic\Hostel"

# App name → index view name mapping
stubs = {
    'dashboard': ('index', 'dashboard:index'),
    'students': ('list', 'students:list'),
    'hostel': ('index', 'hostel:index'),
    'allocations': ('list', 'allocations:list'),
    'fees': ('list', 'fees:list'),
    'complaints': ('list', 'complaints:list'),
    'visitors': ('list', 'visitors:list'),
    'attendance': ('index', 'attendance:index'),
    'reports': ('index', 'reports:index'),
}

for app, (view_name, _) in stubs.items():
    urls_path = os.path.join(base, app, 'urls.py')
    with open(urls_path, 'w') as f:
        f.write(f"""from django.urls import path
from . import views

app_name = '{app}'

urlpatterns = [
    path('', views.index, name='{view_name}'),
]
""")
    
    views_path = os.path.join(base, app, 'views.py')
    with open(views_path, 'w') as f:
        f.write(f"""from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
    return render(request, '{app}/index.html', {{}})
""")
    
    # Create templates dir
    tmpl_dir = os.path.join(base, 'templates', app)
    os.makedirs(tmpl_dir, exist_ok=True)
    tmpl_file = os.path.join(tmpl_dir, 'index.html')
    with open(tmpl_file, 'w') as f:
        f.write(f"""{{% extends 'base.html' %}}
{{% block title %}}{app.title()}{{% endblock %}}
{{% block page_title %}}{app.title()}{{% endblock %}}
{{% block content %}}
<p>Under construction</p>
{{% endblock %}}
""")

print("Stub views and URLs created for all apps")

# Now add apps.py for each
apps_list = ['dashboard', 'students', 'hostel', 'allocations', 'fees', 'complaints', 'visitors', 'attendance', 'reports']
for app in apps_list:
    apps_py = os.path.join(base, app, 'apps.py')
    if not os.path.exists(apps_py):
        with open(apps_py, 'w') as f:
            f.write(f"""from django.apps import AppConfig


class {app.title()}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{app}'
""")

print("Apps.py fixed")
