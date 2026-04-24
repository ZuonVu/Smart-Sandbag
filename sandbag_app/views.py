import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count
import json
from .models import Punch, Session, UserProfile
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
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
            session_forces = []
            for p in punches:
                try:
                    session_forces.append(float(p.force))
                except (ValueError, TypeError):
                    pass
            
            stats['total_punches'] = punches.count()
            stats['max_force'] = max(session_forces) if session_forces else 0
            
            labels = [p.timestamp.strftime("%H:%M:%S") for p in punches]
            forces = session_forces

    # --- ALL-TIME STATS LOGIC (Fixed for string databases) ---
    all_punches = Punch.objects.filter(session__user=user)
    total_all_time_punches = all_punches.count()
    
    all_forces = []
    for p in all_punches:
        try:
            all_forces.append(float(p.force))
        except (ValueError, TypeError):
            pass
            
    max_all_time_force = max(all_forces) if all_forces else 0

    earned_badges = []
    
    # Check Punch Milestones
    if total_all_time_punches >= 10:
        earned_badges.append({"name": "Warming Up", "icon": "🔥", "desc": "10+ Punches"})
    if total_all_time_punches >= 100:
        earned_badges.append({"name": "Centurion", "icon": "💯", "desc": "100+ Punches"})
    if total_all_time_punches >= 1000:
        earned_badges.append({"name": "Iron Fists", "icon": "🥊", "desc": "1,000+ Punches"})
        
    # Check Power Milestones
    if max_all_time_force >= 700:
        earned_badges.append({"name": "Heavy Hitter", "icon": "💥", "desc": "700+ Newtons"})
    if max_all_time_force >= 1500:
        earned_badges.append({"name": "Tyson Power", "icon": "🦍", "desc": "1,500+ Newtons"})
        
    earned_badges.reverse() 

    context = {
        'punches': punches, 
        'labels': labels,
        'forces': forces,
        'stats': stats,
        'profile': profile,
        'badges': earned_badges,
    }
    return render(request, 'dashboard.html', context)


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
    session_to_delete = get_object_or_404(Session, id=session_id, user=request.user)
    session_to_delete.delete()
    return redirect('history')


@login_required(login_url='login')
def history(request):
    user = request.user
    sessions_list = Session.objects.filter(user=user).order_by('-id')
    
    all_time_forces = []
    
    # Manually calculate stats to bypass the string bug
    for session in sessions_list:
        session_punches = Punch.objects.filter(session=session)
        session.total_punches = session_punches.count()
        
        session_forces = []
        for p in session_punches:
            try:
                val = float(p.force)
                session_forces.append(val)
                all_time_forces.append(val)
            except (ValueError, TypeError):
                pass
                
        session.max_force = round(max(session_forces)) if session_forces else 0
        session.average_force = round(sum(session_forces) / len(session_forces)) if session_forces else 0

        # Calculate top target
        top_target = session_punches.values('location').annotate(count=Count('id')).order_by('-count').first()
        session.favorite_target = top_target['location'] if top_target else "None"

    # All-time stats
    all_time_punches = Punch.objects.filter(session__user=user).count()
    all_time_max_force = round(max(all_time_forces)) if all_time_forces else 0
    all_time_avg_force = round(sum(all_time_forces) / len(all_time_forces)) if all_time_forces else 0
    total_sessions = sessions_list.count()

    paginator = Paginator(sessions_list, 5) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'all_time_punches': all_time_punches,
        'all_time_max_force': all_time_max_force,
        'all_time_avg_force': all_time_avg_force,
        'total_sessions': total_sessions,
    }

    return render(request, 'history.html', context)

def export_session_csv(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="smart_sandbag_session_{session_id}.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Punch Number', 'Time Recorded', 'Force (Newtons)', 'Location'])
    
    punches = Punch.objects.filter(session=session).order_by('timestamp')
    
    for index, punch in enumerate(punches, start=1):
        time_str = punch.timestamp.strftime("%Y-%m-%d %H:%M:%S") if punch.timestamp else "N/A"
        writer.writerow([
            index, 
            time_str, 
            punch.force, 
            punch.location 
        ])
        
    return response