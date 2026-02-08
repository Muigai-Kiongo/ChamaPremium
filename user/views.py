from django.shortcuts import render
from django.contrib.auth import login, authenticate, logout
from .forms import RegisterForm, LoginForm
# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Chama, ChamaMember

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()
            login(request, user)
            return redirect('lending:dashboard')
    else:
        form = RegisterForm()

    return render(request, 'user/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('lending:dashboard')
    else:
        form = LoginForm()

    return render(request, 'user/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('user:login')


def profile_detail_view(request):
    return render(request, 'user/profile_detail.html', {'user': request.user})


def index_view(request):
    return render(request, 'user/index.html')


from .forms import UserUpdateForm, ProfileUpdateForm


def profile_update_view(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile_details')  # adjust to your profile page

    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, 'user/profile_update.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def profile(request):
    memberships = ChamaMember.objects.filter(user=request.user).select_related('chama')
    context = {'memberships': memberships}
    return render(request, 'user/profile.html', context)

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
