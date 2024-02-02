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
        all_filenames_in_directory = funcs.get_all_filenames_in_directory(from_path)
        all_multy_pages = list(filter(funcs.get_multy_page_params_from_filename, all_filenames_in_directory))
        all_print_files = list(filter(funcs.get_params_from_filename, all_filenames_in_directory))
        all_other_files = set(all_filenames_in_directory) - (set(all_multy_pages) | set(all_print_files))

        # Перебор всех неизвестных имён, которые не соответствую ни одному регулярному выражению.
        for unknown_name in all_other_files:
            print(f'''[{funcs.get_current_time()}]   {unknown_name}
            \rНе понимаю имя файла. Направляю его в папку с ошибками.\n''')
            funcs.replacer(unknown_name, errors + unknown_name)

        # Перебор всех многостраничных документов (брошюры на скобу и пружину, каталоги).
        for multy_pages_name in all_multy_pages:

            if os.path.isdir(multy_pages_name):
                print(f'''[{funcs.get_current_time()}]   {multy_pages_name}
                \rФайлы многостранички проверяю без папок. Ошибка.\n''')
                funcs.replacer(multy_pages_name, errors + multy_pages_name)
                continue

            multy_pages_param = funcs.get_multy_page_params_from_filename(multy_pages_name)
            # multy_pages_param = [product, colorify, quantity, print_sheet_size]

            pdf_file = PdfReader(multy_pages_name)
            pages = len(pdf_file.pages)

            match multy_pages_param:

                # Проверка цветности документа.
                case _, f_colorify, f_quantity, _ if not funcs.check_colorify(f_colorify, f_quantity, pages):
                    print(f'''[{funcs.get_current_time()}]   {multy_pages_name}
                    \rЦветность многостранички не соответствует подписи.\n''')
                    funcs.replacer(multy_pages_name, errors + multy_pages_name)

                # Проверка раскладки документа.
                case _, _, _, f_print_sheet_size \
                    if not (
                        funcs.CropBox_equal_SRA3_size(pdf_file, f_print_sheet_size) or
                        funcs.CropBox_equal_SRA3_PLUS_size(pdf_file, f_print_sheet_size)):
                    print(f'''[{funcs.get_current_time()}]   {multy_pages_name}
                    \rРазмер печатного листа многостранички не соответствует подписи.\n''')
                    funcs.replacer(multy_pages_name, errors + multy_pages_name)

                # Все остальные случаи идут в папку готово. Wildcard.
                case _:
                    print(f'''[{funcs.get_current_time()}]   {multy_pages_name}
                    \rМногостраничка Ок.\n''')
                    funcs.replacer(multy_pages_name, output + multy_pages_name)

        # Перебор всех листовых/в листах макетов.
        for filename in all_print_files:

            FILE = False
            DIR = False

            if os.path.isfile(filename):
                FILE = True
                pdf_file = PdfReader(filename)
                pages = len(pdf_file.pages)

            elif os.path.isdir(filename):
                DIR = True
                files_in_directory = funcs.get_all_filenames_in_directory(filename)
                # files_in_directory = funcs.get_all_filenames_in_directory(f"{from_path}\\{filename}")

                # Проверка количества файлов внутри папки.
                if len(files_in_directory) != 2:
                    print('Папка содержит более 2ух файлов. Напрвялю в ошибки.')
                    funcs.replacer(filename, errors + filename)
                    continue

                print('Мы тут')
                os.chdir(f"{from_path}\\{filename}")
                lic, ob = (PdfReader(file) for file in files_in_directory)
                print(lic, ob, sep='\n')
                os.chdir(from_path)


                # Проверка количесвта страниц документа внутри папки.
                if len(lic.pages) != 1 or len(ob.pages) != 1:
                    print('Файл внутри папки содержит более одной страницы. Напрвялю в ошибки.')
                    funcs.replacer(filename, errors + filename)
                    continue

            else:
                print(f'''[{funcs.get_current_time()}]   {filename}'
                      \rОбъект не является ни файлом ни папкой, направляю его в папку с ошибками.\n''')
                funcs.replacer(filename, errors + filename)
                continue


            filename_params = funcs.get_params_from_filename(filename)
            # filename_params = [file_product_size, file_colorify, file_quantity, file_print_sheet_size, extra]


            match filename_params:
                # ======================================= В папку errors. =============================================

                # <------------------------------------ Проверка для файлов ------------------------------------>
                # Проверка цветности документа.
                case _, f_colorify, f_quantity, _, _, if FILE and not funcs.check_colorify(f_colorify, f_quantity, pages):
                    print(f'[{funcs.get_current_time()}]   {filename}\nЦветность документа не соответствует подписи.\n')
                    funcs.replacer(filename, errors + filename)

                # Проверка размера документа.
                case f_product_size, _, _, f_print_sheet_size, _, \
                    if FILE and not (
                        funcs.CropBox_equal_product_size(pdf_file, f_product_size) or
                        funcs.CropBox_equal_vizitka_90x50_size(pdf_file, f_product_size) or
                        funcs.CropBox_equal_SRA3_size(pdf_file, f_print_sheet_size) or
                        funcs.CropBox_equal_SRA3_PLUS_size(pdf_file, f_print_sheet_size)):
                    print(f'''[{funcs.get_current_time()}]   {filename}
                        \rCropBox документа не соответствует либо формату раскладки {f_print_sheet_size}, либо \
размеру подписи {f_product_size}.\n''')
                    funcs.replacer(filename, errors + filename)

                # Проверка раскладки на горизонтальное положение.
                case _, _, _, f_print_sheet_size, _, \
                    if FILE and (
                        funcs.CropBox_equal_SRA3_size(pdf_file, f_print_sheet_size) or
                        funcs.CropBox_equal_SRA3_PLUS_size(pdf_file, f_print_sheet_size)) and not \
                           funcs.all_pages_are_landscape(pdf_file, f_print_sheet_size):
                    print(f'''[{funcs.get_current_time()}]   {filename}
                    \rПечать в листах имеет либо разную ориентацию страниц, либо вертикальную.\n''')
                    funcs.replacer(filename, errors + filename)

                # Проверка файла на одинаковую ориентацию страниц документа.
                case f_product_size, _, _, f_print_sheet_size, _, \
                    if FILE and not (
                            funcs.CropBox_equal_SRA3_size(pdf_file, f_print_sheet_size) or
                            funcs.CropBox_equal_SRA3_PLUS_size(pdf_file, f_print_sheet_size)) and not \
                           (funcs.all_pages_are_landscape(pdf_file, f_product_size) or
                            funcs.all_pages_are_portrait(pdf_file, f_product_size)):
                    print(f'''[{funcs.get_current_time()}]   {filename}
                    \rСтраницы документа имеют разную ориентацию.\n''')
                    funcs.replacer(filename, errors + filename)

                # <------------------------------------ Проверка для Папок ------------------------------------>

                # ПАПКА. Проверка размера документа.
                case f_product_size, _, _, f_print_sheet_size, _, \
                    if DIR and not (
                        funcs.CropBox_equal_product_size(lic, f_product_size) and funcs.CropBox_equal_product_size(ob, f_product_size)or
                        funcs.CropBox_equal_vizitka_90x50_size(lic, f_product_size) and funcs.CropBox_equal_vizitka_90x50_size(ob, f_product_size) or
                        funcs.CropBox_equal_SRA3_size(lic, f_print_sheet_size) and funcs.CropBox_equal_SRA3_size(ob, f_print_sheet_size) or
                        funcs.CropBox_equal_SRA3_PLUS_size(lic, f_print_sheet_size) and funcs.CropBox_equal_SRA3_PLUS_size(ob, f_print_sheet_size)):
                    print(f'''[{funcs.get_current_time()}]   {filename}
                        \rCropBox документа не соответствует либо формату раскладки {f_print_sheet_size}, либо \
размеру подписи {f_product_size}.\n''')
                    funcs.replacer(filename, errors + filename)

                # ПАПКА. Проверка раскладки на горизонтальное положение.
                case _, _, _, f_print_sheet_size, _, \
                    if DIR and (
                        funcs.CropBox_equal_SRA3_size(lic, f_print_sheet_size) and funcs.CropBox_equal_SRA3_size(ob, f_print_sheet_size) or
                        funcs.CropBox_equal_SRA3_PLUS_size(lic, f_print_sheet_size) and funcs.CropBox_equal_SRA3_PLUS_size(ob, f_print_sheet_size)
                        ) and not (
                        funcs.all_pages_are_landscape(lic, f_print_sheet_size) and funcs.all_pages_are_landscape(ob, f_print_sheet_size)):
                    print(f'''[{funcs.get_current_time()}]   {filename}
                    \rПечать в листах имеет либо разную ориентацию страниц, либо вертикальную.\n''')
                    funcs.replacer(filename, errors + filename)

                # ПАПКА. Проверка файла на одинаковую ориентацию страниц документа.
                case f_product_size, _, _, f_print_sheet_size, _, \
                    if DIR and not (
                        funcs.CropBox_equal_SRA3_size(lic, f_print_sheet_size) and funcs.CropBox_equal_SRA3_size(ob, f_print_sheet_size) or
                        funcs.CropBox_equal_SRA3_PLUS_size(lic, f_print_sheet_size) and funcs.CropBox_equal_SRA3_PLUS_size(ob, f_print_sheet_size)
                        ) and not (
                        funcs.all_pages_are_landscape(lic, f_product_size) and funcs.all_pages_are_landscape(ob, f_product_size) or
                        funcs.all_pages_are_portrait(lic, f_product_size) and funcs.all_pages_are_portrait(ob, f_product_size)):
                    print(f'''[{funcs.get_current_time()}]   {filename}
                    \rСтраницы документа внутри папки имеют разную ориентацию.\n''')
                    funcs.replacer(filename, errors + filename)
                #
                #
                # ======================================= В папку output. =============================================
                #    
                # Печать в листах либо готовая раскладка.
                case _, _, _, f_print_sheet_size, _, \
                    if FILE and (
                        funcs.CropBox_equal_SRA3_size(pdf_file, f_print_sheet_size) or
                        funcs.CropBox_equal_SRA3_PLUS_size(pdf_file, f_print_sheet_size)):
                    funcs.replacer(filename, output + filename)

                # <------------------------------------ Проверка для Папок ------------------------------------>
                #
                # ПАПКА. Печать в листах либо готовая раскладка. СОЗДАТЬ ПАПКУ ДЛЯ КОМБАЙНА СТРАНИЦ.
                case _, _, _, f_print_sheet_size, _, \
                    if DIR and (
                        funcs.CropBox_equal_SRA3_size(lic, f_print_sheet_size) and funcs.CropBox_equal_SRA3_size(ob, f_print_sheet_size) or
                        funcs.CropBox_equal_SRA3_PLUS_size(lic, f_print_sheet_size) and funcs.CropBox_equal_SRA3_PLUS_size(ob, f_print_sheet_size)
                        ):
                    print(f'''[{funcs.get_current_time()}]   {filename}
                    \rФайлы внутри папки - это готовые расскалдки с правильной ориентацией. Направляюв готово!\n''')
                    funcs.replacer(filename, output + filename)
                #
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
                    funcs.replacer(filename, input_SRA3_plus_1_rez + filename)

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
                    print(f'[{funcs.get_current_time()}][E]   {filename}\nНаправляю в папку с ошибками.\n')
                    funcs.replacer(filename, errors + filename)

    except IndexError:
        print(f'[{funcs.get_current_time()}]   Не понимаю имя файла {filename}.\nНаправляю его в папку с ошибками.\n')
        funcs.replacer(filename, errors + filename)
    except Exception as E:
        print(E)
        print(f'[{funcs.get_current_time()}]   Произошла неожиданная ошибка. Повторяю попытку.')
    finally:
        time.sleep(3)

# TODO:
#  - Что делать с папками:
#   -- не выполнять проверку, сразу сортировать по имени
#   -- либо отправлять в папку с ошибками.                            +++
