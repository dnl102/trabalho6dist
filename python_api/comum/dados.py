"""
Camada de dados compartilhada pelos 4 servidores Python (REST, GraphQL, gRPC e SOAP).

Todos os servidores (tanto Python quanto Node.js) usam exatamente este mesmo
modelo, as mesmas validações e o mesmo gerador determinístico de dados iniciais.
Assim, a única coisa que muda entre eles é a tecnologia de comunicação e a linguagem.

Modelo (enunciado + atributos extras):
    Usuario  (id, nome, idade, email)                 -- 1 usuário tem 0..* playlists
    Musica   (id, nome, artista, genero, duracao_s)   -- 1 música está em 0..* playlists
    Playlist (id, nome, descricao)                    -- pertence a 1 usuário (1..1)
                                                         e contém 1..* músicas
"""

import threading
from dataclasses import dataclass, field


# ---------------------------------------------------------------- entidades

@dataclass
class Usuario:
    id: int
    nome: str
    idade: int
    email: str


@dataclass
class Musica:
    id: int
    nome: str
    artista: str
    genero: str
    duracao_s: int


@dataclass
class Playlist:
    id: int
    nome: str
    descricao: str
    usuario_id: int
    musicas_ids: list[int] = field(default_factory=list)


# ------------------------------------------------------------------- erros

class NaoEncontrado(Exception):
    """O recurso pedido não existe (vira 404 no REST, NOT_FOUND no gRPC...)."""


class DadosInvalidos(Exception):
    """Os dados enviados violam alguma regra (ex.: playlist sem músicas)."""


# ---------------------------------------------------- gerador determinístico
# Usamos um gerador linear congruente simples (mesma fórmula em Python e Node.js)
# para garantir que os 8 servidores comecem com EXATAMENTE os mesmos dados.

class _GeradorDeterministico:
    def __init__(self, semente: int = 42):
        self._estado = semente

    def proximo(self) -> int:
        self._estado = (self._estado * 1103515245 + 12345) & 0x7FFFFFFF
        return self._estado

    def inteiro(self, minimo: int, maximo: int) -> int:
        return minimo + (self.proximo() % (maximo - minimo + 1))

    def escolher(self, lista):
        return lista[self.proximo() % len(lista)]

    def amostra(self, lista, quantidade: int):
        escolhidos = []
        usados = set()
        while len(escolhidos) < quantidade:
            item = self.escolher(lista)
            if item not in usados:
                usados.add(item)
                escolhidos.append(item)
        return escolhidos


# ------------------------------------------------------------- repositório

class Repositorio:
    """Guarda usuários, músicas e playlists em dicionários na memória."""

    def __init__(self):
        self.usuarios: dict[int, Usuario] = {}
        self.musicas: dict[int, Musica] = {}
        self.playlists: dict[int, Playlist] = {}
        self._proximo_id = {"usuario": 1, "musica": 1, "playlist": 1}
        # Os servidores gRPC e SOAP atendem requisições em várias threads,
        # então protegemos as escritas e percursos compostos com uma trava.
        # Nota: usamos Lock simples (não RLock) porque obter_* não readquire
        # a trava quando chamado de dentro de outros métodos.
        self._trava = threading.Lock()

    def _novo_id(self, tipo: str) -> int:
        novo = self._proximo_id[tipo]
        self._proximo_id[tipo] += 1
        return novo

    # ---- validações -----------------------------------------------------

    @staticmethod
    def _validar_texto(valor: str, campo: str) -> None:
        if not valor or not valor.strip():
            raise DadosInvalidos(f"O campo '{campo}' não pode ser vazio")

    @staticmethod
    def _validar_idade(idade: int) -> None:
        if idade < 0:
            raise DadosInvalidos("A idade não pode ser negativa")

    @staticmethod
    def _validar_email(email: str) -> None:
        if not email or "@" not in email.strip():
            raise DadosInvalidos("O campo 'email' deve ser um e-mail válido")

    @staticmethod
    def _validar_duracao(duracao_s: int) -> None:
        if duracao_s <= 0:
            raise DadosInvalidos("A duração da música deve ser maior que zero")

    def _validar_musicas(self, musicas_ids: list[int]) -> list[int]:
        if not musicas_ids:
            raise DadosInvalidos("Uma playlist precisa ter pelo menos 1 música")
        for mid in musicas_ids:
            if mid not in self.musicas:
                raise DadosInvalidos(f"Música {mid} não existe")
        return list(dict.fromkeys(musicas_ids))  # remove repetidas, mantém a ordem

    # ---- usuários -------------------------------------------------------

    def listar_usuarios(self) -> list[Usuario]:
        # No CPython 3.11 (com GIL), list(dict.values()) copia a lista de
        # referências atomicamente em C.
        return list(self.usuarios.values())

    def obter_usuario(self, id: int) -> Usuario:
        usuario = self.usuarios.get(id)
        if usuario is None:
            raise NaoEncontrado(f"Usuário {id} não encontrado")
        return usuario

    def criar_usuario(self, nome: str, idade: int, email: str) -> Usuario:
        self._validar_texto(nome, "nome")
        self._validar_idade(idade)
        self._validar_email(email)
        with self._trava:
            usuario = Usuario(self._novo_id("usuario"), nome, idade, email)
            self.usuarios[usuario.id] = usuario
        return usuario

    def atualizar_usuario(self, id: int, nome: str, idade: int, email: str) -> Usuario:
        self._validar_texto(nome, "nome")
        self._validar_idade(idade)
        self._validar_email(email)
        with self._trava:
            usuario = self.obter_usuario(id)
            usuario.nome, usuario.idade, usuario.email = nome, idade, email
        return usuario

    def remover_usuario(self, id: int) -> None:
        with self._trava:
            self.obter_usuario(id)
            del self.usuarios[id]
            # Uma playlist pertence a exatamente 1 usuário (1..1):
            # se o dono sai, as playlists dele saem junto.
            for pid in [p.id for p in self.playlists.values() if p.usuario_id == id]:
                del self.playlists[pid]

    # ---- músicas --------------------------------------------------------

    def listar_musicas(self) -> list[Musica]:
        return list(self.musicas.values())

    def obter_musica(self, id: int) -> Musica:
        musica = self.musicas.get(id)
        if musica is None:
            raise NaoEncontrado(f"Música {id} não encontrada")
        return musica

    def criar_musica(self, nome: str, artista: str, genero: str, duracao_s: int) -> Musica:
        self._validar_texto(nome, "nome")
        self._validar_texto(artista, "artista")
        self._validar_texto(genero, "genero")
        self._validar_duracao(duracao_s)
        with self._trava:
            musica = Musica(self._novo_id("musica"), nome, artista, genero, duracao_s)
            self.musicas[musica.id] = musica
        return musica

    def atualizar_musica(self, id: int, nome: str, artista: str,
                         genero: str, duracao_s: int) -> Musica:
        self._validar_texto(nome, "nome")
        self._validar_texto(artista, "artista")
        self._validar_texto(genero, "genero")
        self._validar_duracao(duracao_s)
        with self._trava:
            musica = self.obter_musica(id)
            musica.nome = nome
            musica.artista = artista
            musica.genero = genero
            musica.duracao_s = duracao_s
        return musica

    def remover_musica(self, id: int) -> None:
        with self._trava:
            self.obter_musica(id)
            del self.musicas[id]
            # Tira a música das playlists. Como toda playlist precisa ter
            # pelo menos 1 música (1..*), as que ficarem vazias são removidas.
            for playlist in list(self.playlists.values()):
                if id in playlist.musicas_ids:
                    playlist.musicas_ids = [m for m in playlist.musicas_ids if m != id]
                    if not playlist.musicas_ids:
                        del self.playlists[playlist.id]

    # ---- playlists ------------------------------------------------------

    def listar_playlists(self) -> list[Playlist]:
        return list(self.playlists.values())

    def obter_playlist(self, id: int) -> Playlist:
        playlist = self.playlists.get(id)
        if playlist is None:
            raise NaoEncontrado(f"Playlist {id} não encontrada")
        return playlist

    def criar_playlist(self, nome: str, descricao: str,
                       usuario_id: int, musicas_ids: list[int]) -> Playlist:
        self._validar_texto(nome, "nome")
        self._validar_texto(descricao, "descricao")
        with self._trava:
            if usuario_id not in self.usuarios:
                raise DadosInvalidos(f"Usuário {usuario_id} não existe")
            musicas_ids = self._validar_musicas(musicas_ids)
            playlist = Playlist(self._novo_id("playlist"), nome, descricao, usuario_id, musicas_ids)
            self.playlists[playlist.id] = playlist
        return playlist

    def atualizar_playlist(self, id: int, nome: str, descricao: str,
                           musicas_ids: list[int]) -> Playlist:
        """Altera nome, descrição e músicas. O dono da playlist não muda."""
        self._validar_texto(nome, "nome")
        self._validar_texto(descricao, "descricao")
        with self._trava:
            playlist = self.obter_playlist(id)
            playlist.musicas_ids = self._validar_musicas(musicas_ids)
            playlist.nome = nome
            playlist.descricao = descricao
        return playlist

    def remover_playlist(self, id: int) -> None:
        with self._trava:
            self.obter_playlist(id)
            del self.playlists[id]

    # ---- consultas pedidas no enunciado ---------------------------------

    def playlists_do_usuario(self, usuario_id: int) -> list[Playlist]:
        with self._trava:
            self.obter_usuario(usuario_id)
            return [p for p in self.playlists.values() if p.usuario_id == usuario_id]

    def musicas_da_playlist(self, playlist_id: int) -> list[Musica]:
        with self._trava:
            playlist = self.obter_playlist(playlist_id)
            return [self.musicas[mid] for mid in playlist.musicas_ids]

    def playlists_com_musica(self, musica_id: int) -> list[Playlist]:
        with self._trava:
            self.obter_musica(musica_id)
            return [p for p in self.playlists.values() if musica_id in p.musicas_ids]

    # ---- dados iniciais -------------------------------------------------

    def popular(self, n_usuarios=100, n_musicas=1000,
                playlists_por_usuario=3, musicas_por_playlist=10, semente=42):
        """Cria dados de exemplo idênticos em Python e Node.js."""
        rng = _GeradorDeterministico(semente)
        nomes = ["Ana", "Bruno", "Carla", "Diego", "Elisa", "Felipe", "Gabi", "Hugo"]
        artistas = ["Djavan", "Elis Regina", "Gilberto Gil", "Marisa Monte",
                    "Caetano Veloso", "Rita Lee", "Tim Maia", "Gal Costa"]
        generos = ["MPB", "Samba", "Bossa Nova", "Rock", "Pop", "Forró"]

        for i in range(1, n_usuarios + 1):
            nome = f"{rng.escolher(nomes)} {i}"
            idade = rng.inteiro(14, 80)
            email = f"usuario{i}@streaming.com"
            self.criar_usuario(nome, idade, email)

        for i in range(1, n_musicas + 1):
            self.criar_musica(
                f"Música {i}",
                rng.escolher(artistas),
                rng.escolher(generos),
                rng.inteiro(120, 360),
            )

        ids_musicas = list(self.musicas)
        for usuario_id in self.usuarios:
            for j in range(1, playlists_por_usuario + 1):
                escolhidas = rng.amostra(ids_musicas, musicas_por_playlist)
                self.criar_playlist(
                    f"Playlist {j} do usuário {usuario_id}",
                    f"Seleção {j} para ouvir no dia a dia",
                    usuario_id,
                    escolhidas,
                )


def criar_repositorio_populado() -> Repositorio:
    repo = Repositorio()
    repo.popular()
    return repo
