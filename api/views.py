from django.shortcuts import render, redirect
from django.http import Http404, HttpResponse
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.core import serializers
from django.contrib.auth import authenticate, login,logout
import json,requests,arrow
from roboflow import Roboflow
from api.forms import VideoForm, JoinForm, LoginForm

from django.conf import settings
from .models import Video, myuser, SurfSpot,Reel

import os
from datetime import datetime,timedelta
import math
from moviepy.editor import *
# Create your views here.


def home(request):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')

        with open('json_test.json', 'w') as f:
            json.dump(result, f)

    videos = Video.objects.all()
    context = {'videos': videos}
    return render(request, 'home.html', context)


def create_reel(video_url,clip_start,clip_end,user,num_reel):
    video_path = str(video_url)
    tmp = video_url[6:]
    video = Video.objects.get(url=tmp)
    video_title = video.title
    clip = VideoFileClip(video_path)
    reel = clip.subclip(clip_start, clip_end)

    reel_name = f"Reel_{num_reel}.mp4"
    base_path = 'media/reels/'
    reel_url = os.path.join(base_path, reel_name)
    reel.write_videofile(reel_url)

    new_reel = Reel(title=reel_name, url=reel_url, user=user, video_title=video_title)
    new_reel.save()
    clip.close()



def create_clips(video_url,surfer_riding_time,user):
    clip_start = 0.0
    clip_end = 0.0
    reel_num = 0
    for idx in range(len(surfer_riding_time)):
        time = surfer_riding_time[idx]
        if idx == 0:
            clip_start = time
            clip_end = time
        else:
            # if the recognition is less than 2.2 seconds apart,
            # set new end time
            if time - clip_end <= 2.2:
                clip_end = time
            # else create the reel, then continue
            else:
                reel_num = reel_num + 1
                create_reel(video_url,clip_start,clip_end+1,user,reel_num)
                clip_start = time
                clip_end = time


def process_video(request):
    if request.method == 'POST':
        user = request.user
        video_url = request.POST.get('video_url')

        processed_data = f"Processing video at URL: {video_url}"

        rf = Roboflow(api_key="7DP2foaQ6qUPW1lrWQCj")
        project = rf.workspace().project("surfer-detection-dkdry")
        model = project.version("9").model
        job_id, signed_url, expire_time = model.predict_video(
            video_url,
            fps=5,
            prediction_type="batch-video",
        )
        # JSON file of results
        result = model.poll_until_video_results(job_id)
        surfers_riding_time = []
        time_offset = []

        for offset in result['time_offset']:
            time_offset.append(offset)

        for idx,frames in enumerate(result['surfer-detection-dkdry']):
            for position in frames['predictions']:
                if position['class'] == 'Surfer_Riding':
                    surfers_riding_time.append(time_offset[idx])
                    print("found surfer riding at time: ",time_offset[idx])

        create_clips(video_url,surfers_riding_time,user)

        return redirect('/userHome')

def api_weather_call(lat,lng):
    APIKEY = "ff1d73ec-f5e7-11ee-bd26-0242ac130002-ff1d74aa-f5e7-11ee-bd26-0242ac130002"
    API_ENDPOINT = 'https://api.stormglass.io/v2'
    start = arrow.now().floor('day')
    end = arrow.now().ceil('day')

    result = requests.get(
        API_ENDPOINT+'/weather/point',
        params={
                'lat': lat,
                'lng':lng,
                'params': ','.join(['waveHeight', 'airTemperature','airTemperature100m','cloudCover','windDirection','waterTemperature']),
                'start': start.to('UTC').timestamp(),  # Convert to UTC timestamp
                'end': end.to('UTC').timestamp()
        },
        headers={
            'Authorization': APIKEY
        }
    )
    return result.json()


def convert_time(time):
    hour = datetime.strptime(time,"%Y-%m-%dT%H:%M:%S+00:00")
    hour = hour.strftime("%H:%M")
    if hour == "00:00":
        return "12:00am"
    elif hour == "12:00":
        return hour + "pm"
    elif int(hour[:2]) < 12:
        return hour + "am"
    else:
        return str(int(hour[:2]) - 12) + hour[-3:]+"pm"
    return hour

def convert_cel_to_feh(temp):
    return str(int(temp) * 9/5 + 32)

def convert_meters_to_ft(waveHeight):
    return str(float(waveHeight) * 3.28)


def cloud_coverage(coveragePercent):
    coveragePercent = float(coveragePercent)
    if coveragePercent < 12.50:
        return "Clear"
    elif coveragePercent > 12.50 and coveragePercent < 37.50:
        return "Mostly Clear"
    elif coveragePercent > 37.50 and coveragePercent < 62.50:
        return "Partly Cloudy"
    elif coveragePercent > 62.50 and coveragePercent < 87.50:
        return "Mostly Cloudy"
    else:
        return "Cloudy"

#given north winds start at 0 degrees
def wind_Direction(wind):
    wind = float(wind)
    if wind > -1 and wind < 22.5:
        return "North"
    elif wind > 22.5 and wind < 67.5:
        return "North-East"
    elif wind > 67.5 and wind < 112.5:
        return "East"
    elif wind > 112.5 and wind < 157.5:
        return "South-East"
    elif wind > 157.5 and wind < 202.5:
        return "South"
    elif wind > 202.5 and wind < 225.0:
        return "South-West"
    elif wind > 225 and wind < 292.5:
        return "West"
    elif wind > 292.5 and wind < 337.5:
        return "North-West"
    elif wind > 337.5 and wind < 360:
        return "North"
    else:
        "NaN"

    

def get_report(lat,lng):
    day = datetime.now().strftime("%Y-%m-%d")
    surfBreak = f"surf_report_{day}_{lat}_{lng}.json"
    report = os.path.join("static/",surfBreak)
    with open(report,'r') as data:
        report_data = json.load(data)
    return report_data

def save_surf_report(report, lat,lng):
    day = datetime.now().strftime("%Y-%m-%d")
    surfBreak = f"surf_report_{day}_{lat}_{lng}.json"
    filepath = os.path.join("static/",surfBreak)
    with open(filepath,'w') as data:
        json.dump(report,data)

def is_report_updated(lat,lng):
    day = datetime.now().strftime("%Y-%m-%d")
    surfBreak = f"surf_report_{day}_{lat}_{lng}.json"

    filepath = os.path.join("static/",surfBreak)
    return os.path.exists(filepath)


def update_reel_name(request):
    if request.method == 'POST':
        reel_name = request.POST.get('reel_title')
        new_name = request.POST.get('new_reel')
        reel = Reel.objects.get(title=reel_name)
        reel.title = new_name
        reel.save()
        return redirect('/userHome')


def userhome(request):
    if request.user.is_authenticated:
        user = request.user
        first_name = user.first_name
        all_vids = Video.objects.all()
        all_reels = Reel.objects.all()
        user_videos = []
        reel_videos = []
        for video in all_vids:
            if video.user == user:
                user_videos.append(video)

            

        for reel in all_reels:
            if reel.user == user:
                reel_videos.append(reel)

        surfspot = user.user_surf_spot
        if surfspot is not None:
            lat = surfspot.latitude
            lng = surfspot.longitude
            if is_report_updated(lat,lng):
                #report exist
                print("report exist")
            else:
                print("new report coming")
                report = api_weather_call(lat,lng)
                save_surf_report(report,lat,lng)
            report = get_report(lat,lng)
            new_report = []
            #time is wrong. uses utc time.
            tmp = datetime.now()
            tmp.strftime("%H:%M")
           
            curr = tmp.strftime("%d/%m/%y %H:%M")
            hour = curr
          

           
            for data in report['hours']:
                time = convert_time(data['time'])
                print(time)
                airTemp = convert_cel_to_feh(data['airTemperature']['sg'])
                cloudCoverage = cloud_coverage(data['cloudCover']['sg'])
                waterTemp = convert_cel_to_feh(data['waterTemperature']['sg'])
                waveLow = math.ceil(float(convert_meters_to_ft(data['waveHeight']['noaa'])))
                waveHigh = waveLow + 1
                windDirection = wind_Direction(data['windDirection']['sg'])

                hour = {
                    'time': time,
                    'airTemp': airTemp,
                    'cloudCoverage': cloudCoverage,
                    'waterTemp': waterTemp,
                    'waveLow': waveLow,
                    'waveHigh': waveHigh,
                    'windDirection': windDirection
                }
                if hour['time'] == '06:00am' or hour['time'] == '12:00pm' or hour['time'] == '6:00pm':
                    new_report.append(hour)

            context = {'first_name': first_name, 'videos': user_videos,'user':request.user,"surf_spot":surfspot,'report':new_report,'reels': reel_videos}
            return render(request, 'userHome.html', context)

        context = {'first_name': first_name, 'videos': user_videos,'user':request.user,"surf_spot":surfspot,'reels': reel_videos}

        return render(request, 'userHome.html', context)
    return render(request, 'userHome.html')


def upload(request):
    if request.method == 'POST':
        form = VideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.user = request.user

            video.save()
            return redirect('/userHome')
    else:
        form = VideoForm()
    context = {'form': form}
    return render(request, 'upload.html', context)


def settings(request):
    user = request.user
    if request.method == 'POST':
        if user:
            selected_spot = request.POST.get('preferred_spot')
            surf_spot = SurfSpot.objects.get(name = selected_spot)
            user.user_surf_spot = surf_spot
            user.save()
            print("SURF SPOT CHANGED")
    user_spot = user.user_surf_spot
    if user_spot is None:
        print("User has no surf spot")
    else:
        print(type(user_spot))

    surf_spots = SurfSpot.objects.all()
    context = {"surf_spots":surf_spots,"user_spot":user_spot}   
    
    return render(request,'userSettings.html',context)


def auth(request):
    code = request.GET.get('code')
    print(code)
    return HttpResponse(request)


def surfVisual(request):
    states = ["Drop-in", "Ride", "Wipeout"]
    file_path = 'json_test.json'
    surfers_positions = []
    surfer_box_size = []
    with open(file_path, 'r') as file:
        data = json.load(file)


    context = {
        'surfers_positions': json.dumps(surfers_positions)
    }

    return render(request, 'surfVisual.html', context)


def join(request):
    if request.method == 'POST':
        form = JoinForm(request.POST)
        if form.is_valid():
            context = {'valid': 0}
            print(form.cleaned_data)
            user = form.save()
            user.set_password(form.cleaned_data['password'])
            user.save()
            return render(request, 'join.html', context)
        else:
            print(form.errors)
            context = {'form_error': "Error Processing your account. Try Again"}
    else:
        form = JoinForm()
        context = {'form': form, 'valid': 1}

    return render(request, 'join.html', context)


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']

            password = form.cleaned_data['password']

            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                print("Logged in successfully")
                return redirect("/")
            else:
                return render(request, 'login.html', {'error': 'Invalid username or password'})
        else:
            print(form.errors)
            return render(request, 'login.html', {'error': 'Invalid username or password'})
    return render(request, 'login.html')


def log_out(request):
    logout(request)
    return redirect("/")
