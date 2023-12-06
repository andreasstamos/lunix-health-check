from flask import Flask, current_app, render_template
from poll import start_poll
import time
import datetime

def create_app():
	app = Flask(__name__)
	with app.app_context():
		current_app.status = start_poll()
	return app
app = create_app()

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.date.today().year}

@app.get('/')
def main():
	if current_app.status.current == "reconnect":
		return render_template('reconnect.html')
	if current_app.status.current == "down":
		return render_template('down.html', status=current_app.status, current_time=time.time())

	return render_template('up.html', status=current_app.status, current_time=time.time())


if __name__ == "__main__":
	app.run(debug=True)

