from builtins import bytes


def pkcs5_unpad(data):
    """Do PKCS5 unpadding to data and return

    """
    data_bytes = bytes(data)
    return data_bytes[0:-data_bytes[-1]]
