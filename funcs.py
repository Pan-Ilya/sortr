import os
import re
import shutil
import time
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
VILETI = 4

ALLOWED_VIZ_SIZES = {
    'file_signature': ['89x49', '49x89', '90x50', '50x90'],
    'size_value': [[53, 93], [54, 94]],
}


def get_current_time():
    return time.strftime("%H:%M:%S")


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


def check_colorify(f_colorify: str, f_quantity: int, pages: int) -> bool:
    """ Проверка цветности документа, так же учитываются виды. """

    if f_colorify in COLOR_4_4 and pages == f_quantity * 2 or \
            f_colorify in COLOR_4_0 and pages == f_quantity:
        return True

    return False


def decimal_to_mm(size: Decimal) -> int:
    """ Преобразуем inch в целочисленное значение метрической системы. """

    return int(size // Decimal(2.83))


def product_size_to_mm(product_size: str) -> list[int]:
    """ Возвращает список целочисленных значений ВхШ страницы документа. Результат отсортирован по возрастанию. """

    product_size = ''.join('x' if char.isalpha() else char for char in product_size)

    return sorted([int(size) for size in product_size.split('x')])


def all_pages_has_same_size(file: PdfReader) -> bool:
    """ Отвечает на вопрос равенства ВхШ всех страниц документа без учёта поворота. """

    if not isinstance(file, PdfReader):
        return False

    all_pages_sizes = list()
    for page in file.pages:
        page_size = [decimal_to_mm(page.cropbox.height), decimal_to_mm(page.cropbox.width)]
        page_size.sort()
        all_pages_sizes.append(page_size)

    return all(map(lambda x: x == all_pages_sizes[0], all_pages_sizes))


def get_current_page_size(page: 'PageObject') -> list[int]:
    """ Возвращает список из фактической (видимой) высоты и ширины текущей страницы документа. """

    return [decimal_to_mm(page.cropbox.height), decimal_to_mm(page.cropbox.width)]


def all_pages_are_landscape(file: PdfReader, product_size: str) -> bool:
    """ Выполняет проверку на горизонтальное положение всех страниц документа. """

    if product_size in ALLOWED_VIZ_SIZES['file_signature']:
        small_product_side, big_product_side = 50, 90

    elif product_size == SRA3['name']:
        small_product_side = SRA3['height']
        big_product_side = SRA3['width']

    elif product_size == SRA3_PLUS['name']:
        small_product_side = SRA3_PLUS['height']
        big_product_side = SRA3_PLUS['width']

    else:
        small_product_side, big_product_side = product_size_to_mm(product_size)

    for page in file.pages:
        file_height, file_width = get_current_page_size(page)

        if page.rotation % 180 == 0 and not \
                file_height <= small_product_side + VILETI:
            return False

        if page.rotation % 90 == 0 and page.rotation % 180 != 0 and not \
                file_width <= small_product_side + VILETI:
            return False

    return True


def all_pages_are_portrait(file: PdfReader, product_size: str) -> bool:
    """ Выполняет проверку на вертикальное положение всех страниц документа. """

    if product_size in ALLOWED_VIZ_SIZES['file_signature']:
        small_product_side, big_product_side = 50, 90

    elif product_size == SRA3['name']:
        small_product_side = SRA3['height']
        big_product_side = SRA3['width']

    elif product_size == SRA3_PLUS['name']:
        small_product_side = SRA3_PLUS['height']
        big_product_side = SRA3_PLUS['width']

    else:
        small_product_side, big_product_side = product_size_to_mm(product_size)

    for page in file.pages:
        file_height, file_width = get_current_page_size(page)

        if page.rotation % 180 == 0 and not \
                file_width <= small_product_side + VILETI:
            return False

        if page.rotation % 90 == 0 and page.rotation % 180 != 0 and not \
                file_height <= small_product_side + VILETI:
            return False

    return True


def CropBox_equal_product_size(file: PdfReader, product_size: str) -> bool:
    """ Фактический (видимый) размер документа равен размеру готового изделия.
    Размер готового изделия указан в подписи .pdf документа. """

    if not all_pages_has_same_size(file):
        return False

    pure_page_size_values = sorted(side_size - VILETI for side_size in get_current_page_size(file.pages[0]))
    return pure_page_size_values == product_size_to_mm(product_size)


def CropBox_equal_vizitka_90x50_size(file: PdfReader, product_size: str) -> bool:
    """ Фактический (видимый) размер документа равен размеру визитки (диапазон значений). """

    if not all_pages_has_same_size(file):
        return False

    elif product_size in ALLOWED_VIZ_SIZES['file_signature'] and \
            sorted(get_current_page_size(file.pages[0])) in ALLOWED_VIZ_SIZES['size_value']:
        return True


def CropBox_equal_SRA3_size(file: PdfReader, file_print_sheet_size: str) -> bool:
    """ Фактический (видимый) размер документа равен SRA3 (320х450 мм). """

    if not all_pages_has_same_size(file):
        return False

    page_height, page_width = sorted(get_current_page_size(file.pages[0]))

    if file_print_sheet_size == SRA3['name'] and \
            SRA3['height'] - PAGE_SIZE_DIAPASON <= page_height <= SRA3['height'] + VILETI and \
            SRA3['width'] - PAGE_SIZE_DIAPASON <= page_width <= SRA3['width'] + VILETI:
        return True


def CropBox_equal_SRA3_PLUS_size(file: PdfReader, file_print_sheet_size: str) -> bool:
    """ Фактический (видимый) размер документа равен SRA3+ (330х487 мм). """

    if not all_pages_has_same_size(file):
        return False

    page_height, page_width = sorted(get_current_page_size(file.pages[0]))

    if file_print_sheet_size == SRA3_PLUS['name'] and \
            SRA3_PLUS['height'] - PAGE_SIZE_DIAPASON <= page_height <= SRA3_PLUS['height'] + VILETI and \
            SRA3_PLUS['width'] - PAGE_SIZE_DIAPASON <= page_width <= SRA3_PLUS['width'] + VILETI:
        return True


# ====================================== В папки Hot Folder. ==========================================
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
