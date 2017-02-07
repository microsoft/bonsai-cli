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

    def directory(self):
        dirname = os.path.dirname(self.project_path)
        return os.path.dirname(self.project_path)

    def exists(self):
        return os.path.exists(self.project_path)

    def _read(self, path):
        proj = {}
        try:
            with open(path, 'r') as f:
                proj = json.load(f)
        except FileNotFoundError:
            pass
        return proj

    def _write(self):
        output = self.content
        output['files'] = list(self._file_set)
        with open(self.project_path, 'w') as f:
            json.dump(output, f,
                      sort_keys=True, indent=4,
                      separators=(',', ': '))

    def _list_paths(self):
        """
        Lists all file paths referenced by 'files', with directories expanded
        """
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
                    yield from (os.path.join(dirname, f) for f in file_list)
            else:
                yield path

    @property
    def inkling_file(self):
        inkling_path = self.content.get('inkling_main', None)
        if inkling_path:
            return inkling_path
        inkling_files = [f for f in self._list_paths() if f.endswith('.ink')]
        if len(inkling_files) != 1:
            if len(inkling_files) == 0:
                raise ProjectFileInvalidError('No inkling file found')
            raise ProjectFileInvalidError(
                'Multiple inkling files found. Set "inkling_main" in the'
                ' project file to indicate which should be loaded. '
                '{},{}, ... {} total'.format(inkling_files[0],
                                             inkling_files[1],
                                             len(inkling_files)))

        return inkling_files[0]

    @inkling_file.setter
    def inkling_file(self, value):
        self.content['inkling_main'] = value

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
