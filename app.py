import os
import logging
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from flask import Flask, request, render_template, redirect, url_for, session
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

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
    budget = db.Column(db.Float, nullable=False)
    tpr = db.Column(db.Float, nullable=False)
    textbook = db.Column(db.Integer, nullable=False)
    literacy = db.Column(db.Float, nullable=False)

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
    # Line Plot: Teacher to Pupil Ratio (TPR) Impact on Literacy Rate
    line_plot_tpr = plt.figure(figsize=(16, 10))
    df_melted = df.melt(id_vars='TPR_REGION', value_vars='LITERACY')
    sns.lineplot(x='TPR_REGION', y='value', hue='variable', data=df_melted, palette="dark")
    plt.title("Teacher to Pupil Ratio (TPR) Impact on Literacy Rate")
    plt.xlabel("Teacher to Pupil Ratio (TPR)")
    plt.ylabel("Literacy Rate")
    plt.xticks(rotation=45)
    plt.tight_layout()
    line_plot_tpr_path = os.path.join(app.config['STATIC_FOLDER'], 'line_plot_tpr.png')
    plt.savefig(line_plot_tpr_path)

    # Scatter Plot: Budget Allocation and Literacy Rates:
    scatter_plot_budget = plt.figure(figsize=(16, 10))
    sns.regplot(x='BUDGET', y='LITERACY', data=df, color=sns.color_palette("Spectral", 20)[17])
    plt.title('Correlation of Budget Allocation and Literacy Rates')
    plt.xlabel("Budget Allocation")
    plt.ylabel("Literacy Rate")
    plt.tight_layout()
    scatter_plot_budget_path = os.path.join(app.config['STATIC_FOLDER'], 'scatter_plot_literacy.png')
    plt.savefig(scatter_plot_budget_path)

    # Bar plot: Impact of Textbook Availability on Literacy
    bar_plot_textbook = plt.figure(figsize=(16, 10))
    avg_literacy = df.groupby(['TEXTBOOK', 'TPR_REGION'])['LITERACY'].mean().reset_index()
    sns.barplot(x='TEXTBOOK', y='LITERACY', hue='TPR_REGION', data=avg_literacy, palette="Spectral")
    plt.title('Impact of Textbook Availability on Literacy')
    plt.xlabel("Textbooks Per Region")
    plt.ylabel("Average Literacy Rate")
    plt.ylim(20, 150)
    plt.tight_layout()
    plt.legend(title='Region', loc='upper left')
    bar_plot_textbook_path = os.path.join(app.config['STATIC_FOLDER'], 'bar_plot_textbook.png')
    plt.savefig(bar_plot_textbook_path)

    # Line Plot: School Survival Rate Correlation with Region
    line_plot_survival = plt.figure(figsize=(16, 10))
    df_filtered = df[(df['SURVIVAL_YEAR'] >= 2006) & (df['SURVIVAL_YEAR'] <= 2014)]
    sns.barplot(x='SURVIVAL_YEAR', y='SURVIVAL_RATE', hue='REGION_SURVIVAL', data=df_filtered, palette="Spectral")
    plt.title('School Survival Rate Over Time by Region')
    plt.xlabel("Year")
    plt.ylabel("School Survival Rate")
    plt.tight_layout()
    line_plot_survival_path = os.path.join(app.config['STATIC_FOLDER'], 'line_plot_survival.png')
    plt.savefig(line_plot_survival_path)

    # Comparative Regional Analysis
    df_analysis = df[['TPR_REGION', 'BUDGET', 'TPR', 'TEXTBOOK', 'LITERACY']].copy()
    average_budget = df_analysis['BUDGET'].mean()
    average_tpr = df_analysis['TPR'].mean()
    average_textbook = df_analysis['TEXTBOOK'].mean()
    df_analysis['Outlier'] = ((df_analysis['BUDGET'] > average_budget) |
                              (df_analysis['TPR'] < average_tpr) |
                              (df_analysis['TEXTBOOK'] > average_textbook)) & (df_analysis['LITERACY'] < df_analysis['LITERACY'].mean())
    outlier_plot_budget = plt.figure(figsize=(16, 10))
    sns.regplot(x='BUDGET', y='LITERACY', data=df_analysis, scatter_kws={'s': 50, 'alpha': 0.5}, line_kws={'color': 'red'})
    plt.title("Comparative Regional Analysis")
    plt.xlabel("Budget")
    plt.ylabel("Literacy Rate")
    plt.tight_layout()
    outlier_plot_budget_path = os.path.join(app.config['STATIC_FOLDER'], 'outlier_plot_budget.png')
    plt.savefig(outlier_plot_budget_path)

    return {
        'line_plot_tpr': line_plot_tpr_path,
        'scatter_plot_budget': scatter_plot_budget_path,
        'bar_plot_textbook': bar_plot_textbook_path,
        'line_plot_survival': line_plot_survival_path,
        'outlier_plot_budget': outlier_plot_budget_path,
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


''' jfeuhrfnmd '''
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
