import math

"""Exports the Track class that represents individual songs."""


class Track:
    """Represents an individual Spotify track, storing its Spotify ID,
    audio information and its similarity value to the rest of the source
    playlist so it can be compared with other instances.

    __init__ -- defined using the audio features of the corresponding Spotify 
    track and the track's Spotify ID.

    Public methods:
    get_playlist_similarity
    get_id
    get_audio_features
    calculate_playlist_similarity
    """
    def __init__(self, id, audio_features):
        self.__id = id
        self.__audio_features = audio_features
        self.__playlist_similarity = 0.0

    def get_playlist_similarity(self):
        """Return the measure of similarity to the playlist."""
        return self.__playlist_similarity
    
    def get_id(self):
        """Return the Spotify ID for the track."""
        return self.__id

    def get_audio_features(self):
        """Return the audio features of the track."""
        return self.__audio_features

    def calculate_playlist_similarity(self, average_audio_features):
        """Determines how similar a given instance sounds compared to the rest of the playlist.
        This is done by calculating a score between 0 and 1 which represents how similar the 
        audio features of this instance are to the mean values for the entire playlist.
        
        Arguments:
        average_audio_features -- the list of the average audio feature values for the playlist.
        """
        total = 0
        total_difference = 0
        for i in range(len(average_audio_features)):
            # Calculates the absolute value of the difference between each audio feature value
            total_difference += math.fabs(average_audio_features[i] 
                                          - self.__audio_features[i])
            # Calculates the total value between average and own audio features
            total += average_audio_features[i] + self.__audio_features[i]
        self.__playlist_similarity = 1 - (total_difference / total)
