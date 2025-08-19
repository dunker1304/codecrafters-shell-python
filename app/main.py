import sys


def main():
    # Uncomment this block to pass the first stage
    while True:
        sys.stdout.write("$ ")

        # Wait for user input
        input_line = input()
        if input_line == "":
            continue

        command_with_args = input_line.split()
        command = command_with_args[0]

        match command:
            case "exit":
                break
            case "echo":
                print(" ".join(command_with_args[1:]))
            case _:
                print(f"{command}: command not found")


if __name__ == "__main__":
    main()
