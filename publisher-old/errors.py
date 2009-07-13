class MpttCantPublish(Exception):
    """Node is under mptt and can't be published because node parent isn't
    published."""