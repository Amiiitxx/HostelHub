from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Building, Floor, Room, Bed


def staff_required(view_func):
    from functools import wraps

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(settings.LOGIN_URL)

        if not request.user.can_manage_hostel:
            messages.error(request, "Access denied.")
            return redirect('dashboard:index')

        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
def index(request):
    buildings = Building.objects.prefetch_related(
        'floors__rooms__beds'
    ).all()

    context = {
        'buildings': buildings,
        'total_buildings': buildings.count(),
        'total_rooms': Room.objects.count(),
        'total_beds': Bed.objects.count(),
        'available_beds': Bed.objects.filter(status='available').count(),
        'occupied_beds': Bed.objects.filter(status='occupied').count(),
    }

    return render(request, 'hostel/index.html', context)


@login_required
def room_list(request):
    building_id = request.GET.get('building')
    floor_id = request.GET.get('floor')

    qs = Room.objects.select_related(
        'floor__building'
    ).prefetch_related('beds')

    if building_id:
        qs = qs.filter(floor__building_id=building_id)

    if floor_id:
        qs = qs.filter(floor_id=floor_id)

    buildings = Building.objects.all()

    floors = (
        Floor.objects.filter(building_id=building_id)
        if building_id
        else Floor.objects.all()
    )

    return render(request, 'hostel/rooms.html', {
        'rooms': qs,
        'buildings': buildings,
        'floors': floors,
        'selected_building': building_id,
        'selected_floor': floor_id,
    })


@login_required
def room_detail(request, pk):
    room = get_object_or_404(
        Room.objects
        .select_related('floor__building')
        .prefetch_related('beds__allocations__student'),
        pk=pk
    )

    return render(
        request,
        'hostel/room_detail.html',
        {'room': room}
    )


# =========================================================
# AJAX ENDPOINTS
# =========================================================

def ajax_floors(request):
    building_id = request.GET.get('building_id')

    floors = Floor.objects.filter(
        building_id=building_id
    ).values(
        'id',
        'name',
        'floor_number'
    )

    return JsonResponse({
        'floors': [
            {
                'id': f['id'],
                'name': f['name'] or f"Floor {f['floor_number']}"
            }
            for f in floors
        ]
    })


def ajax_rooms(request):
    floor_id = request.GET.get('floor_id')

    rooms = Room.objects.filter(
        floor_id=floor_id,
        status='active'
    ).values(
        'id',
        'room_number',
        'room_type'
    )

    return JsonResponse({
        'rooms': [
            {
                'id': r['id'],
                'name': f"Room {r['room_number']} ({r['room_type'].title()})"
            }
            for r in rooms
        ]
    })


def ajax_beds(request):
    room_id = request.GET.get('room_id')

    beds = Bed.objects.filter(
        room_id=room_id,
        status='available'
    ).values(
        'id',
        'bed_number'
    )

    return JsonResponse({
        'beds': [
            {
                'id': b['id'],
                'name': f"Bed {b['bed_number']}"
            }
            for b in beds
        ]
    })


# =========================================================
# BUILDING CRUD
# =========================================================

@staff_required
def building_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        address = request.POST.get('address', '').strip()

        if name:
            b = Building.objects.create(
                name=name,
                address=address
            )

            messages.success(
                request,
                f"Building '{b.name}' created."
            )

        return redirect('hostel:index')

    return redirect('hostel:index')


@staff_required
def building_delete(request, pk):
    b = get_object_or_404(Building, pk=pk)

    if request.method == 'POST':
        name = b.name

        b.delete()

        messages.success(
            request,
            f"Building '{name}' deleted."
        )

    return redirect('hostel:index')


# =========================================================
# FLOOR CRUD
# =========================================================

@staff_required
def floor_create(request):
    if request.method == 'POST':
        building_id = request.POST.get('building')
        floor_number = request.POST.get('floor_number')
        name = request.POST.get('name', '').strip()

        try:
            f = Floor.objects.create(
                building_id=building_id,
                floor_number=floor_number,
                name=name,
            )

            messages.success(
                request,
                f"Floor '{f.name}' created."
            )

        except Exception as e:
            messages.error(
                request,
                f"Error: {e}"
            )

    return redirect('hostel:index')


# =========================================================
# ROOM CRUD
# =========================================================

@staff_required
def room_create(request):
    if request.method == 'POST':
        floor_id = request.POST.get('floor')
        room_number = request.POST.get('room_number')
        room_type = request.POST.get('room_type', 'double')

        capacity = int(
            request.POST.get('capacity', 2)
        )

        monthly_rent = request.POST.get(
            'monthly_rent',
            0
        )

        try:
            room = Room.objects.create(
                floor_id=floor_id,
                room_number=room_number,
                room_type=room_type,
                capacity=capacity,
                monthly_rent=monthly_rent,
            )

            # Auto-create beds
            for i in range(1, capacity + 1):
                Bed.objects.create(
                    room=room,
                    bed_number=str(i)
                )

            messages.success(
                request,
                f"Room {room_number} created with {capacity} beds."
            )

        except Exception as e:
            messages.error(
                request,
                f"Error: {e}"
            )

    return redirect('hostel:room_list')


@staff_required
def room_delete(request, pk):
    room = get_object_or_404(Room, pk=pk)

    if request.method == 'POST':
        num = room.room_number

        room.delete()

        messages.success(
            request,
            f"Room {num} deleted."
        )

    return redirect('hostel:room_list')


# =========================================================
# BED STATUS TOGGLE
# =========================================================

@staff_required
def bed_toggle_maintenance(request, pk):
    bed = get_object_or_404(Bed, pk=pk)

    if request.method == 'POST':

        if bed.status == 'maintenance':
            bed.status = 'available'

            messages.success(
                request,
                f"Bed {bed.bed_number} marked as available."
            )

        elif bed.status == 'available':
            bed.status = 'maintenance'

            messages.success(
                request,
                f"Bed {bed.bed_number} marked under maintenance."
            )

        else:
            messages.warning(
                request,
                "Cannot change status of an occupied bed."
            )

        bed.save(
            update_fields=['status']
        )

    return redirect(
        'hostel:room_detail',
        pk=bed.room.pk
    )