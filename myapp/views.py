from django.shortcuts import redirect, render
from django.http import HttpResponse, FileResponse
from django.contrib.auth.models import auth
from django.contrib.auth import logout, password_validation
from django.contrib import messages
from django.db.models import Q
from .models import Giver, Universities, Receiver, User, Meeting
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str, DjangoUnicodeDecodeError
from django.utils.html import strip_tags
from django.urls import reverse
from .utils import generate_email_token, generate_confirmation_token
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.conf import settings
import threading
from datetime import datetime, timedelta
from .forms import *
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .models import TimeSlot
import jwt
import requests




########################################################################################
#       MAIN SYSTEM
########################################################################################


# HOME--------------------------------------------------------------------------------------
def home(request):
    givers = Giver.objects.all()
    universities = Universities.objects.all()
    return render(request, 'home.html', {'givers': givers, 'universities':universities})


def selection(request):
    givers = Giver.objects.all()
    universities = Universities.objects.all()
    return render(request, 'selection2.html', {'givers': givers, 'universities':universities})


# LOGIN--------------------------------------------------------------------------------------
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)

        if user and not user.is_email_verified:
            messages.add_message(request, messages.ERROR,
                                    'Email is not verified, please check your email inbox')
            return render(request, 'login.html', status=401)

        if user is not None:
            auth.login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('login')
    return render(request, 'login.html')


# LOGOUT
def logout_view(request):
    logout(request)
    return redirect('home')


# REGISTER FOR STUDENT--------------------------------------------------------------------------------------
def register_student(request):
    if request.method == 'POST':
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Already Used')
                return redirect('register_student')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Already Used')
                return redirect('register_student')
            else:
                receiver = Receiver.objects.create(firstname=firstname, lastname=lastname, username=username, email=email)
                user = User.objects.create_user(username=username, password=password, email=email, firstname=firstname, lastname=lastname)
                receiver.save()
                user.save()

                send_activation_email(user, request)

                messages.add_message(request, messages.SUCCESS,
                                    'We sent you an email to verify your account')
                return redirect('login')
        else:
            messages.info(request, 'Password not the same')
            return redirect('register_student')

    return render(request, 'register_student.html')


# REGISTER FOR TEACHER--------------------------------------------------------------------------------------
def register_teacher(request):
    if request.method == 'POST' and request.FILES['imagefile']:
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        username = request.POST['username']
        password = request.POST['password']
        password2 = request.POST['password2']
        gender = request.POST['gender']
        email = request.POST['email']

        university = request.POST['university']
        major = request.POST['major']
        minor = request.POST['minor']
        education_level = request.POST['education_level']
        timezone = request.POST['timezone']

        fs = FileSystemStorage()
        imagefile = request.FILES['imagefile']
        fs.save(imagefile.name, imagefile)

        resumefile = None
        if request.FILES['resumefile'] == True:
            resumefile = request.FILES['resumefile']
            fs.save(resumefile.name, resumefile)
        
        brief_introduction = request.POST['brief_introduction']
        linkedin = request.POST['linkedin']
        additional_information = request.POST['additional_information']

        if password == password2:
            if User.objects.filter(email=email).exists():
                messages.info(request, 'Email Already Used')
                return redirect('register_teacher')
            elif User.objects.filter(username=username).exists():
                messages.info(request, 'Username Already Used')
                return redirect('register_teacher')
            elif not(email.endswith('.edu')):
                messages.info(request, 'Invalid Email Format (Email must end with .edu)')
                return redirect('register_teacher')
            else:
                giver = Giver.objects.create(firstname=firstname, lastname=lastname,
                                            username=username, gender=gender,
                                            email=email, university=university,
                                            major=major, minor=minor,
                                            education_level=education_level, timezone=timezone,
                                            brief_introduction=brief_introduction,
                                            linkedin=linkedin,
                                            additional_information=additional_information,
                                            resume=resumefile,
                                            profile_image=imagefile)
                user = User.objects.create_user(username=username, password=password, email=email, is_mentor = True, firstname=firstname, lastname=lastname)
                giver.save()
                user.save()

                send_activation_email(user, request)

                messages.add_message(request, messages.SUCCESS,
                                    'We sent you an email to verify your account')
                return redirect('login')
        else:
            messages.info(request, 'Password not the same')
            return redirect('register_teacher')
    return render(request, 'register_teacher.html')


#Class Email
class EmailThread(threading.Thread):
    def __init__(self, email):
        self.email = email
        threading.Thread.__init__(self)
    def run(self):
        self.email.send()


#Send Verification Email
def send_activation_email(user, request):
    current_site = get_current_site(request)
    email_subject = 'Activate your account'
    email_body = render_to_string('activate.html',{
        'user': user,
        'domain':current_site,
        'uid':urlsafe_base64_encode(force_bytes(user.pk)),
        'token': generate_email_token.make_token(user)
    })
    email = EmailMessage(subject=email_subject, body=email_body, from_email=settings.EMAIL_FROM_USER,to=[user.email])
    email.content_subtype = 'html'
    EmailThread(email).start()


#Activate User
def activate_user(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except Exception as e:
        user = None

    if user and generate_email_token.check_token(user, token):
        user.is_email_verified = True
        user.save()
        messages.add_message(request, messages.SUCCESS,'Email verified, you can now login')
        return redirect(reverse('login'))
    return render(request, 'activate-failed.html', {"user": user})

    
# REGISTER PAGE--------------------------------------------------------------------------------------
def register(request):
    return render(request, 'register.html')


# SEARCH SYSTEM--------------------------------------------------------------------------------------
def search(request):
    givers = Giver.objects.all()
    universities = Universities.objects.all()
    query = None
    query_list = []
    results = []
    rests = []
    final_results = []

    if request.method=="GET":
        query=request.GET.get('search')
        query1=request.GET.get('search1')
        query2=request.GET.get('search2')

        if query is not None and query != '':
            query_list.append(query)
        if query1 is not None:
            query_list.append(query1)
        if query2 is not None:
            query_list.append(query2)

        for item in query_list:
            results = Giver.objects.filter(Q(name__icontains=item) | Q(university__icontains=item))
            for result in results:
                if result not in final_results:
                    final_results.append(result)
        for item2 in Giver.objects.filter():
            if item2 not in final_results:
                rests.append(item2)
            
        if query_list == []:
            query_list = None

    return render(request, 'selection2.html', {'query': query_list, 'results': final_results, 'givers':givers, 'rests':rests, 'universities':universities})


########################################################################################
#       RESERVATION
########################################################################################


# GO TO PROFILE PAGE--------------------------------------------------------------------------------------
def profile(request, pk):
    profile = Giver.objects.get(id=pk)
    givers = Giver.objects.all()
    universities = Universities.objects.all()
    meetings = Meeting.objects.filter(giver=profile.username)
    available_timeslots = TimeSlot.objects.filter(user = profile.user, is_reserved = False)
    return render(request, 'profile2.html', {'profile': profile, 'givers':givers, 'universities':universities, 'meetings':meetings, 'available_timeslots': available_timeslots,})


#GO TO CONFIRM RESERVATION PAGE
def confirm_reservation(request,pk):
    if request.user.is_authenticated==True:
        profiles = Giver.objects.get(id=pk)
        if request.user.is_mentor==True:
            messages.add_message(request, messages.SUCCESS,
                                    'You need a student account to reserve a meeting')
            return redirect('register_student')
    return render(request, 'confirm_reservation.html', {'profiles': profiles})


#RESERVATION CONFIRMED
def confirmed(request,pk):
    if request.user.is_authenticated==True:
        profiles = Giver.objects.get(id=pk)
        student = Receiver.objects.get(username=request.user.username)
        meeting = Meeting.objects.create(giver=profiles.username, receiver=request.user.username)
        send_confirmation_email(meeting, profiles, student, request)
        return render(request, 'reservation_request_sent.html', {'profiles': profiles})
    else:
        messages.add_message(request, messages.SUCCESS,
                                    'You need to login to reserve a meeting')
        return redirect('login')


########################################################################################
#       EMAILING
########################################################################################


#SEND COMFIRMATION EMAIL TO MENTOR
def send_confirmation_email(meeting, giver, receiver, request):
    current_site = get_current_site(request)
    email_subject = 'A meeting has been requested! Confirm now.'
    email_body = render_to_string('email_confirm_meeting.html',{
        'meeting': meeting,
        'domain':current_site,
        'student':receiver,
        'uid':urlsafe_base64_encode(force_bytes(meeting.pk)),
        'token': generate_confirmation_token.make_token(meeting)
    })
    email = EmailMessage(subject=email_subject, body=email_body, from_email=settings.EMAIL_FROM_USER,to=[giver.email])
    email.content_subtype = 'html'
    EmailThread(email).start()


#CONFIRM MEETING FROM MENTOR
def confirm_meeting(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        meeting = Meeting.objects.get(pk=uid)
    except Exception as e:
        meeting = None

    if meeting and generate_confirmation_token.check_token(meeting, token):
        meeting.is_confirmed = True
        meeting.save()
        messages.add_message(request, messages.SUCCESS,'Meeting is confirmed')
        return render(request, 'confirm_success.html')
    return render(request, 'activate-failed.html', {"meeting": meeting})


#MEETING RESERVATION COMPLETED EMAIL
def send_meeting_set(meeting, giver, receiver, request):
    current_site = get_current_site(request)
    email_subject = 'A meeting has been confirmed!'
    email_body = render_to_string('email_meeting_set_mentor.html',{
        'meeting': meeting,
        'student': receiver,
        'domain':current_site,
        'uid':urlsafe_base64_encode(force_bytes(meeting.pk)),
    })
    email_body2 = render_to_string('email_meeting_set_student.html',{
        'meeting': meeting,
        'mentor': giver,
        'domain':current_site,
        'uid':urlsafe_base64_encode(force_bytes(meeting.pk)),
    })
    email = EmailMessage(subject=email_subject, body=email_body, from_email=settings.EMAIL_FROM_USER,to=[giver.email])
    email2 = EmailMessage(subject=email_subject, body=email_body2, from_email=settings.EMAIL_FROM_USER,to=[receiver.email])
    email.content_subtype = 'html'
    email2.content_subtype = 'html'
    EmailThread(email).start()
    EmailThread(email2).start()


def send_meeting_cancelled(meeting, giver, receiver, request):
    current_site = get_current_site(request)
    email_subject = 'A meeting has been cancelled!'
    email_body = render_to_string('email_meeting_cancelled.html',{
        'meeting': meeting,
        'student': receiver,
        'domain':current_site,
        'uid':urlsafe_base64_encode(force_bytes(meeting.pk)),
    })
    email = EmailMessage(subject=email_subject, body=email_body, from_email=settings.EMAIL_FROM_USER,to=[giver.email])
    email.content_subtype = 'html'
    EmailThread(email).start()


def send_meeting_rejected(meeting, giver, receiver, request):
    current_site = get_current_site(request)
    email_subject = 'A meeting has been rejected!'
    email_body = render_to_string('email_meeting_rejected.html',{
        'meeting': meeting,
        'mentor': giver,
        'domain':current_site,
        'uid':urlsafe_base64_encode(force_bytes(meeting.pk)),
    })
    email = EmailMessage(subject=email_subject, body=email_body, from_email=settings.EMAIL_FROM_USER,to=[receiver.email])
    email.content_subtype = 'html'
    EmailThread(email).start()



########################################################################################
#       PROFILE - MENTOR
########################################################################################


#MY PROFLE PAGE
def my_profile(request, pk):
    if request.user.is_authenticated==True:
        my_profile = Giver.objects.get(username=request.user.username)
        return render(request, 'my_profile.html', {"my_profile": my_profile})
    return redirect(reverse('login'))

    
#MY MEETINGS PAGE
def my_meetings(request, pk):
    if request.user.is_authenticated==True:
        my_profile = Giver.objects.get(username=request.user.username)
        my_meetings = Meeting.objects.filter(giver=request.user.username)
        return render(request, 'my_meetings.html', {"my_profile": my_profile, "my_meetings": my_meetings})
    return redirect(reverse('login'))


#MEETING CONFIRMATION SUCCESSFUL
def confirmation_successful(request, pk, pk2):
    if request.user.is_authenticated==True:
        my_meeting = Meeting.objects.get(id=pk2)
        giver_profile = Giver.objects.get(username=my_meeting.giver)
        receiver_profile = Receiver.objects.get(username=my_meeting.receiver)
        send_meeting_set(my_meeting, giver_profile, receiver_profile, request)
        my_meeting.is_confirmed = True
        my_meeting.save()
        return render(request, 'confirm_success.html', {"my_meeting": my_meeting})
    return redirect(reverse('login'))


#MEETING REJECTION FROM MENTOR
def reject_reservation(request, pk, pk2):
    if request.user.is_authenticated==True:
        my_meeting = Meeting.objects.get(id=pk2)
        profile = Receiver.objects.get(username=my_meeting.receiver)
        return render(request, 'reject_reservation.html', {"my_meeting": my_meeting, "profiles": profile})
    return redirect(reverse('login'))


#MEETING REJECTED
def reject_for_sure(request, pk, pk2):
    if request.user.is_authenticated==True:
        my_meeting = Meeting.objects.get(id=pk2)
        my_meeting.is_rejected = True
        my_meeting.is_confirmed = False
        my_meeting.save()
        giver_profile = Giver.objects.get(username=my_meeting.giver)
        receiver_profile = Receiver.objects.get(username=my_meeting.receiver)
        send_meeting_rejected(my_meeting, giver_profile, receiver_profile, request)
        return render(request, 'reject_for_sure.html', {"my_meeting": my_meeting})
    return redirect(reverse('login'))


#UPLOAD VIDEO AFTER MEETING
def upload_video(request, pk, pk2):
    if request.user.is_authenticated==True :
        my_meeting = Meeting.objects.get(id=pk2)
        my_meeting.is_waiting_for_video = True
        my_meeting.is_video_uploaded = False
        my_meeting.save()
        if request.method == 'POST' and request.FILES['videofile']:
            fs = FileSystemStorage()
            videofile = request.FILES['videofile']
            fs.save(videofile.name, videofile)
            my_meeting.video = videofile
            my_meeting.is_waiting_for_video = False
            my_meeting.is_video_uploaded = True
            my_meeting.save()
            return render(request, 'video_upload_completed.html', {"my_meetings": my_meeting})
        return render(request, 'upload_video.html', {"my_meeting": my_meeting})
    return redirect(reverse('login'))



########################################################################################
#       PROFILE - STUDENT
########################################################################################


#MY STUDENT PROFILE PAGE
def student_profile(request, pk):
    if request.user.is_authenticated==True:
        my_profile = Receiver.objects.get(username=request.user.username)
        return render(request, 'student_profile.html', {"my_profile": my_profile})
    return redirect(reverse('login'))


#MY STUDENT MEETINGS PAGE
def student_meetings(request, pk):
    if request.user.is_authenticated==True:
        my_profile = Receiver.objects.get(username=request.user.username)
        my_meetings = Meeting.objects.filter(receiver=request.user.username)
        return render(request, 'student_meetings.html', {"my_profile": my_profile, "my_meetings": my_meetings})
    return redirect(reverse('login'))


#SUBMIT RATING
def submit_rating(request, pk, pk2):
    if request.user.is_authenticated==True:
        my_meeting = Meeting.objects.get(id=pk2)
        return render(request, 'submit_rating.html', {"my_meeting": my_meeting})
    return redirect(reverse('login'))


#RATING COMPLETED
def rating_upload_completed(request, pk, pk2):
    if request.user.is_authenticated==True:
        if request.method == 'GET':
            star= request.GET.get('rate')
            feedback = request.GET.get('feedback-input')
            my_meeting = Meeting.objects.get(id=pk2)
            my_meeting.is_waiting_for_rating = False
            my_meeting.is_rating_submitted = True
            my_meeting.stars = int(star)
            my_meeting.feedback = feedback
            my_meeting.save()
            return render(request, 'rating_upload_completed.html', {"my_meetings": my_meeting})
    return redirect(reverse('login'))


#CANCEL RESERVATION
def cancel_reservation(request, pk, pk2):
    if request.user.is_authenticated==True:
        my_meeting = Meeting.objects.get(id=pk2)
        profile = Giver.objects.get(username=my_meeting.giver)
        return render(request, 'cancel_reservation.html', {"my_meeting": my_meeting, "profiles": profile})
    return redirect(reverse('login'))


#CANCEL RESERVATION FOR SURE
def cancel_for_sure(request, pk, pk2):
    if request.user.is_authenticated==True:
        my_meeting = Meeting.objects.get(id=pk2)
        my_meeting.is_cancelled = True
        my_meeting.is_confirmed = False
        my_meeting.save()
        giver_profile = Giver.objects.get(username=my_meeting.giver)
        receiver_profile = Receiver.objects.get(username=my_meeting.receiver)
        send_meeting_cancelled(my_meeting, giver_profile, receiver_profile, request)
        return render(request, 'cancel_for_sure.html', {"my_meeting": my_meeting})
    return redirect(reverse('login'))


def check_Giver_availability(giver, dt, tm):  # check if engineer is available in a given slot
    tm = tm[:-3]  # separate AM/PM
    hr = tm[:-3]  # get hour reading
    mn = tm[-2:]  # get minute reading
    ftm = time(int(hr), int(mn), 0)  # create a time object
    app = Appointment.objects.all().filter(status=True,
                                           giver=Giver,
                                           app_date=dt)  # get all appointments for a given eng and the given date

    if ftm < time(9, 0, 0) or ftm > time(17, 0, 0):  # if time is not in between 9AM to 5PM, reject
        return False

    if time(12, 0, 0) < ftm < time(13, 0, 0):  # if time is in between 12PM to 1PM, reject
        return False

    for a in app:
        if ftm == a.app_time and dt == a.app_date:  # if some other appointment has the same slot, reject
            return False

    return True

def confirm_reservation(request, profile_id):
    return render(request, 'confirm_reservation.html')


def reserve_timeslot(request):
    if request.method == 'POST':
        timeslot_id = request.POST.get('timeslot')
        timeslot = TimeSlot.objects.get(id=timeslot_id)

        # Check if the timeslot is still available
        if timeslot.is_reserved:
            messages.error(request, 'The selected timeslot is no longer available. Please choose another one.')
            return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

        # Reserve the timeslot
        timeslot.is_reserved = True
        timeslot.save()

        # Create a Zoom meeting and get the join URL
        zoom_meeting_link = create_zoom_meeting(timeslot)

        # Send the confirmation email with the Zoom link
        send_confirmation_email(request.user.email, timeslot, zoom_meeting_link)

        messages.success(request, 'Timeslot reserved successfully. A confirmation email has been sent.')
        return redirect(request.META.get('HTTP_REFERER', 'redirect_if_referer_not_found'))

    return redirect('home')

def create_zoom_meeting(timeslot):
    # Replace with your Zoom API credentials
    zoom_api_key = settings.ZOOM_API_KEY
    zoom_api_secret = settings.ZOOM_API_SECRET
    zoom_user_id = settings.ZOOM_USER_ID

    # Generate JWT token for authorization
    payload = {
        'iss': zoom_api_key,
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    jwt_token = jwt.encode(payload, zoom_api_secret, algorithm='HS256')

    # Set up Zoom API headers and endpoint
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {jwt_token}'
    }
    url = f'https://api.zoom.us/v2/users/{zoom_user_id}/meetings'

    # Set up Zoom meeting data
    meeting_data = {
        'topic': 'Mentor Meeting',
        'start_time': timeslot.start_time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        'duration': 60,  # Duration in minutes
        'timezone': 'UTC'
    }

    # Create the Zoom meeting
    response = requests.post(url, headers=headers, json=meeting_data)

    if response.status_code == 201:
        meeting_info = response.json()
        return meeting_info["join_url"]
    else:
        raise ValueError("Failed to create Zoom meeting.")

def send_confirmation_email(receiver_email, timeslot, zoom_meeting_link):
    subject = "Timeslot Reservation Confirmation"
    message = f"Dear {receiver_email},\n\nYour timeslot reservation has been confirmed for {timeslot.start_time.strftime('%Y-%m-%dT%H:%M:%SZ')} - {timeslot.end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}. Please join the meeting using the following Zoom link:\n\n{zoom_meeting_link}\n\nBest regards,\nThe MeetingU Team"
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [receiver_email]

    send_mail(subject, message, from_email, recipient_list)




