from .default import DefaultConfig
from .config import Config

cfg = Config().config

# A shortcut to access the S3 configuration
cfg.s3 = {
    "endpoint": cfg.get('s3', 'endpoint'),
    "accesskey": cfg.get('s3', 'accesskey'),
    "secretkey": cfg.get('s3', 'secretkey'),
    "region": cfg.get('s3', 'region'),
    "bucket": cfg.get('s3', 'bucket')
}