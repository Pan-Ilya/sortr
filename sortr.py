import os
import re
import time


# 1) Open settings.txt file to get hot folder's paths.
# -- All input files go there.
def exit_program(time_sleep: int, exit_code: int) -> None:
    time.sleep(time_sleep)
    exit(exit_code)


try:
    with open('settings.txt', 'r') as settings:
        lines = list(map(str.strip, settings.readlines()))

    input_SRA3 = fr'{lines[0]}'
    input_SRA3_plus = fr'{lines[1]}'
    input_viz_4_0 = fr'{lines[2]}'
    input_viz_4_4 = fr'{lines[3]}'

    # -- All finish files were here.
    output = fr'{lines[4]}'
    # -- All errors files were here.
    errors = fr'{lines[5]}'
except FileNotFoundError:
    print('В текущей директории отсвутствует файл settings.txt')
    exit_program(5, 1)
except IndexError:
    print('В файле settings.txt нужно указать все необходимые пути.')
    exit_program(5, 1)

# 2) Request to user to get path who contains files to do.
print('Укажите путь откуда брать макеты для расскалдки:')
from_path = fr'{input().strip()}'
try:
    os.chdir(from_path)
except FileNotFoundError:
    print('Не верный адрес.')
    exit_program(5, 1)


# TODO: 3) Read all filenames in from_path directory and sort each file to their hot folder.
# TODO: -- Using file size, colorify and canvas print size.


def get_all_filenames_in_directory(path: str) -> list[str]:
    try:
        return [file.name for file in os.scandir(path)]
    except FileNotFoundError:
        print('Не верный адрес.')
        exit_program(5, 1)


def get_params_from_filename(filename: str) -> list[str]:
    right_filename_pattern = r'(?i).*?(?P<size>\d+[xх]\d+).*?' \
                             r'(?P<color>\d\+\d).*?' \
                             r'(?P<canvas_size>SRA\d\+?).*?' \
                             r'(?P<extra>--)?\.'

    file_size, file_colorify, file_canvas_print_siz, extra = re.findall(right_filename_pattern, filename)[0]
    return [file_size, file_colorify, file_canvas_print_siz, extra]


while True:

    try:
        for filename in get_all_filenames_in_directory(from_path):
            filename_params = get_params_from_filename(filename)

            match filename_params:
                # Всё что идёт в viz_4+0
                case f_size, f_colorify, f_canvas_print_size \
                    if f_size in ['89x49', '49x89'] and f_colorify in ['4+0', '1+0'] and f_canvas_print_size == 'SRA3':
                    os.replace(filename, input_viz_4_0 + filename)

                # Всё что идёт в viz_4+4
                case f_size, f_colorify, f_canvas_print_size \
                    if f_size in ['89x49', '49x89'] and f_colorify in ['4+4', '1+1'] and f_canvas_print_size == 'SRA3':
                    os.replace(filename, input_viz_4_4 + filename)

                # Всё что идёт сразу в папку "готово" - output
                case f_size, f_colorify, f_canvas_print_size \
                    if (f_size in ['487x330', '330x487'] and f_canvas_print_size == 'SRA3+') or \
                       (f_size in ['450x320', '320x450'] and f_canvas_print_size == 'SRA3'):
                    os.replace(filename, output + filename)

                # Всё что идёт в SRA3_universal
                case f_size, f_colorify, f_canvas_print_size \
                    if f_size not in ['450x320', '320x450', '487x330', '330x487'] and f_canvas_print_size == 'SRA3':
                    os.replace(filename, input_SRA3 + filename)

                # Всё что идёт в SRA3+_universal
                case f_size, f_colorify, f_canvas_print_size \
                    if f_size not in ['450x320', '320x450', '487x330', '330x487'] and f_canvas_print_size == 'SRA3+':
                    os.replace(filename, input_SRA3_plus + filename)

                # Всё остальное. Wildcard.
                case _:
                    os.replace(filename, errors + filename)

        time.sleep(3)

    except:
        print(f'Не понимаю файл с именем {filename}\n направляю в папку с ошибками')
        os.replace(filename, errors + filename)

# TODO: ??? 4) Check output hot folder "output" and "errors" and send a message to user how many files are done
#  len(output) and how many files are invalid len(errors). summ() of this file will == to len(from_path).
