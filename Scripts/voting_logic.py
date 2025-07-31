import json
import os
import threading
import requests

VOTES_FILE = "votes.json"
LOCK = threading.Lock()

def check_ip_location(ip):
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        data = response.json()
        country = data.get("country_name", "").lower()
        city = data.get("city", "").lower()
        return country, city
    except Exception:
        return None, None

def is_ip_in_germany(ip):
    country, _ = check_ip_location(ip)
    return country == "germany"

def is_ip_in_prague(ip):
    _, city = check_ip_location(ip)
    return city == "prague"

class VoteProcessor:
    def __init__(self):
        self.votes = {}
        self.voted_ips = set()
        self.load_votes()

    def load_votes(self):
        if os.path.exists(VOTES_FILE):
            with open(VOTES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.votes = data.get("votes", {})
                self.voted_ips = set(data.get("voted_ips", []))
        else:
            self.votes = {}
            self.voted_ips = set()

    def save_votes(self):
        with LOCK:
            with open(VOTES_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "votes": self.votes,
                    "voted_ips": list(self.voted_ips)
                }, f, indent=2)

    def add_vote(self, option, ip_address):
        if ip_address in self.voted_ips:
            return False  # IP already voted
        self.voted_ips.add(ip_address)
        self.votes[option] = self.votes.get(option, 0) + 1
        self.save_votes()
        return True

    def get_results(self):
        return self.votes

    def reset_votes(self):
        self.votes = {}
        self.voted_ips = set()
        self.save_votes()
