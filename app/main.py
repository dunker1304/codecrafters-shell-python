import sys
import os

list_buildin_cmd = ['exit', 'echo', 'type']

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
            case "type":
                if len(command_with_args) < 2:
                    continue

                query = command_with_args[1]
                if query in list_buildin_cmd:
                    print(f"{query} is a shell buildin")
                else:
                    path_env = os.environ.get('PATH', '')
                    found = False
                    for d in path_env.split(':'):
                        if not d:
                            continue
                        candidate = os.path.join(d, query)
                        if os.path.isfile(candidate):
                            if os.access(candidate, os.X_OK):
                                print(f"{query} is {candidate}")
                                found = True
                                break
                            else:
                                continue

                    if not found:
                        print(f"{query}: not found")

            case _:
                print(f"{command}: command not found")
        

if __name__ == "__main__":
    main()
