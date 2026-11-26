"""
Teste de concorrência da camada de dados: várias threads lendo enquanto
outras removem. O único erro aceitável é NaoEncontrado (nunca KeyError ou
"dictionary changed size during iteration").
"""

import sys
import threading

import pytest

from python_api.comum.dados import NaoEncontrado, criar_repositorio_populado


class DicionarioQueSomeAposConsulta(dict):
    """Simula outra thread removendo o item logo depois de alguém perguntar
    se ele existe (o pior intercalamento possível para "verificar e depois ler")."""

    def __contains__(self, chave):
        existe = super().__contains__(chave)
        self.pop(chave, None)
        return existe


@pytest.mark.parametrize("colecao, obter", [
    ("usuarios", "obter_usuario"),
    ("musicas", "obter_musica"),
    ("playlists", "obter_playlist"),
])
def test_obter_nao_quebra_se_item_some_no_meio(colecao, obter):
    repo = criar_repositorio_populado()
    setattr(repo, colecao, DicionarioQueSomeAposConsulta(getattr(repo, colecao)))
    try:
        getattr(repo, obter)(1)  # pode achar o item ou dizer que não existe...
    except NaoEncontrado:
        pass  # ...mas nunca pode estourar KeyError


def test_leituras_e_remocoes_simultaneas():
    repo = criar_repositorio_populado()
    erros_inesperados = []
    intervalo_original = sys.getswitchinterval()
    sys.setswitchinterval(1e-6)  # troca de thread o mais frequente possível

    def ler():
        for _ in range(30):
            for id in range(1, 101):
                for operacao in (repo.obter_usuario, repo.playlists_do_usuario):
                    try:
                        operacao(id)
                    except NaoEncontrado:
                        pass
                    except Exception as erro:  # qualquer outro erro é bug
                        erros_inesperados.append(repr(erro))
            for id in range(1, 301):
                try:
                    repo.musicas_da_playlist(id)
                except NaoEncontrado:
                    pass
                except Exception as erro:
                    erros_inesperados.append(repr(erro))

    def remover():
        for id in range(1, 101):
            repo.remover_usuario(id)
            novo = repo.criar_usuario("Novo", 20, f"novo{id}@streaming.com")
            repo.criar_playlist("P", "Desc", novo.id, [1, 2])

    try:
        threads = [threading.Thread(target=ler) for _ in range(4)]
        threads.append(threading.Thread(target=remover))
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    finally:
        sys.setswitchinterval(intervalo_original)

    assert erros_inesperados == []
