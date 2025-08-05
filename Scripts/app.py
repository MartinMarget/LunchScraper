from flask import Flask, request, render_template, redirect, url_for
import scrape
import voting_logic as VL
import os
from flask import send_from_directory
from jinja2 import TemplateNotFound

# PROJECT_ROOT is the parent directory of where app.py is located (e.g., the root of your project)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_FOLDER = os.path.dirname(__file__)

# The Flask application instance is now configured to look for templates
# in the 'Scripts' folder, which is the directory where app.py is located.
# We explicitly set the template folder to the current directory.
app = Flask(__name__, template_folder=SCRIPTS_FOLDER)
vote_processor = VL.VoteProcessor() # Initialize the VoteProcessor

# Route to serve static assets like images from the 'Output' directory
@app.route('/Output/<path:filename>')
def output_static(filename):
    return send_from_directory(os.path.join(PROJECT_ROOT, 'Output'), filename)

@app.route('/', methods=['GET'])
def index():
    """
    Renders the main page with daily menus and the poll.
    """
    print("DEBUG: / route accessed (GET request).")
    
    menus = [scrape.load_menu(r) for r in scrape.RESTAURANTS]
    poll_html = scrape.generate_poll_html("Where do we go for lunch?", menus)
    user_ip = VL.get_client_ip()
    print(f"DEBUG: User IP for GET request: {user_ip}")
    
    show_warning = VL.is_ip_in_germany(user_ip) 
    current_vote_counts = vote_processor.get_results()
    print(f"DEBUG: Vote counts for GET request: {current_vote_counts}")
    
    message = None
    if user_ip in vote_processor.voted_ips:
        message = "You have already voted or voting is blocked."
        print(f"DEBUG: Poll hidden for IP {user_ip} (already voted)")
    
    try:
        # Correctly render the template. Flask now looks for 'template.html' in the 'Scripts' folder.
        return render_template(
            'template.html',  # Your template file name
            poll=poll_html,
            show_warning=show_warning,
            menus=menus,
            message=message,
            vote_counts=current_vote_counts 
        )
    except TemplateNotFound:
        return f"Error: Template 'template.html' not found in the 'Scripts' folder.", 404

@app.route('/vote', methods=['POST'])
def vote():
    """
    Handles poll submissions, processes votes, and re-renders the page with updated results.
    """
    print("DEBUG: /vote route accessed (POST request).")
    option = request.form.get('poll')
    user_ip = VL.get_client_ip()
    print(f"DEBUG: User IP for POST request: {user_ip}, Option selected: {option}")

    message = None
    if not vote_processor.add_vote(option, user_ip):
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
        # Correctly render the template with the new message and vote counts
        return render_template(
            'template.html',  # Your template file name
            poll=poll_html,
            show_warning=show_warning,
            menus=menus,
            message=message, 
            vote_counts=current_vote_counts 
        )
    except TemplateNotFound:
        return f"Error: Template 'template.html' not found in the 'Scripts' folder.", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
