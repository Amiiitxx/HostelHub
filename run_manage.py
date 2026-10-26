import os, sys
os.chdir(r"c:\Users\LENOVO\OneDrive\Desktop\Applet logic\Hostel")
sys.path.insert(0, r"c:\Users\LENOVO\OneDrive\Desktop\Applet logic\Hostel")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hostel_management.settings')

import django
django.setup()

cmd = sys.argv[1] if len(sys.argv) > 1 else 'migrate'
from django.core.management import call_command
if cmd == 'migrate':
    call_command('migrate')
elif cmd == 'seed':
    call_command('seed_data')
elif cmd == 'test':
    call_command('test', sys.argv[2] if len(sys.argv) > 2 else '')
elif cmd == 'runserver':
    call_command('runserver', '0.0.0.0:8000')
elif cmd == 'superuser':
    call_command('createsuperuser')
else:
    from django.core.management import execute_from_command_line
    sys.argv = ['manage.py'] + sys.argv[1:]
    execute_from_command_line(sys.argv)
