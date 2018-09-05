"""
Project file implementation and logic
"""
import os
import json
import glob

DEFAULT_FILE = 'bonsai_brain.bproj'


class ProjectFileInvalidError(Exception):
    pass


class FileTooLargeError(Exception):
    def __init__(self, file):
        self.message = (
            "The file {} exceeds our size"
            " limit. The system does not accept files with a size"
            " greater than 640KB. Please remove the file from the"
            " project file and try again.".format(file))


class ProjectDefault():
    """ Default values for a project file """
    @staticmethod
    def apply(proj):
        if not proj.exists():
            proj.files.add('*.ink')
            proj.files.add('*.py')
            proj.training['simulator'] = 'custom'


class ProjectFile():
    def __init__(self, path=DEFAULT_FILE):
        self.content = self._read(path)
        self.project_path = path
        files = self.content.get('files', [])
        # while the project is loaded, maintain files as a set
        # to prevent duplicates
        self._file_set = set(files)

    @staticmethod
    def from_file_or_dir(file_or_dir):
        if os.path.isfile(file_or_dir):
            return ProjectFile(file_or_dir)
        else:
            return ProjectFile(os.path.join(file_or_dir, DEFAULT_FILE))

    @staticmethod
    def find(directory):
        """ Returns path of 1st project file found given directory. """
        path = os.path.join(directory, DEFAULT_FILE)
        if os.path.exists(path):
            return path
        else:
            return None

    def directory(self):
        return os.path.dirname(self.project_path)

    def exists(self):
        return os.path.exists(self.project_path)

    def _read(self, path):
        proj = {}
        try:
            with open(path, 'r') as f:
                proj = json.load(f)
        except (OSError, IOError):
            pass
        return proj

    def _write(self):
        output = self.content
        output['files'] = sorted(list(self._file_set))
        with open(self.project_path, 'w') as f:
            json.dump(output, f,
                      sort_keys=True, indent=4,
                      separators=(',', ': '))

    def _list_paths(self):
        """
        Lists all file paths (relative) referenced by 'files', with directories
        expanded
        """
        project_dir = os.path.abspath(self.directory())

        path_set = set()

        def add_to_path_set(dir_name, file_name):
            """
            Helper function to add the specified directory and file to
            the set of all file paths.
            """
            # Do nothing if this dir and file should be excluded
            if self._exclude_file(dir_name, file_name):
                return

            # Join the dir and file and get the path relative to the
            # project directory before adding it
            abs_path = os.path.join(dir_name, file_name)
            rel_path = os.path.relpath(abs_path, project_dir)
            path_set.add(rel_path)

        for path in self._file_set:
            # join paths relative to the project directory, otherwise
            # python assumes the current working directory.
            merged = os.path.join(project_dir, path)
            relative = os.path.relpath(merged, project_dir)
            if relative.startswith('..'):
                # Ignore paths which are not under the project
                continue

            # perform glob expansion on each (absolute) path in project
            # iglob returns a (possibly empty) generator of expanded paths
            expanded_paths = glob.iglob(merged)
            for expanded_path in expanded_paths:
                if os.path.isdir(expanded_path):
                    for dirname, _, file_list in os.walk(expanded_path):
                        for f in file_list:
                            add_to_path_set(dirname, f)

                else:
                    dirname, fname = os.path.split(expanded_path)
                    add_to_path_set(dirname, fname)

        return path_set

    def _exclude_file(self, dirname, filename):
        """ Returns True/False if file should be excluded as part of wildcard
        expansion in _list_paths(). """
        path = os.path.join(dirname, filename)

        # Don't include project_file itself.
        try:
            if (os.path.exists(self.project_path) and
                    os.path.samefile(path, self.project_path)):
                return True
        except AttributeError:
            """ Windows/Python2.7 throws an attribute error because
                os.path.samefile does not exist in that environment"""
            if (os.path.exists(self.project_path) and
                    self._samefile(path, self.project_path)):
                return True

        # .git/index, etc.
        dirs_in_path = dirname.split('/')
        if '.git' in dirs_in_path:
            return True

        # .brains, .gitignore, etc.
        if filename.startswith('.'):
            return True

        # python byte code
        if filename.endswith('.pyc'):
            return True

        return False

    def _samefile(self, path1, path2):
        """ os.path.samefile does not exist on windows for python2.7
            so we attempt to emulate it with this function """
        return os.path.normcase(os.path.normpath(path1)) == \
            os.path.normcase(os.path.normpath(path2))

    @property
    def inkling_file(self):
        inkling_files = [f for f in self._list_paths() if f.endswith('.ink')]

        if not inkling_files:
            raise ProjectFileInvalidError('No inkling file found')
        elif len(inkling_files) > 1:
            raise ProjectFileInvalidError(
                'Multiple inkling files found. Set one in "files" in the'
                ' project file to indicate which should be loaded. '
                '{},{}, ... {} total'.format(inkling_files[0],
                                             inkling_files[1],
                                             len(inkling_files)))

        return inkling_files[0]

    @property
    def files(self):
        return self._file_set

    @property
    def training(self):
        section = self.content.get('training', None)
        if not section:
            section = self.content['training'] = {}
        return section

    def save(self):
        self._write()

    def validate_content(self):
        """ Checks project file contents for errors. """
        # Checks "files" exist on disk.
        if "files" in self.content:
            dir = self.directory()
            for filename in self.content["files"]:
                path = os.path.join(dir, filename)
                if not os.path.exists(path) and \
                   not glob.glob(path):
                    msg = "Unable to find {}, as specified in {}".format(
                        filename, self.project_path)
                    raise ProjectFileInvalidError(msg)

                self._check_size_of_files(glob.glob(path))
        return True

    def _check_size_of_files(self, files):
        """ Checks size of files and raises
            an error if they exceed the limit """
        for file in files:
            size = os.path.getsize(file)
            # Throw error if bigger than 640KB
            if size > 655360:
                raise FileTooLargeError(file)
