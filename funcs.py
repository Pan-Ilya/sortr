def vids_detected(f_colorify, f_quantity, pages):
    f_quantity = int(f_quantity) if f_quantity.isdigit() else 1

    if f_colorify in ['1+0', '4+0', '5+0'] and pages == f_quantity or \
            f_colorify in ['1+1', '4+4', '5+5'] and pages == 2 * f_quantity:
        return True
    return False
