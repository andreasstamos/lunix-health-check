from flask import Flask, current_app
from poll import start_poll

app = Flask(__name__)

@app.get('/')
def main():
	if current_app.status.last_update is None:
		return {"status": "Initializing..."}
	if current_app.status.sensors is None:
		return {"status": "down", "last_update": current_app.status.last_update, "reason": current_app.status.reason}
	return {"status": "up", "last_update": current_app.status.last_update, "sensors": current_app.status.sensors}

if __name__ == "__main__":
	with app.app_context():
		current_app.status = start_poll()
	app.run(debug=True)
