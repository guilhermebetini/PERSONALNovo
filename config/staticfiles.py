import os

from django.contrib.staticfiles.finders import FileSystemFinder


class CrossPlatformFileSystemFinder(FileSystemFinder):
    def find(self, path, find_all=False, **kwargs):
        path = path.replace("/", os.sep)
        return super().find(path, find_all=find_all, **kwargs)
