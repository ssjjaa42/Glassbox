# Console section of Glassbox
import os
from os import path as p


class GlassConsole:
    root_alias = '~'

    def __init__(self, server_id: int):
        """Initialize a console for a certain server.

        Checks to make sure that the server's data folder exists. If not, make it.
        Then initialize this console's root directory to that folder and set its working directory to that folder.
        """
        if not p.exists(p.join(p.curdir, 'data', 'serverfiles', str(server_id))):
            os.makedirs(p.join(p.curdir, 'data', 'serverfiles', str(server_id)))
        self.root = p.join(p.curdir, 'data', 'serverfiles', str(server_id))
        self.folder = ''

    def cd(self, path: str):
        """Change the console's working directory.

        Raises NotADirectoryError if it sees unusual characters.
        Tries to keep them within the confines of the data folder.
        Raises NotADirectoryError if the target directory does not exist.
        """
        # Check to go home
        if (path == '~') or (path == ''):
            self.folder = ''
            return
        if path.startswith('~/'):
            self.folder = ''
            path = path[2:]
        # Check for invalid (and unwanted) chars
        for c in '~:?*':
            if c in path:
                raise NotADirectoryError('Invalid path.')

        target_path = p.relpath(p.abspath(p.join(self.root, self.folder, path)), start=p.abspath(self.root))
        # Stop them if they're trying to escape their server
        if target_path.startswith('.'):
            self.folder = ''
            return
        # Check to see if path is valid
        if p.isdir(p.join(self.root, target_path)):
            self.folder = target_path
        else:
            raise NotADirectoryError('Invalid path.')

    def get_path(self):
        """Prints the path to the working directory, relative to the root data folder."""
        return p.normpath(p.join(self.root, self.folder))

    def __str__(self):
        """Prints the path to the working directory, using an alias for the root data folder."""
        return p.normpath(p.join(self.root_alias, self.folder))

    def ls(self):
        """Lists the contents of the current folder, or the target folder, if it exists."""
        folders = [(f+'/') for f in os.listdir(self.get_path()) if os.path.isdir(os.path.join(self.get_path(), f))]
        files = [f for f in os.listdir(self.get_path()) if os.path.isfile(os.path.join(self.get_path(), f))]
        folders.extend(files)
        return folders

    def pwd(self):
        """Outputs the current working directory."""
        return ('~/'+self.folder) if self.folder != '' else '~'
