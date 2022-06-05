import numpy as np
from stl import mesh
import xml.etree.ElementTree as ET
from madcad.triangulation import *
from string import ascii_lowercase
import os
import vtkplotlib as vpl

HEIGHT = 0.01
PLACE = 'upatras'

def read_data(filename='map.osm'):
    # read xml file from map
    tree = ET.parse(filename)
    root = tree.getroot()

    # keep nodes and buildings (set of nodes)
    nodes = {}
    buildings = {}
    building_ids_with_names = []

    for child in root[1:]:
        if child.tag == 'node':
            nodes[child.attrib['id']] = [float(child.attrib['lon']), float(child.attrib['lat'])]
        elif child.tag == 'way':
            name = None
            tags = []
            for tag in child.findall('tag'):
                tags.append(tag.attrib['k'])
                if tag.attrib['k'] == 'name':
                    name = tag.attrib['v']

            if 'building' not in tags:
                continue
            if name:
                building_ids_with_names.append(child.attrib['id'])
            
            buildings[child.attrib['id']] = [nd.attrib['ref'] for nd in child.findall('nd')]


    def find_maxs_mins():
        xs = [nodes[node_id][0] for node_ids in buildings.values() for node_id in node_ids ]
        ys = [nodes[node_id][1] for node_ids in buildings.values() for node_id in node_ids ]
        return max(xs), min(xs), max(ys), min(ys)

    return (nodes, buildings, building_ids_with_names, ) + find_maxs_mins()


def create_plate_meshes(buildings, nodes, max_x, min_x, max_y, min_y):

    # create plate meshes
    plates = []

    for i, building_id in enumerate(building_ids_with_names):

        # average of points coordinates
        avg_x = 0
        avg_y = 0
        for point_id in buildings[building_id]:
            avg_x += (nodes[point_id][0] - min_x) / (max_x - min_x)
            avg_y += (nodes[point_id][1] - min_y) / (max_y - min_y)
        avg_x /= len(buildings[building_id])
        avg_y /= len(buildings[building_id])

        c = ascii_lowercase[i]
        # get current folder os
        current_dir = os.path.dirname(os.path.realpath(__file__))
        # merge with letters folder
        letters_dir = os.path.join(current_dir, 'letters')

        file = letters_dir + '/' + c + '.stl'
        plate = mesh.Mesh.from_file(file)

        plate.points /= plate.points.max() # move to 0-1
        plate.points /= 50

        plate.translate(np.array([avg_x, avg_y, HEIGHT]))
        plates.append(plate)

    return plates


def create_base_mesh():
    # Create the base mesh
    vertices = np.array([
        [0, 0, 0],
        [0, 1, 0],
        [1, 1, 0],
        [1, 0, 0]])
    faces = np.array([
        [0,1,3],
        [1,2,3]])

    base = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            base.vectors[i][j] = vertices[f[j],:]
        
    return base


def create_building_meshes(buildings, nodes):
    vertices = []
    faces = []

    for point_ids in buildings.values():
        points = [[nodes[point_id][0], nodes[point_id][1]] for point_id in point_ids]

        vertices.append(points[0] + [0])
        vertices.append(points[0] + [HEIGHT])

        for point in points[1:]:
            vertices.append(point + [0])
            vertices.append(point + [HEIGHT])
            index = len(vertices)
            faces += [[index-4,index-3,index-2], [index-3,index-2,index-1]]

    vertices = np.array(vertices)
    faces = np.array(faces)

    for point_ids in buildings.values():
        outline = Wire([ vec3(tuple(x for x in nodes[point_id])+(HEIGHT,)) for point_id in point_ids ])
        triangles = triangulation(outline)
        new_vertices = [[coordinate for coordinate in point] for point in triangles.points]
        new_faces = [[x+len(vertices) for x in face] for face in triangles.faces]

        vertices = np.concatenate((vertices, new_vertices))
        faces = np.concatenate((faces, new_faces))


    # Normalization
    for vertice in vertices:
        vertice[0] = (vertice[0] - min_x) / (max_x - min_x)
        vertice[1] = (vertice[1] - min_y) / (max_y - min_y)


    # Create the buildings mesh
    buildings_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            buildings_mesh.vectors[i][j] = vertices[f[j],:]

    return buildings_mesh


def plot(base_mesh, building_meshes, plate_meshes, base_color="grey", buildings_color="cyan", plates_color="red"):
    vpl.mesh_plot(base_mesh, color=base_color)
    vpl.mesh_plot(building_meshes, color=buildings_color)
    for plate_mesh in plate_meshes:
        vpl.mesh_plot(plate_mesh, color=plates_color)
    vpl.show()


if __name__ == "__main__":

    nodes, buildings, building_ids_with_names, max_x, min_x, max_y, min_y = read_data()

    base_mesh = create_base_mesh()
    building_meshes = create_building_meshes(buildings, nodes)
    plate_meshes = create_plate_meshes(buildings, nodes, max_x, min_x, max_y, min_y)

    plot(base_mesh, building_meshes, plate_meshes)

    combined = mesh.Mesh(np.concatenate([building_meshes.data] + [plate.data for plate in plate_meshes] + [base_mesh.data]))
    combined.save(PLACE + '.stl')
