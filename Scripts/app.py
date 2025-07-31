from flask import Flask, request, render_template_string
import scrape
import voting_logic as VL

app = Flask(__name__)
vote_processor = VL.VoteProcessor()

@app.route('/', methods=['GET'])
def index():
    menus = [scrape.load_menu(r) for r in scrape.RESTAURANTS]
    poll_html = scrape.generate_poll_html("Where do we go for lunch?", menus)
    user_ip = request.remote_addr
    show_warning = VL.is_ip_in_germany(user_ip)
    return render_template_string(
        open('output/index.html').read(),
        poll=poll_html,
        show_warning=show_warning,
        menus=menus,
        message=None
    )

@app.route('/vote', methods=['POST'])
def vote():
    option = request.form.get('poll')
    user_ip = request.remote_addr

    if not VL.is_ip_in_prague(user_ip):
        message = "Voting is allowed only from the office."
    elif not vote_processor.add_vote(option, user_ip):
        message = "You have already voted or voting is blocked."
    else:
        message = "Thank you for voting!"

    menus = [scrape.load_menu(r) for r in scrape.RESTAURANTS]
    poll_html = scrape.generate_poll_html("Where do we go for lunch?", menus)
    show_warning = VL.is_ip_in_germany(user_ip)

    return render_template_string(
        open('output/index.html').read(),
        poll=poll_html,
        show_warning=show_warning,
        menus=menus,
        message=message
    )

if __name__ == '__main__':
    app.run(debug=True,port=8000)
