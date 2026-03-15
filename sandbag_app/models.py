from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bag_mass = models.FloatField(default=30.0)      # Default: 30 kg
    bag_length = models.FloatField(default=1.0)     # Default: 1.0 meter
    chain_length = models.FloatField(default=0.5)   # Default: 0.5 meters

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Session(models.Model):
    # Links the session to a specific user account
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Automatically records when the session starts
    start_time = models.DateTimeField(auto_now_add=True)
    
    # Left blank until the user clicks "End Session"
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        username = self.user.username if self.user else "Guest"
        return f"Session {self.id} - {username} ({self.start_time.strftime('%b %d, %Y')})"

    # A handy helper to calculate total workout time
    @property
    def duration(self):
        if self.end_time:
            return self.end_time - self.start_time
        return None

class Punch(models.Model):
    # Links every punch to a specific Session. 
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='punches', null=True, blank=True)
    
    force = models.IntegerField()
    location = models.CharField(max_length=20, default="Unknown")
    timestamp = models.DateTimeField(auto_now_add=True)

    # Combine them into a single, highly detailed string representation!
    def __str__(self):
        return f"Punch: {self.force}N at {self.location} ({self.timestamp.strftime('%H:%M:%S')})"
        