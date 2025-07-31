# voting_logic.py (or VL.py)
import json
import os
import threading
import requests

VOTES_FILE = "votes.json"
LOCK = threading.Lock()

def check_ip_location(ip):
    """
    Checks the geographical location (country and city) of an IP address
    using the ipapi.co service.
    """
    print(f"DEBUG: Checking IP location for: {ip}")
    try:
        response = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        data = response.json()
        country = data.get("country_name", "").lower()
        city = data.get("city", "").lower()
        print(f"DEBUG: IP {ip} location: Country={country}, City={city}")
        return country, city
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Network or HTTP error checking IP location for {ip}: {e}")
        return None, None
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during IP location check for {ip}: {e}")
        return None, None

def is_ip_in_germany(ip):
    """
    Determines if the given IP address is located in Germany.
    """
    country, _ = check_ip_location(ip)
    result = country == "germany"
    print(f"DEBUG: is_ip_in_germany({ip}) -> {result}")
    return result

def is_ip_in_prague(ip):
    """
    Determines if the given IP address is located in Prague.
    """
    _, city = check_ip_location(ip)
    result = city == "prague"
    print(f"DEBUG: is_ip_in_prague({ip}) -> {result}")
    return result

class VoteProcessor:
    def __init__(self):
        self.votes = {} 
        self.voted_ips = set() 
        self.load_votes() # Load existing votes when the processor is initialized
        print(f"DEBUG: VoteProcessor initialized. Current votes: {self.votes}, Voted IPs: {self.voted_ips}")

    def load_votes(self):
        """
        Loads vote counts and voted IPs from a JSON file.
        Initializes empty if the file does not exist.
        """
        print(f"DEBUG: Attempting to load votes from {VOTES_FILE}")
        if os.path.exists(VOTES_FILE):
            try:
                with open(VOTES_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.votes = data.get("votes", {})
                    self.voted_ips = set(data.get("voted_ips", []))
                print(f"DEBUG: Successfully loaded votes. Votes: {self.votes}, IPs: {self.voted_ips}")
            except json.JSONDecodeError as e:
                print(f"ERROR: Error decoding {VOTES_FILE}: {e}. Starting with empty votes.")
                self.votes = {}
                self.voted_ips = set()
            except Exception as e:
                print(f"ERROR: An unexpected error occurred loading votes: {e}. Starting with empty votes.")
                self.votes = {}
                self.voted_ips = set()
        else:
            print(f"DEBUG: {VOTES_FILE} not found. Initializing with empty votes.")
            self.votes = {}
            self.voted_ips = set()

    def save_votes(self):
        """
        Saves current vote counts and voted IPs to a JSON file.
        Uses a lock to ensure thread-safe writing.
        """
        print(f"DEBUG: Attempting to save votes to {VOTES_FILE}. Data: Votes={self.votes}, IPs={self.voted_ips}")
        with LOCK: # Acquire lock to prevent race conditions during file write
            try:
                with open(VOTES_FILE, "w", encoding="utf-8") as f:
                    json.dump({
                        "votes": self.votes,
                        "voted_ips": list(self.voted_ips) # Convert set to list for JSON serialization
                    }, f, indent=2) # Use indent for pretty-printing JSON
                print(f"DEBUG: Successfully saved votes to {VOTES_FILE}")
            except Exception as e:
                print(f"ERROR: Error saving votes to {VOTES_FILE}: {e}")

    def add_vote(self, option, ip_address):
        """
        Adds a vote for the given option from the specified IP.
        Returns True if the vote was added, False if the IP has already voted.
        """
        print(f"DEBUG: add_vote called for option '{option}' from IP '{ip_address}'")
        if ip_address in self.voted_ips:
            print(f"DEBUG: IP {ip_address} has already voted. Vote not added.")
            return False  # IP already voted

        self.voted_ips.add(ip_address) # Add IP to the set of voted IPs
        self.votes[option] = self.votes.get(option, 0) + 1 # Increment vote count
        self.save_votes() # Save the updated votes to file
        print(f"DEBUG: Vote added. New votes: {self.votes}")
        return True

    def get_results(self):
        """
        Returns a dictionary of current vote counts for all options.
        """
        results = dict(self.votes)
        print(f"DEBUG: get_results called. Returning: {results}")
        return results

    def reset_votes(self):
        """
        Resets all vote counts and clears the list of voted IPs.
        """
        print("DEBUG: reset_votes called.")
        self.votes = {}
        self.voted_ips = set()
        self.save_votes() # Save the reset state to file
        print("DEBUG: Votes reset.")