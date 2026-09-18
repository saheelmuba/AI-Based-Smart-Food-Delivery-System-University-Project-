import argparse
import difflib
import re
from pathlib import Path

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    from googletrans import Translator
except ImportError:
    Translator = None

ROOT = Path(__file__).resolve().parent
MENU_CSV = ROOT / 'menu_dataset.csv'

LANGUAGES = {
    'en-US': 'English',
    'ta-IN': 'Tamil',
    'si-LK': 'Sinhala',
    'hi-IN': 'Hindi',
    'es-ES': 'Spanish',
}

DEFAULT_MENU = [
    {'name': 'chicken burger', 'price': 1200},
    {'name': 'orange juice', 'price': 500},
    {'name': 'pizza', 'price': 2500},
    {'name': 'coke', 'price': 300},
]

SPELLED_NUMBERS = {
    'zero': 0,
    'one': 1,
    'two': 2,
    'three': 3,
    'four': 4,
    'five': 5,
    'six': 6,
    'seven': 7,
    'eight': 8,
    'nine': 9,
    'ten': 10,
}

RESPONSE_TEMPLATES = {
    'greeting': 'Welcome to AI Smart Food Delivery System! Please speak your order or type it below.',
    'ask_order': 'What would you like to order today?',
    'menu_header': 'Menu',
    'order_empty': 'No matching food items found. Please try again or ask to show the menu.',
    'order_summary': 'Order Details',
    'total_amount': 'Total Amount = Rs. {total}',
    'add_item': 'Added {qty} x {item} to your order.',
    'goodbye': 'Thank you! Your order is ready.',
    'recommend': 'You may also like: {items}',
    'language_notice': 'Bot responses will appear in the selected language when available.',
}

TRANSLATION_CACHE = {}


def load_menu():
    if MENU_CSV.exists():
        try:
            import pandas as pd
            df = pd.read_csv(MENU_CSV, encoding='utf-8')
            df['name'] = df['name'].astype(str).str.strip()
            df['price'] = pd.to_numeric(df['price'], errors='coerce').fillna(0).astype(int)
            return [{'name': row['name'], 'price': int(row['price'])} for _, row in df.iterrows()]
        except Exception:
            pass
    return DEFAULT_MENU.copy()


def build_item_index(menu_items):
    index = []
    for item in menu_items:
        normalized = normalize_text(item['name'])
        tokens = normalized.split()
        index.append({'name': item['name'], 'price': item['price'], 'normalized': normalized, 'tokens': set(tokens)})
    return index


def normalize_text(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", ' ', text)
    text = re.sub(r"\s+", ' ', text).strip()
    return text


def parse_quantity(text):
    text = text.lower()
    digits = re.findall(r"\b(\d+)\b", text)
    if digits:
        return int(digits[-1])
    for word, value in SPELLED_NUMBERS.items():
        if re.search(rf"\b{word}\b", text):
            return value
    return 1


def find_order_items(text, item_index):
    text = normalize_text(text)
    ordered = []
    for item in item_index:
        if item['normalized'] in text:
            ordered.append(item)
            continue
        if item['tokens'] and item['tokens'].issubset(set(text.split())):
            ordered.append(item)
            continue
        close_matches = difflib.get_close_matches(item['normalized'], [text], cutoff=0.75)
        if close_matches:
            ordered.append(item)
            continue
    if not ordered:
        words = text.split()
        for item in item_index:
            if len(item['tokens'].intersection(words)) >= max(1, len(item['tokens']) - 1):
                ordered.append(item)
    unique = []
    seen = set()
    for item in ordered:
        if item['name'] not in seen:
            seen.add(item['name'])
            unique.append(item)
    return unique


def translate_text(text, target_lang):
    if target_lang.startswith('en') or Translator is None:
        return text
    cache_key = (text, target_lang)
    if cache_key in TRANSLATION_CACHE:
        return TRANSLATION_CACHE[cache_key]
    try:
        translator = Translator()
        translated = translator.translate(text, dest=target_lang.split('-')[0]).text
        TRANSLATION_CACHE[cache_key] = translated
        return translated
    except Exception:
        return text


def format_response(key, lang, **kwargs):
    template = RESPONSE_TEMPLATES.get(key, '')
    message = template.format(**kwargs) if kwargs else template
    return translate_text(message, lang)


def recognize_audio(recognizer, audio, language, backend):
    if backend == 'sphinx':
        if not hasattr(sr, 'PocketSphinx'):
            raise RuntimeError('PocketSphinx is unavailable. Install pocketsphinx for offline mode.')
        return recognizer.recognize_sphinx(audio, language=language)
    return recognizer.recognize_google(audio, language=language)


def transcribe_audio_file(file_path, language='en-US', backend='google'):
    if sr is None:
        raise ImportError('speech_recognition package is required. Install with: pip install SpeechRecognition')
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_path) as source:
            audio = recognizer.record(source)
        text = recognize_audio(recognizer, audio, language=language, backend=backend)
        return text
    except sr.UnknownValueError:
        return ''
    except Exception:
        return ''


def load_recommender():
    try:
        import train_menu_recommender as trainer
        return trainer
    except ImportError:
        return None


def train_recommender():
    trainer = load_recommender()
    if trainer is None:
        print('Recommender training module not available. Install scikit-learn and check train_menu_recommender.py.')
        return
    trainer.train()


def parse_voice_command(transcript):
    normalized_text = normalize_text(transcript)

    if any(keyword in normalized_text for keyword in ['show menu', 'menu', 'what can i order', 'show the menu', 'list']):
        items = [item['name'] for item in load_menu()]
        return 'show_menu', {'items': items}

    items = find_order_items(normalized_text, build_item_index(load_menu()))
    quantity = parse_quantity(normalized_text)
    if items:
        total = sum(item['price'] for item in items) * quantity
        return 'order', {
            'items': [item['name'] for item in items],
            'quantity': quantity,
            'total': total,
        }

    if any(keyword in normalized_text for keyword in ['help', 'assist', 'support']):
        return 'help', {}

    return 'unknown', {}


def log_voice_event(user_id, transcript, command, confidence=None):
    from database import db
    from models import VoiceLog

    voice_log = VoiceLog(
        user_id=user_id,
        transcript=transcript,
        command=command,
        confidence=confidence,
    )
    db.session.add(voice_log)
    db.session.commit()
    return voice_log


def build_parser():
    parser = argparse.ArgumentParser(description='AI Smart Food Delivery multilingual voice-ordering chatbot.')
    parser.add_argument('--lang', choices=LANGUAGES, default='en-US', help='Speech recognition and chatbot language.')
    parser.add_argument('--timeout', type=float, default=5.0, help='Seconds to wait for audio before timing out.')
    parser.add_argument('--phrase-time-limit', type=float, default=6.0, help='Max seconds per spoken phrase.')
    parser.add_argument('--backend', choices=['google', 'sphinx'], default='google', help='Speech recognition backend.')
    parser.add_argument('--mode', choices=['voice', 'text', 'train'], default='voice', help='Run mode: voice input, text input, or train the recommender.')
    parser.add_argument('--show-menu', action='store_true', help='Display the available menu items at startup.')
    return parser


def print_menu(menu_items, lang):
    header = format_response('menu_header', lang)
    print(f'\n{header}:')
    for item in menu_items:
        print(f"- {item['name']}  Rs.{item['price']}")
    print('')


def chat_loop(menu_items, item_index, lang, recognizer=None, microphone=None, backend='google'):
    print(format_response('greeting', lang))
    print(format_response('language_notice', lang))
    print(format_response('ask_order', lang))
    while True:
        if recognizer and microphone:
            try:
                with microphone as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.8)
                    print('Listening...')
                    audio = recognizer.listen(source, timeout=5.0, phrase_time_limit=6.0)
                text = recognize_audio(recognizer, audio, language=lang, backend=backend)
                print(f'Customer Said: {text}')
            except sr.WaitTimeoutError:
                print(format_response('order_empty', lang))
                continue
            except sr.UnknownValueError:
                print(format_response('order_empty', lang))
                continue
            except sr.RequestError as err:
                print(f'Recognition service failed: {err}')
                return
            except KeyboardInterrupt:
                print('\n' + format_response('goodbye', lang))
                return
            except Exception as exc:
                print(f'Error: {exc}')
                return
        else:
            try:
                text = input('> ').strip()
            except KeyboardInterrupt:
                print('\n' + format_response('goodbye', lang))
                return
            if not text:
                continue

        if text.lower() in {'exit', 'quit', 'stop'}:
            print(format_response('goodbye', lang))
            return
        if text.lower() in {'menu', 'show menu', 'show the menu'}:
            print_menu(menu_items, lang)
            continue

        quantity = parse_quantity(text)
        items = find_order_items(text, item_index)
        if not items:
            print(format_response('order_empty', lang))
            continue

        total = sum(item['price'] for item in items) * quantity
        print('\n' + format_response('order_summary', lang))
        for item in items:
            print(f"{item['name'].title()} - Rs.{item['price']}")
        print(format_response('total_amount', lang, total=total))
        order_names = ', '.join(item['name'].title() for item in items)
        print(format_response('add_item', lang, qty=quantity, item=order_names))
        print('')


def main():
    parser = build_parser()
    args = parser.parse_args()
    menu_items = load_menu()
    item_index = build_item_index(menu_items)

    if args.show_menu:
        print_menu(menu_items, args.lang)

    if args.mode == 'train':
        train_recommender()
        return

    if args.mode == 'voice':
        if sr is None:
            raise ImportError('speech_recognition package is required. Install with: pip install SpeechRecognition')
        recognizer = sr.Recognizer()
        try:
            microphone = sr.Microphone()
        except Exception as exc:
            raise RuntimeError('Microphone access failed. Ensure your microphone is available and your OS has granted permission.') from exc
        chat_loop(menu_items, item_index, args.lang, recognizer=recognizer, microphone=microphone, backend=args.backend)
        return

    chat_loop(menu_items, item_index, args.lang)


if __name__ == '__main__':
    main()
