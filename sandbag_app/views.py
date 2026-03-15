from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Max # Removed Avg since we don't average strings
import json
from .models import Punch, Session, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator 

@csrf_exempt
def start_session(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Not logged in"}, status=401)

        user = request.user
        Session.objects.filter(user=user, end_time__isnull=True).update(end_time=timezone.now())
        new_session = Session.objects.create(user=user)
        return JsonResponse({"status": "success", "session_id": new_session.id})
        
    return JsonResponse({"status": "error"}, status=400)

@csrf_exempt
def end_session(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({"status": "error", "message": "Not logged in"}, status=401)

        user = request.user
        active_session = Session.objects.filter(user=user, end_time__isnull=True).first()
        if active_session:
            active_session.end_time = timezone.now()
            active_session.save()
            return JsonResponse({"status": "success"})
            
        return JsonResponse({"status": "error", "message": "No active session found"})
    return JsonResponse({"status": "error"}, status=400)

@csrf_exempt
def record_punch(request):
    if request.method == 'POST':
        try:
            if not request.user.is_authenticated:
                return JsonResponse({"status": "error", "message": "Not logged in"}, status=401)

            data = json.loads(request.body)
            user = request.user
            
            active_session = Session.objects.filter(user=user, end_time__isnull=True).first()
            if not active_session:
                active_session = Session.objects.create(user=user)

            Punch.objects.create(
                session=active_session,
                force=data.get('force', 0),
                location=data.get('location', 'Unknown') 
            )
            
            return JsonResponse({"status": "success", "session_id": active_session.id})
            
        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"status": "error"}, status=400)
            
    return JsonResponse({"status": "Invalid method"}, status=405)

@login_required(login_url='login')
def dashboard(request):
    user = request.user
    profile, created = UserProfile.objects.get_or_create(user=user)
    
    recent_session = Session.objects.filter(user=user).order_by('-id').first()
    
    punches = []
    labels = []
    forces = []
    stats = {'total_punches': 0, 'max_force': 0}

    if recent_session:
        punches = Punch.objects.filter(session=recent_session).order_by('timestamp')
        if punches.exists():
            stats = punches.aggregate(
                total_punches=Count('id'),
                max_force=Max('force')
            )
            labels = [p.timestamp.strftime("%H:%M:%S") for p in punches]
            forces = [p.force for p in punches]

    context = {
        'punches': punches, 
        'labels': labels,
        'forces': forces,
        'stats': stats,
        'profile': profile
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='login')
def history(request):
    user = request.user
    sessions = Session.objects.filter(user=user).annotate(
        total_punches=Count('punches'),
        max_force=Max('punches__force')
    ).order_by('-id')

    # Calculate the most frequently hit target for each session
    for session in sessions:
        # Groups punches by location, counts them, and grabs the highest one
        top_target = session.punches.values('location').annotate(count=Count('id')).order_by('-count').first()
        
        if top_target:
            session.favorite_target = top_target['location']
        else:
            session.favorite_target = "None"

    return render(request, 'history.html', {'sessions': sessions})

@login_required(login_url='login')
def settings(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        profile.bag_mass = request.POST.get('bag_mass', 30.0)
        profile.bag_length = request.POST.get('bag_length', 1.0)
        profile.chain_length = request.POST.get('chain_length', 0.5)
        profile.save()
        return redirect('dashboard')
        
    return render(request, 'settings.html', {'profile': profile})

def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()           
            login(request, user)         
            return redirect('dashboard') 
    else:
        form = UserCreationForm()

    return render(request, 'signup.html', {'form': form})


@login_required(login_url='login')
@require_POST
def delete_session(request, session_id):
    # Fetch the session, ensuring it belongs to the logged-in user
    session_to_delete = get_object_or_404(Session, id=session_id, user=request.user)
    
    # Delete the session (this also deletes all associated punches due to CASCADE)
    session_to_delete.delete()
    
    # Send them right back to the history page
    return redirect('history')

@login_required(login_url='login')
def history(request):
    user = request.user
    
    sessions_list = Session.objects.filter(user=user).annotate(
        total_punches=Count('punches'),
        max_force=Max('punches__force')
    ).order_by('-id')

    # Calculate the top target
    for session in sessions_list:
        top_target = session.punches.values('location').annotate(count=Count('id')).order_by('-count').first()
        session.favorite_target = top_target['location'] if top_target else "None"

    paginator = Paginator(sessions_list, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'history.html', {'page_obj': page_obj})