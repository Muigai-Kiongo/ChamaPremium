from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Chama, ChamaMember

@login_required
def profile(request):
    memberships = ChamaMember.objects.filter(user=request.user).select_related('chama')
    context = {'memberships': memberships}
    return render(request, 'users/profile.html', context)

@login_required
def join_chama(request, chama_id):
    chama = get_object_or_404(Chama, id=chama_id)
    
    # Check if already member
    if ChamaMember.objects.filter(user=request.user, chama=chama).exists():
        messages.warning(request, 'You are already a member!')
        return redirect('profile')
    
    # Create membership
    ChamaMember.objects.create(user=request.user, chama=chama)
    messages.success(request, f'Joined {chama.name} successfully!')
    return redirect('profile')
