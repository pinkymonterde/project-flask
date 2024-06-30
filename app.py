from flask import Flask, render_template, request, redirect, url_for, flash
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from werkzeug.utils import secure_filename
import logging
# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './data'
app.config['STATIC_FOLDER'] = './static'
app.config['ALLOWED_EXTENSIONS'] = {'csv', 'xlsx', 'json'}
app.secret_key = 'your_secret_key'

# Ensure the upload and static folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def load_data(file_path):
    ext = file_path.rsplit('.', 1)[1].lower()
    if ext == 'csv':
        return pd.read_csv(file_path)
    elif ext == 'xlsx':
        return pd.read_excel(file_path)
    elif ext == 'json':
        return pd.read_json(file_path)
    else:
        raise ValueError("Unsupported file format")


@app.route('/')
def index():
    logger.debug("Rendering index page.")
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        logger.debug("POST request received.")
        if 'file' not in request.files:
            flash('No file part')
            logger.error("No file part in request.")
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            logger.error("No file selected for uploading.")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                file.save(file_path)
                logger.debug(f"File saved to {file_path}")
            except Exception as e:
                logger.error(f"Failed to save file: {e}", exc_info=True)
                flash(f"An error occurred while saving the file: {e}")
                return redirect(request.url)

            return redirect(url_for('data_table', filename=filename))

    return render_template('upload.html')


@app.route('/data_table/<filename>', methods=['GET', 'POST'])
def data_table(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        df = load_data(file_path)
        if request.method == 'POST':
            return redirect(url_for('generate_graphs', filename=filename))

        return render_template('data_table.html', tables=[df.to_html(classes='data', header="true")], filename=filename)
    except Exception as e:
        logger.error(f"An error occurred in data_table: {e}", exc_info=True)
        flash(f"An error occurred: {e}")
        return redirect(url_for('upload'))


@app.route('/generate_graphs/<filename>')
def generate_graphs(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    try:
        df = load_data(file_path)

        required_columns = [
            'Region', 'Literacy Rate', 'Teacher', 'Textbook', 'budget'
        ]

        for column in required_columns:
            if column not in df.columns:
                raise ValueError(f"Column '{column}' not found in the uploaded file")

        # Path to save plots
        static_folder = app.config['STATIC_FOLDER']

        # Insight 1: Scatter plot
        plt.figure(figsize=(10, 6))
        sns.scatterplot(data=df, x='Teacher', y='Literacy Rate')
        plt.title('Insight 1: Number of Teachers vs Literacy Rate')
        plt.tight_layout()

        # Save the plot
        insight1_img = os.path.join(static_folder, 'insight1.png')
        plt.savefig(insight1_img)
        plt.close()

        # Similarly, create and save other insights as needed

        return redirect(url_for('insight1', filename=filename))

    except Exception as e:
        logger.error(f"An error occurred in generate_graphs: {e}", exc_info=True)
        flash(f"An error occurred: {e}")
        return redirect(url_for('upload'))


@app.route('/insight1/<filename>')
def insight1(filename):
    return render_template('insight1.html', image='insight1.png', filename=filename)


if __name__ == '__main__':
    logger.debug("Starting Flask app.")
    app.run(debug=True)
