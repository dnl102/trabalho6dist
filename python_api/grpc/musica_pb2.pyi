from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Vazio(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class Id(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: int
    def __init__(self, id: _Optional[int] = ...) -> None: ...

class Usuario(_message.Message):
    __slots__ = ("id", "nome", "idade", "email")
    ID_FIELD_NUMBER: _ClassVar[int]
    NOME_FIELD_NUMBER: _ClassVar[int]
    IDADE_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    id: int
    nome: str
    idade: int
    email: str
    def __init__(self, id: _Optional[int] = ..., nome: _Optional[str] = ..., idade: _Optional[int] = ..., email: _Optional[str] = ...) -> None: ...

class Musica(_message.Message):
    __slots__ = ("id", "nome", "artista", "genero", "duracao_s")
    ID_FIELD_NUMBER: _ClassVar[int]
    NOME_FIELD_NUMBER: _ClassVar[int]
    ARTISTA_FIELD_NUMBER: _ClassVar[int]
    GENERO_FIELD_NUMBER: _ClassVar[int]
    DURACAO_S_FIELD_NUMBER: _ClassVar[int]
    id: int
    nome: str
    artista: str
    genero: str
    duracao_s: int
    def __init__(self, id: _Optional[int] = ..., nome: _Optional[str] = ..., artista: _Optional[str] = ..., genero: _Optional[str] = ..., duracao_s: _Optional[int] = ...) -> None: ...

class Playlist(_message.Message):
    __slots__ = ("id", "nome", "descricao", "usuario_id", "musicas_ids")
    ID_FIELD_NUMBER: _ClassVar[int]
    NOME_FIELD_NUMBER: _ClassVar[int]
    DESCRICAO_FIELD_NUMBER: _ClassVar[int]
    USUARIO_ID_FIELD_NUMBER: _ClassVar[int]
    MUSICAS_IDS_FIELD_NUMBER: _ClassVar[int]
    id: int
    nome: str
    descricao: str
    usuario_id: int
    musicas_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, id: _Optional[int] = ..., nome: _Optional[str] = ..., descricao: _Optional[str] = ..., usuario_id: _Optional[int] = ..., musicas_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class NovoUsuario(_message.Message):
    __slots__ = ("nome", "idade", "email")
    NOME_FIELD_NUMBER: _ClassVar[int]
    IDADE_FIELD_NUMBER: _ClassVar[int]
    EMAIL_FIELD_NUMBER: _ClassVar[int]
    nome: str
    idade: int
    email: str
    def __init__(self, nome: _Optional[str] = ..., idade: _Optional[int] = ..., email: _Optional[str] = ...) -> None: ...

class NovaMusica(_message.Message):
    __slots__ = ("nome", "artista", "genero", "duracao_s")
    NOME_FIELD_NUMBER: _ClassVar[int]
    ARTISTA_FIELD_NUMBER: _ClassVar[int]
    GENERO_FIELD_NUMBER: _ClassVar[int]
    DURACAO_S_FIELD_NUMBER: _ClassVar[int]
    nome: str
    artista: str
    genero: str
    duracao_s: int
    def __init__(self, nome: _Optional[str] = ..., artista: _Optional[str] = ..., genero: _Optional[str] = ..., duracao_s: _Optional[int] = ...) -> None: ...

class NovaPlaylist(_message.Message):
    __slots__ = ("nome", "descricao", "usuario_id", "musicas_ids")
    NOME_FIELD_NUMBER: _ClassVar[int]
    DESCRICAO_FIELD_NUMBER: _ClassVar[int]
    USUARIO_ID_FIELD_NUMBER: _ClassVar[int]
    MUSICAS_IDS_FIELD_NUMBER: _ClassVar[int]
    nome: str
    descricao: str
    usuario_id: int
    musicas_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, nome: _Optional[str] = ..., descricao: _Optional[str] = ..., usuario_id: _Optional[int] = ..., musicas_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class AlteraPlaylist(_message.Message):
    __slots__ = ("id", "nome", "descricao", "musicas_ids")
    ID_FIELD_NUMBER: _ClassVar[int]
    NOME_FIELD_NUMBER: _ClassVar[int]
    DESCRICAO_FIELD_NUMBER: _ClassVar[int]
    MUSICAS_IDS_FIELD_NUMBER: _ClassVar[int]
    id: int
    nome: str
    descricao: str
    musicas_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, id: _Optional[int] = ..., nome: _Optional[str] = ..., descricao: _Optional[str] = ..., musicas_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class ListaUsuarios(_message.Message):
    __slots__ = ("usuarios",)
    USUARIOS_FIELD_NUMBER: _ClassVar[int]
    usuarios: _containers.RepeatedCompositeFieldContainer[Usuario]
    def __init__(self, usuarios: _Optional[_Iterable[_Union[Usuario, _Mapping]]] = ...) -> None: ...

class ListaMusicas(_message.Message):
    __slots__ = ("musicas",)
    MUSICAS_FIELD_NUMBER: _ClassVar[int]
    musicas: _containers.RepeatedCompositeFieldContainer[Musica]
    def __init__(self, musicas: _Optional[_Iterable[_Union[Musica, _Mapping]]] = ...) -> None: ...

class ListaPlaylists(_message.Message):
    __slots__ = ("playlists",)
    PLAYLISTS_FIELD_NUMBER: _ClassVar[int]
    playlists: _containers.RepeatedCompositeFieldContainer[Playlist]
    def __init__(self, playlists: _Optional[_Iterable[_Union[Playlist, _Mapping]]] = ...) -> None: ...
