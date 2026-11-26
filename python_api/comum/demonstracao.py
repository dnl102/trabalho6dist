"""Roteiro de demonstração usado pelos 4 clientes (mesmas chamadas para todos)."""


def demonstrar(cliente, nome_tecnologia):
    print(f"===== Cliente {nome_tecnologia} =====\n")

    usuarios = cliente.listar_usuarios()
    print(f"1) Todos os usuários: {len(usuarios)} -> primeiro: {usuarios[0]}")

    musicas = cliente.listar_musicas()
    print(f"2) Todas as músicas: {len(musicas)} -> primeira: {musicas[0]}")

    playlists = cliente.playlists_do_usuario(1)
    print(f"3) Playlists do usuário 1: {[p['nome'] for p in playlists]}")

    musicas_pl = cliente.musicas_da_playlist(1)
    print(f"4) Músicas da playlist 1: {[m['nome'] for m in musicas_pl]}")

    com_musica = cliente.playlists_com_musica(musicas_pl[0]["id"])
    print(f"5) Playlists com a música {musicas_pl[0]['id']}: {[p['nome'] for p in com_musica]}")

    print("\nCRUD de exemplo:")
    novo = cliente.criar_usuario("Maria", 25, "maria@streaming.com")
    print(f"   criado:     {novo}")
    print(f"   alterado:   {cliente.atualizar_usuario(novo['id'], 'Maria Silva', 26, 'maria.silva@streaming.com')}")
    playlist = cliente.criar_playlist("Favoritas", "Músicas preferidas da Maria", novo["id"], [1, 2, 3])
    print(f"   playlist:   {playlist}")
    cliente.remover_usuario(novo["id"])
    print(f"   removido usuário {novo['id']} (e suas playlists)")
