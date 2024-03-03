'''Load configuration'''

import os
from mgxhub import Singleton
from .default import DefaultConfig

class Config(DefaultConfig, metaclass=Singleton):
    '''Configuration factory.

    Specifies configuration file by environment variable **MGXHUB_CONFIG** or by
    argument. If some attributes are not found in the configuration file, the
    default values will be used.

    Example:
    ```python
    from mgxhub.config import Config

    config = Config().config
    print(config['system']['workdir'])
    ```    
    '''
    
    def __init__(self, cfg_path: str | None = None):
        # Load default configuration
        super().__init__()

        # Try load user configuration to override default
        if cfg_path and os.path.exists(cfg_path):
            self.config.read(cfg_path)
        else:
            config_path = os.getenv('MGXHUB_CONFIG')
            if config_path and os.path.exists(config_path):
                self.config.read(config_path)

        