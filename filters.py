from markupsafe import Markup
import re

def nl2br(value):
    """Convertit les retours à la ligne en balises <br> pour l'affichage HTML."""
    if value is None:
        return ''
    # Échapper le contenu pour éviter les injections XSS
    escaped = str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # Convertir les retours à la ligne en <br>
    result = re.sub(r'\r\n|\r|\n', '<br>', escaped)
    # Marquer comme sûr pour éviter l'échappement HTML supplémentaire
    return Markup(result)
