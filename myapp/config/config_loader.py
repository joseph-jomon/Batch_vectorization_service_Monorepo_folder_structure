import yaml
import os

class ConfigLoader:
    def __init__(self, config_file_path="config/config.yaml"):
        self.config = self._load_config(config_file_path)

    def _load_config(self, config_file_path):
        # Load the YAML configuration file
        with open(config_file_path, "r") as file:
            return yaml.safe_load(file)

    def get_celery_broker_url(self):
        return self.config['celery']['broker_url']

    def get_celery_result_backend(self):
        return self.config['celery']['result_backend']

    def get_aggregation_service_url(self):
        return self.config['aggregation_service']['url']


# Instantiate the ConfigLoader to use throughout the project
config_loader = ConfigLoader()

# Usage examples:
#   config_loader.get_celery_broker_url()
#   config_loader.get_aggregation_service_url()
