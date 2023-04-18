# Console section of Glassbox
import os
import shutil
from os import path as p


class GlassConsole:
    root_alias = '~'
    MAX_DIRECTORIES = 4

    def __init__(self, server_id: int):
        """Initialize a console for a certain server.

        Checks to make sure that the server's data folder exists. If not, make it.
        Then initialize this console's root directory to that folder and set its working directory to that folder.
        """
        if not p.exists(p.join(p.curdir, 'data', 'serverfiles', str(server_id))):
            os.makedirs(p.join(p.curdir, 'data', 'serverfiles', str(server_id)))
        self.root = p.join(p.curdir, 'data', 'serverfiles', str(server_id))
        self.folder = ''

    def count_folders(self, owned_folders, path: str):
        """Update a dictionary of Discord users to the number of folders they own. Counts recursively."""
        if '.owner' in os.listdir(path) and p.isfile(p.join(path, '.owner')):
            with open(p.join(path, '.owner')) as file:
                owner = int(file.read())
            if owner not in owned_folders:
                owned_folders[owner] = 1
            else:
                owned_folders[owner] += 1
        folders = [f for f in os.listdir(path) if p.isdir(p.join(path, f))]
        for f in folders:
            self.count_folders(owned_folders, p.join(path, f))

    def mkdir(self, name: str, owner: int):
        """Make a directory, owned by a specific Discord user ID."""
        if self.folder != '':
            raise PermissionError('Folders can only be created from ~.')
        if '/' in name:
            raise PermissionError('Folders can only be created in ~.')
        for c in '`.~:?*\\\'\"<>| ':
            if c in name:
                raise PermissionError(f'Illegal folder name. Folder names cannot contain \"{c}\".')
        if p.isdir(p.join(self.root, name)):
            raise PermissionError(f'Folder {name} already exists!')

        owned_folders = {owner: 0}
        self.count_folders(owned_folders, self.root)
        if owned_folders[owner] >= self.MAX_DIRECTORIES:
            raise PermissionError(f'You can only have a maximum of {self.MAX_DIRECTORIES} folders.')
        os.mkdir(p.join(self.root, name))
        with open(p.join(self.root, name, '.owner'), 'w') as file:
            file.write(str(owner))

    def rmdir(self, path: str, owner: int):
        """Remove a directory, as long as it's owned by the specific Discord user ID.

        Raises NotADirectoryError if the specified folder does not exist, or is outside the server data folder.
        Raises PermissionError if the folder has no .owner file, or if the owner is not the user.
        """
        target_path = p.relpath(p.abspath(p.join(self.root, self.folder, path)), start=p.abspath(self.root))
        # Stop them if they're trying to escape their server
        if target_path.startswith('.'):
            raise NotADirectoryError('Invalid path.')
        # Stop if the target is not a folder
        if not p.isdir(p.join(self.root, target_path)):
            raise NotADirectoryError('Invalid path.')
        # Stop if the target has no owner
        if not p.isfile(p.join(self.root, target_path, '.owner')):
            raise PermissionError('You do not have permission to modify this folder.')

        with open(p.join(self.root, target_path, '.owner')) as file:
            folder_owner = int(file.read())
        # Stop if the target owner is not the user
        if owner != folder_owner:
            raise PermissionError('You do not have permission to modify this folder.')
        # Proceed with deleting the folder
        if owner == folder_owner:
            shutil.rmtree(p.join(self.root, target_path))

    def rm(self, path: str, owner: id):
        """Removes a file or folder, if it's owned by the right Discord user ID.

        Raises PermissionError if the file/folder has no owner, or if the owner is not the user.
        Raises NotADirectoryError if the folder is outside the server data folder.
        Raises IsADirectoryError if the target is a folder.
        Raises FileNotFoundError if the target is a hidden file/folder.
        """
        target_path = p.relpath(p.abspath(p.join(self.root, self.folder, path)), start=p.abspath(self.root))
        # Stop them if they're trying to escape their server
        if target_path.startswith('.'):
            raise NotADirectoryError('Invalid path.')
        # Stop if the target is hidden
        if p.split(target_path)[1].startswith('.'):
            raise FileNotFoundError('Invalid path.')
        # Redirect if the target is a folder
        if p.isdir(p.join(self.root, target_path)):
            raise IsADirectoryError
        # Stop if the target has no owner
        if not p.isfile(p.join(p.split(p.join(self.root, target_path))[0], '.owner')):
            raise PermissionError('You do not have permission to modify this file.')

        with open(p.join(p.split(p.join(self.root, target_path))[0], '.owner')) as file:
            folder_owner = int(file.read())
        # Stop if the target owner is not the user
        if owner != folder_owner:
            raise PermissionError('You do not have permission to modify this file.')
        # Proceed with deleting the file
        if owner == folder_owner:
            os.remove(p.join(self.root, target_path))

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

    def retrieve_file(self, path: str):
        """Given a relative path to a file, return the actual path to that file, if it exists."""
        for c in '~:?*':
            if c in path[2:]:
                print("A")
                raise FileNotFoundError('Invalid path.')
        if path.startswith('~'):
            path = path[2:]
            print(path)
            target_path = p.relpath(p.abspath(p.join(self.root, path)), start=p.abspath(self.root))
        elif path.startswith('~/'):
            path = path[3:]
            print(path)
            target_path = p.relpath(p.abspath(p.join(self.root, path)), start=p.abspath(self.root))
        else:
            target_path = p.relpath(p.abspath(p.join(self.root, self.folder, path)), start=p.abspath(self.root))
        # Stop them if they're trying to escape their data folder
        if target_path.startswith('.'):
            raise FileNotFoundError('Invalid path.')
        # Check to see if the file exists
        if p.isfile(p.join(self.root, target_path)):
            # Send no file if the target is hidden (starts with .)
            if p.split(p.join(self.root, target_path))[1].startswith('.'):
                raise FileNotFoundError('File not found.')
            else:
                return p.join(self.root, target_path)
        else:
            raise FileNotFoundError('File not found.')

    def get_path(self):
        """Prints the path to the working directory, relative to the root data folder."""
        return p.normpath(p.join(self.root, self.folder))

    def __str__(self):
        """Prints the path to the working directory, using an alias for the root data folder."""
        return p.normpath(p.join(self.root_alias, self.folder))

    def ls(self):
        """Lists the contents of the current folder, or the target folder, if it exists."""
        folders = [(f+'/') for f in os.listdir(self.get_path()) if p.isdir(p.join(self.get_path(), f))]
        files = [f for f in os.listdir(self.get_path()) if p.isfile(p.join(self.get_path(), f))
                 and not f.startswith('.')]  # Hide hidden files (name starts with .)
        folders.extend(files)
        return folders

    def pwd(self):
        """Outputs the current working directory."""
        return ('~/'+self.folder) if self.folder != '' else '~'
