from models import Ticket
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class AIService:
    """
    AI service for generating natural language summaries of incidents.
    This is the AI feature chosen for this system - it helps operators quickly
    understand the situation without reading technical details.
    """
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.enabled = bool(self.api_key)
    
    async def generate_incident_summary(self, ticket: Ticket) -> Optional[str]:
        """
        Generate a natural language summary of the incident for the operator.
        """
        if not self.enabled:
            # Fallback to template-based summary
            return self._generate_template_summary(ticket)
        
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            prompt = f"""
            Generate a concise, professional incident summary for a power distribution control room operator.
            
            Fault Details:
            - Type: {ticket.fault_type}
            - Location: {ticket.fault_location}
            - Affected Poles: {ticket.affected_poles_count}
            - Confidence: {ticket.confidence:.0%}
            - PIN Code: {ticket.pincode or 'Unknown'}
            - Reason: {ticket.confidence_reason}
            
            Write a 2-3 sentence summary that helps the operator understand what happened and what to expect.
            """
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for power grid operators."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"AI summary generated for ticket {ticket.ticket_id}")
            return summary
        
        except Exception as e:
            logger.error(f"Error generating AI summary: {e}")
            return self._generate_template_summary(ticket)
    
    def _generate_template_summary(self, ticket: Ticket) -> str:
        """
        Generate a template-based summary when AI is unavailable.
        """
        fault_type_map = {
            "span": "wire span",
            "distribution_transformer": "distribution transformer",
            "feeder": "feeder line"
        }
        
        fault_type_readable = fault_type_map.get(ticket.fault_type, ticket.fault_type)
        
        summary = f"{fault_type_readable.capitalize()} fault detected at {ticket.fault_location}. "
        summary += f"Approximately {ticket.affected_poles_count} poles affected. "
        summary += f"Location confidence: {ticket.confidence:.0%}."
        
        return summary


ai_service = AIService()
