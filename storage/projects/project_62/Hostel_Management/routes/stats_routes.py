from flask import Blueprint, jsonify
from models import DashboardStats

stats_bp = Blueprint('stats', __name__, url_prefix='/api/stats')

@stats_bp.route('/dashboard', methods=['GET'])
def get_dashboard_stats():
    try:
        metrics = DashboardStats.get_metrics()
        return jsonify({"success": True, "data": metrics}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Error loading dashboard statistics: {str(e)}"}), 500
