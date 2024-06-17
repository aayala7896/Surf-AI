from django.db import models
from django.contrib.auth.models import AbstractUser
from django import forms
from django.conf import settings
# Create your models here.
class Video(models.Model):
    title = models.CharField(max_length=500)
    url = models.FileField(upload_to='videos/', null=True, verbose_name="")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='uploaded_videos', on_delete=models.CASCADE)
    def __str__(self):
        return self.title + ": "+str(self.url)


class SurfSpot(models.Model):
    name = models.CharField(max_length=100)
    latitude = models.FloatField(blank = True,null = True)
    longitude = models.FloatField(blank = True, null = True)

    def __str__(self):
        return self.name


class Reel(models.Model):
    title = models.CharField(max_length=500)
    url = models.FileField(upload_to='reels/', null=True, verbose_name="")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='uploaded_reels', on_delete=models.CASCADE)
    video_title = models.CharField(max_length=500)
    def __str__(self):
        return self.title + ": " + str(self.url)


class myuser(AbstractUser):
    videos = models.ManyToManyField('Video', blank=True,related_name='user_videos')
    reels = models.ManyToManyField('Reel', blank = True, related_name='user_reels')
    user_surf_spot = models.OneToOneField(SurfSpot,on_delete=models.CASCADE,null=True,blank=True)
    class Meta:
        swappable = 'AUTH_USER_MODEL'
    def __str__(self):
        return self.username

