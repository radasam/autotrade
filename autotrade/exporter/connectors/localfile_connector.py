import os
import shutil

class LocalFileConnector:
    def __init__(self, output_path: str):
        self.output_path = output_path
        os.makedirs(output_path, exist_ok=True) 

    def export(self, file_path: str, exported_metric: str, output_name: str):
        new_file_path = os.path.join(self.output_path, f'{output_name}.csv')
        shutil.copy(file_path, new_file_path)
        print(f"{file_path} copied to: {new_file_path}")