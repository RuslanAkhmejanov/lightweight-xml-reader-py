import os
import sys
import logging

import xml.etree.ElementTree as ElementTree
from xml.etree.ElementTree import ParseError


logging.basicConfig(filename='errors.log', level=logging.ERROR)

class Diagram:

    total_num_of_objects = 0
    diagram_object_types = set()
    min_height = None
    min_width = None
    max_height = 0
    max_width = 0

    def __init__(self, selector):
        self._filename = selector.find('filename').text

        width = int(selector.find('size/width').text)
        height = int(selector.find('size/height').text)
        depth = int(selector.find('size/depth').text)
        # to store max and min heights and widths among the diagrams
        if height > Diagram.max_height:
            Diagram.max_height = height
        if width > Diagram.max_width:
            Diagram.max_width = width
        if Diagram.min_height is None or height < Diagram.min_height:
            Diagram.min_height = height
        if Diagram.min_width is None or width < Diagram.min_width:
            Diagram.min_width = width
        self._size = (width, height, depth)

        self._area = height * width

        self._objects = [
            DiagramObject(object) for object in selector.findall('object')
            if Diagram.diagram_object_types.add(object.find('name').text) is None
        ]  # the if statement adds object types to the set at the same time; note: add() always returns None
        Diagram.total_num_of_objects += len(self._objects)

    def __str__(self):
        diagram_objects = ',\n\n'.join(str(object) for object in self._objects)
        height, width, depth = self.size[1], self.size[0], self.size[2]
        stringObj = (
            f"Filename: {self.filename}\n"
            f"Height: {height}\n"
            f"Width: {width}\n"
            f"Depth: {depth}\n"
            f"Dimension: {height} x {width}\n"
            f"Area: {height} x {width} = {self._area}\n"
            f"Objects: [\n"
            f"{diagram_objects}\n]\n"
        )
        return stringObj

    @property
    def filename(self):
        return self._filename

    @property
    def size(self):
        return self._size

    @property
    def area(self):
        return self._area

    @property
    def objects(self):
        return self._objects

class DiagramObject:

    min_area = None
    max_area = 0

    def __init__(self, object):
        self._name = object.find('name').text
        self._truncated = True if int(object.find('truncated').text) == 1 else False
        self._difficult = True if int(object.find('difficult').text) == 1 else False

        xmin = int(object.find('bndbox/xmin').text)
        ymin = int(object.find('bndbox/ymin').text)
        xmax = int(object.find('bndbox/xmax').text)
        ymax = int(object.find('bndbox/ymax').text)
        self._boundary = (xmin, ymin, xmax, ymax)

        self._width = xmax - xmin
        self._height = ymax - ymin
        self._area = self._height * self._width
        if self._area > DiagramObject.max_area:
            DiagramObject.max_area = self._area
        if DiagramObject.min_area is None or self._area < DiagramObject.min_area:
            DiagramObject.min_area = self._area

    def __str__(self):
        stringObj = (
            f"Name: {self.name}\n"
            f"Truncated: {self.truncated}\n"
            f"Difficult: {self.difficult}\n"
            'Boundary: {\n'
            f"\txmin: {self.boundary[0]},\n\tymin: {self.boundary[1]},\n\txmax: {self.boundary[2]},\n\tymax: {self.boundary[3]}\n"
            '}\n'
            f"Height: {self._height}\n"
            f"Width: {self._width}\n"
            f"Area: {self._area}"
        )
        return stringObj

    @property
    def name(self):
        return self._name

    @property
    def truncated(self):
        return self._truncated

    @property
    def difficult(self):
        return self._difficult

    @property
    def boundary(self):
        return self._boundary

    @property
    def height(self):
        return self._height

    @property
    def width(self):
        return self._width

    @property
    def area(self):
        return self._area

def list_current_files(folder_path):
    if not os.path.isabs(folder_path):
        folder_path = os.path.abspath(folder_path)
        print(folder_path)
    try:
        with os.scandir(folder_path) as contents:
            print('\nThe current files are:')
            for content in contents:
                if content.is_file():
                    try:
                        with open(content.path, 'r') as file:
                            try:
                                content = file.read()
                            except (MemoryError, UnicodeDecodeError) as e:
                                logging.error(f"\nError while reading file: {e}", exc_info=True)
                                continue
                            # only find xml files
                            try:
                                ElementTree.fromstring(content)
                                print(os.path.basename(file.name))
                            except (TypeError, ParseError) as e:
                                logging.error(f"\nWrong xml syntax: {e}", exc_info=True)
                                continue
                    except (PermissionError, UnicodeDecodeError) as e:
                        logging.error(f"\nError while opening file: {e}", exc_info=True)
                        continue
            print()  # newline
    except FileNotFoundError:
        logging.error(f"\nError: The directory '{folder_path}' does not exist.", exc_info=True)
    except NotADirectoryError:
        logging.error(f"\nError: The path '{folder_path}' exists but is not a directory.", exc_info=True)
    except PermissionError:
        logging.error(f"\nError: Permission denied to access '{folder_path}'.", exc_info=True)

def load_file(loaded_objects, folder_path, file):
    if not os.path.isabs(folder_path):
        folder_path = os.path.abspath(folder_path)
    file_path = folder_path + '/' + file
    try:
        with open(file_path, 'r') as f:
            try:
                content = f.read()
            except (MemoryError, UnicodeDecodeError) as e:
                logging.error(f"\nError while reading file: {e}", exc_info=True)
            try:    
                selector = ElementTree.fromstring(content)
                diagram = Diagram(selector)
                file_without_ext = os.path.splitext(file)[0]
                if file_without_ext in loaded_objects.keys():
                    print(f"Diagram `{file_without_ext}` has already been loaded.\n")
                else:
                    loaded_objects[file_without_ext] = diagram
                    print(f"Diagram `{file_without_ext}` was successfully loaded.\n")
            except (TypeError, ParseError) as e:
                logging.error(f"\nWrong xml syntax: {e}", exc_info=True)
    except FileNotFoundError:
        logging.error(f"\nError: The directory '{folder_path}' does not exist.", exc_info=True)
        print(f"Error loading file `{file}`. Invalid filename or file not found.\n")
    except PermissionError:
        logging.error(f"\nError: Permission denied to access '{folder_path}'.", exc_info=True)

def search(loaded_objects, option):
    found_diagrams = []
    NEWLINE = '\n'  # to avoid error when using a backslash inside curly braces
    if option == 5.1:
        obj_type = input('Enter the diagram type: ')
        for key in loaded_objects.keys():
            for obj in loaded_objects[key].objects:
                if obj.name == obj_type:
                    found_diagrams.append(key)
                    break
        num_of_found_diagrams = len(found_diagrams)
        found_diagrams_str = ':' + NEWLINE + NEWLINE.join(diagram for diagram in found_diagrams) + NEWLINE
        print(
            f"Found {num_of_found_diagrams} diagram(s)"
            f"{found_diagrams_str if num_of_found_diagrams > 0 else NEWLINE}"
        )
    else:
        while True:
            # sentinel value not to repeat propmts in case of error
            # min_width = max_width = min_height = max_height = None
            try:
                min_width = int(input('Min width (enter blank for zero): ') or 0)
                if min_width >= 0:
                    break
            except ValueError:
                print('Please enter an integer greater than or equal to zero.')

        while True:
            try:
                max_width = int(input('Max width (enter blank for max): ') or Diagram.max_width)
                if int(max_width) >= 0:
                    break
            except ValueError:
                print('Please enter an integer greater than or equal to zero.')

        while True:
            try:
                min_height = int(input('Min height (enter blank for zero): ') or 0)
                if min_width >= 0:
                    break
            except ValueError:
                print('Please enter an integer greater than or equal to zero.')

        while True:
            try:
                max_height = int(input('Max height (enter blank for max): ') or Diagram.max_height)
                if int(max_width) >= 0:
                    break
            except ValueError:
                print('Please enter an integer greater than or equal to zero.')

        while True:
            difficult = input('Difficult (yes/no/All): ').lower()
            if difficult == '' or difficult == 'a' or difficult == 'all':
                difficult = 'all'
                break
            elif difficult == 'n' or difficult == 'no':
                difficult = False
                break
            elif difficult == 'y' or difficult == 'yes':
                difficult = True
                break

        while True:
            truncated = input('Truncated (yes/no/All): ').lower()
            if truncated == '' or truncated == 'a' or truncated == 'all':
                truncated = 'all'
                break
            elif truncated == 'n' or truncated == 'no':
                truncated = False
                break
            elif truncated == 'y' or truncated == 'yes':
                truncated = True
                break

        for key in loaded_objects.keys():
            diagram = loaded_objects[key]
            width = diagram.size[0]
            height = diagram.size[1]
            if width >= min_width and width <= max_width and height >= min_height and height <= max_height:
                found_difficult = False
                for obj in loaded_objects[key].objects:
                    if obj.difficult is True:
                        found_difficult = True
                        break
                found_truncated = False
                for obj in loaded_objects[key].objects:
                    if obj.truncated is True:
                        found_truncated = True
                        break
                # the Cartesian product of 2 variables with 3 possible inputs is 9; thus 9 possible case to handle
                if difficult == 'all' and truncated == 'all':  # we do not even care about the objects; simply can append if user inputs 'all' for both vars
                    found_diagrams.append(key)
                elif difficult == 'all':  # 'difficult' is insignificant in this case; the output only depends on 'truncated'
                    if truncated is True and found_truncated is True:
                        found_diagrams.append(key)
                    elif truncated is False and found_truncated is False: 
                        found_diagrams.append(key)
                elif truncated == 'all':  # 'truncated' is insignificant in this case; the output only depends on 'difficult'
                    if difficult is True and found_difficult is True:
                        found_diagrams.append(key)
                    elif difficult is False and found_difficult is False:
                        found_diagrams.append(key)
                elif difficult is True and truncated is False:
                    if found_difficult is True and found_truncated is False:
                        found_diagrams.append(key)
                elif difficult is False and truncated is True:
                    if found_difficult is False and found_truncated is True:
                        found_diagrams.append(key)
                elif difficult is True and truncated is True:
                    if found_difficult is True and found_truncated is True:
                        found_diagrams.append(key)
                elif difficult is False and truncated is False:
                    if found_difficult is False and found_truncated is False:
                        found_diagrams.append(key)
        num_of_found_diagrams = len(found_diagrams)
        found_diagrams_str = ':' + NEWLINE + NEWLINE.join(diagram for diagram in found_diagrams) + NEWLINE
        print(
            f"Found {num_of_found_diagrams} diagram(s)"
            f"{found_diagrams_str if num_of_found_diagrams > 0 else NEWLINE}"
        )

def main():
    loaded_objects = {}
    if len(sys.argv) < 2:
        print('Please provide the folder path.')
        sys.exit(1)
    folder_path = sys.argv[1]
    while True:
        try:
            choice = int(input(
            '1. List Current Files\n' +
            '2. List Diagrams\n' +
            '3. Load File\n' +
            '4. DisplayDiagramInfo\n' +
            '5. Search\n' +
            '   5.1. Find by type\n' +
            '   5.2. Find by dimension\n' +
            '6. Statistics\n' +
            '7. Exit\n' + 
            '\nEnter your choice: '
            ))
        except ValueError:
            print('\nPlease enter a number between 1 and 7, inclusive.\n')
            continue
        if choice == 1:
            list_current_files(folder_path)
        elif choice == 2:
            num_of_obj = len(loaded_objects.keys())
            if num_of_obj == 0:
                print('\n0 diagrams loaded.\n')
            else:
                print(f"{num_of_obj} diagrams loaded: {', '.join(loaded_objects.keys())}\n")
        elif choice == 3:
            file = input('\nEnter the filename to load: ')
            load_file(loaded_objects, folder_path, file)
        elif choice == 4:
            diagram_name = input('\nEnter diagram name: ')
            diagram = loaded_objects.get(diagram_name)
            if diagram is None:
                print('Diagram not found.\n')
            else:
                print()  # newline
                print(diagram)
        elif choice == 5:
            while True:
                try:
                    option = float(input('\nEnter 5.1 to search by type or enter 5.2 to search by dimension: '))
                    if option == 5.1 or option == 5.2:
                        break
                except ValueError:
                    continue
            search(loaded_objects, option)
        elif choice == 6:
            print(f"\nNumber of loaded diagrams: {len(loaded_objects)}")
            print(f"Total number of total objects: {Diagram.total_num_of_objects}")
            print(f"Diagram Object Types (list names): {', '.join(Diagram.diagram_object_types)}")
            print(f"Minimum diagram height: {Diagram.min_height}")
            print(f"Maximum diagram height: {Diagram.max_height}")
            print(f"Minimum diagram width: {Diagram.min_width}")
            print(f"Maximum diagram width: {Diagram.max_width}")
            print(f"Minimum object area: {DiagramObject.min_area}")
            print(f"Maximum object area: {DiagramObject.max_area}\n")
        elif choice == 7:
            to_stop = input('\nAre you sure you want to quit the program (yes/No)? ')
            if to_stop.lower() == 'y' or to_stop.lower() == 'yes':
                print('Good bye...')
                break
        else:
            print('Please enter a valid number.\n')

if __name__ == '__main__':
    main()
