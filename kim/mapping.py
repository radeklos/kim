from collections import defaultdict

from .type_mapper import BaseTypeMapper
from .exceptions import ValidationError, MappingErrors, FieldError


class BaseMapping(object):
    pass


class Mapping(BaseMapping):
    """:class:`kim.mapping.Mapping` is a factory for generating data
    structures in KIM.

    A mapping consists of a collection of kim `field` types.

    `Mappings` are created by passing `Fields` to the
    contructor of :class:`kim.mapping.Mapping`

     e.g.::

        my_mapping = Mapping(
             String('name'),
             Integer('id'),
        )

    The first argument to the Mapping type is the name of this mapping,
    the following arguments may be any mixture of `Field` types.

    :param fields: contains the `collection` of Field types provided

        Any field inherting from :class:`kim.fields.BaseType` is considered
        to be a valid field passed into a mapping.

    :param collection: Provided as a keyword arg to a `mapping` sets the data
                       structure used to store `fields` in. (default list)

    .. seealso::

        :class:`kim.fields.BaseType`

    """

    def __init__(self, *args, **kwargs):
        """:class:`kim.mapping.Mapping` constructor.

        """
        mapped_types = args[0:]

        self.fields = kwargs.get('collection', list())

        self._arg_loop(mapped_types)

    def __iter__(self):
        return iter(self.fields)

    def _arg_loop(self, items):
        """Iterates over collection of constructor args and assigns
        accordingly.

        :param items: collection of Field and Role type args.

        :returns: None
        """

        for item in items:
            if isinstance(item, BaseTypeMapper):
                self.add_field(item)

    def add_field(self, field):
        """Add a `field` type to the `fields` collection.

        :param field: A field type

        .. seealso::
            :class:`kim.fields.BaseType`

        :returns: None
        """
        self.fields.append(field)


def get_attribute(data, attr):
    """Attempt to find the value for a `field` from `data`.

    :param data: dict like object containing input data
    :param field: mapped field.

    :returns: the value for `field` from `data`
    """
    if attr == '__self__':
        return data
    elif isinstance(data, dict):
        return data.get(attr)
    else:
        return getattr(data, attr, None)


class MappingIterator(object):

    def __init__(self, output=None, errors=None):
        self.output = output or dict()
        self.errors = errors or defaultdict(list)

    @classmethod
    def run(cls, mapping, data, many=False, **kwargs):
        if many:
            return [cls.run(mapping, d, many=False) for d in data]
        else:
            return cls()._run(mapping, data, **kwargs)

    def _run(self, mapping, data, **kwargs):
        """`run` the mapping iteration loop.

        :param data: dict like data being mapped
        :param mapping: :class:`kim.mapping.Mapping`
        :param many: map several instances of `data` to `mapping`

        :raises: MappingErrors
        :returns: serializable output
        """

        for field in mapping.fields:
            try:
                value = self.process_field(field, data)
                self.update_output(field, value)
            except FieldError as e:
                self.errors[e.key].append(e.message)
                continue

        if self.errors:
            raise MappingErrors(self.errors)

        return self.output


class BaseDataMapping(object):

    def get_attribute(self, data, field_name):
        """return the value of field_name from data.

        .. seealso::
            :func:`kim.mapping.get_attribute`

        """
        return get_attribute(data, field_name)

    def process_field(self, field, data):
        """Process a field mapping using `data`.  This method should
        return both the field.name or field.source value plus the value to
        map to the field.

        e.g::
            value = self.get_attribute(data, field.source)
            field.validate_for_marshal(value)

            return field.marshal_value(value or field.default)
        """
        value = self.get_attribute(data, field)
        return self.validate(field, value)

    def update_output(self, field, value):

        raise NotImplementedError("Concrete classes must inplement "
                                  "update_output method")

    def validate(self, field, value):
        try:
            self.validate_field(field, value)
        except ValidationError as e:
            raise FieldError(field.source, e.message)

        return value


class MarshalMixin(BaseDataMapping):

    def get_attribute(self, data, field):

        return get_attribute(data, field.name)

    def update_output(self, field, value):

        if field.source == '__self__':
            self.output.update(value)
        else:
            self.output[field.source] = value

    def validate_field(self, field, value):

        field.validate_for_marshal(value)

    def process_field(self, field, data):

        value = super(MarshalMixin, self).process_field(field, data)
        return field.marshal_value(value or field.default)


class SerializeMixin(BaseDataMapping):

    def get_attribute(self, data, field):

        return get_attribute(data, field.source)

    def update_output(self, field, value):

        self.output[field.name] = value

    def validate_field(self, field, value):

        field.validate_for_serialize(value)

    def process_field(self, field, data):

        value = super(SerializeMixin, self).process_field(field, data)
        return field.serialize_value(value or field.default)


class SerializeMapping(MappingIterator, SerializeMixin):
    pass


class MarshalMapping(MappingIterator, MarshalMixin):
    pass


class ValidateOnlyIterator(MappingIterator):

    def _run(self, mapping, data, **kwargs):
        """`run` the mapping iteration loop.

        :param data: dict like data being mapped
        :param mapping: :class:`kim.mapping.Mapping`
        :param many: map several instances of `data` to `mapping`

        :raises: MappingErrors
        :returns: serializable output
        """

        for field in mapping.fields:
            try:
                self.process_field(field, data)
            except FieldError as e:
                self.errors[e.key].append(e.message)

        if self.errors:
            raise MappingErrors(self.errors)


class ValidateOnlySerializer(ValidateOnlyIterator, SerializeMixin):
    pass


class ValidateOnlyMarshaler(ValidateOnlyIterator, MarshalMixin):
    pass


def marshal(mapping, data, **kwargs):
    """`marshal` data to an expected output for a
    `mapping`

    :param mapping: :class:`kim.mapping.Mapping`
    :param data: `dict` or collection of dicts to marshal to a `mapping`

    :raises: TypeError, ValidationError
    :rtype: dict
    :returns: serializable object mapped from `mapping`
    """
    return MarshalMapping.run(mapping, data, **kwargs)


def serialize(mapping, data, **kwargs):
    """Serialize data to an expected input for a `mapping`

    """
    return SerializeMapping.run(mapping, data, **kwargs)
