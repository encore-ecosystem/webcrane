# ====================
# Parse client arguments
# ====================
from argparse import ArgumentParser

parser = ArgumentParser(
    prog = 'wsvcs',
    description = 'WebSockets Version Control System',
)
parser.add_argument('mode', help='''
init   - Initialize current directory as project
deploy - Use this device as middleware server
pull   - Create pull request
push   - Create push request
client    - Open Command Line Interface
''')
args = parser.parse_args()


# ======================
# Standard functional
# ======================
valid_commands = ['init', 'deploy', 'pull', 'push', 'client', 'run']
