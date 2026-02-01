import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Meeting, LiveNote
from .ai import ai_engine

class MeetingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.meeting_id = self.scope['url_route']['kwargs']['meeting_id']
        self.meeting_group = f'meeting_{self.meeting_id}'
        
        await self.channel_layer.group_add(
            self.meeting_group,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.meeting_group,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        text = data['text']
        
        # AI extracts important notes
        notes = ai_engine.extract_notes(text)
        
        for note in notes:
            live_note = LiveNote.objects.create(
                meeting_id=self.meeting_id,
                speaker=note['speaker'],
                content=note['content'],
                note_type=note['type']
            )
            
            # Broadcast to all members
            await self.channel_layer.group_send(
                self.meeting_group,
                {
                    'type': 'note_update',
                    'note': {
                        'id': live_note.id,
                        'speaker': note['speaker'],
                        'content': note['content'],
                        'type': note['type'],
                        'timestamp': live_note.timestamp.isoformat()
                    }
                }
            )
