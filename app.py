from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/burners')
def burners():
    return render_template('burners.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=False)
