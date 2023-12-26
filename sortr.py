import os
import re
import shutil
import time
from typing import Any
from PyPDF2 import PdfReader
from decimal import Decimal


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
    input_SRA3_1_rez = fr'{lines[2]}'
    input_SRA3_plus_1_rez = fr'{lines[3]}'
    input_viz_4_0 = fr'{lines[4]}'
    input_viz_4_4 = fr'{lines[5]}'

    # -- All finish files were here.
    output = fr'{lines[6]}'
    # -- All errors files were here.
    errors = fr'{lines[7]}'

except FileNotFoundError:
    print('В текущей директории отсутствует файл settings.txt')
    exit_program(5, 1)
except IndexError:
    print('В файле settings.txt нужно указать все необходимые пути.')
    exit_program(5, 1)

# 2) Request to user to get path who contains files to do.
print('Укажите путь откуда брать макеты для раскладки:')
from_path = fr'{input().strip()}'
try:
    os.chdir(from_path)
except FileNotFoundError:
    print('Не верный адрес.')
    exit_program(5, 1)
print('Слушаю текущую папку...\n')


# 3) Read all filenames in from_path directory and sort each file to their hot folder.
# -- Using file size, colorify and canvas print size.


def get_all_filenames_in_directory(path: str) -> list[str]:
    try:
        return [file.name for file in os.scandir(path)]
    except FileNotFoundError:
        print('Не верный адрес.')
        exit_program(5, 1)


def get_params_from_filename(filename: str) -> list[str]:
    right_filename_pattern = r'(?i).*?(?P<size>\d+[xх]\d+).*?' \
                             r'(?P<color>\d\+\d).*?' \
                             r'(?P<quantity>\d*)?' \
                             r'(?P<canvas_size>SRA\d\+?).*?' \
                             r'(?P<extra>--)?(?:$|\.)'

    f_size, f_colorify, f_quantity, f_canvas_print_siz, extra = re.findall(right_filename_pattern, filename)[0]
    return [f_size, f_colorify, f_quantity, f_canvas_print_siz, extra]


def replacer(filename: str, destination: str) -> None:
    # Перемещение файла в указанную директорию
    if os.path.isfile(filename):
        os.replace(filename, destination)

    # Перезапись папки и содержимого
    elif os.path.isdir(filename) and os.path.exists(destination):
        shutil.rmtree(destination)
        os.replace(filename, destination)

    # Перемещение папки в указанную директорию
    elif os.path.isdir(filename):
        os.replace(filename, destination)

    else:
        raise NotADirectoryError('replacer function Error!')


def get_page_height(filename: [PdfReader | Any]) -> int | None:
    if isinstance(filename, PdfReader):
        return filename.pages[0].trimbox.height // Decimal(2.83)
    else:
        return None


def get_page_width(filename: [PdfReader | Any]) -> int | None:
    if isinstance(filename, PdfReader):
        return filename.pages[0].trimbox.width // Decimal(2.83)
    else:
        return None


while True:

    try:
        for filename in get_all_filenames_in_directory(from_path):
            filename_params = get_params_from_filename(filename)
            # filename_params = [f_size, f_colorify, f_quantity, f_canvas_print_siz, extra]
            print(filename_params)

            if os.path.isfile(filename):
                pdf_file = PdfReader(filename)
                pages = len(pdf_file.pages)
            else:
                pdf_file = None
                pages = 0

            match filename_params:
                # Проверка на виды.
                case _, f_colorify, f_quantity, _, _ \
                    if f_colorify in ['1+0', '4+0', '5+0'] and pages == int(f_quantity) or \
                       f_colorify in ['1+1', '4+4', '5+5'] and pages == 2 * int(f_quantity):
                    print('Отработал сценарий с виадами.')
                    replacer(filename, output + filename)

                # Начальная проверка на кол-во страниц документа и его цветность.
                case _, f_colorify, _, _, _ \
                    if f_colorify in ['1+0', '4+0', '5+0'] and pages not in [0, 1] or \
                       f_colorify in ['1+1', '4+4', '5+5'] and pages not in [0, 2]:
                    print(f'{filename} направляю в папку с ошибками.\nЦветность документа не соответствует подписи.\n')
                    replacer(filename, errors + filename)

                # Проверка trimbox-a документа:
                # 1) Если файл уже разложен на формат SRA3 или SRA3+ и его trimbox соответствует -
                #    подписи f_canvas_print_size, отправляем его в папку "готово".
                case _, _, _, f_canvas_print_size, _ \
                    if get_page_height(pdf_file) != get_page_width(pdf_file) \
                       and (
                               (
                                       f_canvas_print_size == 'SRA3' and \
                                       get_page_height(pdf_file) in [320, 450] and \
                                       get_page_width(pdf_file) in [320, 450]
                               )
                               or \
                               (
                                       f_canvas_print_size == 'SRA3+' and \
                                       get_page_height(pdf_file) in [330, 487] and \
                                       get_page_width(pdf_file) in [330, 487]
                               )
                       ):
                    # print(f'Файл {filename} перенаправляю сразу в папку с готовыми макетами.')
                    replacer(filename, output + filename)

                # 2) Если файл уже разложен на формат SRA3 или SRA3+ и его trimbox НЕ соответствует -
                #    подписи f_canvas_print_size, отправляем его в папку с ошибками.
                case _, _, _, f_canvas_print_size, _ \
                    if get_page_height(pdf_file) != get_page_width(pdf_file) \
                       and (
                               (
                                       f_canvas_print_size == 'SRA3' and \
                                       get_page_height(pdf_file) in [330, 487] and \
                                       get_page_width(pdf_file) in [330, 487]
                               )
                               or \
                               (
                                       f_canvas_print_size == 'SRA3+' and \
                                       get_page_height(pdf_file) in [320, 450] and \
                                       get_page_width(pdf_file) in [320, 450]
                               )
                       ):
                    print(
                        f'{filename} направляю в папку с ошибками.\nТрим-бокс текущей раскладки не соответствует подписи документа.\n')
                    replacer(filename, errors + filename)

                # Всё что идёт в viz_4+0
                case f_size, f_colorify, _, f_canvas_print_size, _ \
                    if (f_size in ['89x49', '49x89'] and f_colorify in ['1+0', '4+0', '5+0'] and
                        f_canvas_print_size == 'SRA3'):
                    replacer(filename, input_viz_4_0 + filename)

                # Всё что идёт в viz_4+4
                case f_size, f_colorify, _, f_canvas_print_size, _ \
                    if (f_size in ['89x49', '49x89'] and f_colorify in ['1+1', '4+4', '5+5'] and
                        f_canvas_print_size == 'SRA3'):
                    replacer(filename, input_viz_4_4 + filename)

                # Всё что идёт сразу в папку "готово" - output
                case f_size, f_colorify, _, f_canvas_print_size, _ \
                    if (f_size in ['487x330', '330x487'] and f_canvas_print_size == 'SRA3+') or \
                       (f_size in ['450x320', '320x450'] and f_canvas_print_size == 'SRA3'):
                    # print(f'Файл {filename} направляю в папку с готовыми макетами.')
                    replacer(filename, output + filename)

                # Всё что идёт в SRA3_universal_1_rez
                case f_size, f_colorify, _, f_canvas_print_size, extra \
                    if (f_size not in ['450x320', '320x450', '487x330', '330x487'] and
                        f_canvas_print_size == 'SRA3' and extra):
                    replacer(filename, input_SRA3_1_rez + filename)

                # Всё что идёт в SRA3+_universal_1_rez
                case f_size, f_colorify, _, f_canvas_print_size, extra \
                    if (f_size not in ['450x320', '320x450', '487x330', '330x487'] and
                        f_canvas_print_size == 'SRA3+' and extra):
                    replacer(filename, input_SRA3_plus_1_rez + filename)

                # Всё что идёт в SRA3_universal
                case f_size, f_colorify, _, f_canvas_print_size, _ \
                    if f_size not in ['450x320', '320x450', '487x330', '330x487'] and f_canvas_print_size == 'SRA3':
                    replacer(filename, input_SRA3 + filename)

                # Всё что идёт в SRA3+_universal
                case f_size, f_colorify, _, f_canvas_print_size, _ \
                    if f_size not in ['450x320', '320x450', '487x330', '330x487'] and f_canvas_print_size == 'SRA3+':
                    replacer(filename, input_SRA3_plus + filename)

                # Всё остальное. Wildcard.
                case _:
                    print(f'[E] Файл {filename} направляю в папку с ошибками.')
                    replacer(filename, errors + filename)

    except IndexError:
        print(f'Не понимаю имя файла {filename}.\nНаправляю его в папку с ошибками.\n')
        replacer(filename, errors + filename)
    except Exception as E:
        print(E)
        print('Произошла неожиданная ошибка. Повторяю попытку.')
        # exit_program(5, 1)
    finally:
        time.sleep(3)
