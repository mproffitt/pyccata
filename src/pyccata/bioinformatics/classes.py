"""
Classes for helping collation methods
"""
import pandas as pd

class Dataframe(pd.Dataframe):
    """
    An extension of pandas dataframes for re-combining multiple dataframes into one.
    """

    def recombine(self, sets):
        """
        Given sets A,B,C,D,E in the order of:

        [(A, B, C), (B, C, D), (C, D, E), (D, E, A), (E, A, B)]

        re-merge the frames so they become:

        [(A, B, C, D, E)]

        This is data-specific for BedFileItems...
        """
        pass
