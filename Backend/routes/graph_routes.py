from flask import Blueprint, Response, jsonify, request
import io
import traceback
import matplotlib
# Force matplotlib to use non-interactive backend that works in Flask threads
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

graph_bp = Blueprint('graph', __name__)

@graph_bp.route('/plot', methods=['GET'])
def plot_graph():
    """Generate a simple plot as an image response"""
    try:
        # Create a figure with the non-interactive backend
        fig, ax = plt.subplots(figsize=(6, 4))
        
        # Generate sample data - can be replaced with real data
        x = np.array([1, 2, 3, 4])
        y = np.array([1, 4, 9, 16])
        
        # Create the plot
        ax.plot(x, y, marker='o')
        ax.set_title('Basic Plot')
        ax.set_xlabel('X-axis')
        ax.set_ylabel('Y-axis')

        # Save the plot to a BytesIO object
        img = io.BytesIO()
        fig.savefig(img, format='png')
        img.seek(0)
        plt.close(fig)  # Explicitly close the figure

        # Return the image as a response
        return Response(img, mimetype='image/png')
    except Exception as e:
        # Consistent error handling with other routes
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500

@graph_bp.route('/sample-data', methods=['GET'])
def get_sample_data():
    """Return sample data for testing"""
    try:
        data = {
            "x_values": [1, 2, 3, 4, 5],
            "y_values": [1, 4, 9, 16, 25],
            "title": "Sample Quadratic Data"
        }
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500