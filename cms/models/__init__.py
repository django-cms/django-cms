# isort: skip_file

from .settingmodels import *  # noqa: F401,F403
from .pagemodel import *  # noqa: F401,F403
from .permissionmodels import *  # noqa: F401,F403
from .placeholdermodel import *  # noqa: F401,F403
from .pluginmodel import *  # noqa: F401,F403
from .contentmodels import *  # noqa: F401,F403
from .placeholderpluginmodel import *  # noqa: F401,F403
from .static_placeholder import *  # noqa: F401,F403
from .aliaspluginmodel import *  # noqa: F401,F403
from .apphooks_reload import *  # noqa: F401,F403
# must be last
from cms import signals as s_import  # noqa: F401
