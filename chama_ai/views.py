from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Meeting, LiveNote, AIConversation
from .ai import ai_engine

@login_required
def live_meeting(request):
    if request.method == 'POST':
        meeting = Meeting.objects.create(
            name=request.POST['name'],
            chama_id=request.POST['chama_id'],
            user=request.user
        )
        meeting.is_live = True
        meeting.save()
        return JsonResponse({'meeting_id': meeting.id})
    
    meetings = Meeting.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'chama_ai/live_meeting.html', {'meetings': meetings})

@login_required
def ai_notes(request, meeting_id):
    meeting = Meeting.objects.get(id=meeting_id)
    notes = LiveNote.objects.filter(meeting=meeting).order_by('timestamp')
    
    if request.method == 'POST':
        prompt = request.POST.get('prompt')
        response = ai_engine.smart_reply(prompt)
        
        AIConversation.objects.create(
            user=request.user,
            meeting=meeting,
            prompt=prompt,
            response=response
        )
        return JsonResponse({'response': response})
    
    return render(request, 'chama_ai/ai_notes.html', {
        'meeting': meeting,
        'notes': notes
    })
