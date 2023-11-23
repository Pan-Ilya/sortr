import os
import re

# TODO: 1) Open settings.txt file to get hot folder's paths.
# TODO: -- All input files go there.

try:
    with open('settings.txt', 'r', encoding='utf-8') as settings:
        lines = list(map(str.strip, settings.readlines()))

    input_SRA3 = lines[0]
    input_SRA3_plus = lines[1]
    input_viz_4_0 = lines[2]
    input_viz_4_4 = lines[3]

    # TODO:  -- All finish files were here.
    output = lines[4]
    # TODO:  -- All errors files were here.
    errors = lines[5]
except FileNotFoundError:
    print('В текущей директории отсвутствует файл settings.txt')
except IndexError:
    print('В файле settings.txt нужно указать все необходимые пути.')

# TODO: 2) Request to user to get path who contains files to do.
from_path = input().strip()


# TODO: 3) Read all filenames in from_path directory and sort each file to their hot folder.
# TODO: -- Using file size, colorify and canvas print size.
# TODO: !!! DO RIGHT FILENAME PATTERN !!!


def get_all_filenames_in_directory(path: str) -> list[str]:
    for _, _, filenames in os.walk(from_path):
        return filenames


def get_params_from_filename(filename: str) -> list[str]:
    right_filename_pattern = r'(?i)(?P<date>\d{2}-\d{2}).*?' \
                             r'(?P<OrderID>\d+)_.*?' \
                             r'(?P<size>\d+[xх]\d+)_.*?' \
                             r'(?P<color>\d\+\d)_.*?' \
                             r'(?P<canvas_size>[\w]{3}\d\+?)_.*?' \
                             r'(?P<quantity>[\d ]{1,}).*?' \
                             r'(?P<file_format>\.pdf)?'

    _, _, file_size, file_colorify, file_canvas_print_size, _, _ = re.findall(right_filename_pattern, filename)[0]
    return [file_size, file_colorify, file_canvas_print_size]

# TODO: ??? 4) Check output hot folder "output" and "errors" and send a message to user how many files are done
#  len(output) and how many files are invalid len(errors). summ() of this file will == to len(from_path).
