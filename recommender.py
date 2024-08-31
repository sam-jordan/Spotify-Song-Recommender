# needs comments added - details about client id/secret and app password and approved users

from requests import post, get
from datetime import datetime
import urllib.parse

from flask import Flask, redirect, request, jsonify, session, render_template

from playlist import Playlist

"""Uses the Flask library to run a webpage that allows the user to sign in to
Spotify, then select a playlist from which a new playlist of song recommendations
can be generated.

Files:
recommender.py
playlist.py
source.py
track.py
templates/sign_in.html
templates/main.html
static/styles/main_styles.css
static/styles/sign_in_styles.css
"""

CLIENT_ID = "89c9ac63001946d48ec9815545a185ae"
CLIENT_SECRET = "f859cd86dca34674880192db1273f3df"

AUDIO_FEATURES = ["acousticness", "danceability", "energy", "instrumentalness", 
                  "key", "loudness", "mode", "speechiness", "tempo", "valence"]

REDIRECT = "http://localhost:5000/callback" 
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_URL = "https://api.spotify.com/v1/"

app = Flask(__name__)
app.secret_key = "yourmum"


@app.route("/")
def index():
    """Renders the HTML for the sign in page."""
    return render_template("sign_in.html")


@app.route("/sign-in")
def sign_in():
    """Redirects the user to sign into their Spotify account and allow the permissions
    requested by the application.
    
    Returns:
    redirect(url) -- opens the Spotify login page.
    """

    # All the permissions needed to execute the program
    scope = "playlist-read-private playlist-modify-public playlist-modify-private"

    parameters = {
        "redirect_uri": REDIRECT,
        "client_id": CLIENT_ID,
        "scope": scope,
        "show_dialog": False,
        "response_type": "code"
    }

    url = f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(parameters)}"
    return redirect(url)


@app.route("/callback")
def callback():
    """Gets the response from the Spotify login - if all is correct and a code is recieved,
    a request for an access token is sent to the API - when recieved, the session is updated with the token,
    when it expires, and a code to get a new token when this happens.
    
    Returns:
    jsonify({request.args["error"]}) -- JSON object returned if an error is recieved
    redirect('/enter-playlist') -- redirects to the start of the main program.
    """
    if "error" in request.args:
        return jsonify({request.args["error"]})
    
    if "code" in request.args:
        req_body = {
            "redirect_uri": REDIRECT,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": request.args["code"],
            "grant_type": "authorization_code"
        }

        token_info = post(TOKEN_URL, data=req_body).json()
        session["token"] = token_info["access_token"]
        # Calculates an exact time in seconds that the token expires
        session["expiration"] = datetime.now().timestamp() + token_info["expires_in"]
        session["refresh"] = token_info["refresh_token"]

        return redirect("/enter-playlist")


@app.route("/enter-playlist")
def enter_playlist():  
    """Gets the current user's playlists and renders the main HTML file.
    
    Returns:
    redirect('/refresh-token') -- redirects to refresh the token if it has expired.
    render_template('main.html') -- renders the main HTML page and passes it the playlists.
    """

    # Checks if token has expired
    if datetime.now().timestamp() > session["expiration"]:
        return redirect("/refresh-token")
    
    get_headers()
    url = API_URL + "me/playlists"
    playlist = get_user_playlists(url, [])
    return render_template("main.html", playlists=playlist)


@app.route("/main/<playlist_id>")
def main(playlist_id):   
    """Carries out the main algorithm - the creation of a playlist of recommendations
    through a new instance of Playlist.
    
    Arguments: playlist_id -- the Spotify ID of the playlist selected by the user, passed
    from the html file.

    Returns:
    new_playlist.create_playlist() -- creates the new playlist and ultimately redirects the 
    user to its Spotify page.
    """

    new_playlist = Playlist(playlist_id)
    new_playlist.get_headers()
    new_playlist.assemble_tracks()
    return new_playlist.create_playlist()


@app.route("/refresh-token")
def refresh_token():
    """Gets a new token to access the API if the current one has expired.
    
    Returns:
    redirect('enter-playlist') -- redirects the user back to the playlist
    selection page.
    """

    if datetime.now().timestamp() > session["expiration"]:
        request_data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": session["refresh"]
        }

        new_token_info = post(TOKEN_URL, data=request_data).json()
        session["token"] = new_token_info["access_token"]
        session["expiration"] = datetime.now().timestamp() + new_token_info["expires_in"]

        return redirect("/enter-playlist")
    

def get_user_playlists(url, playlist_data): 
    """Gets the current user from the API, the Spotify ID of which is then used
    to recusively fetch data about their playlists - this is necessary due to 
    return limits.
    
    Arguments:
    url -- the location playlists are fetched from, either the initial url or the url to 
        the next page of items.
    playlist_data -- a 2D array containing lists of playlist data.

    Returns:
    playlist_data -- the fully filled-in list of the current user's playlists.
    get_user_playlists() -- the recursive call with the url for the next page and
        the current list of playlist data.
    """ 

    user = get(API_URL + "me", headers=session["headers"]).json()["id"]

    playlists = get(url, headers=session["headers"]).json()
    # Returns an empty array if user has no playlists
    if playlists["total"] == 0:
        return playlist_data

    for i in playlists["items"]:
        # Only returns playlists authored by the current user
        if i["owner"]["id"] == user:
            if i["images"] != None:
                # Data: playlist name, Spotify ID, link to cover image, playlist length
                playlist_data.append([i["name"].rstrip(), i["id"], 
                                    i["images"][0]["url"], i["tracks"]["total"]])
    # Base case occurs when there is no next page of items
    if playlists["next"] == None:
        return playlist_data
    else:
        return get_user_playlists(playlists["next"], playlist_data)


def get_headers():
    """Updates the Flask session with the correct headings for Spotify API access"""
    session["headers"] = {"Authorization": f"Bearer {session['token']}"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False)