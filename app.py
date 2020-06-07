import os
import shutil

from flask import Flask, render_template, request, make_response, jsonify
import matplotlib.pyplot as plt

from utils import utils


app = Flask(__name__)

# limit upload file size : 10MB
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

# Load config
app.config.from_pyfile('config.ini')

# ex) set UPLOAD_DIR_PATH=C:/tmp/flaskUploadDir
# UPLOAD_DIR = os.getenv("UPLOAD_DIR_PATH")
# UPLOAD_DIR = "./tmp"
UPLOAD_DIR = app.config['UPLOAD_DIR']
os.makedirs(UPLOAD_DIR, exist_ok=True)

p = app.config["PROCESS"]
threshold_rate_undetected = app.config['THREASHOLD_RATE_UNDETECTED']

print(app.config['BISMARK_INDEX_HUMAN'])
print(app.config['BISMARK_INDEX_MOUSE'])

plt.rcParams["font.size"] = app.config['PLOT_FONT_SIZE']

@app.route('/', methods=['GET'])
def input():
    return render_template("input.html")

@app.route('/', methods=['POST'])
def output():
    species = request.form["species"]
    enz1 = request.form['enz1']
    enz2 = request.form['enz2']
    fasta = request.form['fasta']

    dir_tmp = utils.make_tmpdir(UPLOAD_DIR)

    if fasta == "":
        files = request.files.getlist('uploadFile')
        print(files)
        result = utils.process_files(files, dir_tmp)
        if result[0] == 0:
            fasta = result[1]
        else:
            fasta = result[1]
    
    print(fasta)

    if (enz1 != "") & (enz2 != ""):
        fasta = utils.trim_fasta(fasta, enz1, enz2)
    elif enz1 == enz2 == "":
        fasta = fasta
    else:
        render_template('error.html', error='invalid input for restriction enzyme.')
    
    if fasta == "":
        render_template('error.html', error='No valid sequences.')

    if species == "Human":
        f_bismark_index = app.config['BISMARK_INDEX_HUMAN']
    elif species == "Mouse":
        f_bismark_index = app.config['BISMARK_INDEX_MOUSE']
    else:
        render_template('error.html', error='cannot recognize the spiece')

    f_fa = dir_tmp + '/' + app.config['INPUT_FASTA']
    with open(f_fa, 'w') as f:
        f.write(fasta)
    f_bismark = utils.run_bismark(p, dir_tmp, f_fa, species, f_bismark_index)

    fig = utils.plot_bismark(dir_tmp, f_bismark, threshold_rate_undetected, 'output.png')
    figs = []
    figs.append('/'+dir_tmp+'/output.png')

    # import time
    # time.sleep(5)

    # shutil.rmtree(dir_tmp)

    return render_template('output.html', species=species, enz1=enz1, enz2=enz2, fasta=fasta, figs=figs, title='Result')

@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/test')
def test():
    figs=["static/tmp/job_20200601_162507/output.png"]
    return render_template("test.html", figs=figs)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
