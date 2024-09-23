from webcrane import LENGTH_OF_PATH_IN_PBAR
from termcolor import colored


def choice_one(prompts: list, input_prompt: str = ': '):
    while True:
        for i, prompt in enumerate(prompts):
            print(f"{i}) {prompt}")
            choice = input(input_prompt)

            if choice.isnumeric() and int(choice) < len(prompts):
                return choice
            else:
                print("Invalid input")


def input_with_default(prompt: str, default: str):
    command = input(f"{prompt} (skip/y to use [{default}]): ").strip()
    if command in ('', 'skip', 'y'):
        return default
    return command


def pretty_pbar(chunk_index: int, local_path: str) -> str:
    if len(local_path) <= LENGTH_OF_PATH_IN_PBAR:
        desc = f"{local_path:>{LENGTH_OF_PATH_IN_PBAR}}"
    else:
        desc = '...' + local_path[-LENGTH_OF_PATH_IN_PBAR + 3:]

    return f"[chunk: {chunk_index:>4}] Working on: {colored(desc, 'cyan')}"


__all__ = ['choice_one', 'input_with_default', 'pretty_pbar']
