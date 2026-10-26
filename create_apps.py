import os, sys
os.chdir(r"c:\Users\LENOVO\OneDrive\Desktop\Applet logic\Hostel")
sys.argv = ['manage.py']
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_management.settings')

apps = ['accounts','dashboard','students','hostel','allocations','fees','complaints','visitors','attendance','reports']
for app in apps:
    sys.argv = ['manage.py', 'startapp', app]
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
    print(f"Created: {app}")

print("Done!")
