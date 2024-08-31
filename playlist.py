import json
from requests import post, get

from flask import redirect, session

from source import Source

"""Exports the Playlist class, which allows a new playlist 
of recommendations to be created.
"""

API_URL = "https://api.spotify.com/v1/"


class Playlist:
    """Represents the new playlist of recommendations that will be generated
    using its Source object.
    
    __init__ -- initialised with the Spotify ID of the source playlist.

    Public methods:
    get_headers
    get_playlist
    get_audio_features
    assemble_tracks
    get_seed_tracks
    recommend_songs
    create_playlist
    """

    def __init__(self, id):
        self.__source = Source(id)

    def get_headers(self):
        """Updates the Flask session with the correct headings for Spotify API access"""
        session["headers"] = {"Authorization": f"Bearer {session['token']}"}

    def get_playlist(self, url, track_ids): 
        """Recursively gets all the tracks in the source playlist from the API - this is 
        necessary due to return limits.
        
        Arguments:
        url -- the location tracks are fetched from, either the initial url or the url to 
        the next page of items.
        track_ids -- the list of Spotify IDs for every track in the source playlist - 
        initially called with an empty list.

        Returns:
        track_ids -- the completed list of track Spotify IDs
        self.get_playlist() -- the recursive call with the url for the next page and
        the current list of track IDs.
        """

        response = get(url, headers=session["headers"]).json()

        limit_track_ids = []  
        for i in response["items"]: 
            limit_track_ids.append(i["track"]["id"]) 
        track_ids.append(limit_track_ids)

        # Base case occurs when there is no next page of items
        if response["next"] == None:
            return track_ids
        else:
            return self.get_playlist(response["next"], 
                                     track_ids)

    def get_audio_features(self): 
        """Gets the audio feature data stored by Spotify about a given track - fetched using 
        the Spotify ID of the source playlist to get its tracks, which are then added
        to a string to form the url that gets the data from the API.
        
        Returns:
        source_audio_features -- a 2D array of the audio feature values for every track in the 
        source playlist.
        """
        url = API_URL + f"playlists/{self.__source.get_playlist_id()}/tracks"
        source_tracks = self.get_playlist(url, [])

        for i in range(len(source_tracks)):
            tracks_str = ""
            for j in range(len(source_tracks[i])):
                if not j == 0:
                    tracks_str += ","+source_tracks[i][j]
                else:
                    tracks_str += source_tracks[i][j]

            url = API_URL + f"audio-features?ids={tracks_str}"
           
            # Collecting audio feature values
            source_audio_features = []
            for i in get(url, headers=session["headers"]).json()["audio_features"]:
                source_audio_features.append(i)
            return source_audio_features

    def assemble_tracks(self):
        """Adds Track objects containing audio features to the Source object."""
        source_audio_features = self.get_audio_features()
        for i in source_audio_features:
            self.__source.add_song(i)

    def get_seed_tracks(self):
        """Produces the 5 tracks used to seed song recommendations - gets the tracks from
        the Source object, calculates playlist similarity for each then returns the 5 tracks
        with the highest values.

        Returns:
        Source.sort_tracks[:5] -- a list of 5 instances of Track
        """

        for i in self.__source.get_tracks():
            i.calculate_playlist_similarity(self.__source.get_playlist_audio_features())
        return self.__source.sort_tracks()[:5]

    def recommend_songs(self): 
        """Takes the list of Track instances for seeding, adds them to a string and pulls 20
        recommended tracks. These tracks are then compared to the list of IDs from the source
        playlist and duplicates are removed.

        Returns:
        tracks[slice(10)] -- The first 10 items in the list of recommended tracks
        """

        seed_tracks = self.get_seed_tracks()
        seed_str = ""
        for i in range(len(seed_tracks)):
            if not i == 0:
                seed_str += ","+seed_tracks[i].get_id()
            else:
                seed_str += seed_tracks[i].get_id()

        url = API_URL + f"recommendations?limit=20&seed_tracks={seed_str}"
        tracks = get(url, headers=session["headers"]).json()["tracks"]
        
        for i in tracks:
            if i["id"] in self.__source.get_track_ids():
                tracks.remove(i)
        return tracks[slice(10)]

    def create_playlist(self):
        """Create a new playlist on Spotify and populate it with the song recommendations.
        
        Returns:
        redirect() -- a Flask redirect object that in this case opens the link to the playlist.
        """

        recommended_tracks = self.recommend_songs()
        
        url = API_URL + "me/playlists"
        # Sets the name and description of the new playlist
        data = json.dumps({
            "name": "Song Recommendations",
            "description": f"Playlist used: {self.__source.get_playlist_name()}" 
        })
        
        # Creates the new playlist
        playlist_id = post(url, headers=session["headers"], 
                           data=data).json()["id"]
        
        # Populating the new playlist
        url = API_URL + f"playlists/{playlist_id}/tracks"
        uris = []
        for i in recommended_tracks:
            uris.append(i["uri"])
        data = json.dumps({"uris": uris})
        post(url, headers=session["headers"], data=data)
        return redirect(f"https://open.spotify.com/playlist/{playlist_id}")