import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from config import Config
from db import test_db_connection
from setup_database import setup_all
from routes.auth_routes import auth_bp
from routes.student_routes import student_bp
from routes.room_routes import room_bp
from routes.booking_routes import booking_bp
from routes.complaint_routes import complaint_bp
from routes.stats_routes import stats_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(room_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(complaint_bp)
    app.register_blueprint(stats_bp)

    # -------------------------------------------------------------
    # Page Navigation Routes
    # -------------------------------------------------------------
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login')
    def login_page():
        # If user is already logged in, redirect to respective portal
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_portal'))
        elif role == 'student':
            return redirect(url_for('student_portal'))
        return render_template('login.html')

    @app.route('/student')
    def student_portal():
        return render_template('student.html')

    @app.route('/admin')
    def admin_portal():
        return render_template('admin.html')

    # -------------------------------------------------------------
    # Global Error Handlers
    # -------------------------------------------------------------
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "message": "API route not found."}), 404
        return render_template('index.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "message": "Internal server error occurred."}), 500
        return render_template('index.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    # Initialize DB if running directly
    db_engine = test_db_connection()
    print(f"[INIT] Active Database Engine: {db_engine.upper()}")
    # Start web server
    app.run(host='0.0.0.0', port=5000, debug=True)
