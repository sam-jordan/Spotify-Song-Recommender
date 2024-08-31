from requests import get

from flask import session

from track import Track

"""Exports the Source class that represents the source playlist
for recommendations.
"""

AUDIO_FEATURES = ["acousticness", "danceability", "energy", 
                  "instrumentalness", "key", "loudness", "mode", 
                  "speechiness", "tempo", "valence"]
API_URL = "https://api.spotify.com/v1/"


class Source: 
    """Represents the playlist that is used as the source of the 
    recommendations, storing its Spotify ID, tracks and mean audio
    information.
    
    __init__ -- defined with the Spotify ID of the source playlist

    Public methods:
    get_playlist_id
    get_playlist_audio_features
    get_tracks
    get_playlist_name
    get_track_ids
    sort_tracks
    add_song
    """

    def __init__(self, id):
        self.__playlist_id = id
        self.__tracks = []
        self.__average_audio_features = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.__track_ids = []
   
    def get_playlist_id(self):
        """Return the Spotify ID of the selected playlist."""
        return self.__playlist_id
    
    def get_playlist_audio_features(self):
        """Return the average of the audio features for playlist tracks."""
        return self.__average_audio_features
    
    def get_tracks(self):
        """Return the list of instances of Track that correspond to the playlist's songs."""
        return self.__tracks
    
    def get_playlist_name(self):
        """Return the name of the source playlist."""
        response = get(API_URL + f"playlists/{self.__playlist_id}", 
                       headers=session["headers"])
        return response.json()["name"]
    
    def get_track_ids(self):
        """Return the list of Spotify Track IDs featured in the playlist."""
        return self.__track_ids
    
    def sort_tracks(self):
        """Return the list of Track instances sorted according to playlist similarity."""
        self.__tracks.sort(reverse=True, key=Track.get_playlist_similarity)
        return self.__tracks
    
    def add_song(self, track):
        """Adds a new instance of Track to the list of tracks from the source playlist,
        and recalculates the values of the mean audio features to account for this.
        Also adds the Spotify ID of the associated song to the list of track IDs.

        Arguments:
        track -- a list of the audio features of the associated song.
        """
        track_audio_features = []
        for i in AUDIO_FEATURES:
            track_audio_features.insert(0, track[i])

        self.__tracks.append(Track(track["id"], track_audio_features))
        self.__track_ids.append(track["id"])

        # Updates the mean audio feature values
        for i in range(len(self.__average_audio_features)):
            self.__average_audio_features[i] = (self.__average_audio_features[i] 
                                              + track_audio_features[i]) / 2