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


__all__ = ['choice_one', 'input_with_default']
