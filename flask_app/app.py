from flask import Flask, render_template

app = Flask(__name__, static_folder="templates/static")

@app.route('/')
def hello_world():
    return render_template('layouts/index.html')
    
if __name__ == '__main__':
    app.run(host='0.0.0.0')