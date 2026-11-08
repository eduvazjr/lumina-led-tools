# -*- coding: utf-8 -*-
"""Quem pode ver e mexer nos anexos de um registro: a mesma permissão do registro."""


def _codename(acao, content_type):
    return '%s.%s_%s' % (content_type.app_label, acao, content_type.model)


def pode_editar(user, content_type):
    return user.is_authenticated and (user.is_superuser or user.has_perm(_codename('change', content_type)))


def pode_ver(user, content_type):
    return pode_editar(user, content_type) or (
        user.is_authenticated and user.has_perm(_codename('view', content_type)))
