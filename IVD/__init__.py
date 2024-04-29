import os

def DeleteFilesInFolder(folder_path):

    # Iterate over all files in a folder and delete
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)  
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  
        except Exception as e:
            print("Delete %s wrong, because：%s" % (file_path, e))

def main():
	DeleteFilesInFolder('./analyzer/detector/detail')

if __name__ == '__main__':
	main()