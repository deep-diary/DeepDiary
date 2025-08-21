from gradio_tools.tools import StableDiffusionTool
local_file_path = StableDiffusionTool().langchain.run(
    "Please create a photo of a dog riding a skateboard"
)

from PIL import Image
im = Image.open(local_file_path)
from IPython.display import display

display(im)