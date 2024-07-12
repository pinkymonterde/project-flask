import os
import logging
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
import numpy as np

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = './data'
app.config['STATIC_FOLDER'] = './static'
app.config['UPLOAD_EXTENSIONS'] = ['csv', 'xlsx', 'json']
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
app.secret_key = 'your_secret_key'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:12345@127.0.0.1:3306/inte'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Define the database model
class Summary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.String(120), nullable=False)
    tpr_region = db.Column(db.String(120), nullable=False)
    budget = db.Column(db.Integer, nullable=False)
    tpr = db.Column(db.Integer, nullable=False)
    textbook = db.Column(db.Integer, nullable=False)
    literacy = db.Column(db.Integer, nullable=False)
    students = db.Column(db.Integer, nullable=False)
    SURVIVAL_RATE = db.Column(db.Integer, nullable=False)
    def __repr__(self):
        return f'<Summary {self.region}>'


# Create the database tables
with app.app_context():
    db.create_all()  #

# Ensure the upload and static folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['UPLOAD_EXTENSIONS']


def load_data(file_path):
    _, file_extension = os.path.splitext(file_path)
    if file_extension == '.csv':
        return pd.read_csv(file_path)
    elif file_extension == '.xlsx':
        return pd.read_excel(file_path)
    elif file_extension == '.json':
        return pd.read_json(file_path)
    else:
        raise ValueError(f'Unsupported file type: {file_extension}')


def process_data(df):
    # Set the index to the 'REGION' column
    df = df.set_index("REGION")
    df = df.apply(pd.to_numeric, errors='ignore')
    df = df.dropna()
    return df


def create_plots(df):
    sns.set(style="whitegrid")

    # Define region colors
    region_colors = {
        'NCR': '#1f77b4',  # muted blue
        'CAR': '#ff7f0e',  # safety orange
        'I': '#2ca02c',  # cooked asparagus green
        'II': '#d62728',  # brick red
        'III': '#9467bd',  # muted purple
        'IV-A': '#8c564b',  # chestnut brown
        'IV-B': '#e377c2',  # raspberry yogurt pink
        'V': '#7f7f7f',  # middle gray
        'VI': '#bcbd22',  # curry yellow-green
        'VII': '#17becf',  # blue-teal
        'VIII': '#ffbb78',  # light orange
        'IX': '#98df8a',  # light green
        'X': '#ff9896',  # light red
        'XI': '#c5b0d5',  # light purple
        'XII': '#c49c94',  # light brown
        'XIII': '#f7b6d2',  # light pink
        'ARMM': '#dbdb8d'  # light yellow-green
    }

    # Plot: Number of Teachers and Students per Region
    df_melted = df.reset_index().melt(id_vars=['REGION'], value_vars=['TEACHER', 'STUDENTS'], var_name='Category',
                                      value_name='Total')
    bar_plot_tpr, ax = plt.subplots(figsize=(10, 6))
    ax = sns.barplot(data=df_melted, x='REGION', y='Total', hue='Category', palette={'TEACHER': 'b', 'STUDENTS': 'r'})
    ax.set_xticklabels(df_melted['REGION'], rotation=45)
    plt.xlabel('Region', fontweight='bold')
    plt.ylabel('Total Number', fontweight='bold')
    plt.legend()
    bar_plot_tpr_path = os.path.join(app.config['STATIC_FOLDER'], 'bar_plot_tpr.png')
    plt.savefig(bar_plot_tpr_path, bbox_inches='tight', dpi=300)
    plt.close(bar_plot_tpr)

    # Line Graph: Budget Allocation
    line_chart_budget = plt.figure(figsize=(10, 6))
    sns.lineplot(x='REGION', y='BUDGET', data=df, marker='o', color='r')
    plt.xlabel("Region", fontweight='bold')
    plt.ylabel("Average Budget Allocation", fontweight='bold')
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    line_chart_budget_path = os.path.join(app.config['STATIC_FOLDER'], 'line_chart_budget.png')
    plt.savefig(line_chart_budget_path, bbox_inches='tight', dpi=300)
    plt.close(line_chart_budget)

    # Line Graph: Textbook Availability per Region
    line_chart_textbook = plt.figure(figsize=(10, 6))
    sns.lineplot(x='REGION', y='TEXTBOOK', data=df, marker='o', color='b')
    plt.xlabel("Region", fontweight='bold')
    plt.ylabel("Average Textbooks Distribution", fontweight='bold')
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    plt.tight_layout()
    line_chart_textbook_path = os.path.join(app.config['STATIC_FOLDER'], 'line_chart_textbook.png')
    plt.savefig(line_chart_textbook_path, bbox_inches='tight', dpi=300)
    plt.close(line_chart_textbook)


    # Bar plot: School Survival Rate by Region
    bar_plot_survival = plt.figure(figsize=(10, 6))
    sns.barplot(x='REGION', y='SURVIVAL_RATE', data=df, palette=region_colors, ci=None)
    plt.xlabel("Region", fontweight='bold')
    plt.ylabel("School Survival Rate", fontweight='bold')
    plt.xticks(rotation=45, fontsize=12)  # Rotate x-axis labels for better readability
    plt.yticks(fontsize=12)
    plt.tight_layout()
    bar_plot_survival_path = os.path.join(app.config['STATIC_FOLDER'], 'bar_plot_survival.png')
    plt.savefig(bar_plot_survival_path, bbox_inches='tight', dpi=300)
    plt.close(bar_plot_survival)

    # Bar Chart for Literacy Rates
    bar_chart_literacy = plt.figure(figsize=(10, 6))
    sns.barplot(x='TPR_REGION', y='LITERACY', data=df, palette=region_colors)
    plt.xlabel("Region",fontweight='bold')
    plt.ylabel("Literacy Rate", fontweight='bold')
    plt.xticks(rotation=45, fontsize=12)
    plt.yticks(fontsize=12)
    plt.ylim(0, 120)  # Set Y-axis limit to 120
    plt.tight_layout()
    plt.legend()
    bar_chart_literacy_path = os.path.join(app.config['STATIC_FOLDER'], 'bar_chart_literacy.png')
    plt.savefig(bar_chart_literacy_path, bbox_inches='tight', dpi=300)
    plt.close(bar_chart_literacy)


    return {
        'bar_plot_tpr': bar_plot_tpr_path,
        'line_chart_budget': line_chart_budget_path,
        'line_chart_textbook': line_chart_textbook_path,
        'bar_plot_survival': bar_plot_survival_path,
        'bar_chart_literacy': bar_chart_literacy_path,
    }


@app.route('/')
def index():
    logger.debug("Rendering index page.")
    return render_template('index.html')


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if '.' in file.filename:
            file_extension = file.filename.rsplit('.', 1)[1].lower()
        else:
            file_extension = ''

        if file_extension in app.config['UPLOAD_EXTENSIONS']:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Store the filename in the session
            session['filename'] = filename

            # Process the uploaded file
            df = load_data(file_path)
            df = process_data(df)

            # Save summary data to the database
            for index, row in df.iterrows():
                summary = Summary(
                    region=index,
                    tpr_region=row['TPR_REGION'],
                    budget=row['BUDGET'],
                    tpr=row['TPR'],
                    textbook=row['TEXTBOOK'],
                    literacy=row['LITERACY'],
                    students=row['STUDENTS'],
                    SURVIVAL_RATE = row['SURVIVAL_RATE']
                )
                db.session.add(summary)
            db.session.commit()

            # Convert DataFrame to a list of dictionaries
            data_list = df.to_dict('records')
            columns = df.columns.tolist()

            # Generate plots
            plot_paths = create_plots(df)

            # Store the plot_paths dictionary in the session
            session['plot_paths'] = plot_paths

            # Render the upload.html template with the data frame
            return render_template('upload.html', df=data_list, columns=columns)

    return render_template('upload.html', df=[], columns=[])


@app.route('/purge', methods=['POST'])
def purge():
    try:
        # Delete all records from the Summary table
        num_rows_deleted = db.session.query(Summary).delete()
        db.session.commit()
        logger.info(f"All data purged from Summary table. {num_rows_deleted} rows deleted.")
    except Exception as e:
        logger.error(f"Error purging data: {e}")
        db.session.rollback()
    return redirect(url_for('upload'))


@app.route('/generate_graph', methods=['POST'])
def generate_graph():
    plot_paths = session.get('plot_paths', {})
    return render_template('generate_graph.html', plot_paths=plot_paths)


if __name__ == '__main__':
    app.run(debug=True)
