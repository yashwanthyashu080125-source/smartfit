from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route("/")
def splash():
    return render_template("splash.html")

@main.route("/home")
def home():
    return render_template("home.html")

@main.route("/about")
def about():
    return render_template("about.html")

@main.route("/features")
def features():
    return render_template("features.html")

@main.route("/fitness")
def fitness():
    return render_template("fitness.html")

@main.route("/nutrition")
def nutrition():
    return render_template("nutrition.html")

@main.route("/contact")
def contact():
    return render_template("contact.html")