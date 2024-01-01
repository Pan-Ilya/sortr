import os
import time
from PyPDF2 import PdfReader
import funcs

# 1) Open settings.txt file to get hot folder's paths.
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
    funcs.exit_program(5, 1)
except IndexError:
    print('В файле settings.txt нужно указать все необходимые пути.')
    funcs.exit_program(5, 1)

# 2) Request to user to get path who contains files to do.
print('Укажите путь откуда брать макеты для раскладки:')
from_path = fr'{input().strip()}'
try:
    os.chdir(from_path)
except FileNotFoundError:
    print('Не верный адрес.')
    funcs.exit_program(5, 1)
print('Слушаю текущую папку...\n')

# 3) Read all filenames in from_path directory and sort each file to their hot folder.
while True:

    try:
        for filename in funcs.get_all_filenames_in_directory(from_path):
            filename_params = funcs.get_params_from_filename(filename)
            # filename_params = [file_product_size, file_colorify, file_quantity, file_print_sheet_size, extra]

            if os.path.isfile(filename):
                pdf_file = PdfReader(filename)
                pages = len(pdf_file.pages)
            else:
                pdf_file = None
                pages = 0
                print(f'{filename}\nОбъект не является файлом, направляю в папку с ошибками.\n')
                funcs.replacer(filename, errors + filename)
                continue

            match filename_params:
                # ======================================= В папку errors. =============================================

                # Проверка на наличие BleedBox.
                case _, _, _, _, _, if funcs.have_BleedBox():
                    pass

                # Проверка цветности документа.
                case _, f_colorify, f_quantity, _, _, if not funcs.check_colorify(f_colorify, f_quantity, pages):
                    print(f'{filename}\nЦветность документа не соответствует подписи.\n')
                    funcs.replacer(filename, errors + filename)

                # Проверка размера документа.
                case f_product_size, _, _, f_print_sheet_size, _, \
                    if not (
                        funcs.TrimBox_equal_product_size(pdf_file, f_product_size) or \
                        funcs.TrimBox_equal_vizitka_90x50_size(pdf_file, f_product_size) or \
                        funcs.TrimBox_equal_SRA3_size(pdf_file, f_print_sheet_size) or \
                        funcs.TrimBox_equal_SRA3_PLUS_size(pdf_file, f_print_sheet_size)):
                    print(f'''{filename}
                    TrimBox документа не соответствует либо подписи раскладки либо подписи размера.\n''')
                    funcs.replacer(filename, errors + filename)

                # Проверка раскладки на поворот.
                case _, _, _, f_print_sheet_size, _, \
                    if not funcs.SRA3_or_SRA3_PLUS_horizontal(pdf_file, f_print_sheet_size):
                    print(f'{filename}\nФайл формата {f_print_sheet_size} вертикальный.\n')
                    funcs.replacer(filename, errors + filename)

                # ======================================= В папку output. =============================================

                # Печать в листах либо готовая раскладка.
                case _, _, _, f_print_sheet_size, _, \
                    if funcs.TrimBox_equal_SRA3_size(pdf_file, f_print_sheet_size) or \
                       funcs.TrimBox_equal_SRA3_PLUS_size(pdf_file, f_print_sheet_size):
                    funcs.replacer(filename, output + filename)

                # ====================================== В папки Hot Folder. ==========================================
                # Тут идёт работа только с подписями документа.

                # В папку с экшеном SRA3_universal
                case f_product_size, _, _, f_print_sheet_size, extra \
                    if funcs.go_to_SRA3_universal(f_product_size, f_print_sheet_size, extra):
                    funcs.replacer(filename, input_SRA3 + filename)

                # В папку с экшеном SRA3_universal_1_rez
                case f_product_size, _, _, f_print_sheet_size, extra \
                    if funcs.go_to_SRA3_universal_1_rez(f_product_size, f_print_sheet_size, extra):
                    funcs.replacer(filename, input_SRA3_1_rez + filename)

                # В папку с экшеном SRA3+_universal
                case _, _, _, f_print_sheet_size, extra \
                    if funcs.go_to_SRA3_PLUS_universal(f_print_sheet_size, extra):
                    funcs.replacer(filename, input_SRA3_plus + filename)

                # В папку с экшеном SRA3+_universal_1_rez
                case _, _, _, f_print_sheet_size, extra \
                    if funcs.go_to_SRA3_PLUS_universal_1_rez(f_print_sheet_size, extra):
                    funcs.replacer(filename, input_SRA3_plus + filename)

                # В папку с экшеном viz_4+0
                case f_product_size, f_colorify, _, f_print_sheet_size, _, \
                    if funcs.go_to_viz_4_0(f_product_size, f_colorify, f_print_sheet_size):
                    funcs.replacer(filename, input_viz_4_0 + filename)

                # В папку с экшеном viz_4+4
                case f_product_size, f_colorify, _, f_print_sheet_size, _, \
                    if funcs.go_to_viz_4_4(f_product_size, f_colorify, f_print_sheet_size):
                    funcs.replacer(filename, input_viz_4_4 + filename)

                # Все остальные случаи идут в папку с ошибками. Wildcard.
                case _:
                    print(f'[E] Файл {filename} направляю в папку с ошибками.\n')
                    funcs.replacer(filename, errors + filename)

    except IndexError:
        print(f'Не понимаю имя файла {filename}.\nНаправляю его в папку с ошибками.\n')
        funcs.replacer(filename, errors + filename)
    except Exception as E:
        print(E)
        print('Произошла неожиданная ошибка. Повторяю попытку.')
    finally:
        time.sleep(3)

# TODO:
#  - Добавить время для информационных принтов.                       +++
#  - Что делать с папками:
#   -- не выполнять проверку, сразу сортировать по имени
#   -- либо отправлять в папку с ошибками.                            +++
