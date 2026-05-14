from google.cloud import vision

async def get_text(
    image_path: str,
)->str:
    client = vision.ImageAnnotatorClient()

    with open(image_path, "rb") as f:
        content = f.read()

    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    text = response.text_annotations[0].description

    return text