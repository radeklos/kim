import pytest

from kim.field import Field, FieldError, Input, Output


def test_field_opts_correctly_set_for_field():

    new_field = Field(
        required=True,
        default='bar',
        source='new_field',
        name='other_field')

    assert new_field.opts.required is True
    assert new_field.opts.default == 'bar'
    assert new_field.opts.source == 'new_field'
    assert new_field.opts.name == 'other_field'


def test_field_source_defaults_to_name():
    new_field = Field(
        required=True,
        default='bar',
        source='other_field')

    assert new_field.opts.source == 'other_field'
    assert new_field.opts.name == 'other_field'


def test_get_field_name():
    invalid_field = Field(
        required=True,
        default='bar')

    name_field = Field(
        required=True,
        default='bar',
        name='other_field')

    source_field = Field(
        required=True,
        default='bar',
        source='other_field')

    with pytest.raises(FieldError):
        assert invalid_field.get_name()

    assert name_field.get_name() == 'other_field'
    assert source_field.get_name() == 'other_field'


def test_field_invalid():

    field = Field(name='foo')

    with pytest.raises(FieldError):

        field.invalid('not valid')


def test_get_field_input_pipe():

    field = Field(name='foo')

    assert field.input_pipe == Input


def test_get_field_output_pipe():

    field = Field(name='foo')

    assert field.output_pipe == Output