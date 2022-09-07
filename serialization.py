import json

class Serializer:
    def save_dict_to_file(self, d, filename):
        with open(filename, 'w') as json_file:
            json.dump(d, json_file)
    
    def load_dict_from_file(self, filename):
        with open(filename, 'r') as json_file:
            data = json.load(json_file)
        
        return data

