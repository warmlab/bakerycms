class BakeryFilter(BaseFilter):
    def __init__(self, column, name, options=None, data_type=None):
        super(MyBaseFilter, self).__init__(name, options, data_type)

        self.column = column


class ProductFilter(BakeryFilter):
    def apply(self, query, value):
        return query.filter(self.column == value)

    def operation(self):
        return gettext('equals')

    # You can validate values. If value is not valid,
    # return `False`, so filter will be ignored.
    def validate(self, value):
        return True

    # You can "clean" values before they will be
    # passed to the your data access layer
    def clean(self, value):
        return value
