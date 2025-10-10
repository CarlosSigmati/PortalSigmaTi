def permissoes_usuario(request):
    """
    Adiciona a variável 'usuario_pode_alterar' automaticamente em todos os templates.
    """
    if not request.user.is_authenticated:
        return {}

    usuario_pode_alterar = request.user.is_superuser or request.user.groups.filter(name="Técnicos").exists()
    return {
        'usuario_pode_alterar': usuario_pode_alterar
    }
