import requests
import torch
from PIL import Image
from transformers import AlignProcessor, AlignModel

processor = AlignProcessor.from_pretrained("kakaobrain/align-base")
model = AlignModel.from_pretrained("kakaobrain/align-base")

# image embeddings
# url = "http://images.cocodataset.org/val2017/000000039761.jpg"
url = "https://hips.hearstapps.com/hmg-prod/images/dog-puppy-on-garden-royalty-free-image-1586966191.jpg?crop=0.752xw:1.00xh;0.175xw,0&resize=1200:*"
image = Image.open(requests.get(url, stream=True).raw)

# text embeddings
text1 = "a beige puppy sitting in the grass"
text2 = "a dog sitting in the grass"

image.show()

print(f'Text1: {text1}')
print(f'Text2: {text2}')

inputs = processor(images=image, return_tensors="pt")
image_embeds = model.get_image_features(
    pixel_values=inputs['pixel_values'],
)

inputs = processor(text=text1, return_tensors="pt")
text_embeds1 = model.get_text_features(
    input_ids=inputs['input_ids'],
    attention_mask=inputs['attention_mask'],
    token_type_ids=inputs['token_type_ids'],
)

inputs = processor(text=text2, return_tensors="pt")
text_embeds2 = model.get_text_features(
    input_ids=inputs['input_ids'],
    attention_mask=inputs['attention_mask'],
    token_type_ids=inputs['token_type_ids'],
)


# Print the cosine similarity between the image and text embeddings

sim1 = torch.nn.functional.cosine_similarity(image_embeds, text_embeds1)
sim2 = torch.nn.functional.cosine_similarity(image_embeds, text_embeds2)

print(f'Cosine similarity between the image and text1: {sim1.item()}')
print(f'Cosine similarity between the image and text2: {sim2.item()}')