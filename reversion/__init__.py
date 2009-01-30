"""
Transactional version control for Django models.

Project sponsored by Etianen.com

<http://www.etianen.com/>
"""


from reversion.registration import register, unregister, is_registered
from reversion.revisions import revision