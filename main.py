from lxml import etree
from PIL import Image, ImageDraw
import sys


def parse_inkml(inkml_file):
    """Parse the InkML file and extract stroke data."""
    tree = etree.parse(inkml_file)
    root = tree.getroot()

    strokes = []
    for trace in root.findall(".//{http://www.w3.org/2003/InkML}trace"):
        points = trace.text.strip().split(",")
        stroke = []
        for point in points:
            # We include t here because the MathWriting dataset includes triplet points
            x, y, t = map(float, point.strip().split())  # Remove t if this line gives an unpacking error
            stroke.append((x, y))
        strokes.append(stroke)
    return strokes


def get_bounding_box(strokes):
    """Get the bounding box of all strokes."""
    all_points = [point for stroke in strokes for point in stroke]
    min_x = min(point[0] for point in all_points)
    max_x = max(point[0] for point in all_points)
    min_y = min(point[1] for point in all_points)
    max_y = max(point[1] for point in all_points)
    return (min_x, min_y, max_x, max_y)


def normalize_strokes(strokes, bounding_box, image_size):
    """Normalize strokes to fit within the image size while preserving aspect ratio."""
    min_x, min_y, max_x, max_y = bounding_box
    width = max_x - min_x
    height = max_y - min_y

    # Avoid division by zero
    if width == 0:
        width = 1
    if height == 0:
        height = 1

    # Calculate aspect ratios
    stroke_aspect_ratio = width / height
    image_aspect_ratio = image_size[0] / image_size[1]

    # Scale strokes while preserving aspect ratio
    normalized_strokes = []
    for stroke in strokes:
        normalized_stroke = []
        for x, y in stroke:
            # Normalize to [0, 1] range
            normalized_x = (x - min_x) / width
            normalized_y = (y - min_y) / height

            # Adjust for aspect ratio
            if stroke_aspect_ratio > image_aspect_ratio:
                # Width is the limiting dimension
                scaled_x = int(normalized_x * (image_size[0] - 1))
                scaled_y = int(normalized_y * (image_size[0] / stroke_aspect_ratio))
            else:
                # Height is the limiting dimension
                scaled_x = int(normalized_x * (image_size[1] * stroke_aspect_ratio))
                scaled_y = int(normalized_y * (image_size[1] - 1))

            normalized_stroke.append((scaled_x, scaled_y))
        normalized_strokes.append(normalized_stroke)
    return normalized_strokes


def draw_strokes(strokes, output_image, image_size=(500, 500)):
    """Draw strokes on an image and save as JPG."""
    # Create a blank white image
    image = Image.new("RGB", image_size, "white")
    draw = ImageDraw.Draw(image)

    # Draw each stroke
    for stroke in strokes:
        for i in range(len(stroke) - 1):
            start = stroke[i]
            end = stroke[i + 1]
            draw.line([start, end], fill="black", width=2)

    # Save the image
    image.save(output_image, "JPEG")


def inkml_to_jpg(inkml_file, output_image, image_size=(500, 500)):
    """Convert an InkML file to a JPG image."""
    strokes = parse_inkml(inkml_file)
    bounding_box = get_bounding_box(strokes)
    normalized_strokes = normalize_strokes(strokes, bounding_box, image_size)
    draw_strokes(normalized_strokes, output_image, image_size)


if __name__ == "__main__":
    input_inkml = sys.argv[1]
    output_path = sys.argv[2]
    
    inkml_to_jpg(input_inkml, output_path)
    print("Conversion complete. Result saved to {}".format(output_path))
