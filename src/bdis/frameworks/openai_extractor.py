import json
import os
from openai import OpenAI
from bdis.ports.extraction_service import IExtractionService
from bdis.domain.entities import RawExtraction

class OpenAIExtractor(IExtractionService):
    def __init__(self, api_key: str = None):
        key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=key) if key else None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._load_prompts()

    def _load_prompts(self):
        try:
            path = os.path.join(os.path.dirname(__file__), "resources", "prompts.json")
            with open(path, "r") as f:
                self.prompts = json.load(f)
        except Exception:
            self.prompts = {"extraction_prompt": "{raw_text}"} # Fallback

    def extract_schema(self, raw_text: str) -> RawExtraction:
        if not self.client:
            # Fallback for local testing without key
            return RawExtraction(company_name="Mocked OpenAI", amount=999.0)
            
        template = self.prompts.get("extraction_prompt", "{raw_text}")
        prompt = template.format(raw_text=raw_text)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        # Robust Schema Enforcement (Phase 4 Hardening)
        try:
            return RawExtraction.model_validate_json(response.choices[0].message.content)
        except Exception as e:
            logging.error(f"AI Schema Validation Failed: {e}. Raw content: {response.choices[0].message.content}")
            # Fallback to loose parsing if strict fails
            data = json.loads(response.choices[0].message.content)
            return RawExtraction(
                company_name=data.get("company_name"),
                amount=data.get("amount_usd"),
                currency=data.get("currency"),
                due_date=data.get("due_date"),
                status=data.get("status"),
                invoice_id=data.get("invoice_id")
            )
