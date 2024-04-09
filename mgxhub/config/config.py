'''Load configuration'''

import os

from mgxhub.singleton import Singleton

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
    print(config.get('system', 'mapdir')) # /path/to/__workdir/map

    # Or using a shortcut
    from mgxhub.config import cfg

    print(cfg.get('system', 'mapdir')) # /path/to/__workdir/map
    ```    
    '''

    def __init__(self, cfg_path: str | None = None):
        # Load default configuration
        super().__init__()

        # Load user configuration
        self.load(cfg_path)
        if self.config.get('system', 'mapdest') == 'local':
            os.makedirs(self.config.get('system', 'mapdir'), exist_ok=True)

    def load(self, cfg_path: str | None = None):
        '''Load user configuration to override default.
        Absolute path or relative path to the project root.

        Args:
        - **cfg_path**: Path to the user configuration file.

        Example:
        ```python
        Config().load('testconf.ini')
        ```
        '''

        if not cfg_path:
            cfg_path = os.getenv('MGXHUB_CONFIG', '')
            if not cfg_path:
                print('Configuration file or env MGXHUB_CONFIG are not set. Using default configuration.')

        cfg_path = os.path.join(self.project_root(), cfg_path)
        if os.path.exists(cfg_path) and os.path.isfile(cfg_path):
            self.config.read(cfg_path)
            # print(f'Configuration file loaded: {cfg_path}')
