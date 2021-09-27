
import yaml
from redengine.core.parameters import BaseArgument


class YamlArg(BaseArgument):

    def __init__(self, path, items=None):
        self.path = path
        self.items = [] if items is None else items

    def get_value(self):
        path = self.path
        with open(path, 'r') as file:
            cont = yaml.safe_load(file)
        
        for item in self.items:
            if isinstance(item, BaseArgument):
                item = item.get_value()
            cont = cont[item]

        return cont