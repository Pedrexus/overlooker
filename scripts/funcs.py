def trend(value, P):
    if value > 0 and value > P:
        return 1
    elif value < 0 and abs(value) > P:
        return -1
    else:
        return 0
    
def trend2(value, P):
    if value > 0 and value > P:
        return value
    elif value < 0 and abs(value) > P:
        return -value
    else:
        return 0