import os

def extract_entities_and_relationships(file_path):
    entities = []
    relationships = []
    in_entities = False
    in_relationships = False

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            stripped_line = line.strip()
            if stripped_line.startswith('Named Entities:'):
                in_entities = True
                in_relationships = False
            elif stripped_line.startswith('Relationships:'):
                in_entities = False
                in_relationships = True
            elif in_entities and stripped_line:  # Check if the line is not empty
                entities.append(stripped_line)
            elif in_relationships and stripped_line:  # Check if the line is not empty
                relationships.append(stripped_line)

    return entities, relationships

def write_output_file(input_file_path, output_dir, entities, relationships):
    base_name = os.path.basename(input_file_path)
    output_file_path = os.path.join(output_dir, base_name)

    with open(output_file_path, 'w', encoding='utf-8') as file:
        # Write entities (you can format them as needed)
        if entities:
            file.write('Named Entities:\n')
            for entity in entities:
                file.write(f'{entity}\n')
            file.write('\n')  # Add a newline for separation

        # Write relationships (you can format them as needed)
        if relationships:
            file.write('Relationships:\n')
            for relationship in relationships:
                file.write(f'{relationship}\n')

def process_input_files(input_dir, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.endswith('.txt'):  # Or whatever file extension you are using
            input_file_path = os.path.join(input_dir, filename)
            entities, relationships = extract_entities_and_relationships(input_file_path)
            write_output_file(input_file_path, output_dir, entities, relationships)

# Example usage:
input_directory = 'output1/'  # Replace with the actual path
output_directory = 'output2/'  # Replace with the actual path
process_input_files(input_directory, output_directory)