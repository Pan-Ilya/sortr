import os
import re
import shutil
import time
from typing import Any
from PyPDF2 import PdfReader
from decimal import Decimal

COLOR_4_0 = ['1+0', '4+0', '5+0']
COLOR_4_4 = ['1+1', '4+4', '5+5']

SRA3 = {
    'name': 'SRA3',
    'file_signature': ['450x320', '320x450'],
    'size_value': [320, 450],
    'height': 320,
    'width': 450
}

SRA3_PLUS = {
    'name': 'SRA3+',
    'file_signature': ['487x330', '330x487'],
    'size_value': [330, 487],
    'height': 330,
    'width': 487
}

PAGE_SIZE_DIAPASON = 10

ALLOWED_VIZ_SIZES = {
    'file_signature': ['89x49', '49x89', '90x50', '50x90'],
    'size_value': [[49, 89], [50, 90], [53, 93], [54, 94]],
}


def get_current_time():
    return time.strftime("%H:%M:%S")


def get_page_size(file: [PdfReader | Any], height: bool = False, width: bool = False) -> int | list[int] | None:
    """ Если все страницы документа имеют одинаковую длину и ширину - возвращает указанный параметр
    height или width документа. """

    if not isinstance(file, PdfReader):
        return None

    all_document_heights = [int(page.trimbox.height // Decimal(2.83)) for page in file.pages]
    all_document_widths = [int(page.trimbox.width // Decimal(2.83)) for page in file.pages]

    document_width = all_document_widths[0]
    document_height = all_document_heights[0]

    all_heights_equal = all(map(lambda x: x == document_height, all_document_heights))
    all_widths_equal = all(map(lambda x: x == document_width, all_document_widths))

    if not (all_heights_equal and all_widths_equal):
        return None
    elif height and width or not (height or width):
        return sorted([document_height, document_width])
    elif height:
        return document_height
    elif width:
        return document_width
    else:
        return None


def SRA3_or_SRA3_PLUS_horizontal(file: PdfReader, file_print_sheet_size: str) -> bool:
    """ Проверяет TrimBox .pdf файла и его подпись, на основании чего делается вывод о положении документа
    (требуется горизонтальное расположение). """

    if file_print_sheet_size == SRA3['name'] and \
            get_page_size(file) == SRA3['size_value'] and get_page_size(file, height=True) != SRA3['height'] \
            or \
            file_print_sheet_size == SRA3_PLUS['name'] and \
            get_page_size(file) == SRA3_PLUS['size_value'] and get_page_size(file, height=True) != SRA3_PLUS['height']:
        return False
    return True


def check_BleedBox(file: PdfReader) -> bool:
    """ Выполняется проверка равенства BleedBox == TrimBox каждой страницы документа. """

    return all(page.trimbox == page.bleedbox for page in file.pages)


def check_colorify(f_colorify: str, f_quantity: int, pages: int) -> bool:
    """ Проверка цветности документа, так же учитываются виды. """

    if (
            f_colorify in COLOR_4_0 and pages == f_quantity
    ) or (
            f_colorify in COLOR_4_4 and pages == f_quantity * 2
    ):
        return True

    return False


def exit_program(time_sleep: int, exit_code: int) -> None:
    """ Прекращение исполнения программы через заданное время. """

    time.sleep(time_sleep)
    exit(exit_code)


def get_all_filenames_in_directory(path: str) -> list[str]:
    """ Читает имена всех файлов и папок в указанной директории. """

    try:
        return [file.name for file in os.scandir(path)]
    except FileNotFoundError:
        print('Не верный адрес.')
        exit_program(5, 1)


def get_params_from_filename(filename: str) -> list[str | int]:
    """ Возвращает список параметров .pdf файла из его названия.
     Пример имени файла:
     12-05_1108608_2v_160_120x45_4+0_350mat_lamGL1+1_2SRA3_po_160_listov.pdf """

    right_filename_pattern = r'(?i).*?' \
                             r'(?P<f_product_size>\d+[xх]\d+).*?' \
                             r'(?P<color>\d\+\d).*?' \
                             r'(?P<quantity>\d*)?' \
                             r'(?P<print_sheet_size>SRA\d\+?).*?' \
                             r'(?P<extra>--)?' \
                             r'(?:$|\.)'

    f_product_size, f_colorify, f_quantity, f_print_sheet_size, extra = re.findall(right_filename_pattern, filename)[0]
    f_quantity = int(f_quantity) if f_quantity.isdigit() else 1

    return [f_product_size, f_colorify, f_quantity, f_print_sheet_size, extra]


def replacer(filename: str, destination: str) -> None:
    """ Перемещает файл в указанную директорию. Всего 3 возможных варианта:
    1) Перемещение файла в указанную директорию
    2) Перезапись папки и содержимого
    3) Перемещение папки в указанную директорию
    """

    if os.path.isfile(filename):
        os.replace(filename, destination)

    elif os.path.isdir(filename) and os.path.exists(destination):
        shutil.rmtree(destination)
        os.replace(filename, destination)

    elif os.path.isdir(filename):
        os.replace(filename, destination)

    else:
        raise NotADirectoryError('replacer function Error!')


def TrimBox_equal_product_size(file: PdfReader, product_size: str) -> bool:
    """ Возвращает True, если TrimBox .pdf файла соответствует подписи размера готового изделия. """

    return get_page_size(file) == sorted(int(x) for x in product_size.split('x'))


def TrimBox_equal_vizitka_90x50_size(file: PdfReader, product_size: str) -> bool:
    """ Возвращает True, если TrimBox .pdf файла входит в множество допустимых размеров визитки 90х50 мм. """

    if product_size in ALLOWED_VIZ_SIZES['file_signature'] and \
            get_page_size(file) in ALLOWED_VIZ_SIZES['size_value']:
        return True
    return False


def TrimBox_equal_SRA3_size(file: PdfReader, file_print_sheet_size: str) -> bool:
    """ Возвращает True, если TrimBox .pdf файла соответствует размеру 450х320 мм. """

    if file_print_sheet_size == SRA3['name'] and \
            SRA3['height'] - PAGE_SIZE_DIAPASON <= get_page_size(file, height=True) <= SRA3['height'] and \
            SRA3['width'] - PAGE_SIZE_DIAPASON <= get_page_size(file, width=True) <= SRA3['width']:
        return True
    return False


def TrimBox_equal_SRA3_PLUS_size(file: PdfReader, file_print_sheet_size: str) -> bool:
    """ Возвращает True, если TrimBox .pdf файла соответствует размеру 487x330 мм. """

    if file_print_sheet_size == SRA3_PLUS['name'] and \
            SRA3_PLUS['height'] - PAGE_SIZE_DIAPASON <= get_page_size(file, height=True) <= SRA3_PLUS['height'] and \
            SRA3_PLUS['width'] - PAGE_SIZE_DIAPASON <= get_page_size(file, width=True) <= SRA3_PLUS['width']:
        return True
    return False


def go_to_SRA3_universal(product_size: str, file_print_sheet_size: str, extra: str) -> bool:
    """ Отвечает на вопрос, какие файлы идут на раскладку с помощью экшена SRA3_universal. """

    return product_size not in ALLOWED_VIZ_SIZES['file_signature'] and \
        file_print_sheet_size == SRA3['name'] and \
        not extra


def go_to_SRA3_universal_1_rez(product_size: str, file_print_sheet_size: str, extra: str) -> bool:
    """ Отвечает на вопрос, какие файлы идут на раскладку с помощью экшена SRA3_universal_1_rez. """

    return product_size not in ALLOWED_VIZ_SIZES['file_signature'] and \
        file_print_sheet_size == SRA3['name'] and \
        extra


def go_to_SRA3_PLUS_universal(file_print_sheet_size: str, extra: str) -> bool:
    """ Отвечает на вопрос, какие файлы идут на раскладку с помощью экшена SRA3+_universal. """

    return file_print_sheet_size == SRA3_PLUS['name'] and not extra


def go_to_SRA3_PLUS_universal_1_rez(file_print_sheet_size: str, extra: str) -> bool:
    """ Отвечает на вопрос, какие файлы идут на раскладку с помощью экшена SRA3+_universal_1_rez. """

    return file_print_sheet_size == SRA3_PLUS['name'] and extra


def go_to_viz_4_0(product_size: str, file_colorify: str, file_print_sheet_size: str) -> bool:
    """ Отвечает на вопрос, какие файлы идут на раскладку с помощью экшена viz_4+0. """

    return product_size in ALLOWED_VIZ_SIZES['file_signature'] and \
        file_colorify in COLOR_4_0 and \
        file_print_sheet_size == SRA3['name']


def go_to_viz_4_4(product_size: str, file_colorify: str, file_print_sheet_size: str) -> bool:
    """ Отвечает на вопрос, какие файлы идут на раскладку с помощью экшена viz_4+4. """

    return product_size in ALLOWED_VIZ_SIZES['file_signature'] and \
        file_colorify in COLOR_4_4 and \
        file_print_sheet_size == SRA3['name']
