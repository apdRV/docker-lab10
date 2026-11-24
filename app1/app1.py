from flask import Flask, render_template

# тут подсказал, где искать index.html
app = Flask(__name__, template_folder="/storage")

# тут сделал путь соответственно readme
@app.route('/')
def hello_world():
    return render_template('index.html', source_app='app1')


if __name__ == '__main__':
   app.run(debug=True, host='0.0.0.0', port=8080)
