# Console section of Glassbox
import os
from os import path as p


class GlassConsole:
    root_alias = '~'

    def __init__(self, server_id: int):
        self.root = p.join(p.curdir, 'data', 'serverfiles', str(server_id))
        self.folder = ''

    def cd(self, path: str):
        # Check for invalid (and unwanted) chars
        for c in ':?*':
            if c in path:
                raise NotADirectoryError('Invalid path.')

        new_folder = p.normpath(p.join(self.folder, path))
        # Stop them if they're trying to escape their server
        if new_folder.startswith('.'):
            self.folder = ''
            return
        # Check to see if path is valid
        if p.isdir(p.join(self.root, new_folder)):
            self.folder = new_folder
        else:
            raise NotADirectoryError('Invalid path.')

    def get_path(self):
        return p.normpath(p.join(self.root, self.folder))

    def __str__(self):
        return p.normpath(p.join(self.root_alias, self.folder))

    def ls(self):
        folders = [f for f in os.listdir(self.get_path()) if os.path.isdir(os.path.join(self.get_path(), f))]
        files = [f for f in os.listdir(self.get_path()) if os.path.isfile(os.path.join(self.get_path(), f))]
        folders.extend(files)
        return folders
