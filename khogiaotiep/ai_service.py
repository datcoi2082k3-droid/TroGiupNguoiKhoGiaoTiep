import os
import datetime
import logging
from google import genai
from dotenv import load_dotenv
import PIL.Image

# --- Professional Logging Setup ---
logging.basicConfig(
    filename="app_system.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Load API Key
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1'})
else:
    client = None
    logging.warning("Gemini AI API Key not found. Offline mode active.")

class AIService:
    MODEL_ID = 'gemini-1.5-flash' # Default
    
    # Premium Local Fallback: 100% Core board translations for data.json
    FALLBACK_DICT = {
        # Categories
        "GIAO TIẾP CƠ BẢN": "BASIC COMMUNICATION",
        "NHU CẦU THIẾT YẾU": "ESSENTIAL NEEDS",
        "CHẨN ĐOÁN Y TẾ": "MEDICAL DIAGNOSIS",
        "CẢM XÚC": "EMOTIONS",
        
        # Phrases: Basic
        "Chào buổi sáng": "Good morning", 
        "Chào buổi tối": "Good evening", 
        "Cảm ơn rất nhiều": "Thank you so much",
        "Tôi là robot AI": "I am an AI robot",
        "Đúng là như vậy": "That is correct",
        "Không thể nào": "No way / Impossible",
        
        # Phrases: Needs
        "Tôi muốn ăn cơm": "I want to eat",
        "Làm ơn cho tôi nước": "Please give me water",
        "Tôi mệt, muốn nghỉ ngơi": "I am tired, need rest",
        "Đi vệ sinh": "Go to restroom",
        "Tôi muốn đi dạo": "I want to walk",
        
        # Phrases: Medical
        "Tôi đau đầu quá": "I have a headache",
        "Tôi cảm thấy khó thở": "I can't breathe well",
        "Đau vùng bụng": "Stomach pain",
        "Đau mỏi vai gáy": "Neck and shoulder pain",
        "Liên lạc bác sĩ ngay": "Call a doctor now",
        
        # Phrases: Emotions
        "Tôi thấy rất hạnh phúc": "I feel happy",
        "Một ngày thật tệ": "I'm having a bad day",
        "Tôi đang bình tĩnh": "I am calm",
        "Cái này tuyệt quá!": "This is great!"
    }

    @staticmethod
    def discover_model():
        if not client: return 'OFFLINE'
        # The user's log suggests models/gemini-1.5-flash is the standard for V1
        targets = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
        for model in targets:
            # We will use the model name with/without the 'models/' prefix depending on SDK behavior
            # In google-genai, it usually appends 'models/' automatically if not present.
            try:
                client.models.generate_content(model=model, contents="Hi")
                AIService.MODEL_ID = model
                return model
            except Exception as e:
                logging.warning(f"Model {model} failed: {e}")
                continue
        return 'gemini-1.5-flash'
    
    @staticmethod
    def get_contextual_prediction(current_input, target_lang="VI"):
        if not client: return []
        lang_map = {"EN": "English", "VI": "Vietnamese"}
        target = lang_map.get(target_lang, "Vietnamese")
        prompt = f"USER TYPED: {current_input}. Predict 3 short communicative phrases in {target}. Return ONLY JSON array."
        try:
            response = client.models.generate_content(model=AIService.MODEL_ID, contents=prompt)
            import json
            text = response.text.strip()
            if "[" in text and "]" in text:
                return json.loads(text[text.find("["):text.find("]")+1])
            return []
        except Exception as e:
            logging.error(f"Prediction Error: {e}")
            return []

    @staticmethod
    def translate_phrase(text, target_lang="EN"):
        if not client: return AIService.FALLBACK_DICT.get(text, text)
        if target_lang == "EN":
            if text in AIService.FALLBACK_DICT: return AIService.FALLBACK_DICT[text]
        
        lang_map = {"EN": "English", "VI": "Vietnamese"}
        target = lang_map.get(target_lang, "Vietnamese")
        prompt = f"Translate to {target}: '{text}'. Return ONLY translated string."
        try:
            response = client.models.generate_content(model=AIService.MODEL_ID, contents=prompt)
            return response.text.strip()
        except:
            return AIService.FALLBACK_DICT.get(text, text)

    @staticmethod
    def translate_batch(data_dict, target_lang="EN"):
        """
        Premium Feature: Translates board data in one batch call.
        """
        if not client or target_lang == "VI": return data_dict
        lang_map = {"EN": "American English", "VI": "Vietnamese"}
        target = lang_map.get(target_lang, "American English")
        
        prompt = f"""
        TASK: Translate every value in this JSON to {target}.
        DATA: {data_dict}
        FORMAT: Return ONLY the translated JSON object.
        """
        try:
            # Check local fallback first for 100% reliability
            if target_lang == "EN":
                results = {}
                for cat, items in data_dict.items():
                    # Translate the Category Key itself
                    new_cat = AIService.FALLBACK_DICT.get(cat, cat)
                    if isinstance(items, list):
                        new_items = []
                        for item in items:
                            new_phrase = AIService.FALLBACK_DICT.get(item["phrase"], item["phrase"])
                            new_items.append({"phrase": new_phrase, "icon": item["icon"]})
                        results[new_cat] = new_items
                    else:
                        results[new_cat] = AIService.FALLBACK_DICT.get(items, items)
                return results

            response = client.models.generate_content(model=AIService.MODEL_ID, contents=prompt)
            import json
            text = response.text.strip()
            # Clean possible markdown markers
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
            return data_dict
        except Exception as e:
            logging.error(f"Batch Translation Error: {e}")
            return data_dict

    @staticmethod
    def describe_object_intent(image_path, target_lang="VI"):
        if not client or not os.path.exists(image_path): return "Error."
        lang_map = {"EN": "English", "VI": "Vietnamese"}
        target = lang_map.get(target_lang, "Vietnamese")
        try:
            img = PIL.Image.open(image_path)
            prompt = f"Describe user's need for this in {target} (short sentence). Return ONLY text."
            response = client.models.generate_content(model=AIService.MODEL_ID, contents=[prompt, img])
            return response.text.strip()
        except Exception as e:
            logging.error(f"Vision error: {e}")
            return "Vision error."
