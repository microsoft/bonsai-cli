"""
This file implements the .brains settings support.  If .brains
exists in the local directory while running the CLI, it will
be queried for the active brain.
"""
import os
import json

DEFAULT_FILE = '.brains'


class BrainRef():
    """
    A reference to a brain, which stores the name and default state.
    The main behaviors are converting the object to and from a json
    dictionary.
    """
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', "brain")
        self.default = kwargs.get('default', False)

    def to_dict(self):
        return self.__dict__

    def __repr__(self):
        return str(self.__dict__)

    @staticmethod
    def from_json(dict_):
        if 'name' in dict_:
            return BrainRef(**dict_)
        return dict_


class DotBrains():
    """
    Represents the .brains file, essentially a list of names which
    can be flagged as 'default', and a lookup to find the brain name
    that is currently flagged. Modifying the file triggers a write.
    """
    def __init__(self, path='.'):
        self.path = path
        self.brains = self._read()

    @staticmethod
    def find_file(directory):
        """ Returns path of 1st .brains file found given directory. """
        path = os.path.join(directory, DEFAULT_FILE)
        if os.path.exists(path):
            return path
        else:
            return None

    def _read(self):
        brains = []
        try:
            path = os.path.join(self.path, '.brains')
            with open(path, 'r') as f:
                b_obj = json.load(f, object_hook=BrainRef.from_json)
                brains = b_obj.get('brains', [])
        except (OSError, IOError):
            pass
        return brains

    def _write(self):
        output = {
            'brains': [b.to_dict() for b in self.brains]
            }
        path = os.path.join(self.path, '.brains')
        with open(path, 'w') as f:
            json.dump(output, f)

    def find(self, brain_name):
        for b in self.brains:
            if (b.name == brain_name):
                return b
        return None

    def get_default(self):
        for b in self.brains:
            if b.default:
                return b

    def add(self, brain_name):
        newRef = BrainRef(name=brain_name)
        self.brains.append(newRef)
        self.set_default(newRef)
        self._write()
        return newRef

    def set_default(self, ref):
        if not isinstance(ref, BrainRef):
            raise RuntimeError("ref argument was not a BrainRef. set_default"
                               "must be passed the result of add() or find()")

        for b in self.brains:
            b.default = False
        ref.default = True
        self._write()
