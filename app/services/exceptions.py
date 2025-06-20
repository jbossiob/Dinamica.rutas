class ServicioExternoError(Exception):
    """Error al consumir un servicio externo (por ejemplo, Google Maps API)."""
    pass

class ErrorDeNegocio(Exception):
    """Error de lógica de negocio."""
    pass 