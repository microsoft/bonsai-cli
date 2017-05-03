"""
Project file implementation and logic
"""
import os
import json

DEFAULT_FILE = 'bonsai_brain.bproj'


class ProjectFileInvalidError(Exception):
    pass


class ProjectDefault():
    """ Default values for a project file """
    @staticmethod
    def apply(proj):
        if not proj.exists():
            proj.files.add('./')
            proj.training['simulator'] = 'openai.gym.unknown'
            proj.training['command'] = 'python --version'


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
        except (OSError, IOError, ValueError):
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
        # This logic is shared with the backend project's parsing
        # of project files and functionality should be shared
        # see T1643
        project_dir = os.path.abspath(self.directory())
        for path in self._file_set:
            # join paths relative to the project directory, otherwise
            # python assumes the current working directory.
            merged = os.path.join(project_dir, path)
            relative = os.path.relpath(merged, project_dir)
            if relative.startswith('..'):
                # Ignore paths which are not under the project
                continue

            if os.path.isdir(merged):
                for dirname, _, file_list in os.walk(merged):
                    for f in file_list:
                        if self._exclude_file(dirname, f):
                            continue

                        abs_path = os.path.join(dirname, f)
                        rel_path = os.path.relpath(abs_path, project_dir)
                        yield rel_path
            else:
                yield path

    def _exclude_file(self, dirname, filename):
        """ Returns True/False if file should be excluded as part of wildcard
        expansion in _list_paths(). """
        path = os.path.join(dirname, filename)

        # Don't include project_file itself.
        if (os.path.exists(self.project_path) and
                os.path.samefile(path, self.project_path)):
            return True

        # .git/index, etc.
        dirs_in_path = dirname.split('/')
        if '.git' in dirs_in_path:
            return True

        # .brains, .gitignore, etc.
        if filename.startswith('.'):
            return True

        return False

    @property
    def inkling_file(self):
        inkling_files = [f for f in self._list_paths() if f.endswith('.ink')]
        if len(inkling_files) != 1:
            if len(inkling_files) == 0:
                raise ProjectFileInvalidError('No inkling file found')
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
                if not os.path.exists(path):
                    msg = "Unable to find {}, as specified in {}".format(
                        filename, self.project_path)
                    raise ProjectFileInvalidError(msg)

        return True
