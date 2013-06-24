from os import path

def get_asset_filename(filename):
    return path.join(path.dirname(__file__), 'assets', filename)
