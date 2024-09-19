def merge_files(file1: str, file2: str) -> str:
    lines1 = [line for line in file1.splitlines(keepends=False) if len(line.strip()) > 0]
    lines2 = [line for line in file2.splitlines(keepends=False) if len(line.strip()) > 0]

    table = [[False] * len(lines2) for _ in range(len(lines1))]
    for i in range(len(lines1)):
        for j in range(len(lines2)):
            table[i][j] = hash(lines1[i]) == hash(lines2[j])

    f_ptr = 0
    s_ptr = 0
    result = ""

    while f_ptr < len(lines1) and s_ptr < len(lines2):
        if table[f_ptr][s_ptr]:
            result += lines1[f_ptr] + '\n'
            f_ptr += 1
            s_ptr += 1
        else:
            h_shift = None
            h_lines = []
            for shift in range(s_ptr, len(lines2)):
                if table[f_ptr][shift]:
                    h_shift = shift - s_ptr
                    break
                h_lines.append(lines2[shift])

            v_shift = None
            v_lines = []
            for shift in range(f_ptr, len(lines1)):
                if table[shift][s_ptr]:
                    v_shift = shift - f_ptr
                    break
                v_lines.append(lines1[shift])

            if h_shift is None and v_shift is None:
                print("Something went wrong")
                return ''

            elif h_shift is not None and v_shift is None:
                v_shift = float("inf")

            elif h_shift is None and v_shift is not None:
                h_shift = float("inf")

            if h_shift == v_shift:
                # merge conflict
                print("Merge conflict: ")
                print("A:")
                for row in h_lines:
                    print(row)

                print("B:")
                for row in v_lines:
                    print(row)

                choice = input('A or B: ')
                h_shift = float('inf') if choice == 'B' else h_shift
                v_shift = float('inf') if choice == 'A' else v_shift

            if h_shift > v_shift:
                result += lines1[f_ptr] + '\n'
                f_ptr += 1

            else:
                result += lines2[s_ptr] + '\n'
                s_ptr += 1

    while f_ptr < len(lines1):
        result += lines1[f_ptr] + '\n'
        f_ptr += 1

    while s_ptr < len(lines2):
        result += lines2[s_ptr] + '\n'
        s_ptr += 1

    return result


__all__ = [
    'merge_files'
]
