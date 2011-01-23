class AttributeObject(object):
    """
    mock = AttributeObject(hello='world')
    mock.hello # 'world'
    """
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class DefaultAttributeObject(AttributeObject):
    def __init__(self, default, **kwargs):
        self.__default = default
        super(DefaultAttributeObject, self).__init__(**kwargs)