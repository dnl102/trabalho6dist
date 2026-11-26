/**
 * Roteiro de demonstração usado pelos 4 clientes Node.js (mesmas chamadas do Python).
 */

async function demonstrar(cliente, nomeTecnologia) {
  console.log(`===== Cliente ${nomeTecnologia} (Node.js) =====\n`);

  const usuarios = await cliente.listarUsuarios();
  console.log(`1) Todos os usuários: ${usuarios.length} -> primeiro:`, usuarios[0]);

  const musicas = await cliente.listarMusicas();
  console.log(`2) Todas as músicas: ${musicas.length} -> primeira:`, musicas[0]);

  const playlists = await cliente.playlistsDoUsuario(1);
  console.log("3) Playlists do usuário 1:", playlists.map((p) => p.nome));

  const musicasPl = await cliente.musicasDaPlaylist(1);
  console.log("4) Músicas da playlist 1:", musicasPl.map((m) => m.nome));

  const comMusica = await cliente.playlistsComMusica(musicasPl[0].id);
  console.log(`5) Playlists com a música ${musicasPl[0].id}:`, comMusica.map((p) => p.nome));

  console.log("\nCRUD de exemplo:");
  const novo = await cliente.criarUsuario("Maria", 25, "maria@streaming.com");
  console.log("   criado:  ", novo);
  const alterado = await cliente.atualizarUsuario(novo.id, "Maria Silva", 26, "maria.silva@streaming.com");
  console.log("   alterado:", alterado);
  const playlist = await cliente.criarPlaylist("Favoritas", "Músicas preferidas da Maria", novo.id, [1, 2, 3]);
  console.log("   playlist:", playlist);
  await cliente.removerUsuario(novo.id);
  console.log(`   removido usuário ${novo.id} (e suas playlists)`);
}

module.exports = { demonstrar };
