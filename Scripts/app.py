from flask import Flask, request, render_template_string
import scrape 
import voting_logic as VL 

app = Flask(__name__)
vote_processor = VL.VoteProcessor() # Initialize the VoteProcessor

@app.route('/', methods=['GET'])
def index():
    """
    Renders the main page with daily menus, a poll, and current voting results.
    """
    print("DEBUG: / route accessed (GET request).")
    menus = [scrape.load_menu(r) for r in scrape.RESTAURANTS]
    poll_html = scrape.generate_poll_html("Where do we go for lunch?", menus)
    user_ip = request.remote_addr
    print(f"DEBUG: User IP for GET request: {user_ip}")
    
    show_warning = VL.is_ip_in_germany(user_ip) 
    
    current_vote_counts = vote_processor.get_results()
    print(f"DEBUG: Vote counts for GET request: {current_vote_counts}")
    print(f"DEBUG: show_warning for GET request: {show_warning}")

    try:
        with open('output/index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return render_template_string(
            html_content, 
            poll=poll_html,
            show_warning=show_warning,
            menus=menus,
            message=None, # No initial message on page load
            vote_counts=current_vote_counts 
        )
    except FileNotFoundError:
        print("ERROR: output/index.html not found during GET request.")
        return "Error: output/index.html not found. Please ensure the menu scraper script has been run.", 404
    except UnicodeDecodeError as e:
        print(f"ERROR: Error decoding output/index.html during GET request: {e}")
        return f"Error decoding output/index.html: {e}. Please verify its encoding.", 500
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while loading the page (GET request): {e}")
        return f"An unexpected error occurred: {e}", 500

@app.route('/vote', methods=['POST'])
def vote():
    """
    Handles poll submissions, processes votes, and re-renders the page with updated results.
    """
    print("DEBUG: /vote route accessed (POST request).")
    option = request.form.get('poll')
    user_ip = request.remote_addr
    message = None 
    print(f"DEBUG: User IP for POST request: {user_ip}, Option selected: {option}")

    if not VL.is_ip_in_prague(user_ip):
        message = "Voting is allowed only from the office."
        print(f"DEBUG: Voting blocked for IP {user_ip}: Not in Prague.")
    elif not vote_processor.add_vote(option, user_ip):
        message = "You have already voted or voting is blocked."
        print(f"DEBUG: Voting blocked for IP {user_ip}: Already voted or add_vote failed.")
    else:
        message = "Thank you for voting!"
        print(f"DEBUG: Vote successfully processed for IP {user_ip}.")

    print(f"DEBUG: Message after vote processing: {message}")

    menus = [scrape.load_menu(r) for r in scrape.RESTAURANTS]
    poll_html = scrape.generate_poll_html("Where do we go for lunch?", menus)
    show_warning = VL.is_ip_in_germany(user_ip)

    current_vote_counts = vote_processor.get_results()
    print(f"DEBUG: Vote counts for POST request (after vote): {current_vote_counts}")

    try:
        with open('output/index.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return render_template_string(
            html_content, 
            poll=poll_html,
            show_warning=show_warning,
            menus=menus,
            message=message, 
            vote_counts=current_vote_counts 
        )
    except FileNotFoundError:
        print("ERROR: output/index.html not found during POST request.")
        return "Error: output/index.html not found after vote. Please ensure the menu scraper script has been run.", 404
    except UnicodeDecodeError as e:
        print(f"ERROR: Error decoding output/index.html during POST request: {e}")
        return f"Error decoding output/index.html after vote: {e}. Please verify its encoding.", 500
    except Exception as e:
        print(f"ERROR: An unexpected error occurred after voting (POST request): {e}")
        return f"An unexpected error occurred after voting: {e}", 500

if __name__ == '__main__':
    app.run(debug=False)
    #app.run(debug=True, port=8000)
