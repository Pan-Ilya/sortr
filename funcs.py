import os
import re
import shutil
import time
from typing import Any
from PyPDF2 import PdfReader
from decimal import Decimal

COLOR_4_0 = ['1+0', '4+0', '5+0']
COLOR_4_4 = ['1+1', '4+4', '5+5']

SRA3 = (['450x320', '320x450'], [320, 450])
SRA3_PLUS = (['487x330', '330x487'], [330, 487])

ALLOWED_VIZ_SIZES = (['89x49', '49x89', '90x50', '50x90', '54x94', '94x54', '53x93', '93x53'], \
                     [[49, 89], [50, 90], [53, 93], [54, 94]])

PAGE_SIZE_DIAPASON = 10


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
    elif height and width:
        return sorted([document_height, document_width])
    elif height:
        return document_height
    elif width:
        return document_width
    else:
        return None


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
                             r'(?P<size>\d+[xх]\d+).*?' \
                             r'(?P<color>\d\+\d).*?' \
                             r'(?P<quantity>\d*)?' \
                             r'(?P<print_sheet_size>SRA\d\+?).*?' \
                             r'(?P<extra>--)?' \
                             r'(?:$|\.)'

    f_size, f_colorify, f_quantity, f_print_sheet_size, extra = re.findall(right_filename_pattern, filename)[0]
    f_quantity = int(f_quantity) if f_quantity.isdigit() else 1

    return [f_size, f_colorify, f_quantity, f_print_sheet_size, extra]


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
