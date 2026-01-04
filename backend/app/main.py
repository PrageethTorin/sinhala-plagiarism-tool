from flask import Flask
from flask_cors import CORS

from app.routes.plagiarism import plagiarism_bp
from app.routes import auth  # if auth is Flask-based

app = Flask(__name__)
CORS(app)

# Register routes
app.register_blueprint(plagiarism_bp, url_prefix="/api/plagiarism")

# If auth is Flask blueprint
if hasattr(auth, "auth_bp"):
    app.register_blueprint(auth.auth_bp, url_prefix="/auth")

@app.route("/")
def root():
    return {"status": "Backend running"}

if __name__ == "__main__":
    app.run(debug=True)
