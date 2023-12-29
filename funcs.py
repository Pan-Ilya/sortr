from typing import Any
from decimal import Decimal
from PyPDF2 import PdfReader


def get_page_size(filename: [PdfReader | Any], height: bool = False, width: bool = False) -> int | list[int] | None:
    """ Если все страницы документа имеют одинаковую длину и ширину - возвращает указанный параметр
    height или width документа. """

    if not isinstance(filename, PdfReader):
        return None

    all_document_heights = [page.trimbox.height // Decimal(2.83) for page in filename.pages]
    all_document_widths = [page.trimbox.width // Decimal(2.83) for page in filename.pages]

    all_heights_equal = all(map(lambda x: x == all_document_heights[0], all_document_heights))
    all_widths_equal = all(map(lambda x: x == all_document_widths[0], all_document_widths))

    if not all_heights_equal and not all_widths_equal:
        return None
    elif height:
        return all_document_heights[0]
    elif width:
        return all_document_widths[0]
    elif height and width:
        return sorted([all_document_heights[0], all_document_widths[0]])
    else:
        return None


def check_colorify(f_colorify: str, f_quantity: int, pages: int) -> bool:
    """ Проверка цветности документа, так же учитываются виды. """

    if f_colorify in ['1+0', '4+0', '5+0'] and pages == f_quantity or \
            f_colorify in ['1+1', '4+4', '5+5'] and pages == 2 * f_quantity:
        return True

    return False
