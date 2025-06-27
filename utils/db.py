import json
import os

BASE = os.path.dirname(__file__)
USER_FILE = os.path.join(BASE, "../data/users.json")
PHOTO_FILE = os.path.join(BASE, "../data/photos.json")

def load_users():
    with open(USER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(data):
    with open(USER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_photos():
    with open(PHOTO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_photos(data):
    with open(PHOTO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def all_user_ids():
    return load_users().keys()
