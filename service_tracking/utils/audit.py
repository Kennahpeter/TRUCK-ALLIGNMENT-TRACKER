def log_action(user, action, obj, details=""):
    """Write one AuditLog row. Cheap, explicit, called from views on the actions
    that matter (create/update/delete/export) rather than via signals, so the
    log always has a human-meaningful 'details' string attached.
    """
    from ..models import AuditLog

    AuditLog.objects.create(
        user=user if getattr(user, 'is_authenticated', False) else None,
        action=action,
        model_name=obj.__class__.__name__,
        object_id=str(getattr(obj, 'pk', '')),
        object_repr=str(obj)[:255],
        details=details,
    )
