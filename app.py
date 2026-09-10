from database import init_db
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

init_db()

@app.route("/")
def index():
    return render_template("index.html")

# Launch flask developement server
if __name__ == "__main__":
    app.run(debug=True)