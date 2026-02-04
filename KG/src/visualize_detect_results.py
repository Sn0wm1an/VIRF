import random

from PIL import Image, ImageDraw, ImageFont


def visualize_detection_results(
    image_path: str, detection_results: list, output_path: str
) -> bool:
    try:
        # Open the original image
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image)

        # Generate colors for different categories
        colors = {}

        # Try to load a font, fallback to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None

        # Draw bounding boxes and labels
        for obj in detection_results:
            label = obj["initial_label"]
            bbox = obj["box_coords"]

            if len(bbox) >= 4:
                x1, y1, x2, y2 = bbox[:4]

                # Generate consistent color for each category
                if label not in colors:
                    colors[label] = (
                        random.randint(50, 255),
                        random.randint(50, 255),
                        random.randint(50, 255),
                    )

                color = colors[label]

                # Draw bounding box
                draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

                # Draw label background
                if font:
                    # Get text size using textbbox (newer PIL) or textsize (older PIL)
                    try:
                        bbox_text = draw.textbbox((x1, y1), label, font=font)
                        text_width = bbox_text[2] - bbox_text[0]
                        text_height = bbox_text[3] - bbox_text[1]
                    except AttributeError:
                        # text_width, text_height = draw.textsize(label, font=font)
                        pass
                else:
                    text_width, text_height = len(label) * 10, 15

                # Draw label background rectangle
                draw.rectangle(
                    [x1, y1 - text_height - 5, x1 + text_width + 10, y1],
                    fill=color,
                    outline=color,
                )

                # Draw label text
                draw.text(
                    (x1 + 5, y1 - text_height - 2), label, fill="white", font=font
                )

        # Save the visualization
        image.save(output_path)
        return True

    except Exception as e:
        print(f"Error visualizing results: {str(e)}")
        return False
