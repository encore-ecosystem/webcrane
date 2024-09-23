class Package:
    def __init__(self):
        self.data = {}

    def __repr__(self):
        return f"Package: {self.data}"


class FileChunk(Package):
    def __init__(self, data: bytes, local_path: str):
        super().__init__()
        self.data['data'] = data
        self.data['local_path'] = local_path


class PackageChunk(Package):
    def __init__(self, package: Package):
        super().__init__()
        self.data['package'] = package


class StartSection(Package):
    pass


class EndSection(Package):
    pass


class StartGenerator(Package):
    pass


class EndGenerator(Package):
    pass


class PackageHash(Package):
    def __init__(self, hash_: str, filepath: str):
        super().__init__()
        self.data['hash'] = hash_
        self.data['filepath'] = filepath


class ProjectPackage(Package):
    def __init__(self, project_name: str):
        super().__init__()
        self.data['project_name'] = project_name


class MissingFiles(Package):
    def __init__(self, missing_files: set):
        super().__init__()
        self.data['missing_files'] = missing_files


class CompletePackage(Package):
    pass


class ClosePackage(Package):
    pass


class RefreshPackage(Package):
    def __init__(self, subs: list):
        super().__init__()
        self.data['subs'] = subs


class RolePackage(Package):
    def __init__(self, role: str):
        super().__init__()
        self.data['role'] = role
