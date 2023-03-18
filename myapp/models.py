from django.db import models, connection
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.
class User(AbstractUser):
    is_email_verified = models.BooleanField(default=False)
    is_mentor =  models.BooleanField(default=False)
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)


class Giver(models.Model):
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    gender  = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    university = models.CharField(max_length=100)
    major = models.CharField(max_length=100)
    minor = models.CharField(max_length=100)
    profile_image = models.ImageField(null=True, blank=True, upload_to="images/")
    resume = models.FileField(null=True, blank=True, upload_to="resumes/")
    linkedin = models.URLField(max_length=300, null=True)
    brief_introduction = models.CharField(max_length=10000)
    additional_information = models.CharField(max_length=10000, null=True)
    education_level = models.CharField(max_length=100)
    timezone = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    def __str__(self):
        temp = self.firstname + " / " + self.username + " / " + self.email
        return temp


class Receiver(models.Model):
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    email = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    def __str__(self):
        temp = self.firstname + " / " + self.username + " / " + self.email
        return temp


class Meeting(models.Model):
    is_confirmed = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    is_waiting_for_video =  models.BooleanField(default=False)
    is_video_uploaded = models.BooleanField(default=False)

    is_rejected = models.BooleanField(default=False)
    is_cancelled = models.BooleanField(default=False)

    giver = models.CharField(max_length=100)
    receiver = models.CharField(max_length=100)

    video = models.FileField(null=True, blank=True, upload_to="videos/")

    is_waiting_for_rating =  models.BooleanField(default=False)
    is_rating_submitted = models.BooleanField(default=False)
    stars = models.IntegerField(default=0)
    feedback = models.CharField(max_length=10000, null=True, blank=True)

    datetime = models.DateTimeField(default=datetime.now, blank=True)


class Universities(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
         return self.name



class TimeSlot(models.Model):
    giver = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    
    def __str__(self) -> str:
        return f"{self.giver.username} - {self.start_time.strftime('%Y-%m-%d %H:%M')} to {self.end_time.strftime('%Y-%m-%d %H:%M')}"


class Reservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)