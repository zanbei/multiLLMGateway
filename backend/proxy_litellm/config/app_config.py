import os
import yaml
import litellm

def load_config():
    config_path = "litellm_config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Configure litellm with the loaded config
    litellm.model_list = config.get('model_list', [])
    if 'general_settings' in config:
        for key, value in config['general_settings'].items():
            setattr(litellm, key, value)

    return config
