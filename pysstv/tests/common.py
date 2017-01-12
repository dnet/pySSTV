from os import path
import pickle

def get_asset_filename(filename):
    return path.join(path.dirname(__file__), 'assets', filename)

def load_pickled_asset(filename):
    with open(get_asset_filename(filename + '.p'), 'rb') as f:
        return pickle.load(f)
