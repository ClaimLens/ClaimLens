import google.generativeai as genai
import os
import json
from PIL import Image
import time
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # CRITICAL FIX #5: Validate API key exists
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.error("❌ GEMINI_API_KEY not found in environment!")
            raise ValueError("GEMINI_API_KEY is required but not set in .env")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✅ Gemini AI Service initialized")
    
    def extract_document_data(self, image_path, max_retries=3):
        """
        Extract structured data from insurance documents with retry logic
        CRITICAL FIX #1: Added retry, timeout, and fallback
        """
        
        for attempt in range(max_retries):
            try:
                # Load image
                img = Image.open(image_path)
                
                # Prepare prompt
                prompt = """
                You are an expert insurance claim document analyzer. 
                Analyze this document and extract the following information in JSON format:
                
                {
                  "document_type": "hospital_bill/invoice/estimate/medical_report",
                  "policy_number": "extracted policy number or null",
                  "claim_amount": number (amount claimed),
                  "date_of_service": "YYYY-MM-DD or null",
                  "provider_name": "hospital/garage/service provider name",
                  "patient_name": "name if visible or null",
                  "diagnosis": "medical condition/damage description or null",
                  "items": ["list of services/items if itemized"],
                  "total_amount": number,
                  "currency": "INR/USD",
                  "red_flags": ["any suspicious patterns you notice"],
                  "missing_information": ["list of critical missing fields"],
                  "document_quality": "clear/blurry/damaged",
                  "confidence_score": number (0-100)
                }
                
                Be thorough. If information is not visible, use null.
                List ALL red flags you notice.
                """
                
                # CRITICAL FIX #1: Add timeout and retry
                logger.info(f"Calling Gemini API (attempt {attempt + 1}/{max_retries})")
                
                # Set generation config with timeout
                generation_config = {
                    'temperature': 0.3,
                    'top_p': 0.8,
                    'top_k': 40,
                    'max_output_tokens': 2048,
                }
                
                response = self.model.generate_content(
                    [prompt, img],
                    generation_config=generation_config,
                    request_options={'timeout': 30}  # 30 second timeout
                )
                
                # Check if response is empty
                if not response or not response.text:
                    logger.warning(f"Empty response from Gemini (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    else:
                        raise Exception("Gemini returned empty response after all retries")
                
                # Parse JSON response
                extracted_data = self._parse_json_response(response.text)
                
                # CRITICAL FIX: Validate extracted data structure
                extracted_data = self._validate_extracted_data(extracted_data)
                
                logger.info("✅ Gemini extraction successful")
                
                return {
                    'success': True,
                    'data': extracted_data,
                    'raw_response': response.text[:500]  # Truncate for logging
                }
                
            except Exception as e:
                logger.error(f"Gemini API error (attempt {attempt + 1}): {str(e)}")
                
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # All retries failed - return safe fallback
                    logger.error("All Gemini retries failed, using fallback")
                    return {
                        'success': False,
                        'error': str(e),
                        'data': self._get_fallback_data()
                    }
    
    def validate_claim_narrative(self, description, extracted_data, max_retries=2):
        """
        Check if claim description matches document data
        CRITICAL FIX #1: Added retry logic
        """
        for attempt in range(max_retries):
            try:
                prompt = f"""
                Compare this claim description with extracted document data.
                
                Claim Description: {description}
                
                Extracted Data: {json.dumps(extracted_data, indent=2)}
                
                Analyze and return JSON:
                {{
                  "consistency_score": number (0-100),
                  "inconsistencies": ["list of mismatches"],
                  "verification_status": "consistent/inconsistent/needs_review",
                  "concerns": ["list of concerns if any"]
                }}
                """
                
                response = self.model.generate_content(
                    prompt,
                    request_options={'timeout': 20}
                )
                
                if response and response.text:
                    return self._parse_json_response(response.text)
                    
            except Exception as e:
                logger.error(f"Narrative validation error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
        
        # Fallback
        return {
            'consistency_score': 50,
            'inconsistencies': [],
            'verification_status': 'needs_review',
            'concerns': ['AI validation unavailable']
        }
    
    def detect_document_tampering(self, image_path, max_retries=2):
        """
        Detect if document has been altered/forged
        CRITICAL FIX #1: Added retry logic
        """
        for attempt in range(max_retries):
            try:
                img = Image.open(image_path)
                
                prompt = """
                Analyze this document for signs of tampering or forgery:
                - Inconsistent fonts
                - Misaligned text
                - Color variations
                - Digital artifacts
                
                Return JSON:
                {
                  "tampering_detected": boolean,
                  "confidence": number (0-100),
                  "suspicious_areas": ["description of areas"],
                  "authenticity_score": number (0-100)
                }
                """
                
                response = self.model.generate_content(
                    [prompt, img],
                    request_options={'timeout': 20}
                )
                
                if response and response.text:
                    return self._parse_json_response(response.text)
                    
            except Exception as e:
                logger.error(f"Tampering detection error (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
        
        # Safe fallback
        return {
            'tampering_detected': False,
            'confidence': 0,
            'suspicious_areas': [],
            'authenticity_score': 50
        }
    
    def _parse_json_response(self, text):
        """
        Extract JSON from Gemini response
        MAJOR FIX #3: More robust parsing
        """
        try:
            # Remove markdown code blocks
            text = text.strip()
            
            # Handle various markdown formats
            if '```json' in text:
                text = text.split('```json')[1].split('```')[0]
            elif '```' in text:
                text = text.split('```')[1].split('```')[0]
            
            # Remove any leading/trailing whitespace
            text = text.strip()
            
            # Try to parse
            parsed = json.loads(text)
            
            # Validate it's a dict
            if not isinstance(parsed, dict):
                raise ValueError("Parsed JSON is not a dictionary")
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Text was: {text[:200]}")
            
            # Try to extract JSON from anywhere in the text
            try:
                # Find first { and last }
                start = text.find('{')
                end = text.rfind('}') + 1
                if start != -1 and end > start:
                    extracted = text[start:end]
                    return json.loads(extracted)
            except:
                pass
            
            # Final fallback
            return self._get_fallback_data()
        
        except Exception as e:
            logger.error(f"Unexpected parsing error: {e}")
            return self._get_fallback_data()
    
    def _validate_extracted_data(self, data):
        """
        MAJOR FIX #3: Validate and sanitize extracted data
        """
        # Ensure required fields exist
        defaults = {
            'document_type': 'unknown',
            'policy_number': None,
            'claim_amount': 0,
            'date_of_service': None,
            'provider_name': 'Not extracted',
            'patient_name': None,
            'diagnosis': None,
            'items': [],
            'total_amount': 0,
            'currency': 'INR',
            'red_flags': [],
            'missing_information': [],
            'document_quality': 'unclear',
            'confidence_score': 50
        }
        
        # Merge defaults with extracted data
        validated = {**defaults, **data}
        
        # Type validation
        if not isinstance(validated['claim_amount'], (int, float)):
            validated['claim_amount'] = 0
        
        if not isinstance(validated['confidence_score'], (int, float)):
            validated['confidence_score'] = 50
        
        if not isinstance(validated['red_flags'], list):
            validated['red_flags'] = []
        
        return validated
    
    def _get_fallback_data(self):
        """
        Return safe fallback when AI fails
        CRITICAL FIX #1: Enhanced fallback
        """
        return {
            'document_type': 'unknown',
            'policy_number': None,
            'claim_amount': 0,
            'provider_name': 'Not extracted - AI unavailable',
            'red_flags': ['⚠️ AI extraction failed - manual review required'],
            'confidence_score': 0,
            'missing_information': ['All fields require manual verification'],
            'document_quality': 'unclear',
            'currency': 'INR',
            'items': [],
            'total_amount': 0
        }

# Singleton instance
ai_service = AIService()