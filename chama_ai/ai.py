import re
from datetime import datetime

class ChamaAI:
    def extract_notes(self, text):
        """Extracts smart notes from transcription"""
        notes = []
        
        # Contributions 
        contrib_match = re.findall(r'([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s*(?:contribute|pay|give)\s*(?:KSh\s*)?(\d+(?:,\d{3})*(?:\.\d{2})?)', text, re.I)
        for name, amount in contrib_match:
            notes.append({
                'speaker': name.strip(),
                'content': f"Contributes KSh {amount}",
                'type': 'contribution'
            })
        
        # Decisions 
        if re.search(r'\b(approved|passed|agreed|decided)\b', text, re.I):
            notes.append({
                'speaker': 'Group',
                'content': 'Decision made',
                'type': 'decision'
            })
        
        # Members 
        member_match = re.findall(r'(?:new|welcome)\s+member\s+([A-Z][a-z]+)', text, re.I)
        for name in member_match:
            notes.append({
                'speaker': name,
                'content': 'New member joined',
                'type': 'member'
            })
            
        return notes
    
    def smart_reply(self, prompt, context=""):
        prompt = prompt.lower()
        
        responses = {
            'contribution': "Use /ai-contributions to extract all payments mentioned",
            'summary': "Key notes extracted above. Use /ai-tasks for action items",
            'meeting': "Live transcription active. Speaking detected → notes auto-generated"
        }
        
        if any(word in prompt for word in ['summary', 'minutes']):
            return "Meeting summary generated with action items"
        elif 'contribution' in prompt:
            return responses['contribution']
        
        return "Try: /ai-summary, /ai-contributions, /ai-tasks"
    
    def generate_agenda(self, chama_name):
        return f"{chama_name} Agenda:\n1. Contributions\n2. New members\n3. Decisions\n4. Next meeting"

ai_engine = ChamaAI()
