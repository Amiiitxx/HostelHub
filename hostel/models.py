from django.db import models
from django.core.exceptions import ValidationError


class Building(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_rooms(self):
        return Room.objects.filter(floor__building=self).count()

    @property
    def total_beds(self):
        return Bed.objects.filter(room__floor__building=self).count()

    @property
    def available_beds(self):
        return Bed.objects.filter(room__floor__building=self, status='available').count()


class Floor(models.Model):
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='floors')
    floor_number = models.IntegerField()
    name = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['building', 'floor_number']
        unique_together = ['building', 'floor_number']

    def __str__(self):
        return self.name or f"Floor {self.floor_number} — {self.building.name}"

    def save(self, *args, **kwargs):
        if not self.name:
            self.name = f"Floor {self.floor_number}"
        super().save(*args, **kwargs)

    @property
    def total_rooms(self):
        return self.rooms.count()

    @property
    def available_beds(self):
        return Bed.objects.filter(room__floor=self, status='available').count()


class Room(models.Model):
    TYPE_SINGLE = 'single'
    TYPE_DOUBLE = 'double'
    TYPE_TRIPLE = 'triple'
    TYPE_DORMITORY = 'dormitory'

    ROOM_TYPES = [
        (TYPE_SINGLE, 'Single'),
        (TYPE_DOUBLE, 'Double'),
        (TYPE_TRIPLE, 'Triple'),
        (TYPE_DORMITORY, 'Dormitory'),
    ]

    STATUS_ACTIVE = 'active'
    STATUS_MAINTENANCE = 'maintenance'
    STATUS_INACTIVE = 'inactive'

    ROOM_STATUSES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_MAINTENANCE, 'Maintenance'),
        (STATUS_INACTIVE, 'Inactive'),
    ]

    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=20)
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default=TYPE_DOUBLE)
    capacity = models.PositiveIntegerField(default=2)
    status = models.CharField(max_length=20, choices=ROOM_STATUSES, default=STATUS_ACTIVE)
    description = models.TextField(blank=True)
    monthly_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['floor__building__name', 'floor__floor_number', 'room_number']
        unique_together = ['floor', 'room_number']

    def __str__(self):
        return f"Room {self.room_number} — {self.floor.building.name} F{self.floor.floor_number}"

    @property
    def total_beds(self):
        return self.beds.count()

    @property
    def occupied_beds(self):
        return self.beds.filter(status='occupied').count()

    @property
    def available_beds(self):
        return self.beds.filter(status='available').count()

    @property
    def occupancy_percent(self):
        total = self.total_beds
        if total == 0:
            return 0
        return round((self.occupied_beds / total) * 100)

    @property
    def is_full(self):
        return self.available_beds == 0

    @property
    def display_status(self):
        if self.status == self.STATUS_MAINTENANCE:
            return 'maintenance'
        if self.is_full:
            return 'full'
        if self.available_beds == self.total_beds:
            return 'available'
        return 'partial'


class Bed(models.Model):
    STATUS_AVAILABLE = 'available'
    STATUS_OCCUPIED = 'occupied'
    STATUS_MAINTENANCE = 'maintenance'

    BED_STATUSES = [
        (STATUS_AVAILABLE, 'Available'),
        (STATUS_OCCUPIED, 'Occupied'),
        (STATUS_MAINTENANCE, 'Maintenance'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='beds')
    bed_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=BED_STATUSES, default=STATUS_AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['room', 'bed_number']
        unique_together = ['room', 'bed_number']

    def __str__(self):
        return f"Bed {self.bed_number} — Room {self.room.room_number}"

    @property
    def full_name(self):
        return f"{self.room.floor.building.name} / F{self.room.floor.floor_number} / Room {self.room.room_number} / Bed {self.bed_number}"

    def get_current_allocation(self):
        return self.allocations.filter(status='active').first()
