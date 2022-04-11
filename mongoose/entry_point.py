import click
from pathlib import Path
from mongoose import Mongoose, CNC

@click.group()
def cli():
    pass


@cli.command()
@click.argument("resource_path")
@click.option("--file", is_flag=True)
def test(resource_path, file):
    """
    Just using this function for testing and debugging commands :)
    """
    if file:
        cnc_class = CNC.from_name("FileCNC")
        m = Mongoose(cnc_class(Path(resource_path).resolve()))
    else:
        cnc_class = CNC.from_name("Genmitsu3018CNC")
        m = Mongoose(cnc_class(resource_path))

    with m:
        print(m.grbl_settings)
        print(m.get_work_coordinate_offset())
        print(m.machine_position())
        print(m.work_position())
        m.home()
        m.move_to(42, 56, 78)


@cli.command()
@click.argument("resource_path")
@click.option("--file", is_flag=True)
@click.argument("center", nargs=3, required=True)
@click.argument("radius")
@click.argument("feed")
def circle(resource_path, file, center, radius, feed):
    if file:
        cnc_class = CNC.from_name("FileCNC")
        m = Mongoose(cnc_class(Path(resource_path).resolve()))
    else:
        cnc_class = CNC.from_name("Genmitsu3018CNC")
        m = Mongoose(cnc_class(resource_path))

    with m:
        x, y, z = center
        m.home()
        m.circle(float(x), float(y), float(z), float(radius), float(feed))
        

@cli.command()
@click.argument("resource_path")
@click.option("--file", is_flag=True)
@click.argument("corner", nargs=3, required=True)
@click.argument("side_length")
@click.argument("feed")
def square(resource_path, file, corner, side_length, feed):
    if file:
        cnc_class = CNC.from_name("FileCNC")
        m = Mongoose(cnc_class(Path(resource_path).resolve()))
    else:
        cnc_class = CNC.from_name("Genmitsu3018CNC")
        m = Mongoose(cnc_class(resource_path))
        
    with m:
        x, y, z = corner
        m.square(float(x), float(y), float(z), float(side_length), float(feed))


@cli.command()
@click.argument("resource_path")
@click.option("--file", is_flag=True)
@click.argument("sides")
@click.argument("center", nargs=3, required=True)
@click.argument("radius")
@click.argument("feed")
def polygon(resource_path, file, center, sides, radius, feed):
    if file:
        cnc_class = CNC.from_name("FileCNC")
        m = Mongoose(cnc_class(Path(resource_path).resolve()))
    else:
        cnc_class = CNC.from_name("Genmitsu3018CNC")
        m = Mongoose(cnc_class(resource_path))
        
    with m:
        x, y, z = center
        m.polygon(int(sides), float(x), float(y), float(z), float(radius), float(feed))