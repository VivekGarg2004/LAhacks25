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

# ...existing code...

@graph_bp.route('/table', methods=['GET', 'POST'])
def create_table_image():
    """Generate a table visualization as an image response"""
    try:
        # Get data from request or use sample data
        if request.method == 'POST' and request.is_json:
            data = request.json
        else:
            # Sample data as fallback
            data = {
                "headers": ["Name", "Value", "Change"],
                "rows": [
                    ["Item A", 100, "+20%"],
                    ["Item B", 80, "-5%"],
                    ["Item C", 120, "+10%"],
                    ["Item D", 90, "0%"]
                ]
            }
        
        # Extract headers and rows
        headers = data.get("headers", [])
        rows = data.get("rows", [])
        
        # Calculate dynamic figure size based on data
        num_rows = len(rows)
        num_cols = len(headers) if headers else (len(rows[0]) if rows else 0)
        
        # Base size + additional space per row/column
        width = 2 + (num_cols * 1.2)
        height = 2 + (num_rows * 0.6)
        
        # Create a figure and axis with dynamic sizing
        fig, ax = plt.subplots(figsize=(width, height))
        
        # Hide axes
        ax.axis('tight')
        ax.axis('off')
        
        # Create the table
        table = ax.table(
            cellText=rows,
            colLabels=headers,
            cellLoc='center',
            loc='center'
        )
        
        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.2, 1.5)  # Adjust table size
        
        # Add a title if provided
        if "title" in data:
            plt.title(data["title"], fontsize=16, pad=20)
        
        # Save the plot to a BytesIO object
        img = io.BytesIO()
        fig.savefig(img, format='png', bbox_inches='tight', dpi=150, transparent=True)
        img.seek(0)
        plt.close(fig)  # Explicitly close the figure
        
        # Return the image as a response
        return Response(img, mimetype='image/png')
    except Exception as e:
        # Consistent error handling
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500