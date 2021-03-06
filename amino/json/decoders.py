from typing import Type, TypeVar, Collection, Mapping, Callable, Tuple
from numbers import Number
from uuid import UUID

from amino.json.decoder import Decoder, decode, decode_json_type_json
from amino import (Maybe, Either, List, Lists, Left, Boolean, Try, Map, Right, Nothing, Just, Path, do, Do, _, L, ADT,
                   Dat)
from amino.json.data import JsonError, Json, JsonObject, tpe_key
from amino.dat import Field

A = TypeVar('A')
B = TypeVar('B')
Sub = TypeVar('Sub', bound=Dat)


class StringDecoder(Decoder, tpe=str):

    def decode(self, tpe: Type[str], data: Json) -> Either[JsonError, str]:
        return data.scalar.e(f'invalid type for `str`: {data}', data.data)


class NumberDecoder(Decoder, sub=Number):

    def decode(self, tpe: Type[int], data: Json) -> Either[JsonError, int]:
        return data.scalar.e(f'invalid type for `int`: {data}', data.data)


class MapDecoder(Decoder, sub=Mapping):

    def decode(self, tpe: Type[Mapping], data: Json) -> Either[JsonError, Map[str, A]]:
        def dec() -> Either[JsonError, Map[str, A]]:
            return Map(data.data).traverse(decode.match, Either)
        return data.object.c(dec, lambda: Left(f'invalid type for `Map`: {data}'))


class ListDecoder(Decoder, sub=Collection):

    def decode(self, tpe: Type[Collection], data: Json) -> Either[JsonError, List[A]]:
        def dec() -> Either[JsonError, List[A]]:
            return Lists.wrap(data.data).traverse(decode.match, Either)
        return data.array.c(dec, lambda: Left(f'invalid type for `List`: {data}'))


def maybe_from_object(data: JsonObject, inner: Maybe[Type[A]]) -> Either[JsonError, Maybe[A]]:
    return (
        decode.match(data) / Just
        if data.has_type else
        inner.traverse(lambda a: decode_json_type_json(data, a), Either)
    )


class MaybeDecoder(Decoder, tpe=Maybe):

    def decode(self, tpe: Type[Maybe], data: Json) -> Either[JsonError, Maybe[A]]:
        inner = Lists.wrap(tpe.__args__).head
        return (
            Right(Nothing)
            if data.absent else
            maybe_from_object(data, inner)
            if data.object else
            decode.match(data) / Just
            if data.array else
            Right(Nothing)
            if data.null else
            inner.cata(
                lambda a: decode_json_type_json(data, a) / Just,
                lambda: data.scalar.e(f'invalid type for `Maybe`: {data}', Maybe.check(data.data))
            )
        )


@do(Either[JsonError, Either[A, B]])
def either_from_object(data: JsonObject, ltype: Type[A], rtype: Type[B]) -> Do:
    value = yield data.field('value')
    decoded = yield decode.match(value)
    tpe = yield data.tpe
    yield Right(tpe(decoded))


class EitherDecoder(Decoder, tpe=Either):

    @do(Either[JsonError, Either[A, B]])
    def decode(self, tpe: Type[Either], data: Json) -> Do:
        err = JsonError(data, f'too few types in Either')
        ltype, rtype = yield Lists.wrap(tpe.__args__).lift_all(0, 1).to_either(err)
        yield (
            either_from_object(data, ltype, rtype)
            if data.object else
            Left(JsonError(data, f'invalid type for `Either`'))
        )


class BooleanDecoder(Decoder, tpe=Boolean):

    def decode(self, tpe: Type[Boolean], data: Json) -> Either[JsonError, Boolean]:
        return data.scalar.e(f'invalid type for `Boolean`: {data}', Boolean(data.data))


class UUIDDecoder(Decoder, tpe=UUID):

    def decode(self, tpe: Type[UUID], data: Json) -> Either[JsonError, UUID]:
        return data.scalar.flat_e(f'invalid type for `UUID`: {data}', Try(UUID, data.data))


class PathDecoder(Decoder, tpe=Path):

    def decode(self, tpe: Type[Path], data: Json) -> Either[JsonError, Path]:
        return data.scalar.flat_e(lambda: JsonError(data, f'invalid type for `Path`'), Try(Path, data.data))


def decode_instance(data: Json, desc: str) -> Either[JsonError, A]:
        @do(Either[JsonError, A])
        def run(data: Json) -> Do:
            mod_field = yield data.field('mod')
            mod_path = yield mod_field.as_scalar
            names_field = yield data.field('names')
            names_json = yield names_field.as_array
            names = Lists.wrap(names_json.native)
            mod = yield (
                Either.import_module(mod_path.native)
                if isinstance(mod_path.native, str) else
                Left(JsonError(data, 'module is not a string'))
            )
            yield names.fold_m(Right(mod))(Either.getattr)
        return (
            run(data)
            if data.object else
            Left(JsonError(data, f'invalid type for `{desc}`'))
        )


class CallableDecoder(Decoder, tpe=Callable):

    def decode(self, tpe: Type[Callable], data: Json) -> Either[JsonError, Callable]:
        return decode_instance(data, 'Callable')


class TupleDecoder(Decoder, tpe=tuple):

    @do(Either[JsonError, Tuple])
    def decode(self, tpe: Type[Tuple], data: Json) -> Do:
        t_data = yield data.field('data')
        a_data = yield t_data.as_array
        yield Try(tuple, a_data.native)


@do(Either[JsonError, type])
def decode_type(data: Json) -> Do:
    mod = yield data.field('mod')
    names = yield data.field('names')
    yield (
        Right(type(None))
        if mod.native == 'builtins' and names.native == ['NoneType']
        else decode_instance(data, 'type')
    )


class TypeDecoder(Decoder, tpe=type):

    @do(Either[JsonError, Type])
    def decode(self, tpe: Type[Type], data: Json) -> Do:
        yield decode_type(data)


class TTypeDecoder(Decoder, tpe=Type):

    @do(Either[JsonError, Type])
    def decode(self, tpe: Type[Type], data: Json) -> Do:
        yield decode_type(data)


def decode_field(data: Json) -> Do:
    @do(Either[JsonError, A])
    def decode_field(field: Field) -> Do:
        value = yield data.field(field.name)
        dec = yield Decoder.e(field.tpe).lmap(L(JsonError)(data, _))
        yield dec.decode(field.tpe, value)
    return decode_field


def decode_dat(tpe: Type[A], data: Json) -> Either[JsonError, A]:
    return tpe._dat__fields.traverse(decode_field(data), Either).map(lambda a: tpe(*a))


class DatDecoder(Decoder, tpe=Dat):

    def decode(self, tpe: Type[Sub], data: Json) -> Either[JsonError, Sub]:
        return decode_dat(tpe, data)


class ADTDecoder(Decoder, tpe=ADT):

    @do(Either[JsonError, Sub])
    def decode(self, tpe: Type[Sub], data: JsonObject) -> Do:
        sub_json = yield data.field(tpe_key)
        sub = yield sub_json.as_scalar
        sub_type = yield Either.import_path(sub.native)
        yield decode_dat(sub_type, data)


__all__ = ('MaybeDecoder', 'StringDecoder', 'NumberDecoder', 'ListDecoder', 'BooleanDecoder', 'MapDecoder',
           'PathDecoder', 'decode_instance', 'CallableDecoder', 'TupleDecoder', 'decode_type', 'TypeDecoder',
           'TTypeDecoder', 'ADTDecoder',)
