from wsvcs.src.tui import input_with_default
from .manifest import Manifest
from pathlib import Path


def get_default_manifest(project_root: Path) -> Manifest:
    manifest = Manifest()

    manifest['project'] = {
        'name': input_with_default(
            prompt  = 'Enter project name',
            default = project_root.name,
        ),

        'authors': input_with_default(
            prompt  = 'Enter authors separated by comma',
            default = 'unknown',
        ).split(','),

        'licence': input_with_default(
            prompt  = 'Licence',
            default = 'MIT',
        ),

        'ignore': [
            'wsvcs/.wsvcsignore',
        ]
    }

    manifest['sync'] = {
        'server': input_with_default(
            prompt  = 'Server Host',
            default = 'localhost:8765'
        ),
    }

    return manifest


__all__ = [
    'get_default_manifest'
]
