from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session
import identity
import identity.web
import requests
import app_config

auth = Blueprint('auth', __name__)

# Create the auth object dynamically using the current app config
@auth.before_app_request
def before_request():
    global auth_instance
    auth_instance = identity.web.Auth(
        session=session,
        authority=current_app.config.get("AUTHORITY"),
        client_id=current_app.config["CLIENT_ID"],
        client_credential=current_app.config["CLIENT_SECRET"],
    )

def pr(s):
    print(s)
    return ""

@auth.route("/login")
def login():
    return render_template("login.html", version=identity.__version__, **auth_instance.log_in(
        scopes=app_config.SCOPE,  # Have user consent to scopes during log-in
        redirect_uri=url_for("auth.auth_response", _external=True)
    ))

@auth.route(app_config.REDIRECT_PATH)
def auth_response():
    result = auth_instance.complete_log_in(request.args)
    if "error" in result:
        return render_template("auth_error.html", result=result)
    return redirect(url_for("auth.index"))

@auth.route("/logout")
def logout():
    return redirect(auth_instance.log_out(url_for("auth.index", _external=True)))

@auth.route("/")
def index():
    if not (current_app.config["CLIENT_ID"] and current_app.config["CLIENT_SECRET"]):
        return render_template('config_error.html')
    if not auth_instance.get_user():
        return redirect(url_for("auth.login"))
    return render_template('index.html', user=auth_instance.get_user(), version=identity.__version__)

@auth.route("/call_downstream_api")
def call_downstream_api():
    token = auth_instance.get_token_for_user(app_config.SCOPE)
    if "error" in token:
        return redirect(url_for("auth.login"))
    # Use access token to call downstream API
    api_result = requests.get(
        app_config.ENDPOINT,
        headers={'Authorization': 'Bearer ' + token['access_token']},
        timeout=30,
    ).json()
    return render_template('display.html', result=api_result)
