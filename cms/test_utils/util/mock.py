class AttributeObject:
    """
    mock = AttributeObject(hello='world')
    mock.hello # 'world'
    """
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return '<AttributeObject: %r>' % self.kwargs


class DefaultAttributeObject(AttributeObject):
    def __init__(self, default, **kwargs):
        self.__default = default
        super().__init__(**kwargs)
